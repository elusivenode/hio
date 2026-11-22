"""Build one factor's total-return series from its spec and a pinned snapshot (OD-0213).

The spec names the factor, its series class, its numeraire and its symbol. The snapshot (verified against the
pin and its manifest) supplies raw closes, distributions and splits, and `eodhd_eval.analyse` builds the
periods. This tool recomputes the invariants from those periods, then writes `series.csv` and `build.json`
under `<out>/<factor_id>/<spec version>/<build_id>/`. The command prints counts, ids, hashes and pass or fail
only: never a return, a level or a date from the data.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml

from hio.library.numeric import CTX

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
    return {
        "factor_id": factor_id,
        "version": version,
        "series_class": series_class,
        "numeraire": numeraire,
        "symbol": prefixes.pop(),
        "source_id": sources.pop(),
        "sha256": _sha(raw),
    }


def check_out(out: Path) -> Path:
    resolved = out.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("--out must lie outside the repository")
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


def _build(spec_path, root, snapshot, manifest_sha256, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
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
    dividends = _base._read(root, manifest, symbol, "div")
    splits = _base._read(root, manifest, symbol, "splits")
    listed = _base.quote_currency(_base._read(root, manifest, exchange, "symbols"), symbol)
    series = _base.analyse(symbol, spec["numeraire"], listed, eod, dividends, splits)
    if not series.qualified["Q1"] or not series.qualified["Q2"]:
        raise ValueError("the series did not qualify (Q1 or Q2 failed)")
    if not series.periods:
        raise ValueError("the series has no periods")
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
    series_bytes = render_series(series.periods)
    code = commit if commit is not None else _base.code_commit()["commit"]
    build_id = _sha((spec["sha256"] + manifest_hash + code).encode())[:16]
    inputs = sorted(
        ({"path": e["path"], "sha256": e["sha256"]} for e in [*entries.values(), *listing]),
        key=lambda i: i["path"],
    )
    record = {
        "factor_id": spec["factor_id"],
        "spec_version": spec["version"],
        "spec_sha256": spec["sha256"],
        "series_class": spec["series_class"],
        "numeraire": spec["numeraire"],
        "source_id": spec["source_id"],
        "symbol": symbol,
        "snapshot": snapshot,
        "snapshot_manifest_sha256": manifest_hash,
        "inputs": inputs,
        "code_commit": code,
        "periods": len(series.periods),
        "first": series.periods[0].start.isoformat(),
        "last": series.periods[-1].end.isoformat(),
        "qualified": {q: bool(series.qualified[q]) for q in ("Q1", "Q2", "Q3")},
        "invariants": invariants,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record, existed = _build(args.spec, args.root, args.snapshot, args.manifest_sha256, args.out, None)
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"factor_id: {record['factor_id']}")
    print(f"build_id: {record['build_id']}")
    print(f"periods: {record['periods']}")
    for name, result in record["invariants"].items():
        print(f"{name}: {'pass' if result['passed'] else 'fail'} ({result['checked']} checked)")
    print(f"series_sha256: {record['series_sha256']}")
    if existed:
        print("already built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
