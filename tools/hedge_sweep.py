"""Hedge-ratio sweep: the AUD return of a USD asset at a grid of hedge ratios (OD-0217; RA 4.3).

Descriptive only. It describes locally built series. It forecasts, optimises and recommends nothing.

Inputs are `tools/factor_build.py` builds (verified as `tools/factor_translate.py` verifies them:
`series.csv` hashes to `build.json`, every invariant passed, the numeraire is the one the role needs): the
USD asset, an AUD cash build, a USD cash build, optional AUD total-return companions held at fixed weights,
and the pinned Federal Reserve H.10 archive.

**Per period.** The periods are exactly those `factor_translate.translate_hedged` uses (the dates common to
the asset, both cash builds and a fresh H.10 rate; each build compounded exactly between them). Per period,
with `s = q_a/q_b - 1` (USD per AUD quoted: RA-INV-007) and `f = (1 + r_h)/(1 + r_f) - 1`,

    R(h) = (1 + R_f)(1 + s) - 1 - h (s - f)           (RA 4.3, hedge ratio h)

Asserted for every period and ratio (relative tolerance 1e-12), refusing on failure: `R(0)` is the unhedged
return `(1 + R_f)(1 + s) - 1`; `R(1)` is `R_f + f + R_f s` (RA-INV-009); `R(h) = R(0) - h (R(0) - R(1))`.
Ratios outside [0, 1] are allowed and labelled: over- and under-hedging are legitimate to describe.

**Monthly statistics** follow `hio.portfolio.fixed_allocation` and `tools/portfolio_analytics.py`: per-period
returns become `Interval` rows, `align` compounds them between the dates common to everything, `wealth_path`
resets monthly to the target weights, `period_returns` measures between the last common dates of consecutive
calendar months (first and last periods dropped as possibly partial), volatility is ddof 1 times sqrt(12), the
annualised return is geometric on 365.25 days, and the drawdown is from the running peak. Scope `asset` is
the asset alone and scope `portfolio` the asset at `--asset-weight` plus the companions; both on the dates
common to everything.

**Currency contribution and the sample minimum-variance ratio.** Monthly `R_m(0)` and `R_m(1)` come from their
own compounded series (the asset alone through `wealth_path`). The monthly currency contribution is defined as
`c_m = R_m(0) - R_m(1)`. The reported correlation is the sample correlation of `R_m(0)` with `c_m`. The sample
minimum-variance ratio is `h* = cov(R_m(0), c_m) / var(c_m)` (ddof 1). Its volatility is computed by building
the `h*` series through the same code path. A monthly-compounded series is only approximately linear in `h`,
so the gap between the volatility at `h*` and the lowest grid volatility is reported, not asserted to be zero.
`h*` is in-sample, descriptive: not a recommendation.

The command prints counts, hashes and pass or fail only: never a return, a rate, a ratio result or a date.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import sys
from collections import namedtuple
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from hio.portfolio import fixed_allocation as fa

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_ft = _load("factor_translate_for_hedge_sweep", "factor_translate.py")

CTX = _ft.CTX
ONE = Decimal(1)
ASSET = "asset"
IDENTITY_TOLERANCE = Decimal("1e-12")
WEIGHT_TOLERANCE = 1e-12
GRID_TOLERANCE = 1e-9
DEFAULT_RATIOS = "0,0.25,0.5,0.75,1"
H_STAR_LABEL = "in-sample, descriptive: not a recommendation"
CSV_HEADER = [
    "hedge_ratio",
    "scope",
    "annualised_return",
    "annualised_volatility",
    "max_drawdown",
    "drawdown_peak",
    "drawdown_trough",
    "worst_month",
    "worst_month_return",
]

Period = namedtuple("Period", "start end foreign_return spot forward_premium")


# ---------------------------------------------------------------------------------------------- per period


def asset_periods(
    foreign: dict, home: dict, foreign_cash: dict, rates: Mapping[date, Decimal]
) -> list[Period]:
    """The common periods with `R_f` (asset, USD), `s` (spot return) and `f` (CIP forward premium),
    exactly as `factor_translate` computes them for its hedged mode."""
    result = _ft.translate_hedged(foreign, home, foreign_cash, dict(rates))
    return [Period(d[0], d[1], d[2], d[3], d[4]) for d in result["decomposition"]]


def _hedged(p: Period, h: Decimal) -> Decimal:
    unhedged = CTX.subtract(CTX.multiply(CTX.add(ONE, p.foreign_return), CTX.add(ONE, p.spot)), ONE)
    return CTX.subtract(unhedged, CTX.multiply(h, CTX.subtract(p.spot, p.forward_premium)))


def hedged_returns(periods: Sequence[Period], h: Decimal) -> list[Decimal]:
    """`R(h) = (1 + R_f)(1 + s) - 1 - h (s - f)` for every period (RA 4.3)."""
    h = Decimal(h)
    return [_hedged(p, h) for p in periods]


def check_identities(periods: Sequence[Period], ratios: Sequence[Decimal]) -> dict[str, int]:
    """Assert the three identities for every period (and every ratio, for linearity); refuse on a failure."""
    close = _ft._close
    linear = 0
    for p in periods:
        r0 = CTX.subtract(CTX.multiply(CTX.add(ONE, p.foreign_return), CTX.add(ONE, p.spot)), ONE)
        r1 = CTX.add(CTX.add(p.foreign_return, p.forward_premium), CTX.multiply(p.foreign_return, p.spot))
        if not close(_hedged(p, Decimal(0)), r0):
            raise ValueError(f"R(0) is not the unhedged return in the period starting {p.start}")
        if not close(_hedged(p, ONE), r1):
            raise ValueError(f"R(1) is not R_f + f + R_f s in the period starting {p.start}")
        for h in ratios:
            expected = CTX.subtract(r0, CTX.multiply(h, CTX.subtract(r0, r1)))
            if not close(_hedged(p, h), expected):
                raise ValueError(f"R(h) is not linear in h in the period starting {p.start}")
            linear += 1
    n = len(periods)
    return {"periods": n, "unhedged": n, "fully_hedged": n, "linearity": linear}


# -------------------------------------------------------------------------------------------- statistics


def _intervals(periods: Sequence[Period], h: Decimal) -> list[fa.Interval]:
    returns = hedged_returns(periods, h)
    return [
        fa.Interval(date.fromisoformat(p.start), date.fromisoformat(p.end), r)
        for p, r in zip(periods, returns, strict=True)
    ]


def _panel(periods: Sequence[Period], h: Decimal, companions: Mapping[str, tuple[float, list]]) -> fa.Panel:
    series = {ASSET: _intervals(periods, h)}
    series.update({f"companion:{k}": v[1] for k, v in companions.items()})
    return fa.align(series)


def _weights(asset_weight: float, companions: Mapping[str, tuple[float, list]]) -> dict[str, float]:
    return {ASSET: asset_weight, **{f"companion:{k}": v[0] for k, v in companions.items()}}


def _solo(panel: fa.Panel) -> fa.Panel:
    column = panel.sleeves.index(ASSET)
    return fa.Panel((ASSET,), panel.dates, panel.returns[:, [column]], panel.omitted_dates)


def _describe(panel: fa.Panel, weights: Mapping[str, float]) -> tuple[dict, np.ndarray]:
    """Statistics and the monthly returns of a weighted path on a panel."""
    path = fa.wealth_path(panel, weights)
    ends = fa.period_ends(panel.dates, "monthly")
    if len(ends) < 3:
        raise ValueError("fewer than two complete months in the common span")
    month_ends = [panel.dates[i] for i in ends[1:]]
    monthly = fa.period_returns(panel.dates, path.wealth, "monthly")
    drawdown = fa.drawdown(panel.dates, path.wealth)
    worst = int(np.argmin(monthly))
    stats = {
        "annualised_return": fa.annualised_return(path),
        "annualised_volatility": fa.annualised_volatility(monthly, "monthly"),
        "max_drawdown": drawdown.max_drawdown,
        "drawdown_peak": drawdown.peak.isoformat(),
        "drawdown_trough": drawdown.trough.isoformat(),
        "worst_month": month_ends[worst].isoformat(),
        "worst_month_return": float(monthly[worst]),
    }
    return stats, monthly


def _label(h: Decimal) -> str:
    if h < 0:
        return "outside [0, 1]: below unhedged (extra USD exposure)"
    if h > 1:
        return "outside [0, 1]: more than fully hedged"
    return "within [0, 1]"


def _at_ratio(periods, h: Decimal, asset_weight, companions) -> tuple[dict, np.ndarray]:
    """One ratio through the one code path: the statistics and the asset's monthly returns."""
    panel = _panel(periods, h, companions)
    asset, monthly = _describe(_solo(panel), {ASSET: 1.0})
    entry = {"hedge_ratio": format(h, "f"), "label": _label(h), "asset": asset}
    if companions:
        entry["portfolio"], _ = _describe(panel, _weights(asset_weight, companions))
    return entry, monthly


def sweep(
    periods: Sequence[Period],
    ratios: Sequence[Decimal],
    *,
    asset_weight: float = 1.0,
    companions: Mapping[str, tuple[float, list]] | None = None,
) -> dict:
    """The sweep record. `companions` maps a factor id to (weight, intervals of AUD total returns)."""
    companions = dict(companions or {})
    ratios = sorted({Decimal(r) for r in ratios})
    if not ratios:
        raise ValueError("no hedge ratios")
    if not periods:
        raise ValueError("no common periods")
    counts = check_identities(periods, ratios)

    entries, vols = [], []
    for h in ratios:
        entry, _monthly = _at_ratio(periods, h, asset_weight, companions)
        entries.append(entry)
        vols.append(entry["asset"]["annualised_volatility"])
    _s0, r0 = _at_ratio(periods, Decimal(0), asset_weight, companions)
    _s1, r1 = _at_ratio(periods, ONE, asset_weight, companions)
    currency = r0 - r1
    variance = float(np.var(currency, ddof=1))
    if not variance > 0:
        raise ValueError(
            "the monthly currency contribution has no variance: no sample minimum-variance ratio"
        )
    h_star = float(np.cov(r0, currency, ddof=1)[0, 1]) / variance
    correlation = float(np.corrcoef(r0, currency)[0, 1])
    h_dec = Decimal(repr(h_star))
    star_counts = check_identities(periods, [h_dec])
    counts["linearity"] += star_counts["linearity"]
    star_entry, _ = _at_ratio(periods, h_dec, asset_weight, companions)
    star_vol = star_entry["asset"]["annualised_volatility"]
    lowest = int(np.argmin(vols))
    gap = star_vol - vols[lowest]
    panel = _panel(periods, Decimal(0), companions)
    months = len(fa.period_ends(panel.dates, "monthly")) - 1
    return {
        "span": {
            "first": panel.dates[0].isoformat(),
            "last": panel.dates[-1].isoformat(),
            "months": months,
            "periods": len(periods),
        },
        "ratios": [format(h, "f") for h in ratios],
        "weights": _weights(asset_weight, companions),
        "by_ratio": entries,
        "correlation": {
            "value": correlation,
            "definition": "sample correlation of monthly R(0) with c = monthly R(0) - monthly R(1)",
        },
        "h_star": {
            "value": h_star,
            "label": H_STAR_LABEL,
            "definition": "cov(R_m(0), c) / var(c), ddof 1, c = R_m(0) - R_m(1)",
            "statistics": star_entry["asset"],
            "volatility": star_vol,
            "lowest_grid_ratio": format(ratios[lowest], "f"),
            "lowest_grid_volatility": vols[lowest],
            "gap_to_lowest_grid": gap,
            "no_grid_ratio_lower_by_more_than_1e-9": bool(gap <= GRID_TOLERANCE),
        },
        "identities": {**counts, "ratios_checked": len(ratios) + 1},
    }


# ------------------------------------------------------------------------------------------------ files


def _csv_bytes(result: Mapping) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for entry in result["by_ratio"]:
        for scope in ("asset", "portfolio"):
            if scope not in entry:
                continue
            s = entry[scope]
            writer.writerow(
                [
                    entry["hedge_ratio"],
                    scope,
                    repr(s["annualised_return"]),
                    repr(s["annualised_volatility"]),
                    repr(s["max_drawdown"]),
                    s["drawdown_peak"],
                    s["drawdown_trough"],
                    s["worst_month"],
                    repr(s["worst_month_return"]),
                ]
            )
    return buffer.getvalue().encode()


def _write(path: Path, data: bytes) -> str:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    path.chmod(0o600)
    return hashlib.sha256(data).hexdigest()


def parse_ratios(text: str | Sequence) -> list[Decimal]:
    items = text.split(",") if isinstance(text, str) else list(text)
    ratios = []
    for item in items:
        try:
            h = Decimal(str(item).strip())
        except InvalidOperation:
            raise ValueError("a hedge ratio is not a number") from None
        if not h.is_finite():
            raise ValueError("a hedge ratio is not finite")
        ratios.append(h)
    if not ratios:
        raise ValueError("no hedge ratios")
    if len(set(ratios)) != len(ratios):
        raise ValueError("a hedge ratio is given twice")
    return ratios


def _weight(value) -> float:
    try:
        w = float(value)
    except (TypeError, ValueError):
        raise ValueError("a weight is not a number") from None
    if not np.isfinite(w) or not 0 < w <= 1:
        raise ValueError("a weight is not in (0, 1]")
    return w


def run(
    foreign_dir: Path,
    home_cash_dir: Path,
    foreign_cash_dir: Path,
    h10_zip: Path,
    h10_sha256: str,
    out: Path,
    *,
    ratios: str | Sequence = DEFAULT_RATIOS,
    asset_weight: float | str = 1,
    companions: Sequence[tuple[Path, float | str]] = (),
) -> dict:
    """Verify, sweep and write `sweep.json` and `sweep.csv` under `out`. Refuses with ValueError."""
    out = _ft.check_out(Path(out))
    grid = parse_ratios(ratios)
    weights = [_weight(asset_weight), *(_weight(w) for _d, w in companions)]
    if abs(sum(weights) - 1) > WEIGHT_TOLERANCE:
        raise ValueError("the asset weight and the companion weights do not sum to 1")
    foreign = _ft.load_build(Path(foreign_dir), role="foreign", numeraire="USD")
    home = _ft.load_build(Path(home_cash_dir), role="home cash", numeraire="AUD")
    fcash = _ft.load_build(Path(foreign_cash_dir), role="foreign cash", numeraire="USD")
    loaded = []
    for (directory, _w), weight in zip(companions, weights[1:], strict=True):
        build = _ft.load_build(Path(directory), role="companion", numeraire="AUD")
        loaded.append((build, weight))
    ids = [b["record"]["factor_id"] for b in (foreign, home, fcash, *(b for b, _w in loaded))]
    if len(set(ids)) != len(ids):
        raise ValueError("the same build was given for more than one role")
    rates, h10_hash = _ft.read_h10(Path(h10_zip), h10_sha256)
    periods = asset_periods(foreign, home, fcash, rates)
    comp = {
        b["record"]["factor_id"]: (
            w,
            [fa.Interval(date.fromisoformat(r[0]), date.fromisoformat(r[1]), r[4]) for r in b["rows"]],
        )
        for b, w in loaded
    }
    result = sweep(periods, grid, asset_weight=weights[0], companions=comp)
    inputs = [
        {"role": role, **{k: b["record"][k] for k in ("factor_id", "build_id", "series_sha256")}}
        for role, b in (("foreign", foreign), ("home_cash", home), ("foreign_cash", fcash))
    ]
    inputs += [
        {"role": "companion", **{k: b["record"][k] for k in ("factor_id", "build_id", "series_sha256")}}
        for b, _w in loaded
    ]
    inputs.append({"role": "h10", "path": Path(h10_zip).name, "sha256": h10_hash})
    result["inputs"] = inputs
    _ft._fb._make_dirs(out)
    out.chmod(0o700)
    sweep_json = (json.dumps(result, sort_keys=True, indent=1) + "\n").encode()
    return {
        "months": result["span"]["months"],
        "ratios": len(result["ratios"]),
        "companions": bool(companions),
        "sweep_json_sha256": _write(out / "sweep.json", sweep_json),
        "sweep_csv_sha256": _write(out / "sweep.csv", _csv_bytes(result)),
    }


def _parse_with(items: Sequence[str]) -> list[tuple[Path, str]]:
    parsed = []
    for item in items:
        directory, sep, weight = item.rpartition("=")
        if not sep or not directory:
            raise ValueError("--with must be DIR=WEIGHT")
        parsed.append((Path(directory), weight))
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--foreign", type=Path, required=True)
    parser.add_argument("--home-cash", type=Path, required=True)
    parser.add_argument("--foreign-cash", type=Path, required=True)
    parser.add_argument("--h10", type=Path, required=True)
    parser.add_argument("--h10-sha256", required=True)
    parser.add_argument("--ratios", default=DEFAULT_RATIOS)
    parser.add_argument("--asset-weight", default="1")
    parser.add_argument("--with", dest="companions", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = run(
            args.foreign,
            args.home_cash,
            args.foreign_cash,
            args.h10,
            args.h10_sha256,
            args.out,
            ratios=args.ratios,
            asset_weight=args.asset_weight,
            companions=_parse_with(args.companions),
        )
    except (ValueError, OSError) as exc:
        print(f"refused: {type(exc).__name__}: {exc if isinstance(exc, ValueError) else ''}", file=sys.stderr)
        return 2
    print(f"months: {summary['months']}")
    print(f"ratios: {summary['ratios']}")
    print(f"companions: {'yes' if summary['companions'] else 'no'}")
    print(f"sweep.json sha256: {summary['sweep_json_sha256']}")
    print(f"sweep.csv sha256: {summary['sweep_csv_sha256']}")
    print("identities hold: yes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
