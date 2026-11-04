"""E-0002's AUD variant V2 (OD-0167): the three allocations, unhedged, in AUD on H.10's noon New York rate.

Monthly only, because noon New York isn't a market close (RA 4.4). Each sleeve's USD return between common
month ends is translated under RA 4.1: r_aud = (1 + r_usd)(1 + s) - 1, with s = q(t-1)/q(t) - 1 for q in USD
per AUD (RA-INV-007). Values go only to reports/ for the owner; stdout and summary-aud.json hold counts and
pass or fail. BIL translated to AUD is USD bills plus currency risk, not AUD cash. It isn't hedged, and it's
no forecast or recommendation.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

import eodhd_eval as ev
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation
from hio.contracts.temporal import KnowledgeMode
from hio.library.numeric import CTX
from hio.portfolio import fixed_allocation as fa
from hio.rights.gate import RightsGate
from hio.storage.objectstore import LocalObjectStore
from research_reader import Pin, read_panel

H10_SOURCE = "frb_h10.aud_usd"
H10_SERIES = "RXI$US_N.B.AL"
MAX_STALE_DAYS = 5
FX_BANDS = (Decimal("0.005"), Decimal("0.01"), Decimal("0.02"))
NOTICE = "FX: Board of Governors of the Federal Reserve System, H.10. No endorsement by the Board is implied."


def parse_h10(body: bytes) -> tuple[dict[date, Decimal], int]:
    """The Australian daily series, and how many rows hold no value. Other non-numeric text stops."""
    rates: dict[date, Decimal] = {}
    absent = 0
    for series in ET.fromstring(body).iter():
        if not series.tag.endswith("}Series") or series.get("SERIES_NAME") != H10_SERIES:
            continue
        for obs in series:
            if not obs.tag.endswith("}Obs"):
                continue
            day, text = date.fromisoformat(obs.get("TIME_PERIOD", "")), obs.get("OBS_VALUE", "")
            if obs.get("OBS_STATUS") == "ND" or text in {"", "ND"}:
                absent += 1
                continue
            try:
                value = Decimal(text)
            except ArithmeticError as exc:
                raise ev.Stop(f"{day}: a non-numeric H.10 value") from exc
            if not value.is_finite() or value <= 0:
                raise ev.Stop(f"{day}: an impossible H.10 value")
            if day in rates and rates[day] != value:
                raise ev.Stop(f"{day}: conflicting H.10 rows")
            rates[day] = value
    if not rates:
        raise ev.Stop(f"no {H10_SERIES} in the archive")
    return rates, absent


def rate_on(rates: Mapping[date, Decimal], ordered: Sequence[date], day: date) -> tuple[Decimal, int]:
    """The latest rate on or before `day`, and its age. Too stale stops: nothing is interpolated."""
    index = bisect_right(ordered, day) - 1
    if index < 0:
        raise ev.Stop(f"no H.10 rate on or before {day}")
    age = (day - ordered[index]).days
    if age > MAX_STALE_DAYS:
        raise ev.Stop(f"the H.10 rate for {day} is {age} days old")
    return rates[ordered[index]], age


def fx_return(rate_then: Decimal, rate_now: Decimal) -> Decimal:
    """s for an AUD holder of USD, with rates in USD per AUD (RA-INV-007)."""
    return CTX.subtract(CTX.divide(rate_then, rate_now), Decimal(1))


def monthly_usd(panel: fa.Panel) -> tuple[list[date], fa.Floats]:
    """Month-end dates and each sleeve's USD return between them."""
    ends = fa.period_ends(panel.dates, "monthly")
    levels = fa.sleeve_levels(panel)[ends]
    return [panel.dates[i] for i in ends], levels[1:] / levels[:-1] - 1


def translate(
    months: Sequence[date], usd: fa.Floats, rates: Mapping[date, Decimal]
) -> tuple[fa.Floats, fa.Floats, dict[str, int]]:
    ordered = sorted(rates)
    q, ages = [], []
    for day in months:
        rate, age = rate_on(rates, ordered, day)
        q.append(rate)
        ages.append(age)
    s = np.array([float(fx_return(a, b)) for a, b in pairwise(q)], dtype=np.float64)
    aud = (1 + usd) * (1 + s[:, None]) - 1
    return (
        aud,
        s,
        {"months": len(s), "rates_not_on_the_day": sum(1 for a in ages if a), "oldest_rate_days": max(ages)},
    )


def _path_stats(dates: Sequence[date], returns: fa.Floats) -> dict[str, Any]:
    levels = np.concatenate(([1.0], np.cumprod(1 + returns)))
    dd = fa.drawdown(dates, levels)
    years = (dates[-1] - dates[0]).days / fa.DAYS_PER_YEAR
    return {
        "final_wealth": float(levels[-1]),
        "annualised_return": float(levels[-1] ** (1 / years) - 1),
        "volatility": fa.annualised_volatility(returns, "monthly"),
        "max_drawdown": dd.max_drawdown,
        "trough": dd.trough.isoformat(),
        "recovery": dd.recovery.isoformat() if dd.recovery else None,
        "longest_underwater_days": dd.longest_underwater_days,
    }


def attribution(usd: fa.Floats, s: fa.Floats) -> dict[str, float]:
    """Compounded contributions over the span: asset in USD, currency alone, and the cross term left."""
    total = float(np.prod((1 + usd) * (1 + s)) - 1)
    asset, currency = float(np.prod(1 + usd) - 1), float(np.prod(1 + s) - 1)
    return {"asset_usd": asset, "currency": currency, "cross": total - asset - currency, "total_aud": total}


def compare_aud(
    sleeves: Sequence[str], months: Sequence[date], usd: fa.Floats, aud: fa.Floats, s: fa.Floats
) -> dict[str, Any]:
    results: dict[str, Any] = {"windows": {}, "bootstrap_treasury_minus_cash": {}}
    vectors = {a: np.array([w[x] for x in sleeves]) for a, w in ev.ALLOCATIONS.items()}
    for name, (start, end) in ev.WINDOWS.items():
        kept = [i for i in range(len(s)) if start <= months[i] and months[i + 1] <= end]
        if len(kept) < 3 or (start != date.min and start < months[0]):
            results["windows"][name] = {"available": False}
            continue
        dates = [months[kept[0]], *(months[i + 1] for i in kept)]
        block = {}
        for allocation, v in vectors.items():
            usd_p, aud_p = usd[kept] @ v, aud[kept] @ v
            block[allocation] = {
                "aud": _path_stats(dates, aud_p),
                "usd": _path_stats(dates, usd_p),
                "attribution": attribution(usd_p, s[kept]),
                "correlation_with_currency": float(np.corrcoef(usd_p, s[kept])[0, 1]),
            }
        a, b = sleeves.index("equity"), sleeves.index("treasury")
        results["windows"][name] = {
            "available": True,
            "allocations": block,
            "equity_treasury_correlation_aud": float(np.corrcoef(aud[kept][:, a], aud[kept][:, b])[0, 1]),
            "equity_treasury_correlation_usd": float(np.corrcoef(usd[kept][:, a], usd[kept][:, b])[0, 1]),
        }
    for size in ev.BLOCKS:
        boot = fa.paired_block_bootstrap(
            aud,
            vectors["60_equity_40_cash"],
            vectors["60_equity_40_treasury"],
            block_months=size,
            replications=ev.REPLICATIONS,
            seed=ev.SEED,
        )
        results["bootstrap_treasury_minus_cash"][str(size)] = {
            m: vars(getattr(boot, m)) for m in ("volatility", "annualised_return", "max_drawdown")
        }
    return results


def compare_fx_sources(
    eodhd: Sequence[Mapping[str, Any]], rates: Mapping[date, Decimal], start: date
) -> dict[str, Any]:
    """EODHD's AUD/USD against H.10 from `start`, as counts by relative band. Different times of day, so it
    can flag a problem but can't validate either. Pass: within 1% on at least 95% of common dates."""
    gaps = []
    weekend = 0
    for row in eodhd:
        day = date.fromisoformat(str(row["date"]))
        if day < start:
            continue
        if day.weekday() >= 5:
            weekend += 1
        if day in rates:
            gaps.append(abs(CTX.divide(Decimal(str(row["close"])), rates[day]) - 1))
    if not gaps:
        return {"common_dates": 0, "within_1pct_on_95pct": False}
    counts = {f"within_{band}": sum(1 for g in gaps if g <= band) for band in FX_BANDS}
    ok = Decimal(counts["within_0.01"]) / Decimal(len(gaps)) >= Decimal("0.95")
    return {"common_dates": len(gaps), **counts, "weekend_rows": weekend, "within_1pct_on_95pct": ok}


def reconcile_reports(usd: Mapping[str, Any], aud: Mapping[str, Any]) -> dict[str, dict[str, bool | None]]:
    """The USD report against the AUD report's USD column, by window (V3). A check not made is None, not True:
    wealth is compared only where the spans match, and an availability mismatch is a failure."""
    out: dict[str, dict[str, bool | None]] = {}
    for name in sorted(usd["windows"].keys() | aud["windows"].keys()):
        window, other = usd["windows"].get(name, {}), aud["windows"].get(name, {})
        here, there = bool(window.get("available")), bool(other.get("available"))
        row: dict[str, bool | None] = {"availability_matches": here == there}
        if not (here and there):
            row |= dict.fromkeys(
                ("monthly_volatility_equal", "month_end_drawdown_at_most_daily", "wealth_equal")
            )
            out[name] = row
            continue
        spans_match = name in {"2008", "q1_2020", "2022"}
        row |= {
            "monthly_volatility_equal": True,
            "month_end_drawdown_at_most_daily": True,
            "wealth_equal": True if spans_match else None,
        }
        for allocation, daily in window["allocations"].items():
            monthly = other["allocations"][allocation]["usd"]
            row["monthly_volatility_equal"] &= abs(daily["volatility_monthly"] - monthly["volatility"]) < 1e-9
            row["month_end_drawdown_at_most_daily"] &= (
                monthly["max_drawdown"] <= daily["max_drawdown"] + 1e-12
            )
            if spans_match:
                row["wealth_equal"] &= abs(daily["final_wealth"] - monthly["final_wealth"]) < 1e-9
        out[name] = row
    return out


def render(results: Mapping[str, Any]) -> str:
    lines = [
        "# E-0002 AUD variant: for the owner and HIO's agents. Licensed-derived: don't commit or share.",
        "",
        "Monthly, unhedged, on H.10's noon New York rate; no costs or tax. BIL in AUD is USD bills plus "
        "currency risk, not AUD cash. Descriptive: no recommendation or forecast. " + NOTICE,
    ]
    for name, window in results["windows"].items():
        lines.append(f"\n## Window: {name}\n")
        if not window["available"]:
            lines.append("Not available.")
            continue
        lines.append(
            "| Allocation | Return AUD | Return USD | Vol AUD | Vol USD | Drawdown AUD | Drawdown USD "
            "| Recovery AUD | Corr with AUD/USD move |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---|---:|")
        for allocation, d in window["allocations"].items():
            lines.append(
                f"| {allocation} | {d['aud']['annualised_return']:.2%} | "
                f"{d['usd']['annualised_return']:.2%} | "
                f"{d['aud']['volatility']:.2%} | {d['usd']['volatility']:.2%} | "
                f"{d['aud']['max_drawdown']:.2%} | "
                f"{d['usd']['max_drawdown']:.2%} | {d['aud']['recovery'] or 'not recovered'} | "
                f"{d['correlation_with_currency']:.3f} |"
            )
        lines.append(
            "\n| Allocation | Asset (USD) | Currency | Cross | Total (AUD) |\n|---|---:|---:|---:|---:|"
        )
        for allocation, d in window["allocations"].items():
            t = d["attribution"]
            lines.append(
                f"| {allocation} | {t['asset_usd']:.2%} | {t['currency']:.2%} | {t['cross']:.2%} | "
                f"{t['total_aud']:.2%} |"
            )
        lines.append(
            f"\nEquity-Treasury correlation: AUD {window['equity_treasury_correlation_aud']:.3f}, "
            f"USD {window['equity_treasury_correlation_usd']:.3f}."
        )
    lines.append("\n## 60/40 Treasury minus 60/40 BIL, in AUD, paired block bootstrap (this history only)\n")
    lines.append("| Block (months) | Metric | Observed | 2.5% | 97.5% |\n|---:|---|---:|---:|---:|")
    for block, metrics in results["bootstrap_treasury_minus_cash"].items():
        for metric, v in metrics.items():
            lines.append(f"| {block} | {metric} | {v['estimate']:.2%} | {v['low']:.2%} | {v['high']:.2%} |")
    return "\n".join(lines) + "\n"


def run(root: Path, h10_root: Path, snapshot: str, *, gate: RightsGate) -> dict[str, Any]:
    ev.check_root(root)
    gate.authorise(Operation.BUILD, [H10_SOURCE])
    gate.authorise(Operation.BUILD, [ev.SOURCE_ID])
    summary = json.loads((root / "summary.json").read_text())
    if summary.get("snapshot") != snapshot or not summary.get("comparison_ran"):
        raise ev.Stop("the USD run for this snapshot hasn't passed")
    store = LocalObjectStore(root / "store")
    hashes = summary["releases"]
    pins = [Pin(s, ev.SLEEVES[s][1], sha) for s, sha in hashes.items()]
    first = hashes["equity"]
    core = json.loads(
        (root / "store" / "releases" / ev.SLEEVES["equity"][1] / first / "manifest.json").read_text()
    )
    panel, _ = read_panel(
        store, pins, mode=KnowledgeMode.LATEST, cutoff=parse_instant(core["knowledge_cutoff"]), gate=gate
    )
    with zipfile.ZipFile(h10_root / "FRB_h10_xml.zip") as archive:
        rates, absent = parse_h10(archive.read("H10_data.xml"))
    months, usd = monthly_usd(panel)
    aud, s, facts = translate(months, usd, rates)
    results = compare_aud(panel.sleeves, months, usd, aud, s)
    manifest = ev.load_snapshot(root, snapshot)
    fx = compare_fx_sources(ev._read(root, manifest, ev.FOREX, "eod"), rates, months[0])
    reports = root / "reports"
    ev.private_write(reports / "owner-report-aud.md", render(results).encode())
    ev.private_write(
        reports / "owner-values-aud.json", (json.dumps(results, indent=1, sort_keys=True) + "\n").encode()
    )
    out = {
        "snapshot": snapshot,
        "h10_rows": len(rates),
        "h10_absent_rows": absent,
        "h10_first": min(rates).isoformat(),
        "h10_last": max(rates).isoformat(),
        "first_month": months[0].isoformat(),
        "last_month": months[-1].isoformat(),
        **facts,
        "windows_available": {k: v["available"] for k, v in results["windows"].items()},
        "eodhd_fx_against_h10": fx,
    }
    usd_values = reports / "owner-values.json"
    if usd_values.is_file():
        out["reports_reconciled"] = reconcile_reports(json.loads(usd_values.read_text()), results)
    ev.private_write(root / "summary-aud.json", (json.dumps(out, indent=1, sort_keys=True) + "\n").encode())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--h10", type=Path, default=Path.home() / ".hio-research" / "H10")
    parser.add_argument("--snapshot", default="s2")
    args = parser.parse_args(argv)
    try:
        ev.code_commit()
        out = run(args.root, args.h10, args.snapshot, gate=ev.make_gate())
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
