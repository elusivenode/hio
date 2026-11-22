"""Build the reconstructed AUD cash series as a total-return build (OD-0216).

The levels are E-0003's: HIO's ACT/365 accrual of the RBA's historical overnight rate up to the first level of
the RBA Cash Rate Total Return Index, then the index by level, scaled to continue the accrual
(`tools/e0003_extended.py`: `accrue`, `joined_levels`). Each pair of consecutive level dates is one period,
`total_return = level_b / level_a - 1`; cash earns income only, so `income_return = total_return` and
`price_return = 0`. The index chains from 1 at the first date.

Reads the historical rate extract (`<history>/firmmcrid.csv` with `extract-manifest.json`) and the captured
RBA F1 receipt (`<f1>/raw/rba_f1.csv` with `raw/manifest.json`), each pinned by sha256.
Writes `series.csv` and `build.json` under `<out>/<factor_id>/<spec version>/<build_id>/`.
The command prints counts, ids, hashes and pass or fail only: never a return, a rate, a level or a date.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml

from hio.library.numeric import CTX

_HERE = Path(__file__).resolve().parent


def _load(name: str, alias: str):
    """Load a sibling tool. Siblings import each other by bare name, so `tools/` goes on `sys.path`."""
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    spec = importlib.util.spec_from_file_location(alias, _HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


_fb = _load("factor_build", "factor_build_for_factor_cash_aud")
_ext = _load("e0003_extended", "e0003_extended_for_factor_cash_aud")
_cash = _load("e0003_aud_cash", "e0003_aud_cash_for_factor_cash_aud")

REPO = _fb.REPO
HEADER = _fb.HEADER
TOLERANCE = _fb.TOLERANCE
ONE = Decimal(1)
ZERO = Decimal(0)
INVARIANTS = ("RA-INV-001", "index_chain", "level_ratio", "seam", "non_negative_before_seam")
_sha = _fb._sha
_fmt = _fb._fmt
check_out = _fb.check_out


def read_spec(path: Path) -> dict:
    """The facts this build needs from the cash spec, refusing anything outside its scope."""
    raw = Path(path).read_bytes()
    spec = yaml.safe_load(raw)
    try:
        factor_id = str(spec["identity"]["factor_id"])
        version = str(spec["identity"]["version"])
        series_class = spec["classification"]["series_class"]
        numeraire = str(spec["return_convention"]["numeraire"])
        observations = [(str(o["series_id"]), str(o["source_id"])) for o in spec["observations"]]
    except (KeyError, TypeError):
        raise ValueError(
            "the spec lacks identity, classification, return_convention or observations"
        ) from None
    if series_class != "total_return":
        raise ValueError(f"series_class must be total_return, not {series_class}")
    if numeraire != "AUD":
        raise ValueError(f"numeraire must be AUD, not {numeraire}")
    if not observations:
        raise ValueError("the spec has no observations")
    return {
        "factor_id": factor_id,
        "version": version,
        "series_class": series_class,
        "numeraire": numeraire,
        "source_ids": sorted({s for _i, s in observations}),
        "sha256": _sha(raw),
    }


def _read_pinned(path: Path, pin: str, role: str) -> bytes:
    body = Path(path).read_bytes()
    if _sha(body) != str(pin).lower():
        raise ValueError(f"the {role} file does not match its pin")
    return body


def assemble(history_rates: dict, tri: dict) -> dict:
    """The joined level series: the accrual to the TRI's first date, then the TRI scaled to continue it."""
    start = min(tri)
    before = {d: v for d, v in history_rates.items() if d < start}
    if not before:
        raise ValueError("no historical rate before the first index level")
    levels = _ext.joined_levels(_ext.accrue(before, until=start), tri)
    dates = list(levels)
    if dates != sorted(set(dates)):
        raise ValueError("level dates are not strictly increasing")
    if len(levels) < 2:
        raise ValueError("fewer than two levels")
    if min(levels.values()) <= 0:
        raise ValueError("a level is not positive")
    return levels


def periods_of(levels: dict) -> list[tuple[date, date, Decimal]]:
    return [
        (a, b, CTX.subtract(CTX.divide(levels[b], levels[a]), ONE)) for a, b in itertools.pairwise(levels)
    ]


def render_series(periods) -> bytes:
    lines = [HEADER]
    level = ONE
    for a, b, tr in periods:
        level = CTX.multiply(level, CTX.add(ONE, tr))
        cells = [a.isoformat(), b.isoformat(), _fmt(ZERO), _fmt(tr), _fmt(tr), _fmt(level)]
        lines.append(",".join(cells) + "\n")
    return "".join(lines).encode()


def check_invariants(series_bytes: bytes, levels: dict, tri: dict) -> dict:
    """Recompute each invariant from the written bytes: {name: {"checked", "passed"}}."""
    rows = list(csv.reader(series_bytes.decode().splitlines()[1:]))
    seam = min(tri)
    ra1, chain, previous = True, True, ONE
    for k, (a, b, pr, ir, tr, index) in enumerate(rows):
        pr, ir, tr, index = Decimal(pr), Decimal(ir), Decimal(tr), Decimal(index)
        if abs(CTX.subtract(tr, CTX.add(pr, ir))) > TOLERANCE * max(ONE, abs(tr)):
            ra1 = False
        if b <= a or (k and a != rows[k - 1][1]) or index != CTX.multiply(previous, CTX.add(ONE, tr)):
            chain = False
        previous = index
    ordered = sorted(levels)
    growth = ONE
    for r in rows:
        growth = CTX.multiply(growth, CTX.add(ONE, Decimal(r[4])))
    ratio = CTX.divide(levels[ordered[-1]], levels[ordered[0]])
    level_ratio = bool(rows) and abs(CTX.subtract(growth, ratio)) <= TOLERANCE * abs(ratio)
    from_seam = [r for r in rows if date.fromisoformat(r[0]) >= seam]
    seam_ok = bool(from_seam)
    for r in from_seam:
        theirs = CTX.divide(tri[date.fromisoformat(r[1])], tri[date.fromisoformat(r[0])])
        if abs(CTX.subtract(CTX.add(ONE, Decimal(r[4])), theirs)) > TOLERANCE * abs(theirs):
            seam_ok = False
    negative = sum(1 for r in rows if date.fromisoformat(r[1]) <= seam and Decimal(r[4]) < 0)
    return {
        "RA-INV-001": {"checked": len(rows), "passed": ra1},
        "index_chain": {"checked": len(rows), "passed": chain},
        "level_ratio": {"checked": len(rows), "passed": level_ratio},
        "seam": {"checked": len(from_seam), "passed": seam_ok},
        # recorded, not required: a published negative rate would be real
        "non_negative_before_seam": {
            "checked": len(rows) - len(from_seam),
            "passed": True,
            "negative": negative,
        },
    }


def _build(spec_path, history, f1, history_sha256, f1_sha256, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
    spec = read_spec(Path(spec_path))
    history, f1 = Path(history), Path(f1)
    rate_bytes = _read_pinned(history / "firmmcrid.csv", history_sha256, "historical rate")
    f1_bytes = _read_pinned(f1 / "raw" / "rba_f1.csv", f1_sha256, "F1 receipt")
    receipt = json.loads((f1 / "raw" / "manifest.json").read_bytes())
    if _sha(f1_bytes) != receipt.get("receipt_id"):
        raise ValueError("the F1 receipt does not match its manifest")
    rates = _ext.load_history(history)  # verifies the extract manifest
    tri = _cash.parse_tri(f1_bytes)
    levels = assemble(rates, tri)
    periods = periods_of(levels)
    series_bytes = render_series(periods)
    invariants = check_invariants(series_bytes, levels, tri)
    failed = [name for name, result in invariants.items() if not result["passed"]]
    if failed:
        raise ValueError(f"invariants failed: {', '.join(failed)}")
    seam = min(tri)
    before = sum(1 for _a, b, _r in periods if b <= seam)
    code = commit if commit is not None else _fb._base.code_commit()["commit"]
    history_hash, f1_hash = _sha(rate_bytes), _sha(f1_bytes)
    build_id = _sha((spec["sha256"] + history_hash + f1_hash + code).encode())[:16]
    record = {
        "factor_id": spec["factor_id"],
        "spec_version": spec["version"],
        "spec_sha256": spec["sha256"],
        "series_class": spec["series_class"],
        "numeraire": spec["numeraire"],
        "source_ids": spec["source_ids"],
        "inputs": [
            {"path": "firmmcrid.csv", "sha256": history_hash},
            {"path": "raw/rba_f1.csv", "sha256": f1_hash},
        ],
        "seam_date": seam.isoformat(),
        "periods_before_seam": before,
        "periods_from_seam": len(periods) - before,
        "code_commit": code,
        "periods": len(periods),
        "first": periods[0][0].isoformat(),
        "last": periods[-1][1].isoformat(),
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
    _fb._make_dirs(target)
    _fb._write_new(target / "series.csv", series_bytes)
    _fb._write_new(target / "build.json", record_bytes)
    return record, False


def build(spec_path, history, f1, history_sha256, f1_sha256, out, *, commit=None) -> dict:
    """Build the AUD cash series; returns the build record. Refuses with ValueError."""
    return _build(spec_path, history, f1, history_sha256, f1_sha256, out, commit)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--f1", type=Path, required=True)
    parser.add_argument("--history-sha256", required=True)
    parser.add_argument("--f1-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record, existed = _build(
            args.spec, args.history, args.f1, args.history_sha256, args.f1_sha256, args.out, None
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"factor_id: {record['factor_id']}")
    print(f"build_id: {record['build_id']}")
    print(f"periods: {record['periods']}")
    print(f"periods_before_seam: {record['periods_before_seam']}")
    print(f"periods_from_seam: {record['periods_from_seam']}")
    for name, result in record["invariants"].items():
        print(f"{name}: {'pass' if result['passed'] else 'fail'} ({result['checked']} checked)")
    print(f"series_sha256: {record['series_sha256']}")
    if existed:
        print("already built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
