"""Lake catalogue: a rebuildable DuckDB index over the bronze, silver and gold layers (OD-0231).

Files are the record and the catalogue is a disposable index: `build` reads the three layers, verifies every
file against its manifest, and writes one fresh DuckDB file (a temporary file, then replace). `verify` does
the same reading and writes nothing. See docs/decisions/local-data-layers-proposal.md.

Layouts read:
- bronze: `<root>/raw/<snapshot>/manifest.json`, whose `files` list holds paths relative to the root. A
  snapshot's identity is the sha256 of its manifest file.
- silver: `<silver_root>/<instrument>/<silver_id>/manifest.json` and its three CSV files (version 1), and
  `<silver_root>/v2/<release_id>/` (version 2; contract: docs/decisions/silver-v2-contract.md §6), each
  checked with `hio.contracts.silver.verify_release`. The directory `v2` is never an instrument.
- gold: `<gold_root>/<factor_id>/<spec_version>/<build_id>/` with `build.json` and `series.csv`.

A bundle with a problem (unparseable JSON, a missing or changed file, a directory name that disagrees with
its record, a row count that disagrees) is reported once, in the `problem` table (its first problem only), and
appears in no other table. Roots may be absent or empty. `parent_present` in `lineage` says whether a gold,
silver or bronze parent is itself a good bundle in this catalogue; it is NULL for a `file` parent.

Choices where the contract is silent: lineage roles for silver and bronze parents are `silver` and `bronze`;
`first`, `last`, `stopped`, `retrieved_at` and `request` are kept as text (a non-string JSON value as its
canonical JSON); no `gold_latest_series` view is defined, because "latest" has no meaning here; a snapshot
whose manifest hash is already loaded from an earlier root is the same snapshot and is loaded once.

Version 2 adds `silver2_release`, `silver2_selection`, `silver2_selection_row`, an `s2_<name>` table (every
cell text, led by `release_id`) for each silver version 2 table, and the views `s2_bar` and `s2_distribution`.
A release is `silver2` in `lineage` (its parents are its snapshots, role `bronze`); a gold record whose
`silver` holds a `release_id` has a `silver2` parent (role `silver2`). An empty cell stays the empty string.

Gold marts (OD-0233; contract: docs/decisions/gold-marts-contract.md §3) add the option `--mart-root`: a
directory of `<kind>/<build_id>/` bundles, each checked with `hio.contracts.gold.verify_bundle` (through
`open_bundle`). They add `gold_bundle` (one row per bundle, with its recipe as canonical JSON), a `g_<table>`
for every table of every kind (all text; the rows of every bundle of that kind) and the views
`g_panel_return` and `g_portfolio_return` (numbers beside the text; the panel view also has the member's
`factor_id`). The kinds `covariance` and `risk_contribution` (contract §6a, OD-0234) load the same way, a
risk bundle with its two mart parents (roles `covariance` and `portfolio`); `gold_bundle.environment_json` is
a float kind's `environment` as canonical JSON and the empty string for the decimal kinds. The view
`g_covariance` is the fact with `covariance_value` and `correlation_value` and its window's kind, span and
count; the view `g_risk_contribution` is the fact with numeric columns, its window's portfolio risk (text and
`_value`) and, through the lineage role `covariance`, the window's kind, span and count. A bundle is `mart`
in `lineage` (layer `mart` in `problem`): a `factor_series` parent is
`gold` (the factor build id), a bundle parent is `mart` (its build id), the role is the parent's. The mart
root may be absent or empty. The CLI prints the mart tables' counts only when `--mart-root` is given.

The CLI prints counts per table, the number of problems, and `pass` or `fail`: never a value from the data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import sys
from datetime import date
from pathlib import Path, PurePosixPath

import duckdb

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from hio.contracts import gold as gold_marts  # noqa: E402
from hio.contracts import silver as silver2  # noqa: E402
from hio.contracts.canonical import canonical_json  # noqa: E402

SILVER_SCHEMA = "hio.silver/1"
SILVER2_DIR = "v2"
SILVER_FILES = ("closes.csv", "distributions.csv", "splits.csv")
GOLD_REQUIRED = (
    "factor_id",
    "spec_version",
    "build_id",
    "series_class",
    "numeraire",
    "spec_sha256",
    "code_commit",
    "periods",
    "first",
    "last",
    "series_sha256",
)
SILVER_REQUIRED = (
    "schema",
    "instrument",
    "quote_currency",
    "source_id",
    "observation_spec",
    "snapshot",
    "snapshot_manifest_sha256",
    "code_commit",
    "files",
    "first",
    "last",
    "silver_id",
)
TABLES = {
    "bronze_snapshot": (
        "snapshot_manifest_sha256 VARCHAR, snapshot VARCHAR, source_id VARCHAR, code_commit VARCHAR, "
        "stopped VARCHAR, directory VARCHAR"
    ),
    "bronze_file": (
        "snapshot_manifest_sha256 VARCHAR, path VARCHAR, sha256 VARCHAR, bytes BIGINT, kind VARCHAR, "
        "symbol VARCHAR, retrieved_at VARCHAR, request VARCHAR"
    ),
    "silver_set": (
        "silver_id VARCHAR, instrument VARCHAR, quote_currency VARCHAR, source_id VARCHAR, "
        "observation_spec_version VARCHAR, observation_spec_sha256 VARCHAR, snapshot VARCHAR, "
        'snapshot_manifest_sha256 VARCHAR, code_commit VARCHAR, "first" VARCHAR, "last" VARCHAR, '
        "corrections BIGINT, directory VARCHAR, manifest_sha256 VARCHAR"
    ),
    "silver_file": "silver_id VARCHAR, name VARCHAR, sha256 VARCHAR, row_count BIGINT",
    "gold_build": (
        "build_id VARCHAR, factor_id VARCHAR, spec_version VARCHAR, series_class VARCHAR, numeraire VARCHAR, "
        'spec_sha256 VARCHAR, code_commit VARCHAR, periods BIGINT, "first" VARCHAR, "last" VARCHAR, '
        "series_sha256 VARCHAR, input_layer VARCHAR, directory VARCHAR, record_json VARCHAR"
    ),
    "gold_series": (
        "build_id VARCHAR, factor_id VARCHAR, period_start DATE, period_end DATE, measure VARCHAR, "
        "value_text VARCHAR, value DOUBLE"
    ),
    "lineage": (
        "child_kind VARCHAR, child_id VARCHAR, parent_kind VARCHAR, parent_id VARCHAR, role VARCHAR, "
        "parent_present BOOLEAN"
    ),
    "silver2_release": (
        "release_id VARCHAR, release_name VARCHAR, release_version VARCHAR, code_commit VARCHAR, "
        "register_sha256 VARCHAR, directory VARCHAR, core_json VARCHAR"
    ),
    "silver2_selection": 'release_id VARCHAR, selection_id VARCHAR, "name" VARCHAR, "rows" BIGINT',
    "silver2_selection_row": (
        "release_id VARCHAR, selection_id VARCHAR, "
        + ", ".join(f'"{c}" {"BIGINT" if c == "row_index" else "VARCHAR"}' for c in silver2.SELECTION_COLUMNS)
    ),
    # One s2_<name> table for every silver version 2 table: `release_id` and the table's columns, all text.
    **{
        f"s2_{name}": "release_id VARCHAR, " + ", ".join(f'"{c}" VARCHAR' for c in columns)
        for name, columns in silver2.TABLES.items()
    },
    "gold_bundle": (
        "kind VARCHAR, build_id VARCHAR, spec_name VARCHAR, spec_version VARCHAR, spec_sha256 VARCHAR, "
        "code_commit VARCHAR, numeric_policy VARCHAR, payload_sha256 VARCHAR, directory VARCHAR, "
        "recipe_json VARCHAR, environment_json VARCHAR"
    ),
    # One g_<table> for every gold mart table of every kind: the table's columns, all text.
    **{
        f"g_{name}": ", ".join(f'"{c}" VARCHAR' for c in columns)
        for kind_tables in gold_marts.TABLES.values()
        for name, columns in kind_tables.items()
    },
    "problem": "layer VARCHAR, id VARCHAR, path VARCHAR, problem VARCHAR",
}
MART_TABLES = tuple(
    ["gold_bundle", *(f"g_{name}" for kind_tables in gold_marts.TABLES.values() for name in kind_tables)]
)
# Views over the version 2 tables: the fact joined to its dimensions within one release_id, the measures
# also cast to numbers (NULL when the cell is empty or not a number) beside the exact text. A left join keeps
# every fact row, so a view has exactly as many rows as its fact table. A distribution has no listing key, so
# its listing is the one its source symbol maps to.
VIEWS = {
    "s2_bar": (
        'SELECT f.*, TRY_CAST(f."open" AS DOUBLE) AS open_value, TRY_CAST(f.high AS DOUBLE) AS high_value, '
        "TRY_CAST(f.low AS DOUBLE) AS low_value, TRY_CAST(f.close AS DOUBLE) AS close_value, "
        "TRY_CAST(f.volume AS DOUBLE) AS volume_value, "
        "l.instrument_code, l.mic, l.ticker, l.valid_from, l.quote_currency, "
        'i."name", i.issuer_code, i.vehicle_type, i.domicile '
        "FROM s2_fact_listing_bar_day f "
        "LEFT JOIN s2_dim_listing l ON l.release_id = f.release_id AND l.listing_sk = f.listing_sk "
        "LEFT JOIN s2_dim_instrument i ON i.release_id = f.release_id AND i.instrument_sk = f.instrument_sk"
    ),
    "s2_distribution": (
        "SELECT f.*, TRY_CAST(f.amount_unadjusted AS DOUBLE) AS amount_unadjusted_value, "
        "TRY_CAST(f.amount_split_adjusted AS DOUBLE) AS amount_split_adjusted_value, "
        "TRY_CAST(f.franking AS DOUBLE) AS franking_value, "
        "l.instrument_code, l.mic, l.ticker, l.valid_from, l.quote_currency, "
        'i."name", i.issuer_code, i.vehicle_type, i.domicile '
        "FROM s2_fact_distribution_event f "
        "LEFT JOIN s2_dim_series s ON s.release_id = f.release_id AND s.series_sk = f.series_sk "
        "LEFT JOIN s2_source_identity_mapping m ON m.release_id = f.release_id "
        "AND m.source_id = s.source_id AND m.source_symbol = s.source_symbol "
        "LEFT JOIN s2_dim_listing l ON l.release_id = f.release_id AND l.listing_sk = m.listing_sk "
        "LEFT JOIN s2_dim_instrument i ON i.release_id = f.release_id AND i.instrument_sk = f.instrument_sk"
    ),
    # Gold mart views: the numbers beside the exact text (NULL when the cell is empty or not a number). The
    # panel view adds the member's factor_id; a left join keeps every row of the fact table.
    "g_panel_return": (
        'SELECT f.*, TRY_CAST(f."return" AS DOUBLE) AS return_value, '
        "TRY_CAST(f.asset_return AS DOUBLE) AS asset_return_value, "
        "TRY_CAST(f.cash_return AS DOUBLE) AS cash_return_value, m.factor_id "
        "FROM g_fact_panel_return f "
        "LEFT JOIN g_bridge_panel_member m "
        "ON m.panel_build_id = f.panel_build_id AND m.member_code = f.member_code"
    ),
    "g_portfolio_return": (
        "SELECT f.*, TRY_CAST(f.portfolio_return AS DOUBLE) AS portfolio_return_value, "
        "TRY_CAST(f.wealth_index AS DOUBLE) AS wealth_index_value "
        "FROM g_fact_portfolio_return f"
    ),
    # The covariance fact beside its window's kind, span and count (contract §6a). The floats are written as
    # Python's repr, which DuckDB reads back exactly.
    "g_covariance": (
        "SELECT f.*, TRY_CAST(f.covariance AS DOUBLE) AS covariance_value, "
        "TRY_CAST(f.correlation AS DOUBLE) AS correlation_value, "
        "w.window_kind, w.first_period_end, w.last_period_end, w.n_obs "
        "FROM g_fact_covariance f "
        "LEFT JOIN g_dim_window w "
        "ON w.covariance_build_id = f.covariance_build_id AND w.window_id = f.window_id"
    ),
    # The risk fact beside the portfolio's risk in the same window and that window's kind, span and count. A
    # risk bundle's windows are its covariance parent's (lineage role `covariance`), so the window dimension
    # is reached through lineage. A left join keeps every row of the fact table.
    "g_risk_contribution": (
        "SELECT f.*, TRY_CAST(f.weight AS DOUBLE) AS weight_value, "
        "TRY_CAST(f.marginal_contribution AS DOUBLE) AS marginal_contribution_value, "
        "TRY_CAST(f.component_contribution AS DOUBLE) AS component_contribution_value, "
        "TRY_CAST(f.percentage_contribution AS DOUBLE) AS percentage_contribution_value, "
        "p.portfolio_variance, p.portfolio_volatility, p.diversification_ratio, p.euler_relative_gap, "
        "TRY_CAST(p.portfolio_variance AS DOUBLE) AS portfolio_variance_value, "
        "TRY_CAST(p.portfolio_volatility AS DOUBLE) AS portfolio_volatility_value, "
        "TRY_CAST(p.diversification_ratio AS DOUBLE) AS diversification_ratio_value, "
        "TRY_CAST(p.euler_relative_gap AS DOUBLE) AS euler_relative_gap_value, "
        "l.parent_id AS covariance_build_id, "
        "w.window_kind, w.first_period_end, w.last_period_end, w.n_obs "
        "FROM g_fact_risk_contribution f "
        "LEFT JOIN g_fact_portfolio_risk p "
        "ON p.risk_build_id = f.risk_build_id AND p.window_id = f.window_id "
        "LEFT JOIN lineage l ON l.child_kind = 'mart' AND l.child_id = f.risk_build_id "
        "AND l.role = 'covariance' "
        "LEFT JOIN g_dim_window w ON w.covariance_build_id = l.parent_id AND w.window_id = f.window_id"
    ),
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value):
    """None stays NULL, a string stays as it is, anything else becomes its canonical JSON."""
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def _json_object(raw: bytes, what: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except ValueError as exc:  # includes UnicodeDecodeError and JSONDecodeError
        raise ValueError(f"{what} is not parseable JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{what} is not a JSON object")
    return value


def _require(record: dict, keys: tuple[str, ...], what: str) -> None:
    missing = [k for k in keys if k not in record]
    if missing:
        raise ValueError(f"{what} lacks {', '.join(missing)}")


def _need_str(value, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} is not a non-empty string")
    return value


def _checked_file(base: Path, rel: str, sha256: str, what: str) -> None:
    pure = PurePosixPath(rel)
    if not rel or pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"{what}: unsafe path")
    target = base / pure
    root = base.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"{what}: path leaves its root")
    if not target.is_file():
        raise ValueError(f"{what}: file missing")
    if _sha_file(target) != sha256:
        raise ValueError(f"{what}: sha256 differs from the manifest")


def _subdirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(p for p in path.iterdir() if p.is_dir())


def _load_bronze(snap_dir: Path, root: Path) -> dict:
    manifest_path = snap_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("manifest.json missing")
    raw = manifest_path.read_bytes()
    manifest = _json_object(raw, "manifest.json")
    _require(manifest, ("snapshot", "source_id", "code_commit", "stopped", "files"), "manifest")
    if manifest["snapshot"] != snap_dir.name:
        raise ValueError("directory name disagrees with the manifest's snapshot")
    if not isinstance(manifest["files"], list):
        raise ValueError("manifest files is not a list")
    identity = _sha_bytes(raw)
    files = []
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ValueError("manifest file entry is not an object")
        path = _need_str(entry.get("path"), "file path")
        sha = _need_str(entry.get("sha256"), "file sha256")
        size = entry.get("bytes")
        if size is not None and (isinstance(size, bool) or not isinstance(size, int)):
            raise ValueError("file bytes is not an integer")
        _checked_file(root, path, sha, f"file {path}")
        files.append(
            (
                identity,
                path,
                sha,
                size,
                _text(entry.get("kind")),
                _text(entry.get("symbol")),
                _text(entry.get("retrieved_at")),
                _text(entry.get("request")),
            )
        )
    snapshot = (
        identity,
        snap_dir.name,
        _text(manifest["source_id"]),
        _text(manifest["code_commit"]),
        _text(manifest["stopped"]),
        str(snap_dir),
    )
    return {"id": identity, "snapshot": snapshot, "files": files}


def _load_silver(set_dir: Path, instrument: str) -> dict:
    manifest_path = set_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("manifest.json missing")
    raw = manifest_path.read_bytes()
    manifest = _json_object(raw, "manifest.json")
    _require(manifest, SILVER_REQUIRED, "manifest")
    if manifest["schema"] != SILVER_SCHEMA:
        raise ValueError("manifest schema is not hio.silver/1")
    silver_id = _need_str(manifest["silver_id"], "silver_id")
    if silver_id != set_dir.name:
        raise ValueError("directory name disagrees with the manifest's silver_id")
    if manifest["instrument"] != instrument:
        raise ValueError("instrument directory disagrees with the manifest's instrument")
    spec = manifest["observation_spec"]
    if not isinstance(spec, dict) or "version" not in spec or "sha256" not in spec:
        raise ValueError("observation_spec lacks version or sha256")
    snapshot_sha = _need_str(manifest["snapshot_manifest_sha256"], "snapshot_manifest_sha256")
    files = manifest["files"]
    if not isinstance(files, dict) or any(name not in files for name in SILVER_FILES):
        raise ValueError("manifest files lacks one of the three CSV files")
    corrections = manifest.get("corrections", [])
    if not isinstance(corrections, list):
        raise ValueError("corrections is not a list")
    file_rows = []
    for name in SILVER_FILES:
        entry = files[name]
        if not isinstance(entry, dict):
            raise ValueError(f"files entry for {name} is not an object")
        sha = _need_str(entry.get("sha256"), f"{name} sha256")
        rows = entry.get("rows")
        if rows is not None and (isinstance(rows, bool) or not isinstance(rows, int)):
            raise ValueError(f"{name} rows is not an integer")
        _checked_file(set_dir, name, sha, name)
        file_rows.append((silver_id, name, sha, rows))
    row = (
        silver_id,
        instrument,
        _text(manifest["quote_currency"]),
        _text(manifest["source_id"]),
        _text(spec["version"]),
        _text(spec["sha256"]),
        _text(manifest["snapshot"]),
        snapshot_sha,
        _text(manifest["code_commit"]),
        _text(manifest["first"]),
        _text(manifest["last"]),
        len(corrections),
        str(set_dir),
        _sha_bytes(raw),
    )
    return {
        "id": silver_id,
        "set": row,
        "files": file_rows,
        "lineage": [("silver", silver_id, "bronze", snapshot_sha, "bronze")],
    }


def _load_silver2(release_dir: Path) -> dict:
    """One silver version 2 release: verified by `hio.contracts.silver.verify_release`, then read once more
    (each file checked against the hash in the manifest core) into the `s2_` rows."""
    core = silver2.verify_release(release_dir)
    rid = silver2.release_id(core)
    tables: dict[str, list[tuple]] = {}
    for entry in core["tables"]:
        name = entry["name"]
        data = (release_dir / "tables" / f"{name}.csv").read_bytes()
        if _sha_bytes(data) != entry["file_sha256"]:
            raise ValueError(f"table {name}: file sha256 differs from the manifest")
        columns = silver2.TABLES[name]
        tables[f"s2_{name}"] = [(rid, *(row[c] for c in columns)) for row in silver2.parse_table(name, data)]
    selections, selection_rows = [], []
    for entry in core["selections"]:
        sid = entry["selection_id"]
        data = (release_dir / "selections" / f"{sid}.csv").read_bytes()
        if _sha_bytes(data) != entry["file_sha256"]:
            raise ValueError(f"selection {sid}: file sha256 differs from the manifest")
        selections.append((rid, sid, entry["name"], entry["rows"]))
        for row in silver2.parse_selection(data):
            if not row["row_index"].isascii() or not row["row_index"].isdigit():
                raise ValueError(f"selection {sid}: row_index is not an unsigned integer")
            selection_rows.append(
                (rid, sid, *(int(row[c]) if c == "row_index" else row[c] for c in silver2.SELECTION_COLUMNS))
            )
    spec = core["release_spec"]
    release = (
        rid,
        _text(spec["name"]),
        _text(spec["version"]),
        _text(core["code_commit"]),
        core["register_sha256"],
        str(release_dir),
        canonical_json(core).decode("utf-8"),
    )
    parents = list(dict.fromkeys(entry["manifest_sha256"] for entry in core["snapshots"]))
    return {
        "id": rid,
        "release": release,
        "selections": selections,
        "selection_rows": selection_rows,
        "tables": tables,
        "lineage": [("silver2", rid, "bronze", parent, "bronze") for parent in parents],
    }


def _gold_lineage(record: dict) -> list[tuple[str, str, str]]:
    """The (parent_kind, parent_id, role) triples of one gold record."""
    parents: list[tuple[str, str, str]] = []
    silver = record.get("silver")
    if silver is not None:
        if not isinstance(silver, dict):
            raise ValueError("silver is not an object")
        if "release_id" in silver:
            parents.append(("silver2", _need_str(silver["release_id"], "silver.release_id"), "silver2"))
        if "release_id" not in silver or "silver_id" in silver:
            parents.append(("silver", _need_str(silver.get("silver_id"), "silver.silver_id"), "silver"))
    elif "snapshot_manifest_sha256" in record:
        parents.append(
            ("bronze", _need_str(record["snapshot_manifest_sha256"], "snapshot_manifest_sha256"), "bronze")
        )
    for leg in ("asset_leg", "cash_leg"):
        if leg in record:
            ref = record[leg]
            if not isinstance(ref, dict):
                raise ValueError(f"{leg} is not an object")
            parents.append(("gold", _need_str(ref.get("build_id"), f"{leg}.build_id"), leg))
    if "inputs" in record:
        inputs = record["inputs"]
        if not isinstance(inputs, list) or not all(isinstance(i, dict) for i in inputs):
            raise ValueError("inputs is not a list of objects")
        for item in inputs:
            if "build_id" in item:
                role = item.get("role", "input")
                parents.append(
                    ("gold", _need_str(item["build_id"], "inputs build_id"), _need_str(role, "inputs role"))
                )
            elif "path" in item and "sha256" in item:
                parents.append(("file", _need_str(item["sha256"], "inputs sha256"), "input"))
    return list(dict.fromkeys(parents))


def _parse_series(data: bytes, periods: int) -> list[tuple[date, date, list[str], list[str]]]:
    try:
        text = data.decode("utf-8")
        rows = [r for r in csv.reader(io.StringIO(text, newline="")) if r]
    except (ValueError, csv.Error) as exc:
        raise ValueError("series.csv is not parseable") from exc
    if not rows or rows[0][:2] != ["period_start", "period_end"]:
        raise ValueError("series.csv does not start with period_start,period_end")
    header = rows[0]
    body = rows[1:]
    if len(body) != periods:
        raise ValueError("series.csv row count disagrees with periods")
    parsed = []
    for row in body:
        if len(row) != len(header):
            raise ValueError("series.csv row has the wrong number of columns")
        try:
            start, end = date.fromisoformat(row[0]), date.fromisoformat(row[1])
        except ValueError as exc:
            raise ValueError("series.csv has an unparseable period date") from exc
        parsed.append((start, end, header[2:], row[2:]))
    return parsed


def _number(text: str) -> float | None:
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _load_gold(build_dir: Path) -> dict:
    record_path, series_path = build_dir / "build.json", build_dir / "series.csv"
    if not record_path.is_file():
        raise ValueError("build.json missing")
    if not series_path.is_file():
        raise ValueError("series.csv missing")
    record_bytes = record_path.read_bytes()
    record = _json_object(record_bytes, "build.json")
    _require(record, GOLD_REQUIRED, "record")
    named = {
        "factor_id": build_dir.parents[1].name,
        "spec_version": build_dir.parent.name,
        "build_id": build_dir.name,
    }
    for key, directory_name in named.items():
        if str(record[key]) != directory_name:
            raise ValueError(f"directory name disagrees with the record's {key}")
    periods = record["periods"]
    if isinstance(periods, bool) or not isinstance(periods, int):
        raise ValueError("periods is not an integer")
    series_bytes = series_path.read_bytes()
    if _sha_bytes(series_bytes) != record["series_sha256"]:
        raise ValueError("series.csv sha256 differs from the record")
    parsed = _parse_series(series_bytes, periods)
    lineage = [
        ("gold", str(record["build_id"]), kind, pid, role) for kind, pid, role in _gold_lineage(record)
    ]
    build_id, factor_id = str(record["build_id"]), str(record["factor_id"])
    series = [
        (build_id, factor_id, start, end, measure, cell, _number(cell))
        for start, end, measures, cells in parsed
        for measure, cell in zip(measures, cells, strict=True)
    ]
    row = (
        build_id,
        factor_id,
        str(record["spec_version"]),
        _text(record["series_class"]),
        _text(record["numeraire"]),
        _text(record["spec_sha256"]),
        _text(record["code_commit"]),
        periods,
        _text(record["first"]),
        _text(record["last"]),
        _text(record["series_sha256"]),
        _text(record.get("input_layer")),
        str(build_dir),
        record_bytes.decode("utf-8"),
    )
    return {"id": build_id, "build": row, "series": series, "lineage": lineage}


def _load_mart(mart_root: Path, kind: str, bundle_dir: Path) -> dict:
    """One gold mart bundle: verified by `hio.contracts.gold.verify_bundle` (inside `open_bundle`), then each
    table read once more (checked against the manifest) into the `g_` rows."""
    bundle = gold_marts.open_bundle(mart_root, kind, bundle_dir.name)
    recipe = bundle.recipe
    spec = recipe["spec"]
    tables = {
        f"g_{name}": [tuple(row[c] for c in columns) for row in bundle.table(name)]
        for name, columns in gold_marts.TABLES[kind].items()
    }
    lineage = []
    for parent in recipe["parents"]:
        parent_kind = "gold" if parent["kind"] == "factor_series" else "mart"
        lineage.append(("mart", bundle.build_id, parent_kind, parent["id"], parent["role"]))
    row = (
        kind,
        bundle.build_id,
        spec["name"],
        spec["version"],
        spec["sha256"],
        recipe["code_commit"],
        recipe["numeric_policy"],
        bundle.payload_sha256,
        str(bundle_dir),
        canonical_json(recipe).decode("utf-8"),
        # A float kind's environment; empty for the decimal kinds, which have none.
        canonical_json(recipe["environment"]).decode("utf-8") if "environment" in recipe else "",
    )
    return {"id": bundle.build_id, "bundle": row, "tables": tables, "lineage": lineage}


def _scan(bronze_roots, silver_root, gold_root, mart_root=None) -> dict[str, list[tuple]]:
    tables: dict[str, list[tuple]] = {name: [] for name in TABLES}
    problems = tables["problem"]
    seen = {"bronze": set(), "silver": set(), "silver2": set(), "gold": set(), "mart": set()}
    lineage: list[tuple] = []

    for root in bronze_roots or []:
        root = Path(root).expanduser()
        if root.exists() and not root.is_dir():
            raise ValueError("a bronze root is not a directory")
        for snap_dir in _subdirs(root / "raw"):
            try:
                bundle = _load_bronze(snap_dir, root)
            except (ValueError, OSError) as exc:
                problems.append(("bronze", snap_dir.name, str(snap_dir), str(exc)))
                continue
            if bundle["id"] in seen["bronze"]:
                continue
            seen["bronze"].add(bundle["id"])
            tables["bronze_snapshot"].append(bundle["snapshot"])
            tables["bronze_file"].extend(bundle["files"])

    if silver_root is not None:
        silver_root = Path(silver_root).expanduser()
        if silver_root.exists() and not silver_root.is_dir():
            raise ValueError("the silver root is not a directory")
        for release_dir in _subdirs(silver_root / SILVER2_DIR):
            try:
                bundle = _load_silver2(release_dir)
            except (ValueError, OSError) as exc:
                problems.append(("silver2", release_dir.name, str(release_dir), str(exc)))
                continue
            seen["silver2"].add(bundle["id"])
            tables["silver2_release"].append(bundle["release"])
            tables["silver2_selection"].extend(bundle["selections"])
            tables["silver2_selection_row"].extend(bundle["selection_rows"])
            for name, rows in bundle["tables"].items():
                tables[name].extend(rows)
            lineage.extend(bundle["lineage"])
        for instrument_dir in _subdirs(silver_root):
            if instrument_dir.name == SILVER2_DIR:
                continue
            for set_dir in _subdirs(instrument_dir):
                try:
                    bundle = _load_silver(set_dir, instrument_dir.name)
                except (ValueError, OSError) as exc:
                    problems.append(("silver", set_dir.name, str(set_dir), str(exc)))
                    continue
                seen["silver"].add(bundle["id"])
                tables["silver_set"].append(bundle["set"])
                tables["silver_file"].extend(bundle["files"])
                lineage.extend(bundle["lineage"])

    if gold_root is not None:
        gold_root = Path(gold_root).expanduser()
        if gold_root.exists() and not gold_root.is_dir():
            raise ValueError("the gold root is not a directory")
        for factor_dir in _subdirs(gold_root):
            for version_dir in _subdirs(factor_dir):
                for build_dir in _subdirs(version_dir):
                    try:
                        bundle = _load_gold(build_dir)
                        if bundle["id"] in seen["gold"]:
                            raise ValueError("build_id already loaded from another directory")
                    except (ValueError, OSError) as exc:
                        problems.append(("gold", build_dir.name, str(build_dir), str(exc)))
                        continue
                    seen["gold"].add(bundle["id"])
                    tables["gold_build"].append(bundle["build"])
                    tables["gold_series"].extend(bundle["series"])
                    lineage.extend(bundle["lineage"])

    if mart_root is not None:
        mart_root = Path(mart_root).expanduser()
        if mart_root.exists() and not mart_root.is_dir():
            raise ValueError("the mart root is not a directory")
        for kind_dir in _subdirs(mart_root):
            for bundle_dir in _subdirs(kind_dir):
                try:
                    bundle = _load_mart(mart_root, kind_dir.name, bundle_dir)
                except (ValueError, OSError) as exc:
                    problems.append(("mart", bundle_dir.name, str(bundle_dir), str(exc)))
                    continue
                seen["mart"].add(bundle["id"])
                tables["gold_bundle"].append(bundle["bundle"])
                for name, rows in bundle["tables"].items():
                    tables[name].extend(rows)
                lineage.extend(bundle["lineage"])

    present = seen
    for child_kind, child_id, parent_kind, parent_id, role in lineage:
        flag = None if parent_kind == "file" else parent_id in present[parent_kind]
        tables["lineage"].append((child_kind, child_id, parent_kind, parent_id, role, flag))
    for rows in tables.values():
        rows.sort(key=lambda r: tuple("" if v is None else str(v) for v in r))
    return tables


def _report(tables: dict[str, list[tuple]]) -> dict:
    counts = {name: len(rows) for name, rows in tables.items()}
    problems = counts["problem"]
    return {"counts": counts, "problems": problems, "result": "fail" if problems else "pass"}


def verify(bronze_roots, silver_root, gold_root, mart_root=None) -> dict:
    """Read and verify the layers (and the gold marts, when `mart_root` is given); writes nothing. Refuses
    with ValueError."""
    return _report(_scan(bronze_roots, silver_root, gold_root, mart_root))


def _check_out(out: Path) -> Path:
    resolved = Path(out).expanduser().resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--out must lie outside the repository")
    if resolved.is_dir():
        raise ValueError("--out is a directory")
    return resolved


def _mkdir_private(path: Path) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chmod(directory, 0o700)


def _insert(con, table: str, rows: list[tuple]) -> None:
    if not rows:
        return
    marks = "(" + ",".join(["?"] * len(rows[0])) + ")"
    for start in range(0, len(rows), 200):
        chunk = rows[start : start + 200]
        con.execute(
            f"INSERT INTO {table} VALUES " + ",".join([marks] * len(chunk)), [v for r in chunk for v in r]
        )


def build(bronze_roots, silver_root, gold_root, out, mart_root=None) -> dict:
    """Write a fresh catalogue to `out` (atomically; an existing catalogue is replaced) and return the report.
    Bundles with a problem are reported and left out. Refuses with ValueError."""
    out = _check_out(out)
    tables = _scan(bronze_roots, silver_root, gold_root, mart_root)
    _mkdir_private(out.parent)
    tmp = out.with_name(out.name + ".tmp")
    wal = Path(str(tmp) + ".wal")
    for stale in (tmp, wal):
        stale.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    try:
        for name, columns in TABLES.items():
            con.execute(f"CREATE TABLE {name} ({columns})")
            _insert(con, name, tables[name])
        for name, query in VIEWS.items():
            con.execute(f"CREATE VIEW {name} AS {query}")
    finally:
        con.close()
    os.chmod(tmp, 0o600)
    os.replace(tmp, out)
    wal.unlink(missing_ok=True)
    return _report(tables)


def _print(report: dict, show_marts: bool = False) -> None:
    for name, count in report["counts"].items():
        if name in MART_TABLES and not show_marts:
            continue
        print(f"{name}: {count}")
    print(f"problems: {report['problems']}")
    print(report["result"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--bronze-root", type=Path, action="append", default=[])
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--gold-root", type=Path, required=True)
    parser.add_argument("--mart-root", type=Path, default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        roots = (args.bronze_root, args.silver_root, args.gold_root)
        if args.command == "build":
            if args.out is None:
                raise ValueError("--out is required with build")
            report = build(*roots, args.out, mart_root=args.mart_root)
        else:
            if args.out is not None:
                raise ValueError("--out is not valid with verify")
            report = verify(*roots, mart_root=args.mart_root)
    except (ValueError, OSError, duckdb.Error) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    _print(report, show_marts=args.mart_root is not None)
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
