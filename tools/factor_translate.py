"""Translate a built USD total-return series into AUD, unhedged or hedged (OD-0216; RA 4.1 and 4.3).

Inputs are `tools/factor_build.py` builds (verified: `series.csv` hashes to `build.json`, every invariant
passed, the numeraire is the one the role needs), the Federal Reserve H.10 archive (pinned by sha256; USD per
AUD, a noon New York rate: RA 4.4) and a translated-series spec. Output is a total-return build under
`<out>/<factor_id>/<spec version>/<build_id>/`: `series.csv`, `decomposition.csv` and `build.json`.

Quote convention: H.10 gives `q`, USD per AUD. The AUD investor's spot return on USD is `s = q_(t-1)/q_t - 1`,
never `q_t/q_(t-1) - 1` (RA-INV-007). `e0002_aud.fx_return` is that inversion-safe formula.

**Unhedged** (RA 4.1), one period per period of the foreign series: `price_h = (1 + PR_f)(1 + s) - 1`,
`income_h = IR_f (1 + s)`, so `total_h = (1 + TR_f)(1 + s) - 1` exactly (RA-INV-006) and the cross term
`TR_f s` is reported. The series stops at the last period whose end date has a rate at most
`MAX_STALE_DAYS` old; later periods are dropped and counted (`periods_after_fx`). A stale or missing rate
inside the span refuses.

**Hedged**, ratio one, reset every period, forward `cip_implied` (RA 4.3). Common dates are the dates that are
period boundaries of the foreign series and of both cash builds and have a fresh H.10 rate; each build is
compounded exactly between consecutive common dates (as `tools/factor_excess.py` does) and nothing is filled.
Per common period `f = (1 + r_h)/(1 + r_f) - 1` and `total = R_f + f + R_f s` (exact for h = 1, RA-INV-009).
`r_h` is the AUD cash build's return and `r_f` the USD cash build's. The hedged series does not decompose
price and income: `price_return = total_return` and `income_return = 0`. Here `periods_after_fx` counts
foreign periods starting at or after the last common date (not translated, whatever the reason).

The command prints counts, ids, hashes and pass or fail only: never a return, a rate, a level or a date.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import sys
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml

from hio.library.fx_forward import cip_forward
from hio.library.numeric import CTX

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    """Load a sibling tool as its siblings do: bare-name imports need `tools/` on sys.path."""
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_fe = _load("factor_excess_for_factor_translate", "factor_excess.py")
_aud = _load("e0002_aud_for_factor_translate", "e0002_aud.py")
_fb = _fe._fb

REPO = _fb.REPO
TOLERANCE = _fb.TOLERANCE
ONE = Decimal(1)
SERIES_HEADER = _fb.HEADER
DECOMPOSITION_HEADERS = {
    "unhedged": "period_start,period_end,foreign_return,spot_return,cross_term,total_return\n",
    "hedged": (
        "period_start,period_end,foreign_return,spot_return,forward_premium,cross_term,"
        "hedge_payoff,total_return\n"
    ),
}
MODES = ("unhedged", "hedged")
H10_MEMBER = "H10_data.xml"
MAX_STALE_DAYS = _aud.MAX_STALE_DAYS
_sha = _fb._sha
_fmt = _fb._fmt
check_out = _fb.check_out


def read_spec(path: Path, mode: str) -> dict:
    """The facts this build needs from a translated-series spec, refusing anything outside its scope."""
    raw = Path(path).read_bytes()
    spec = yaml.safe_load(raw)
    try:
        factor_id = str(spec["identity"]["factor_id"])
        version = str(spec["identity"]["version"])
        series_class = spec["classification"]["series_class"]
        investability = str(spec["classification"]["investability"])
        numeraire = str(spec["return_convention"]["numeraire"])
        hedging = str(spec["return_convention"]["hedging"])
        ids = [str(o["series_id"]) for o in spec["observations"]]
    except (KeyError, TypeError):
        raise ValueError(
            "the spec lacks identity, classification (series_class, investability), "
            "return_convention (numeraire, hedging) or observations"
        ) from None
    if series_class != "total_return":
        raise ValueError(f"series_class must be total_return, not {series_class}")
    if numeraire != "AUD":
        raise ValueError(f"numeraire must be AUD, not {numeraire}")
    declared = (
        "unhedged" if hedging.startswith("unhedged") else "hedged" if hedging.startswith("hedged") else None
    )
    if declared is None:
        raise ValueError("return_convention.hedging must start with unhedged or hedged")
    if declared != mode:
        raise ValueError(f"the spec is {declared} but --mode is {mode}")
    return {
        "factor_id": factor_id,
        "version": version,
        "series_class": series_class,
        "numeraire": numeraire,
        "investability": investability,
        "series_ids": ids,
        "sha256": _sha(raw),
    }


def load_build(directory: Path, *, role: str, numeraire: str) -> dict:
    """Read and verify one total-return build. `periods` are (start, end, total_return, index) for
    `factor_excess` helpers; `rows` carry every column."""
    directory = Path(directory)
    series_bytes = (directory / "series.csv").read_bytes()
    record = json.loads((directory / "build.json").read_bytes())
    if _sha(series_bytes) != record.get("series_sha256"):
        raise ValueError(f"the {role} build's series.csv does not hash to its build.json")
    if record.get("series_class") != "total_return":
        raise ValueError(f"the {role} build's series_class is not total_return")
    if record.get("numeraire") != numeraire:
        raise ValueError(f"the {role} build's numeraire is not {numeraire}")
    invariants = record.get("invariants")
    if not invariants or any(not r.get("passed") for r in invariants.values()):
        raise ValueError(f"the {role} build has a failed or missing invariant")
    lines = series_bytes.decode().splitlines()
    if not lines or lines[0] + "\n" != SERIES_HEADER:
        raise ValueError(f"the {role} build's series.csv has an unexpected header")
    rows = []
    for cells in csv.reader(lines[1:]):
        if len(cells) != 6:
            raise ValueError(f"the {role} build's series.csv has a malformed row")
        start, end = date.fromisoformat(cells[0]), date.fromisoformat(cells[1])
        if end <= start or (rows and rows[-1][1] != cells[0]):
            raise ValueError(f"the {role} build's periods are not increasing and contiguous")
        rows.append((cells[0], cells[1], *(Decimal(c) for c in cells[2:])))
    if not rows:
        raise ValueError(f"the {role} build has no periods")
    return {
        "record": record,
        "rows": rows,
        "periods": [(r[0], r[1], r[4], r[5]) for r in rows],
    }


def read_h10(path: Path, pin: str) -> tuple[dict[date, Decimal], str]:
    """The pinned H.10 archive's Australian series and the file's sha256."""
    data = Path(path).read_bytes()
    digest = _sha(data)
    if digest != str(pin).lower():
        raise ValueError("the H.10 archive does not match the pin")
    try:
        with zipfile.ZipFile(Path(path)) as archive:
            body = archive.read(H10_MEMBER)
    except (zipfile.BadZipFile, KeyError):
        raise ValueError("the H.10 archive is not a zip holding the expected member") from None
    rates, _absent = _aud.parse_h10(body)
    return rates, digest


def forward_premium(q0: Decimal, r_home: Decimal, r_foreign: Decimal) -> Decimal:
    """f = F/S_0 - 1 from the library's CIP forward.

    `cip_forward(s0, r_home, r_foreign) = s0 (1 + r_home)/(1 + r_foreign)` takes `s0` as units of the HOME
    currency per unit of the FOREIGN currency (RA 4.2: a home investor buys foreign currency at S_0). Home is
    AUD and foreign USD, so `s0` is AUD per USD, `1/q0` for H.10's `q0` in USD per AUD. Then
    `f = (1 + r_h)/(1 + r_f) - 1`, independent of the quote level.
    """
    s0 = CTX.divide(ONE, q0)
    return CTX.subtract(CTX.divide(cip_forward(s0, r_home, r_foreign), s0), ONE)


def _spot(q_then: Decimal, q_now: Decimal) -> Decimal:
    return _aud.fx_return(q_then, q_now)


def _fx_counts(ages: list[int]) -> dict[str, int]:
    return {
        "on_the_day": sum(1 for a in ages if a == 0),
        "before_the_day": sum(1 for a in ages if a > 0),
    }


def translate_unhedged(foreign: dict, rates: dict[date, Decimal]) -> dict:
    ordered = sorted(rates)
    last_day = ordered[-1]
    rows, decomposition, used, ages = [], [], [], []
    rows_in = foreign["rows"]
    dropped = 0
    q_a = None
    for i, (start, end, pr, ir, tr, _index) in enumerate(rows_in):
        if q_a is None:
            q_a, age = _aud.rate_on(rates, ordered, date.fromisoformat(start))
            ages.append(age)
        try:
            q_b, age = _aud.rate_on(rates, ordered, date.fromisoformat(end))
        except ValueError:
            if date.fromisoformat(end) > last_day:
                dropped = len(rows_in) - i
                break
            raise
        ages.append(age)
        s = _spot(q_a, q_b)
        grow = CTX.add(ONE, s)
        price_h = CTX.subtract(CTX.multiply(CTX.add(ONE, pr), grow), ONE)
        income_h = CTX.multiply(ir, grow)
        total_h = CTX.add(price_h, income_h)
        rows.append((start, end, price_h, income_h, total_h))
        decomposition.append((start, end, tr, s, CTX.multiply(tr, s), total_h))
        used.append((q_a, q_b))
        q_a = q_b
    if not rows:
        raise ValueError("no period of the foreign series has a usable H.10 rate")
    return {
        "rows": rows,
        "decomposition": decomposition,
        "rates": used,
        "periods_after_fx": dropped,
        "fx_dates": _fx_counts(ages),
        "parts": {},
        "span": (rows[0][0], rows[-1][1]),
        "legs": {},
    }


def translate_hedged(foreign: dict, home: dict, foreign_cash: dict, rates: dict[date, Decimal]) -> dict:
    ordered = sorted(rates)
    bounds = [{d for p in leg["periods"] for d in p[:2]} for leg in (foreign, home, foreign_cash)]
    fresh: dict[str, tuple[Decimal, int]] = {}
    for day in sorted(bounds[0] & bounds[1] & bounds[2]):
        try:
            fresh[day] = _aud.rate_on(rates, ordered, date.fromisoformat(day))
        except ValueError:
            continue  # no fresh rate: not a common date; the legs compound across it
    common = sorted(fresh)
    if len(common) < 2:
        raise ValueError("fewer than two common dates with a fresh H.10 rate")
    big_r = _fe._compound(foreign["periods"], common)
    r_h = _fe._compound(home["periods"], common)
    r_f = _fe._compound(foreign_cash["periods"], common)
    rows, decomposition, used = [], [], []
    for (lo, hi), rf_asset, rh, rf in zip(itertools.pairwise(common), big_r, r_h, r_f, strict=True):
        q_a, q_b = fresh[lo][0], fresh[hi][0]
        s = _spot(q_a, q_b)
        f = forward_premium(q_a, rh, rf)
        cross = CTX.multiply(rf_asset, s)
        total = CTX.add(CTX.add(rf_asset, f), cross)
        payoff = CTX.minus(CTX.subtract(s, f))
        rows.append((lo, hi, total, Decimal(0), total))
        decomposition.append((lo, hi, rf_asset, s, f, cross, payoff, total))
        used.append((q_a, q_b))
    after = sum(1 for p in foreign["periods"] if p[0] >= common[-1])
    return {
        "rows": rows,
        "decomposition": decomposition,
        "rates": used,
        "periods_after_fx": after,
        "fx_dates": _fx_counts([fresh[d][1] for d in common]),
        "parts": {"r_h": r_h, "r_f": r_f},
        "span": (common[0], common[-1]),
        "legs": {"foreign": foreign, "home_cash": home, "foreign_cash": foreign_cash},
    }


def render_series(rows: list[tuple]) -> bytes:
    lines = [SERIES_HEADER]
    level = ONE
    for start, end, price, income, total in rows:
        level = CTX.multiply(level, CTX.add(ONE, total))
        lines.append(",".join([start, end, _fmt(price), _fmt(income), _fmt(total), _fmt(level)]) + "\n")
    return "".join(lines).encode()


def render_decomposition(mode: str, decomposition: list[tuple]) -> bytes:
    lines = [DECOMPOSITION_HEADERS[mode]]
    for row in decomposition:
        lines.append(",".join([row[0], row[1], *(_fmt(x) for x in row[2:])]) + "\n")
    return "".join(lines).encode()


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(CTX.subtract(a, b)) <= TOLERANCE * max(ONE, abs(b))


def check_invariants(mode: str, series_bytes: bytes, decomposition_bytes: bytes, result: dict) -> dict:
    """Recompute each invariant from the written bytes (and the rates used): {name: {"checked", "passed"}}."""
    rows = list(csv.reader(series_bytes.decode().splitlines()[1:]))
    dec = list(csv.reader(decomposition_bytes.decode().splitlines()[1:]))
    n = len(rows)
    ra1 = all(_close(Decimal(t), CTX.add(Decimal(p), Decimal(i))) for _s, _e, p, i, t, _x in rows)
    chain, previous = True, ONE
    for k, (start, end, _p, _i, total, index) in enumerate(rows):
        if end <= start or (k and start != rows[k - 1][1]):
            chain = False
        previous = CTX.multiply(previous, CTX.add(ONE, Decimal(total)))
        if previous != Decimal(index):
            chain = False
    same_dates = len(dec) == n and all(
        d[:2] == r[:2] and Decimal(d[-1]) == Decimal(r[4]) for d, r in zip(dec, rows, strict=True)
    )
    # RA-INV-007: s recomputed from the rates used is q_(t-1)/q_t - 1, so a fall in q (USD per AUD, a weaker
    # AUD) is a positive s.
    ra7 = len(result["rates"]) == n and all(
        _close(Decimal(d[3]), CTX.subtract(CTX.divide(a, b), ONE)) and (b < a) == (Decimal(d[3]) > 0)
        for d, (a, b) in zip(dec, result["rates"], strict=True)
    )
    out = {
        "RA-INV-001": {"checked": n, "passed": ra1},
        "index_chain": {"checked": n, "passed": chain and same_dates},
        "RA-INV-007": {"checked": n, "passed": ra7},
        "fx_dates": {"checked": sum(result["fx_dates"].values()), "passed": True},
    }
    if mode == "unhedged":
        ok = True
        for _s, _e, fr, sp, cross, total in dec:
            fr, sp, cross, total = Decimal(fr), Decimal(sp), Decimal(cross), Decimal(total)
            ok &= _close(CTX.add(ONE, total), CTX.multiply(CTX.add(ONE, fr), CTX.add(ONE, sp)))
            ok &= _close(total, CTX.add(CTX.add(fr, sp), cross))
        out["RA-INV-006"] = {"checked": n, "passed": bool(ok)}
        return out
    ok9, ok_f = True, True
    for (_s, _e, fr, sp, fp, cross, payoff, total), rh, rf in zip(
        dec, result["parts"]["r_h"], result["parts"]["r_f"], strict=True
    ):
        fr, sp, fp, cross, payoff, total = (Decimal(x) for x in (fr, sp, fp, cross, payoff, total))
        expected = CTX.subtract(CTX.multiply(CTX.add(ONE, fr), CTX.add(ONE, sp)), ONE)
        ok9 &= _close(total, CTX.add(expected, payoff))
        ok9 &= _close(payoff, CTX.minus(CTX.subtract(sp, fp)))
        ok_f &= _close(fp, CTX.subtract(CTX.divide(CTX.add(ONE, rh), CTX.add(ONE, rf)), ONE))
    out["RA-INV-009"] = {"checked": n, "passed": bool(ok9)}
    out["cip_forward"] = {"checked": n, "passed": bool(ok_f)}
    aligned = bool(rows)
    if rows:
        first, last = result["span"]
        compounded = {
            "foreign": [Decimal(d[2]) for d in dec],
            "home_cash": result["parts"]["r_h"],
            "foreign_cash": result["parts"]["r_f"],
        }
        for role, returns in compounded.items():
            growth = ONE
            for x in returns:
                growth = CTX.multiply(growth, CTX.add(ONE, x))
            ratio = _fe._leg_ratio(result["legs"][role], first, last)
            if abs(CTX.subtract(growth, ratio)) > TOLERANCE * abs(ratio):
                aligned = False
    out["alignment"] = {"checked": n, "passed": aligned}
    return out


def _build(
    spec_path, mode, foreign_dir, h10_zip, h10_sha256, out, home_cash, foreign_cash, commit
) -> tuple[dict, bool]:
    if mode not in MODES:
        raise ValueError("--mode must be unhedged or hedged")
    out = check_out(Path(out))
    spec = read_spec(Path(spec_path), mode)
    if mode == "hedged" and (home_cash is None or foreign_cash is None):
        raise ValueError("hedged needs --home-cash and --foreign-cash")
    if mode == "unhedged" and (home_cash is not None or foreign_cash is not None):
        raise ValueError("unhedged takes no cash builds")
    foreign = load_build(Path(foreign_dir), role="foreign", numeraire="USD")
    builds = [("foreign", foreign)]
    if mode == "hedged":
        home = load_build(Path(home_cash), role="home cash", numeraire="AUD")
        fcash = load_build(Path(foreign_cash), role="foreign cash", numeraire="USD")
        builds += [("home cash", home), ("foreign cash", fcash)]
    for role, leg in builds:
        if leg["record"].get("factor_id") not in spec["series_ids"]:
            raise ValueError(f"the {role} build's factor_id is not among the spec's observations")
    if len({leg["record"]["factor_id"] for _r, leg in builds}) != len(builds):
        raise ValueError("the same build was given for more than one role")
    rates, h10_hash = read_h10(Path(h10_zip), h10_sha256)
    if mode == "unhedged":
        result = translate_unhedged(foreign, rates)
    else:
        result = translate_hedged(foreign, home, fcash, rates)
    series_bytes = render_series(result["rows"])
    decomposition_bytes = render_decomposition(mode, result["decomposition"])
    invariants = check_invariants(mode, series_bytes, decomposition_bytes, result)
    failed = [name for name, r in invariants.items() if not r["passed"]]
    if failed:
        raise ValueError(f"invariants failed: {', '.join(failed)}")
    code = commit if commit is not None else _fb._base.code_commit()["commit"]
    hashes = [leg["record"]["series_sha256"] for _r, leg in builds]
    build_id = _sha((spec["sha256"] + hashes[0] + h10_hash + "".join(hashes[1:]) + mode + code).encode())[:16]
    inputs = [
        {
            "role": role.replace(" ", "_"),
            **{k: leg["record"][k] for k in ("factor_id", "build_id", "series_sha256")},
        }
        for role, leg in builds
    ]
    inputs.append({"role": "h10", "path": Path(h10_zip).name, "sha256": h10_hash})
    record = {
        "factor_id": spec["factor_id"],
        "spec_version": spec["version"],
        "spec_sha256": spec["sha256"],
        "series_class": spec["series_class"],
        "numeraire": spec["numeraire"],
        "mode": mode,
        "investability": spec["investability"],
        "inputs": inputs,
        "code_commit": code,
        "periods": len(result["rows"]),
        "first": result["rows"][0][0],
        "last": result["rows"][-1][1],
        "periods_after_fx": result["periods_after_fx"],
        "fx_dates": result["fx_dates"],
        "invariants": invariants,
        "decomposition_sha256": _sha(decomposition_bytes),
        "series_sha256": _sha(series_bytes),
        "build_id": build_id,
    }
    record_bytes = (json.dumps(record, indent=1, sort_keys=True) + "\n").encode()
    target = out / spec["factor_id"] / spec["version"] / build_id
    files = {"series.csv": series_bytes, "decomposition.csv": decomposition_bytes, "build.json": record_bytes}
    if target.exists():
        if not all((target / n).is_file() and (target / n).read_bytes() == b for n, b in files.items()):
            raise ValueError("the build directory exists with different bytes")
        return record, True
    _fb._make_dirs(target)
    for name, data in files.items():
        _fb._write_new(target / name, data)
    return record, False


def build(
    spec_path, mode, foreign_dir, h10_zip, h10_sha256, out, *, home_cash=None, foreign_cash=None, commit=None
) -> dict:
    """Build the translated series; returns the build record. Refuses with ValueError."""
    return _build(spec_path, mode, foreign_dir, h10_zip, h10_sha256, out, home_cash, foreign_cash, commit)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--foreign", type=Path, required=True)
    parser.add_argument("--h10", type=Path, required=True)
    parser.add_argument("--h10-sha256", required=True)
    parser.add_argument("--home-cash", type=Path)
    parser.add_argument("--foreign-cash", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record, existed = _build(
            args.spec,
            args.mode,
            args.foreign,
            args.h10,
            args.h10_sha256,
            args.out,
            args.home_cash,
            args.foreign_cash,
            None,
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"factor_id: {record['factor_id']}")
    print(f"build_id: {record['build_id']}")
    print(f"mode: {record['mode']}")
    print(f"periods: {record['periods']}")
    print(f"periods_after_fx: {record['periods_after_fx']}")
    for name, result in record["invariants"].items():
        print(f"{name}: {'pass' if result['passed'] else 'fail'} ({result['checked']} checked)")
    print(f"series_sha256: {record['series_sha256']}")
    if existed:
        print("already built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
