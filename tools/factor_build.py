"""Build one factor's total-return series from its spec and a pinned snapshot (OD-0213).

The spec names the factor, its series class, its numeraire and its symbol. The snapshot (verified against the
pin and its manifest) supplies raw closes, distributions and splits, and `eodhd_eval.analyse` builds the
periods. This tool recomputes the invariants from those periods, then writes `series.csv` and `build.json`
under `<out>/<factor_id>/<spec version>/<build_id>/`. The command prints counts, ids, hashes and pass or fail
only: never a return, a level or a date from the data.

It also runs a distribution plausibility screen (OD-0228) over the periods and the raw distribution
records: D1 against neighbouring distributions, D2 against the price move, D3 for duplicate amounts. The
rules and thresholds are the OD-0228 table, declared before any run. A flag refuses nothing: the build record
carries the thresholds, the counts and the flagged days, and the command prints counts only. `--screen-only`
verifies the pin and the snapshot as a build does, runs the screen and writes no build; `--screen-report`
(with `--screen-only`) writes the screen result to a new private file outside the repository.

A correction lives in the spec, never in the snapshot (OD-0230). A spec may list, at
`construction.source_corrections`, distribution records to exclude (`action: exclude_distribution`, the
only action), each naming its `ex_date`, a `reason` and its `evidence`. The tool removes exactly one
matching record per correction from the distributions it read, before the series is analysed, so the
periods, the invariants and the screen all use the corrected list. A correction that matches no record, or
more than one, refuses. The snapshot files are never written; the build record, a screen-only result and a
screen report carry the applied corrections (the action, the date and the sha256 of the excluded record),
and the command prints their count only.

Silver input mode (OD-0231, `docs/decisions/local-data-layers-proposal.md`). `--silver-root` and
`--silver-id` replace `--root`, `--snapshot` and `--manifest-sha256` (the two sets never mix) for a build
and for `--screen-only`. The tool loads `<silver_root>/<SYMBOL.EXCHANGE>/<silver_id>/manifest.json`,
refuses unless the manifest is this instrument's and this source's, its silver_id is the directory name
and the argument, and each CSV file has its manifest sha256 and the contract's header, then turns the rows
back into the vendor-shaped records and builds as the bronze mode does: the same bytes for the same data.
A factor spec that declares `source_corrections` is refused in this mode: corrections belong to the
observation spec, and the silver manifest records those it applied. The record names the silver set
(`input_layer: "silver"`) and its `build_id` hashes the spec, `silver:<silver_id>` and the code commit.

Silver version 2 input mode (OD-0233, `docs/decisions/silver-v2-contract.md` §5 to §7). `--silver-root`,
`--silver-release` and `--selection` (a selection's name or id) form a third input set; the three sets never
mix, and a partial set is refused with exit 2. The tool opens the release with
`hio.marketdata.silver_reader.open_release` (which verifies the whole release), resolves the selection and
reads the spec's `<SYMBOL>.<EXCHANGE>` through `fund_observations`. It refuses unless the observations'
`source_id` is the spec's, and a spec that declares `source_corrections` is refused as in silver mode. The
observations' rows are turned into vendor-shaped records by the same code the silver mode uses, then the
build is the one shared path. The record has `input_layer: "silver2"`, a `silver` block (`release_id`,
`manifest_sha256`, `selection_id`) and its `build_id` hashes the spec, `silver2:<release_id>:<selection_id>`
and the code commit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml

from hio.library.numeric import CTX
from hio.marketdata.silver_reader import open_release

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("eodhd_eval_for_factor_build", _HERE / "eodhd_eval.py")
_base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _base
_spec.loader.exec_module(_base)

REPO = _base.REPO
HEADER = "period_start,period_end,price_return,income_return,total_return,index\n"
TOLERANCE = Decimal("1e-12")
ONE = Decimal(1)
INVARIANTS = ("RA-INV-001", "index_chain", "RA-INV-020")

# The OD-0228 screen thresholds. Changing one changes the declared rule: it needs a new owner decision.
D1_MIN_YIELD = Decimal("0.005")
D1_MULTIPLE = Decimal(3)
D1_NEIGHBOURS_EACH_SIDE = 4
D1_MIN_NEIGHBOURS = 4
D2_MIN_YIELD = Decimal("0.02")
D2_PRICE_FALL_FRACTION = Decimal("0.5")
D3_MIN_DAYS_APART = 1
D3_MAX_DAYS_APART = 10

CORRECTION_ACTION = "exclude_distribution"  # the only action a spec may declare (OD-0230)
CORRECTION_KEYS = frozenset({"action", "series_id", "ex_date", "reason", "evidence"})


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fmt(x: Decimal) -> str:
    return format(x, "f")


def read_spec(path: Path) -> dict:
    """The facts this build needs from a factor spec, refusing anything outside its scope."""
    raw = path.read_bytes()
    spec = yaml.safe_load(raw)
    try:
        factor_id = str(spec["identity"]["factor_id"])
        version = str(spec["identity"]["version"])
        series_class = spec["classification"]["series_class"]
        numeraire = str(spec["return_convention"]["numeraire"])
        observations = spec["observations"]
    except (KeyError, TypeError):
        raise ValueError(
            "the spec lacks identity, classification, return_convention or observations"
        ) from None
    if series_class != "total_return":
        raise ValueError(f"series_class must be total_return, not {series_class}")
    if not observations:
        raise ValueError("the spec has no observations")
    prefixes = {".".join(str(o["series_id"]).split(".")[:2]) for o in observations}
    if len(prefixes) != 1 or "" in prefixes or any("." not in p for p in prefixes):
        raise ValueError("observations must all name the same <SYMBOL>.<EXCHANGE> prefix")
    sources = {str(o["source_id"]) for o in observations}
    if len(sources) != 1:
        raise ValueError("observations must all have the same source_id")
    symbol = prefixes.pop()
    return {
        "factor_id": factor_id,
        "version": version,
        "series_class": series_class,
        "numeraire": numeraire,
        "symbol": symbol,
        "source_id": sources.pop(),
        "source_corrections": _read_corrections(spec, symbol),
        "sha256": _sha(raw),
    }


def _read_corrections(spec: dict, symbol: str) -> list[dict]:
    """`construction.source_corrections` (OD-0230), validated; `[]` when it or `construction` is absent."""
    construction = spec.get("construction")
    if construction is None:
        return []
    if not isinstance(construction, dict):
        raise ValueError("construction must be a mapping")
    if "source_corrections" not in construction:
        return []
    corrections = construction["source_corrections"]
    if not isinstance(corrections, list) or not all(isinstance(c, dict) for c in corrections):
        raise ValueError("source_corrections must be a list of mappings")
    seen: set[str] = set()
    for correction in corrections:
        if set(correction) != CORRECTION_KEYS:
            raise ValueError(
                f"each correction must have exactly the keys {', '.join(sorted(CORRECTION_KEYS))}"
            )
        if correction["action"] != CORRECTION_ACTION:
            raise ValueError(f"a correction's action must be {CORRECTION_ACTION}")
        series_id = correction["series_id"]
        if not isinstance(series_id, str) or not series_id.startswith(f"{symbol}."):
            raise ValueError(f"a correction's series_id must start with {symbol}.")
        ex_date = correction["ex_date"]
        try:
            valid = isinstance(ex_date, str) and date.fromisoformat(ex_date).isoformat() == ex_date
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("a correction's ex_date must be an ISO date string")
        for key in ("reason", "evidence"):
            if not isinstance(correction[key], str) or not correction[key].strip():
                raise ValueError(f"a correction's {key} must be a non-empty string")
        if ex_date in seen:
            raise ValueError("two corrections share an ex_date")
        seen.add(ex_date)
    return corrections


def apply_corrections(dividends: list[dict], corrections: list[dict]) -> tuple[list[dict], list[dict]]:
    """Remove, for each correction, the one distribution record on its `ex_date` with a positive
    `unadjustedValue`. Returns (kept records in their original order and bytes, the applied list).
    Refuses with ValueError unless exactly one record matches; the message has the count, never an amount."""
    drop: dict[int, dict] = {}
    applied = []
    for correction in corrections:
        ex_date = correction["ex_date"]
        matches = [
            i
            for i, r in enumerate(dividends)
            if str(r.get("date")) == ex_date and _positive_amount(r) is not None
        ]
        if len(matches) != 1:
            raise ValueError(f"a correction must match exactly one distribution record, not {len(matches)}")
        index = matches[0]
        drop[index] = correction
        digest = _sha(json.dumps(dividends[index], sort_keys=True, default=str).encode("utf-8"))
        applied.append({"action": correction["action"], "ex_date": ex_date, "record_sha256": digest})
    kept = [r for i, r in enumerate(dividends) if i not in drop]
    return kept, applied


def check_out(out: Path, option: str = "--out") -> Path:
    resolved = out.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError(f"{option} must lie outside the repository")
    return resolved


def _action_days(days: list[date], records: list[dict], *, keep) -> set[date]:
    """Days carrying an action, by the next-observed-day rule `analyse` uses (an action on an unobserved
    day moves to the first observed day after it). A period has no split factor, so it is derived here."""
    observed = set(days)
    out = set()
    for record in records:
        if not keep(record):
            continue
        day = date.fromisoformat(str(record["date"]))
        if day not in observed:
            later = [d for d in days if d > day]
            if not later:
                continue
            day = later[0]
        out.add(day)
    return out


def check_invariants(
    periods, levels: list[Decimal], split_days: set[date], distribution_days: set[date]
) -> dict:
    """Recompute each invariant from the periods and the written levels: {name: {"checked", "passed"}}."""
    ra1 = True
    for p in periods:
        diff = abs(CTX.subtract(p.total_return, CTX.add(p.price_return, p.income_return)))
        if diff > TOLERANCE * max(ONE, abs(p.total_return)):
            ra1 = False
    chain, previous = True, ONE
    for k, (p, level) in enumerate(zip(periods, levels, strict=True)):
        if p.end <= p.start or (k and p.start != periods[k - 1].end):
            chain = False  # not strictly increasing, or not contiguous
        if level != CTX.multiply(previous, CTX.add(ONE, p.total_return)):
            chain = False
        previous = level
    split_only = [p for p in periods if p.end in split_days and p.end not in distribution_days]
    ra20 = all(p.income_return == 0 for p in split_only)
    return {
        "RA-INV-001": {"checked": len(periods), "passed": ra1},
        "index_chain": {"checked": len(periods), "passed": chain},
        "RA-INV-020": {"checked": len(split_only), "passed": ra20},
    }


def _median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return CTX.divide(CTX.add(ordered[mid - 1], ordered[mid]), Decimal(2))


def _positive_amount(record: dict) -> Decimal | None:
    raw = record.get("unadjustedValue")
    if raw is None:
        return None
    amount = Decimal(str(raw))
    return amount if amount > 0 else None


def screen_distributions(periods, dividends) -> dict:
    """The OD-0228 distribution plausibility screen: pure, exact `Decimal` arithmetic, never refuses.

    A distribution day is a period with income_return > 0; its yield is that income return. D1 compares a
    yield with its nearest distribution days, D2 with the price move, D3 looks for duplicate records."""
    thresholds = {
        "D1_min_yield": str(D1_MIN_YIELD),
        "D1_multiple_of_neighbour_median": str(D1_MULTIPLE),
        "D1_neighbours_each_side": str(D1_NEIGHBOURS_EACH_SIDE),
        "D1_min_neighbours": str(D1_MIN_NEIGHBOURS),
        "D2_min_yield": str(D2_MIN_YIELD),
        "D2_price_fall_fraction_of_yield": str(D2_PRICE_FALL_FRACTION),
        "D3_min_days_apart": str(D3_MIN_DAYS_APART),
        "D3_max_days_apart": str(D3_MAX_DAYS_APART),
    }
    distribution = [p for p in periods if p.income_return > 0]
    yields = [p.income_return for p in distribution]
    rules: dict[date, set[str]] = {}
    d1_checked = 0
    for i, p in enumerate(distribution):
        side = D1_NEIGHBOURS_EACH_SIDE
        neighbours = yields[max(0, i - side) : i] + yields[i + 1 : i + 1 + side]
        if len(neighbours) < D1_MIN_NEIGHBOURS:
            continue
        d1_checked += 1
        median = _median(neighbours)
        if yields[i] >= D1_MIN_YIELD and yields[i] > CTX.multiply(D1_MULTIPLE, median):
            rules.setdefault(p.end, set()).add("D1")
    for p in distribution:
        floor = -CTX.multiply(p.income_return, D2_PRICE_FALL_FRACTION)
        if p.income_return >= D2_MIN_YIELD and p.price_return > floor:
            rules.setdefault(p.end, set()).add("D2")
    days = [periods[0].start, *(p.end for p in periods)] if periods else []
    records = [(r, _positive_amount(r)) for r in dividends]
    positive = [(date.fromisoformat(str(r["date"])), a, r) for r, a in records if a is not None]
    flagged_ids: set[int] = set()
    for i, (day_i, amount_i, _record_i) in enumerate(positive):
        for j in range(i + 1, len(positive)):
            day_j, amount_j, _record_j = positive[j]
            if amount_i == amount_j and D3_MIN_DAYS_APART <= abs((day_i - day_j).days) <= D3_MAX_DAYS_APART:
                flagged_ids.update((i, j))
    d3_flagged = 0
    for i in sorted(flagged_ids):
        landed = _action_days(days, [positive[i][2]], keep=lambda _r: True)
        if not landed:
            continue  # after the last close: ignored
        d3_flagged += 1
        rules.setdefault(next(iter(landed)), set()).add("D3")
    flagged = [{"day": d.isoformat(), "rules": sorted(r)} for d, r in sorted(rules.items())]
    return {
        "thresholds": thresholds,
        "distribution_days": len(distribution),
        "D1": {"checked": d1_checked, "flagged": sum("D1" in r for r in rules.values())},
        "D2": {"checked": len(distribution), "flagged": sum("D2" in r for r in rules.values())},
        "D3": {"checked": len(positive), "flagged": d3_flagged},
        "flagged": flagged,
        "flagged_days": len(flagged),
        "flagged_d1_and_d2": sum({"D1", "D2"} <= r for r in rules.values()),
    }


def index_levels(periods) -> list[Decimal]:
    levels, level = [], ONE
    for p in periods:
        level = CTX.multiply(level, CTX.add(ONE, p.total_return))
        levels.append(level)
    return levels


def render_series(periods) -> bytes:
    lines = [HEADER]
    for p, level in zip(periods, index_levels(periods), strict=True):
        cells = [p.start.isoformat(), p.end.isoformat()]
        cells += [_fmt(x) for x in (p.price_return, p.income_return, p.total_return, level)]
        lines.append(",".join(cells) + "\n")
    return "".join(lines).encode()


def _write_new(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    path.chmod(0o600)


def _make_dirs(target: Path) -> None:
    """Create `target` and any missing parents, each mode 0o700."""
    missing, directory = [], target
    while not directory.exists():
        missing.append(directory)
        directory = directory.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        directory.chmod(0o700)


def _load_pinned(spec_path, root, snapshot, manifest_sha256) -> dict:
    """Verify the pin and the snapshot, then analyse and qualify the series: the part a build and a
    screen-only run share. Refuses with ValueError."""
    root = Path(root)
    spec = read_spec(Path(spec_path))
    manifest_path = _base.snapshot_dir(root, snapshot) / "manifest.json"
    manifest_hash = _sha(manifest_path.read_bytes())
    if manifest_hash != str(manifest_sha256).lower():
        raise ValueError("the snapshot manifest does not match the pin")
    manifest = _base.load_snapshot(root, snapshot)  # verifies every retained file
    symbol = spec["symbol"]
    entries = {}
    for kind in _base.KINDS:
        found = [f for f in manifest["files"] if f["symbol"] == symbol and f["kind"] == kind]
        if not found:
            raise ValueError(f"the snapshot has no {kind} file for the symbol")
        entries[kind] = found[0]
    exchange = f"EXCHANGE.{symbol.rsplit('.', 1)[1]}"
    listing = [f for f in manifest["files"] if f["symbol"] == exchange and f["kind"] == "symbols"]
    if not listing:
        raise ValueError("the snapshot has no exchange symbol list for the symbol")
    eod = _base._read(root, manifest, symbol, "eod")
    dividends, applied = apply_corrections(
        _base._read(root, manifest, symbol, "div"), spec["source_corrections"]
    )
    splits = _base._read(root, manifest, symbol, "splits")
    listed = _base.quote_currency(_base._read(root, manifest, exchange, "symbols"), symbol)
    series = _qualified_series(spec, listed, eod, dividends, splits)
    inputs = sorted(
        ({"path": e["path"], "sha256": e["sha256"]} for e in [*entries.values(), *listing]),
        key=lambda i: i["path"],
    )
    return {
        "spec": spec,
        "series": series,
        "dividends": dividends,
        "splits": splits,
        "source_corrections": applied,
        "input_layer": "bronze",
        "id_basis": manifest_hash,  # the build_id hashes the snapshot manifest's sha256 (unchanged)
        "lineage": {
            "snapshot": snapshot,
            "snapshot_manifest_sha256": manifest_hash,
            "inputs": inputs,
        },
    }


def _qualified_series(spec, listed, eod, dividends, splits):
    """`analyse` the series; refuse unless it qualifies and has periods. Both input layers share this."""
    series = _base.analyse(spec["symbol"], spec["numeraire"], listed, eod, dividends, splits)
    if not series.qualified["Q1"] or not series.qualified["Q2"]:
        raise ValueError("the series did not qualify (Q1 or Q2 failed)")
    if not series.periods:
        raise ValueError("the series has no periods")
    return series


# --- silver mode (OD-0231): the same series built from one silver set instead of a bronze snapshot

SILVER_SCHEMA = "hio.silver/1"
SILVER_ID = re.compile(r"[0-9a-f]{16}")
SILVER_FILES = {  # the contract's exact headers, and the vendor field each column reads back to
    "closes.csv": ("date", "close", "adjusted_close"),
    "distributions.csv": (
        "ex_date",
        "amount",
        "split_adjusted_amount",
        "currency",
        "payment_date",
        "record_date",
        "declaration_date",
        "period",
    ),
    "splits.csv": ("date", "ratio"),
}
SILVER_FIELDS = {
    "closes.csv": ("date", "close", "adjusted_close"),
    "distributions.csv": (
        "date",
        "unadjustedValue",
        "value",
        "currency",
        "paymentDate",
        "recordDate",
        "declarationDate",
        "period",
    ),
    "splits.csv": ("date", "split"),
}
SILVER_NUMBERS = frozenset({"close", "adjusted_close", "unadjustedValue", "value"})  # read back as Decimal


def _silver_records(name: str, data: bytes) -> list[dict]:
    """The rows of one verified silver CSV as the vendor-shaped records `analyse` expects."""
    header = ",".join(SILVER_FILES[name]) + "\n"
    if not data.startswith(header.encode()):
        raise ValueError(f"{name} does not have the contract's header")
    try:
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
    except (UnicodeDecodeError, csv.Error):
        raise ValueError(f"{name} is not readable CSV") from None
    columns = SILVER_FILES[name]
    cells = []
    for row in rows[1:]:
        if len(row) != len(columns):
            raise ValueError(f"{name} has a row with the wrong number of cells")
        cells.append(dict(zip(columns, row, strict=True)))
    return _vendor_records(name, cells)


def _vendor_records(name: str, rows: list[dict[str, str]]) -> list[dict]:
    """Rows keyed by the version 1 column names (text cells) as the vendor-shaped records `analyse` expects:
    an empty cell is None, a number cell is a `Decimal`. The silver 1 and silver 2 modes share this."""
    columns = SILVER_FILES[name]
    records = []
    for row in rows:
        if set(row) != set(columns):
            raise ValueError(f"{name} has a row without exactly the contract's columns")
        record = {}
        for column, field in zip(columns, SILVER_FIELDS[name], strict=True):
            cell = row[column]
            if cell == "":
                record[field] = None
            elif field in SILVER_NUMBERS:
                try:
                    record[field] = Decimal(cell)
                except ArithmeticError:
                    raise ValueError(f"{name} has a number cell that is not a number") from None
            else:
                record[field] = cell
        records.append(record)
    return records


def _silver_manifest(set_dir: Path, symbol: str, source_id: str, silver_id: str) -> tuple[dict, str]:
    """The silver manifest and its sha256, refusing unless it is this spec's, this id's and well formed."""
    path = set_dir / "manifest.json"
    if not path.is_file():
        raise ValueError("no silver set with that silver_id for the spec's instrument")
    raw = path.read_bytes()
    manifest = json.loads(raw)
    try:
        facts = (
            manifest["schema"],
            manifest["instrument"],
            manifest["source_id"],
            manifest["silver_id"],
            manifest["quote_currency"],
            manifest["snapshot"],
            manifest["snapshot_manifest_sha256"],
            manifest["observation_spec"]["sha256"],
        )
        files = {name: manifest["files"][name]["sha256"] for name in SILVER_FILES}
        corrections = manifest["corrections"]
    except (KeyError, TypeError):
        raise ValueError("the silver manifest lacks a required field") from None
    if not isinstance(corrections, list) or not all(isinstance(c, dict) for c in corrections):
        raise ValueError("the silver manifest's corrections must be a list of mappings")
    if not all(isinstance(f, str) for f in (*facts, *files.values())):
        raise ValueError("the silver manifest has a field of the wrong type")
    if facts[0] != SILVER_SCHEMA:
        raise ValueError(f"the silver manifest's schema is not {SILVER_SCHEMA}")
    if facts[1] != symbol:
        raise ValueError("the silver manifest is for a different instrument")
    if facts[2] != source_id:
        raise ValueError("the silver manifest has a different source_id from the spec")
    if facts[3] != silver_id:
        raise ValueError("the silver manifest's silver_id is not its directory name")
    return manifest, _sha(raw)


def _load_silver(spec_path, silver_root, silver_id) -> dict:
    """Verify one silver set against its manifest, rebuild the vendor-shaped records, then analyse and
    qualify the series: what a silver build and a silver screen-only run share. Refuses with ValueError."""
    spec = read_spec(Path(spec_path))
    if spec["source_corrections"]:
        raise ValueError("corrections belong to the observation spec, not the factor spec")
    symbol = spec["symbol"]
    silver_id = str(silver_id)
    if not SILVER_ID.fullmatch(silver_id) or Path(symbol).name != symbol:
        raise ValueError("a silver_id is 16 lowercase hex characters")
    prefix = f"{symbol}/{silver_id}"
    set_dir = Path(silver_root) / symbol / silver_id
    manifest, manifest_hash = _silver_manifest(set_dir, symbol, spec["source_id"], silver_id)
    records, inputs = {}, []
    for name in SILVER_FILES:
        if not (set_dir / name).is_file():
            raise ValueError(f"the silver set has no {name}")
        data = (set_dir / name).read_bytes()
        if _sha(data) != manifest["files"][name]["sha256"]:
            raise ValueError(f"{name} does not match the silver manifest")
        records[name] = _silver_records(name, data)
        inputs.append({"path": f"{prefix}/{name}", "sha256": manifest["files"][name]["sha256"]})
    series = _qualified_series(
        spec,
        manifest["quote_currency"],
        records["closes.csv"],
        records["distributions.csv"],
        records["splits.csv"],
    )
    return {
        "spec": spec,
        "series": series,
        "dividends": records["distributions.csv"],
        "splits": records["splits.csv"],
        "source_corrections": manifest["corrections"],
        "input_layer": "silver",
        "id_basis": f"silver:{silver_id}",
        "lineage": {
            "snapshot": manifest["snapshot"],
            "snapshot_manifest_sha256": manifest["snapshot_manifest_sha256"],
            "inputs": sorted(inputs, key=lambda i: i["path"]),
            "silver": {
                "silver_id": silver_id,
                "manifest_sha256": manifest_hash,
                "observation_spec_sha256": manifest["observation_spec"]["sha256"],
            },
        },
    }


# --- silver version 2 mode (OD-0233): the same series built from one selection of a verified release


def _load_silver2(spec_path, silver_root, release_id, selection) -> dict:
    """Open and verify a silver version 2 release, resolve the selection, read the spec's instrument and
    qualify the series: what a silver 2 build and a silver 2 screen-only run share. Refuses with
    ValueError."""
    spec = read_spec(Path(spec_path))
    if spec["source_corrections"]:
        raise ValueError("corrections belong to the observation spec, not the factor spec")
    release = open_release(silver_root, release_id)  # verifies the whole release
    selection_id = release.selection_id(str(selection))
    observed = release.fund_observations(selection_id, spec["symbol"])
    if observed.source_id != spec["source_id"]:
        raise ValueError("the release's source_id for the instrument differs from the spec's")
    records = {
        "closes.csv": _vendor_records("closes.csv", observed.closes),
        "distributions.csv": _vendor_records("distributions.csv", observed.distributions),
        "splits.csv": _vendor_records("splits.csv", observed.splits),
    }
    series = _qualified_series(
        spec,
        observed.quote_currency,
        records["closes.csv"],
        records["distributions.csv"],
        records["splits.csv"],
    )
    return {
        "spec": spec,
        "series": series,
        "dividends": records["distributions.csv"],
        "splits": records["splits.csv"],
        "source_corrections": observed.corrections,
        "input_layer": "silver2",
        "id_basis": f"silver2:{release.release_id}:{selection_id}",
        "lineage": {
            "snapshot": observed.snapshot_name,
            "snapshot_manifest_sha256": observed.snapshot_id,
            "inputs": [{"path": f"v2/{release.release_id}/manifest.json", "sha256": release.manifest_sha256}],
            "silver": {
                "release_id": release.release_id,
                "manifest_sha256": release.manifest_sha256,
                "selection_id": selection_id,
            },
        },
    }


def _build(spec_path, root, snapshot, manifest_sha256, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
    return _write_build(_load_pinned(spec_path, root, snapshot, manifest_sha256), out, commit)


def _build_silver(spec_path, silver_root, silver_id, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
    return _write_build(_load_silver(spec_path, silver_root, silver_id), out, commit)


def _build_silver2(spec_path, silver_root, release_id, selection, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
    return _write_build(_load_silver2(spec_path, silver_root, release_id, selection), out, commit)


def _write_build(loaded: dict, out: Path, commit) -> tuple[dict, bool]:
    """The qualification-to-bytes path both input layers share: invariants, screen, record, files."""
    spec, series = loaded["spec"], loaded["series"]
    dividends, splits = loaded["dividends"], loaded["splits"]
    symbol = spec["symbol"]
    days = series.days
    split_days = _action_days(days, splits, keep=lambda _r: True)
    distribution_days = _action_days(
        days,
        dividends,
        keep=lambda r: r.get("unadjustedValue") is not None and Decimal(r["unadjustedValue"]) > 0,
    )
    invariants = check_invariants(series.periods, index_levels(series.periods), split_days, distribution_days)
    failed = [name for name, result in invariants.items() if not result["passed"]]
    if failed:
        raise ValueError(f"invariants failed: {', '.join(failed)}")
    screen = screen_distributions(series.periods, dividends)  # a flag never refuses a build
    series_bytes = render_series(series.periods)
    code = commit if commit is not None else _base.code_commit()["commit"]
    build_id = _sha((spec["sha256"] + loaded["id_basis"] + code).encode())[:16]
    record = {
        "factor_id": spec["factor_id"],
        "spec_version": spec["version"],
        "spec_sha256": spec["sha256"],
        "series_class": spec["series_class"],
        "numeraire": spec["numeraire"],
        "source_id": spec["source_id"],
        "symbol": symbol,
        "input_layer": loaded["input_layer"],
        **loaded["lineage"],
        "code_commit": code,
        "periods": len(series.periods),
        "first": series.periods[0].start.isoformat(),
        "last": series.periods[-1].end.isoformat(),
        "qualified": {q: bool(series.qualified[q]) for q in ("Q1", "Q2", "Q3")},
        "invariants": invariants,
        "source_corrections": loaded["source_corrections"],
        "distribution_screen": screen,
        "series_sha256": _sha(series_bytes),
        "build_id": build_id,
    }
    record_bytes = (json.dumps(record, indent=1, sort_keys=True) + "\n").encode()
    target = out / spec["factor_id"] / spec["version"] / build_id
    if target.exists():
        same = (
            (target / "series.csv").is_file()
            and (target / "build.json").is_file()
            and (target / "series.csv").read_bytes() == series_bytes
            and (target / "build.json").read_bytes() == record_bytes
        )
        if not same:
            raise ValueError("the build directory exists with different bytes")
        return record, True
    _make_dirs(target)
    _write_new(target / "series.csv", series_bytes)
    _write_new(target / "build.json", record_bytes)
    return record, False


def build(spec_path, root, snapshot, manifest_sha256, out, *, commit=None) -> dict:
    """Build one factor's series; returns the build record. Refuses with ValueError."""
    return _build(spec_path, root, snapshot, manifest_sha256, out, commit)[0]


def build_silver(spec_path, silver_root, silver_id, out, *, commit=None) -> dict:
    """Build one factor's series from one silver set (OD-0231); returns the build record. The series is
    the bytes the bronze build gives for the same data. Refuses with ValueError."""
    return _build_silver(spec_path, silver_root, silver_id, out, commit)[0]


def build_silver2(spec_path, silver_root, release_id, selection, out, *, commit=None) -> dict:
    """Build one factor's series from one selection of a silver version 2 release (OD-0233); returns the
    build record. The series is the bytes the bronze build gives for the same data. Refuses with
    ValueError."""
    return _build_silver2(spec_path, silver_root, release_id, selection, out, commit)[0]


def _check_report(report):
    if report is None:
        return None
    report = check_out(Path(report).parent, "--screen-report") / Path(report).name
    if report.exists() or report.is_symlink():
        raise ValueError("--screen-report must not exist")
    return report


def _screen_result(loaded: dict, report) -> dict:
    spec, series, lineage = loaded["spec"], loaded["series"], loaded["lineage"]
    result = {
        "factor_id": spec["factor_id"],
        "input_layer": loaded["input_layer"],
        "symbol": spec["symbol"],
        "snapshot": lineage["snapshot"],
        "snapshot_manifest_sha256": lineage["snapshot_manifest_sha256"],
        "periods": len(series.periods),
        "source_corrections": loaded["source_corrections"],
        "distribution_screen": screen_distributions(series.periods, loaded["dividends"]),
    }
    if "silver" in lineage:
        result["silver"] = lineage["silver"]
    if report is not None:
        identity = {k: v for k, v in result.items() if k not in ("periods", "distribution_screen")}
        body = {**result["distribution_screen"], **identity}
        _write_new(report, (json.dumps(body, indent=1, sort_keys=True) + "\n").encode())
    return result


def screen_only(spec_path, root, snapshot, manifest_sha256, report=None) -> dict:
    """Verify the pin and the snapshot as a build does and run the screen; writes no build and runs no git.
    With `report`, writes the screen result as JSON to that new file (mode 0o600). Refuses with ValueError."""
    report = _check_report(report)
    return _screen_result(_load_pinned(spec_path, root, snapshot, manifest_sha256), report)


def screen_only_silver(spec_path, silver_root, silver_id, report=None) -> dict:
    """`screen_only` for a silver set: verifies the set against its manifest, runs the screen, writes no
    build and runs no git. Refuses with ValueError."""
    report = _check_report(report)
    return _screen_result(_load_silver(spec_path, silver_root, silver_id), report)


def screen_only_silver2(spec_path, silver_root, release_id, selection, report=None) -> dict:
    """`screen_only` for a silver version 2 selection: verifies the release, runs the screen, writes no build
    and runs no git. Refuses with ValueError."""
    report = _check_report(report)
    return _screen_result(_load_silver2(spec_path, silver_root, release_id, selection), report)


def _print_screen(screen: dict) -> None:
    """The screen's counts only: never a day, a yield or an amount."""
    for rule in ("D1", "D2", "D3"):
        print(f"{rule}: {screen[rule]['flagged']} flagged ({screen[rule]['checked']} checked)")
    days, both = screen["flagged_days"], screen["flagged_d1_and_d2"]
    print(f"distribution_screen: {days} day(s) flagged, {both} by D1 and D2")


def _input_mode(args) -> tuple[str | None, str | None]:
    """(mode, problem): exactly one complete input set is allowed. bronze is `--root --snapshot
    --manifest-sha256`; silver is `--silver-root --silver-id`; silver2 is `--silver-root --silver-release
    --selection`. Any mixture or partial set gives a problem."""
    bronze = (args.root, args.snapshot, args.manifest_sha256)
    silver2 = (args.silver_release, args.selection)
    has_bronze = any(v is not None for v in bronze)
    has_silver = args.silver_root is not None
    has_id = args.silver_id is not None
    has_silver2 = any(v is not None for v in silver2)
    if has_bronze and (has_silver or has_id or has_silver2):
        return None, "give one input set only: bronze, silver or silver2, never a mixture"
    if has_id and has_silver2:
        return None, "--silver-id and --silver-release/--selection are different input sets: give one"
    if has_bronze:
        if any(v is None for v in bronze):
            return None, "give --root, --snapshot and --manifest-sha256 together"
        return "bronze", None
    if has_id:
        if not has_silver:
            return None, "--silver-root and --silver-id are given together"
        return "silver", None
    if has_silver2:
        if not has_silver or any(v is None for v in silver2):
            return None, "--silver-root, --silver-release and --selection are given together"
        return "silver2", None
    if has_silver:
        return None, "--silver-root needs --silver-id, or --silver-release and --selection"
    return None, (
        "give --root, --snapshot and --manifest-sha256, or --silver-root and --silver-id, "
        "or --silver-root, --silver-release and --selection"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--snapshot")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--silver-root", type=Path)
    parser.add_argument("--silver-id")
    parser.add_argument("--silver-release")
    parser.add_argument("--selection")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--screen-only", action="store_true")
    parser.add_argument("--screen-report", type=Path)
    args = parser.parse_args(argv)
    mode, problem = _input_mode(args)
    if problem is None:
        if args.screen_only and args.out is not None:
            problem = "--out is not valid with --screen-only"
        elif not args.screen_only and args.out is None:
            problem = "--out is required without --screen-only"
        elif args.screen_report is not None and not args.screen_only:
            problem = "--screen-report is valid only with --screen-only"
    if problem:
        print(f"refused: {problem}", file=sys.stderr)
        return 2
    try:
        if args.screen_only:
            if mode == "silver2":
                result = screen_only_silver2(
                    args.spec, args.silver_root, args.silver_release, args.selection, args.screen_report
                )
            elif mode == "silver":
                result = screen_only_silver(args.spec, args.silver_root, args.silver_id, args.screen_report)
            else:
                pin = (args.spec, args.root, args.snapshot, args.manifest_sha256)
                result = screen_only(*pin, args.screen_report)
            print(f"factor_id: {result['factor_id']}")
            print(f"input_layer: {result['input_layer']}")
            print(f"periods: {result['periods']}")
            print(f"source_corrections: {len(result['source_corrections'])} applied")
            _print_screen(result["distribution_screen"])
            return 0
        if mode == "silver2":
            record, existed = _build_silver2(
                args.spec, args.silver_root, args.silver_release, args.selection, args.out, None
            )
        elif mode == "silver":
            record, existed = _build_silver(args.spec, args.silver_root, args.silver_id, args.out, None)
        else:
            record, existed = _build(
                args.spec, args.root, args.snapshot, args.manifest_sha256, args.out, None
            )
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"factor_id: {record['factor_id']}")
    print(f"input_layer: {record['input_layer']}")
    print(f"build_id: {record['build_id']}")
    print(f"periods: {record['periods']}")
    print(f"source_corrections: {len(record['source_corrections'])} applied")
    for name, result in record["invariants"].items():
        print(f"{name}: {'pass' if result['passed'] else 'fail'} ({result['checked']} checked)")
    _print_screen(record["distribution_screen"])
    print(f"series_sha256: {record['series_sha256']}")
    if existed:
        print("already built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
