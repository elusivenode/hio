"""T-0023 step 5 (OD-0178, preregistration 1): what remains. X1 and G1 are checks, S8 and S9 sensitivities.

X1 counts H.10 against EODHD's AUD/USD at the panel's month ends. Both quote USD per AUD (a test checks the
direction), so the ratio is taken directly. S8 and S9 rebuild the panel's FX return from EODHD's rate and from
H.10's next published date, and compare classes. G1 asks whether reinvesting on the payment date rather than
the ex-date explains the SPY gap to the issuer's returns. Values go only to the report under the output
directory; stdout and summary.json hold hashes, counts, pass or fail, verdicts and classes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from bisect import bisect_right
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

import e0002_aud as aud_tool
import e0002_issuer_check as ic
import eodhd_eval as ev
import t0023_common as tc
from hio.contracts.rights import Operation
from hio.library.numeric import CTX
from hio.library.vehicle_return import VehiclePeriod
from hio.portfolio import fixed_allocation as fa
from hio.rights.gate import RightsGate

SNAPSHOT = "s2"
STEP = "t0023_basis"
H10_QUOTE = "USD per AUD"
EODHD_QUOTE = "USD per AUD"  # AUDUSD.FOREX is the price of one AUD in USD
FUNDS = ("SPY.US", "IEF.US", "BIL.US")
SPY_FACTOR = 0.5  # preregistered: every SPY gap at least halves
BOND_TOLERANCE_PCT = 0.10  # preregistered: BIL and IEF stay within this, points a year
ONE = Decimal(1)


@dataclass(frozen=True)
class Distribution:
    ex_date: date
    payment_date: date | None
    amount: Decimal  # unadjusted cash per unit


# X1, S8, S9


def month_end_rates(months: Sequence[date], rates: Mapping[date, Decimal]) -> list[Decimal]:
    """The latest rate on or before each month end. One too stale stops."""
    ordered = sorted(rates)
    return [aud_tool.rate_on(rates, ordered, day)[0] for day in months]


def next_published_rates(months: Sequence[date], rates: Mapping[date, Decimal]) -> list[Decimal]:
    """For each month end, the rate of the next published date after the one `rate_on` would choose. A month
    end with no later date keeps its own rate (preregistration-1, amendment 1)."""
    ordered = sorted(rates)
    out = []
    for day in months:
        aud_tool.rate_on(rates, ordered, day)  # a stale choice stops here
        later = bisect_right(ordered, day)
        out.append(rates[ordered[min(later, len(ordered) - 1)]])
    return out


def fx_returns(quotes: Sequence[Decimal]) -> fa.Floats:
    """s between consecutive quotes in USD per AUD, as the panel's builder computes it."""
    return np.array([float(aud_tool.fx_return(a, b)) for a, b in pairwise(quotes)], dtype=np.float64)


def eodhd_rates(rows: Sequence[Mapping[str, Any]]) -> dict[date, Decimal]:
    out: dict[date, Decimal] = {}
    for row in rows:
        day, value = date.fromisoformat(str(row["date"])), Decimal(str(row["close"]))
        if not value.is_finite() or value <= 0:
            raise ev.Stop(f"{day}: an impossible EODHD AUD/USD close")
        if out.setdefault(day, value) != value:
            raise ev.Stop(f"{day}: conflicting EODHD AUD/USD rows")
    if not out:
        raise ev.Stop("no EODHD AUD/USD rows")
    return out


def x1_gaps(h10: Sequence[Decimal], eodhd: Sequence[Decimal]) -> list[Decimal]:
    """|EODHD / H.10 - 1| at each month end."""
    return [abs(CTX.divide(e, h) - ONE) for h, e in zip(h10, eodhd, strict=True)]


def x1_counts(gaps: Sequence[Decimal]) -> dict[str, int]:
    within = {f"within_{b}": sum(1 for g in gaps if g <= b) for b in aud_tool.FX_BANDS}
    return {"month_ends": len(gaps)} | within


def sensitivity(
    panel: tc.FrozenPanel,
    s: fa.Floats,
    classify: Callable[[tc.FrozenPanel], Mapping[str, Any]],
    frozen: Mapping[str, Any],
) -> dict[str, Any]:
    """The bar is no change of class in any effect and metric pair."""
    changes = tc.class_changes(frozen, classify(tc.with_changes(panel, s=s)))
    return {"performed": True, "passes": not changes, "class_changes": changes}


# G1


def payment_date_periods(
    closes: Sequence[tuple[date, Decimal]],
    records: Sequence[Distribution],
    splits: Mapping[date, Decimal] | None = None,
) -> tuple[list[VehiclePeriod], dict[str, int]]:
    """Daily periods when each distribution is reinvested on its payment date, not its ex-date.

    The holder owns u units. On the ex-date the price drop stays in the price return and the cash, D per unit
    held at the close before, is set aside: it earns nothing and isn't in wealth. On the first trading day on
    or after paymentDate it buys units at that day's close. A record with no paymentDate stays on its ex-date.
    Wealth is u times the close, so a period's return is u_after P_t / (u_before P_{t-1}) - 1. A split factor
    f (new units per old unit, as vehicle_series) multiplies u on its day, before that day's distribution,
    so a split alone gives no return.
    """
    days = [d for d, _ in closes]
    counts: Counter = Counter()
    ex_at: dict[int, list[tuple[Decimal, int | None]]] = {}
    for record in records:
        i = _first_on_or_after(days, record.ex_date)
        if i is None:
            counts["after_the_last_close"] += 1
            continue
        if i == 0:
            counts["on_or_before_the_first_close"] += 1
            continue
        if record.payment_date is None:
            counts["no_payment_date_left_on_ex_date"] += 1
            paid: int | None = i
        else:
            paid = _first_on_or_after(days, record.payment_date)
            if paid is None:
                counts["payment_after_the_last_close"] += 1
            elif paid < i:
                counts["payment_before_ex_left_on_ex_date"] += 1
                paid = i
        ex_at.setdefault(i, []).append((record.amount, paid))
    factors: dict[int, Decimal] = {}
    for day, factor in (splits or {}).items():
        i = _first_on_or_after(days, day)
        if i is None or i == 0:
            counts["splits_outside_the_closes"] += 1
            continue
        factors[i] = CTX.multiply(factors.get(i, ONE), factor)
    units = CTX.divide(ONE, closes[0][1])
    pending: dict[int, Decimal] = {}
    periods = []
    for i in range(1, len(closes)):
        (day, close), (_, before) = closes[i], closes[i - 1]
        if close <= 0 or before <= 0:
            raise ValueError(f"a close is not positive at {day}")
        factor = factors.get(i, ONE)
        split_units = CTX.multiply(units, factor)
        cash = pending.pop(i, Decimal(0))
        for amount, paid in ex_at.get(i, []):
            held = CTX.multiply(amount, split_units)
            if paid == i:
                cash = CTX.add(cash, held)
            elif paid is not None:
                pending[paid] = CTX.add(pending.get(paid, Decimal(0)), held)
        after = CTX.add(split_units, CTX.divide(cash, close))
        total = CTX.subtract(CTX.divide(CTX.multiply(after, close), CTX.multiply(units, before)), ONE)
        price = CTX.subtract(CTX.divide(CTX.multiply(close, factor), before), ONE)
        periods.append(VehiclePeriod(closes[i - 1][0], day, price, CTX.subtract(total, price), total))
        units = after
    return periods, dict(counts)


def _first_on_or_after(days: Sequence[date], day: date) -> int | None:
    low, high = 0, len(days)
    while low < high:
        mid = (low + high) // 2
        if days[mid] < day:
            low = mid + 1
        else:
            high = mid
    return low if low < len(days) else None


def fund_records(dividends: Sequence[Mapping[str, Any]]) -> tuple[list[Distribution], int]:
    """Distributions with their unadjusted amount; one without is left out of both series, and counted."""
    out, missing = [], 0
    for record in dividends:
        if record.get("unadjustedValue") is None:
            missing += 1
            continue
        paid = record.get("paymentDate")
        out.append(
            Distribution(
                date.fromisoformat(str(record["date"])),
                date.fromisoformat(str(paid)) if paid else None,
                Decimal(record["unadjustedValue"]),
            )
        )
    return out, missing


def compare_gaps(
    checks: Sequence[ic.Check], ex: Mapping[str, Sequence[Any]], pay: Mapping[str, Sequence[Any]]
) -> list[dict[str, Any]]:
    """Each issuer row's gap (HIO minus issuer, points a year), both ways. None if out of range."""
    rows = []
    for check in checks:
        if check.symbol not in FUNDS or check.symbol not in ex or check.symbol not in pay:
            continue
        row: dict[str, Any] = {"symbol": check.symbol, "kind": check.kind, "end": check.end.isoformat()}
        row |= {"years": check.years, "issuer": check.percent}
        for name, series in (("ex", ex), ("pay", pay)):
            total = ic.compounded(series[check.symbol], check.start, check.end)
            hio = None if total is None else ic.annual_percent(total, check.years)
            row[name] = hio
            row[f"gap_{name}"] = None if hio is None else hio - check.percent
        rows.append(row)
    return rows


def g1_verdict(rows: Sequence[Mapping[str, Any]]) -> str:
    """'supported' only if every SPY gap at least halves in size and every BIL and IEF gap, on the payment
    date, stays within 0.10 points a year. Otherwise 'unexplained'. A row or fund missing isn't a verdict."""
    for symbol in FUNDS:
        if not any(r["symbol"] == symbol for r in rows):
            return f"not performed: no issuer rows for {symbol}"
    if any(r["gap_ex"] is None or r["gap_pay"] is None for r in rows):
        return "not performed: an issuer row lies outside the retained closes"
    spy = all(abs(r["gap_pay"]) <= SPY_FACTOR * abs(r["gap_ex"]) for r in rows if r["symbol"] == "SPY.US")
    bonds = all(abs(r["gap_pay"]) <= BOND_TOLERANCE_PCT for r in rows if r["symbol"] != "SPY.US")
    return "supported" if spy and bonds else "unexplained"


def g1(
    checks: Sequence[ic.Check], eods: Mapping[str, Sequence[Mapping[str, Any]]], fund_data: Mapping[str, Any]
) -> dict[str, Any]:
    """Both series for each fund, the gaps and the verdict. `fund_data`: symbol to (dividends, splits)."""
    ex: dict[str, list[VehiclePeriod]] = {}
    pay: dict[str, list[VehiclePeriod]] = {}
    facts: dict[str, Any] = {}
    for symbol in FUNDS:
        dividends, splits = fund_data[symbol]
        built = ev.analyse(symbol, ev.ETFS[symbol], ev.ETFS[symbol], eods[symbol], dividends, splits)
        if not built.periods:
            return {"verdict": f"not performed: {symbol}'s closes fail the identity checks"}
        records, missing = fund_records(dividends)
        closes = [(date.fromisoformat(str(r["date"])), Decimal(r["close"])) for r in eods[symbol]]
        ex[symbol] = built.periods
        factors = {date.fromisoformat(str(r["date"])): ev.parse_split(r["split"]) for r in splits}
        pay[symbol], counts = payment_date_periods(closes, records, factors)
        facts[symbol] = {"distributions": len(records), "missing_unadjusted": missing, **counts}
    rows = compare_gaps(checks, ex, pay)
    return {"verdict": g1_verdict(rows), "rows": rows, "records": facts}


# Run


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_h10(h10_root: Path) -> tuple[dict[date, Decimal], str]:
    """H.10's series, with its archive hash-checked against the manifest."""
    meta = json.loads((h10_root / "manifest.json").read_text())
    body = (h10_root / "FRB_h10_xml.zip").read_bytes()
    if sha256(body) != meta["sha256"]:
        raise ev.Stop("the retained H.10 archive doesn't match its manifest")
    with zipfile.ZipFile(h10_root / "FRB_h10_xml.zip") as archive:
        rates, _ = aud_tool.parse_h10(archive.read("H10_data.xml"))
    return rates, meta["sha256"]


def summarise(g: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"verdict": g["verdict"]}
    if "rows" in g:
        by_symbol: dict[str, int] = Counter(r["symbol"] for r in g["rows"])
        out |= {"issuer_rows": dict(by_symbol), "records": g["records"]}
    return out


def render(x1: Mapping[str, Any], worst: Decimal, g: Mapping[str, Any], sens: Mapping[str, Any]) -> str:
    lines = [
        "# T-0023 step 5: X1, G1, S8, S9. Licensed-derived: don't commit or share.",
        "",
        f"H.10 quotes {H10_QUOTE}; EODHD's AUDUSD.FOREX quotes {EODHD_QUOTE}. X1 has no bar.",
        "",
        "## X1: H.10 against EODHD at month ends",
        "",
        "| Month ends | " + " | ".join(f"within {b}" for b in aud_tool.FX_BANDS) + " | Worst gap |",
        "|---:|" + "---:|" * (len(aud_tool.FX_BANDS) + 1),
        f"| {x1['month_ends']} | "
        + " | ".join(str(x1[f"within_{b}"]) for b in aud_tool.FX_BANDS)
        + f" | {float(worst):.4%} |",
        "",
        "## G1: reinvestment on the payment date",
        "",
        f"Verdict: **{g['verdict']}**. Supported only if every SPY gap at least halves and every BIL and IEF "
        f"gap stays within {BOND_TOLERANCE_PCT} points a year.",
    ]
    if "rows" in g:
        lines += [
            "",
            "| Fund | Type | Period to | Years | Issuer % | Ex-date % | Gap | Payment-date % | Gap |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for r in g["rows"]:
            ex, pay = r["ex"], r["pay"]
            lines.append(
                f"| {r['symbol']} | {r['kind']} | {r['end']} | {r['years']} | {r['issuer']:.2f} | "
                + " | ".join(
                    "n/a" if v is None else f"{v:{f}}"
                    for v, f in ((ex, ".2f"), (r["gap_ex"], "+.2f"), (pay, ".2f"), (r["gap_pay"], "+.2f"))
                )
                + " |"
            )
        lines += ["", "Records:", ""]
        lines += [f"- {symbol}: {json.dumps(v, sort_keys=True)}" for symbol, v in g["records"].items()]
    lines += ["", "## Sensitivities", ""]
    for name, s in sens.items():
        result = "pass" if s["passes"] else "FAIL"
        lines.append(f"- {name}: {result}; changes: {s['class_changes'] or 'none'}")
    return "\n".join(lines) + "\n"


def run(
    root: Path,
    e0002: Path,
    h10_root: Path,
    out_root: Path,
    *,
    gate: RightsGate,
    commit: str,
    panel_id: str | None = None,
    classify: Callable[[tc.FrozenPanel], Mapping[str, Any]] = tc.classes_of,
) -> dict[str, Any]:
    for path in (root, e0002):
        ev.check_root(path)
    for source in (aud_tool.H10_SOURCE, ev.SOURCE_ID):
        gate.authorise(Operation.BUILD, [source])
    panel, run_dir = tc.load_frozen(root) if panel_id is None else tc.load_frozen(root, panel_id)
    h10, h10_sha = load_h10(h10_root)
    manifest = ev.load_snapshot(e0002, SNAPSHOT)
    eodhd = eodhd_rates(ev._read(e0002, manifest, ev.FOREX, "eod"))
    h10_q, eodhd_q = month_end_rates(panel.months, h10), month_end_rates(panel.months, eodhd)
    gaps = x1_gaps(h10_q, eodhd_q)
    x1 = x1_counts(gaps)
    frozen = classify(panel)
    sens = {
        "S8": sensitivity(panel, fx_returns(eodhd_q), classify, frozen),
        "S9": sensitivity(panel, fx_returns(next_published_rates(panel.months, h10)), classify, frozen),
    }
    checks = ic.load_checks(e0002 / "reference" / ic.REFERENCE)
    eods = {s: ev._read(e0002, manifest, s, "eod") for s in FUNDS}
    data = {s: (ev._read(e0002, manifest, s, "div"), ev._read(e0002, manifest, s, "splits")) for s in FUNDS}
    g = g1(checks, eods, data)
    summary = {
        "panel_run": run_dir.name,
        "h10_sha256": h10_sha,
        "months": len(panel.months) - 1,
        "panel_months_with_s_unlike_h10": int(np.sum(np.abs(fx_returns(h10_q) - panel.s) > 1e-12)),
        "X1": x1,
        "G1": summarise(g),
        **sens,
    }
    tc.write_outputs(tc.new_output(out_root, STEP, commit), render(x1, max(gaps), g, sens), summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    research = Path.home() / ".hio-research"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=research / "T-0023")
    parser.add_argument("--e0002", type=Path, default=research / "E-0002-eodhd")
    parser.add_argument("--h10", type=Path, default=research / "H10")
    args = parser.parse_args(argv)
    try:
        commit = ev.code_commit()["commit"]
        out = run(args.root, args.e0002, args.h10, args.root, gate=ev.make_gate(), commit=commit)
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
