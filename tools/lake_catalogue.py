"""Lake catalogue: a rebuildable DuckDB index over the bronze, silver and gold layers (OD-0231).

Files are the record and the catalogue is a disposable index: `build` reads the three layers, verifies every
file against its manifest, and writes one fresh DuckDB file (a temporary file, then replace). `verify` does
the same reading and writes nothing. See docs/decisions/local-data-layers-proposal.md.

Layouts read:
- bronze: `<root>/raw/<snapshot>/manifest.json`, whose `files` list holds paths relative to the root. A
  snapshot's identity is the sha256 of its manifest file.
- silver: `<silver_root>/<instrument>/<silver_id>/manifest.json` and its three CSV files.
- gold: `<gold_root>/<factor_id>/<spec_version>/<build_id>/` with `build.json` and `series.csv`.

A bundle with a problem (unparseable JSON, a missing or changed file, a directory name that disagrees with
its record, a row count that disagrees) is reported once, in the `problem` table (its first problem only), and
appears in no other table. Roots may be absent or empty. `parent_present` in `lineage` says whether a gold,
silver or bronze parent is itself a good bundle in this catalogue; it is NULL for a `file` parent.

Choices where the contract is silent: lineage roles for silver and bronze parents are `silver` and `bronze`;
`first`, `last`, `stopped`, `retrieved_at` and `request` are kept as text (a non-string JSON value as its
canonical JSON); no `gold_latest_series` view is defined, because "latest" has no meaning here; a snapshot
whose manifest hash is already loaded from an earlier root is the same snapshot and is loaded once.

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
SILVER_SCHEMA = "hio.silver/1"
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
    "problem": "layer VARCHAR, id VARCHAR, path VARCHAR, problem VARCHAR",
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


def _gold_lineage(record: dict) -> list[tuple[str, str, str]]:
    """The (parent_kind, parent_id, role) triples of one gold record."""
    parents: list[tuple[str, str, str]] = []
    silver = record.get("silver")
    if silver is not None:
        if not isinstance(silver, dict):
            raise ValueError("silver is not an object")
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


def _scan(bronze_roots, silver_root, gold_root) -> dict[str, list[tuple]]:
    tables: dict[str, list[tuple]] = {name: [] for name in TABLES}
    problems = tables["problem"]
    seen = {"bronze": set(), "silver": set(), "gold": set()}
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
        for instrument_dir in _subdirs(silver_root):
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

    present = {"bronze": seen["bronze"], "silver": seen["silver"], "gold": seen["gold"]}
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


def verify(bronze_roots, silver_root, gold_root) -> dict:
    """Read and verify the three layers; writes nothing. Refuses with ValueError."""
    return _report(_scan(bronze_roots, silver_root, gold_root))


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


def build(bronze_roots, silver_root, gold_root, out) -> dict:
    """Write a fresh catalogue to `out` (atomically; an existing catalogue is replaced) and return the report.
    Bundles with a problem are reported and left out. Refuses with ValueError."""
    out = _check_out(out)
    tables = _scan(bronze_roots, silver_root, gold_root)
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
    finally:
        con.close()
    os.chmod(tmp, 0o600)
    os.replace(tmp, out)
    wal.unlink(missing_ok=True)
    return _report(tables)


def _print(report: dict) -> None:
    for name, count in report["counts"].items():
        print(f"{name}: {count}")
    print(f"problems: {report['problems']}")
    print(report["result"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--bronze-root", type=Path, action="append", default=[])
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--gold-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        roots = (args.bronze_root, args.silver_root, args.gold_root)
        if args.command == "build":
            if args.out is None:
                raise ValueError("--out is required with build")
            report = build(*roots, args.out)
        else:
            if args.out is not None:
                raise ValueError("--out is not valid with verify")
            report = verify(*roots)
    except (ValueError, OSError, duckdb.Error) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    _print(report)
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
