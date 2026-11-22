"""Build an excess-return series from two built total-return series and an excess spec (OD-0215).

The spec names the excess factor, its numeraire, its cash leg and (in `observations`) the asset leg. The two
legs are `tools/factor_build.py` builds. The common dates are the dates both legs have as a period boundary.
Each leg is compounded exactly (Decimal) between consecutive common dates, `R = prod(1 + total_return) - 1`
over that leg's own periods; nothing is filled. The excess is arithmetic per common period,
`X = R - r` (RA 3.3), and is never chained into an index (RA-INV-016: a cumulative figure compounds each leg
and differences the results). The funded return reconstructs as `r + X` (RA-INV-005).

Writes `series.csv` and `build.json` under `<out>/<factor_id>/<spec version>/<build_id>/`. The command prints
counts, ids, hashes and pass or fail only: never a return, a level or a date from the data.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import sys
from decimal import Decimal
from pathlib import Path

import yaml

from hio.library.numeric import CTX

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("factor_build_for_factor_excess", _HERE / "factor_build.py")
_fb = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _fb
_spec.loader.exec_module(_fb)

REPO = _fb.REPO
HEADER = "period_start,period_end,asset_return,cash_return,excess_return\n"
TOLERANCE = _fb.TOLERANCE
ONE = Decimal(1)
INVARIANTS = ("RA-INV-004", "RA-INV-005", "alignment")
_sha = _fb._sha
_fmt = _fb._fmt
check_out = _fb.check_out


def read_spec(path: Path) -> dict:
    """The facts this build needs from an excess spec, refusing anything outside its scope."""
    raw = Path(path).read_bytes()
    spec = yaml.safe_load(raw)
    try:
        factor_id = str(spec["identity"]["factor_id"])
        version = str(spec["identity"]["version"])
        series_class = spec["classification"]["series_class"]
        numeraire = str(spec["return_convention"]["numeraire"])
        cash_leg = str(spec["return_convention"]["cash_leg"])
        ids = [str(o["series_id"]) for o in spec["observations"]]
    except (KeyError, TypeError):
        raise ValueError(
            "the spec lacks identity, classification, return_convention (numeraire, cash_leg) or observations"
        ) from None
    if series_class != "excess_return":
        raise ValueError(f"series_class must be excess_return, not {series_class}")
    if len(ids) != 2 or len(set(ids)) != 2:
        raise ValueError("observations must name exactly two distinct series ids")
    if cash_leg not in ids:
        raise ValueError("the cash leg must be one of the observation series ids")
    (asset_leg,) = [i for i in ids if i != cash_leg]
    return {
        "factor_id": factor_id,
        "version": version,
        "series_class": series_class,
        "numeraire": numeraire,
        "cash_leg": cash_leg,
        "asset_leg": asset_leg,
        "sha256": _sha(raw),
    }


def load_leg(directory: Path, *, role: str, factor_id: str) -> dict:
    """Read and verify one total-return build; returns its record and parsed periods."""
    directory = Path(directory)
    series_bytes = (directory / "series.csv").read_bytes()
    record = json.loads((directory / "build.json").read_bytes())
    if _sha(series_bytes) != record.get("series_sha256"):
        raise ValueError(f"the {role} leg's series.csv does not hash to its build.json")
    if record.get("series_class") != "total_return":
        raise ValueError(f"the {role} leg's series_class is not total_return")
    invariants = record.get("invariants")
    if not invariants or any(not r.get("passed") for r in invariants.values()):
        raise ValueError(f"the {role} leg has a failed or missing invariant")
    if record.get("factor_id") != factor_id:
        raise ValueError(f"the {role} leg's factor_id is not the one the spec names")
    lines = series_bytes.decode().splitlines()
    header = "period_start,period_end,price_return,income_return,total_return,index"
    if not lines or lines[0] != header:
        raise ValueError(f"the {role} leg's series.csv has an unexpected header")
    periods = []
    for row in csv.reader(lines[1:]):
        periods.append((row[0], row[1], Decimal(row[4]), Decimal(row[5])))
    return {"record": record, "periods": periods}


def _compound(periods: list[tuple], common: list[str]) -> list[Decimal]:
    """The leg's exact compounded return between each pair of consecutive common dates."""
    by_start = {p[0]: p for p in periods}
    out = []
    for lo, hi in itertools.pairwise(common):
        growth, cursor = ONE, lo
        while cursor != hi:
            p = by_start.get(cursor)
            if p is None or p[1] > hi:
                raise ValueError("a leg's periods are not contiguous between common dates")
            growth = CTX.multiply(growth, CTX.add(ONE, p[2]))
            cursor = p[1]
        out.append(CTX.subtract(growth, ONE))
    return out


def render_series(common: list[str], asset: list[Decimal], cash: list[Decimal]) -> bytes:
    lines = [HEADER]
    for (lo, hi), a, c in zip(itertools.pairwise(common), asset, cash, strict=True):
        lines.append(",".join([lo, hi, _fmt(a), _fmt(c), _fmt(CTX.subtract(a, c))]) + "\n")
    return "".join(lines).encode()


def _leg_ratio(leg: dict, first: str, last: str) -> Decimal:
    levels = {leg["periods"][0][0]: ONE}
    levels.update({p[1]: p[3] for p in leg["periods"]})
    return CTX.divide(levels[last], levels[first])


def check_invariants(series_bytes: bytes, legs: dict, cash_leg_id: str) -> dict:
    """Recompute each invariant from the written bytes: {name: {"checked", "passed"}}."""
    rows = list(csv.reader(series_bytes.decode().splitlines()[1:]))
    inv4 = (
        all(Decimal(x) == CTX.subtract(Decimal(a), Decimal(c)) for _s, _e, a, c, x in rows)
        and legs["cash"]["record"]["factor_id"] == cash_leg_id
    )
    inv5 = True
    for _s, _e, a, c, x in rows:
        asset = Decimal(a)
        if abs(CTX.subtract(CTX.add(Decimal(c), Decimal(x)), asset)) > TOLERANCE * max(ONE, abs(asset)):
            inv5 = False
    aligned = all(r[0] < r[1] for r in rows) and all(p[1] == n[0] for p, n in itertools.pairwise(rows))
    if rows and aligned:
        for column, role in ((2, "asset"), (3, "cash")):
            growth = ONE
            for r in rows:
                growth = CTX.multiply(growth, CTX.add(ONE, Decimal(r[column])))
            ratio = _leg_ratio(legs[role], rows[0][0], rows[-1][1])
            if abs(CTX.subtract(growth, ratio)) > TOLERANCE * abs(ratio):
                aligned = False
    return {
        "RA-INV-004": {"checked": len(rows), "passed": bool(inv4)},
        "RA-INV-005": {"checked": len(rows), "passed": inv5},
        "alignment": {"checked": len(rows), "passed": bool(rows) and bool(aligned)},
    }


def _build(spec_path, asset_dir, cash_dir, out, commit) -> tuple[dict, bool]:
    out = check_out(Path(out))
    spec = read_spec(Path(spec_path))
    if Path(asset_dir).resolve() == Path(cash_dir).resolve():
        raise ValueError("the same build was given for both legs")
    asset = load_leg(Path(asset_dir), role="asset", factor_id=spec["asset_leg"])
    cash = load_leg(Path(cash_dir), role="cash", factor_id=spec["cash_leg"])
    a_rec, c_rec = asset["record"], cash["record"]
    if (a_rec["factor_id"], a_rec["build_id"]) == (c_rec["factor_id"], c_rec["build_id"]) or (
        a_rec["series_sha256"] == c_rec["series_sha256"]
    ):
        raise ValueError("the same build was given for both legs")
    if {a_rec.get("numeraire"), c_rec.get("numeraire"), spec["numeraire"]} != {spec["numeraire"]}:
        raise ValueError("the legs and the spec must have the same numeraire")
    bounds = {
        role: {d for p in leg["periods"] for d in (p[0], p[1])}
        for role, leg in (("asset", asset), ("cash", cash))
    }
    common = sorted(bounds["asset"] & bounds["cash"])
    if len(common) < 2:
        raise ValueError("fewer than two common dates")
    inside = {d for d in bounds["asset"] | bounds["cash"] if common[0] < d < common[-1]}
    omitted = {
        "asset": len((bounds["asset"] - bounds["cash"]) & inside),
        "cash": len((bounds["cash"] - bounds["asset"]) & inside),
    }
    series_bytes = render_series(
        common, _compound(asset["periods"], common), _compound(cash["periods"], common)
    )
    invariants = check_invariants(series_bytes, {"asset": asset, "cash": cash}, spec["cash_leg"])
    failed = [name for name, result in invariants.items() if not result["passed"]]
    if failed:
        raise ValueError(f"invariants failed: {', '.join(failed)}")
    code = commit if commit is not None else _fb._base.code_commit()["commit"]
    build_id = _sha((spec["sha256"] + a_rec["series_sha256"] + c_rec["series_sha256"] + code).encode())[:16]

    def leg_ref(rec):
        return {k: rec[k] for k in ("factor_id", "build_id", "series_sha256")}

    record = {
        "factor_id": spec["factor_id"],
        "spec_version": spec["version"],
        "spec_sha256": spec["sha256"],
        "series_class": spec["series_class"],
        "numeraire": spec["numeraire"],
        "asset_leg": leg_ref(a_rec),
        "cash_leg": leg_ref(c_rec),
        "code_commit": code,
        "periods": len(common) - 1,
        "first": common[0],
        "last": common[-1],
        "omitted_dates": omitted,
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


def build(spec_path, asset_dir, cash_dir, out, *, commit=None) -> dict:
    """Build the excess series; returns the build record. Refuses with ValueError."""
    return _build(spec_path, asset_dir, cash_dir, out, commit)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--cash", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record, existed = _build(args.spec, args.asset, args.cash, args.out, None)
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
