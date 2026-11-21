"""T-0023 step 3 (OD-0178): SPY, BIL and IEF against references that don't come from EODHD.

Checks C1 to C5 and sensitivities S1 to S5 of docs/evidence/t0023/preregistration-1.md, with its bars as
constants below. Inputs: the frozen panel, EODHD's raw snapshot s2, State Street's NAV files, the Treasury par
feed and E-0001's variant V1, the audited fund reports, each from the workspaces. A check whose reference
isn't there is "not performed", never passed. Values go only to report.md under a new output directory;
stdout and summary.json hold counts, passes and classes. Descriptive: no series here is a validated factor.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

import e0001_run as e1
import e0003_aud_cash as base
import e0003_extended as ext
import e0003_panel as panel_tool
import eodhd_eval as ev
import t0023_common as common
from hio.contracts.rights import Operation
from hio.library.numeric import CTX
from hio.library.vehicle_return import VehicleDay, VehiclePeriod, vehicle_series
from hio.portfolio import fixed_allocation as fa
from hio.rights.gate import RightsGate

D = Decimal
FUNDS = {"SPY": ("equity", "SPY.US"), "BIL": ("bills", "BIL.US"), "IEF": ("treasury", "IEF.US")}
# The preregistration's bars, unchanged. Returns are fractions, so "1.00 point" is 0.01.
C1_CLOSE_BAR = {"SPY": D("0.01"), "IEF": D("0.01"), "BIL": D("0.0025")}
C1_SHARE = (99, 100)
C2_MONTH_BAR = {"SPY": D("0.01"), "IEF": D("0.01"), "BIL": D("0.0025")}
C2_SHARE = (95, 100)
C2_2008_BAR = D("0.01")
C2_ANNUAL_BAR = D("0.001")
C3_2008_BAR = D("0.01")
C3_ANNUAL_BAR = D("0.005")
C4_CORRELATION = D("0.90")
C4_2008_BAR = D("0.04")
C5_PER_SHARE_BAR = D("0.01")
C5_TOTAL_POINTS_BAR = D("0.25")  # the audited figure is a percentage
C5_NAV_BAR = D("0.01")
WINDOW_2008 = ext.WINDOWS["2008"]
WINDOW_2008_2009 = (date(2007, 12, 31), date(2009, 12, 31))
MONTHS_IN_2008 = 12
SPLIT_FIT = D("0.25")  # a split day's NAV jump must lie this near one of the two bases
PAR_FIELDS = ("BC_1MONTH", "BC_10YEAR")
FACT_COLUMNS = (
    "symbol",
    "fiscal_start",
    "fiscal_end",
    "distributions_per_share",
    "total_return_pct",
    "nav_start",
    "nav_end",
    "filing",
    "section",
)
CHECKS = {
    "C1": "Close against NAV at month ends",
    "C2": "HIO's market return against a NAV return, monthly",
    "C3": "BIL against the 1-month par yield, accrued simple ACT/365",
    "C4": "IEF against E-0001 V1's 10-year construction (consistency only)",
    "C5": "Audited fiscal years covering 2008, against EODHD and HIO",
}
SENSITIVITIES = {
    "S1": ("SPY on its NAV return", {"equity": "nav_SPY"}),
    "S2": ("BIL on its NAV return", {"bills": "nav_BIL"}),
    "S3": ("BIL on the 1-month accrual", {"bills": "par_BIL"}),
    "S4": ("IEF on the 10-year construction", {"treasury": "v1_IEF"}),
    "S5": ("S1 and S2 together", {"equity": "nav_SPY", "bills": "nav_BIL"}),
}
BAR_TEXT = {
    "C1": "within 1.00% (SPY, IEF) or 0.25% (BIL) in at least 99% of month ends and in every month of 2008",
    "C2": "within 1.00 point (SPY, IEF) or 0.25 (BIL) in at least 95% of months; 2008 compounded within "
    "1.00 point; full sample within 0.10 points a year",
    "C3": "2008 compounded within 1.00 point; full sample within 0.50 points a year",
    "C4": "monthly correlation at least 0.90 in full and over 2008-2009; 2008 compounded within 4.00 points",
    "C5": "per share within 0.01; total return within 0.25 points; NAV within 0.01",
}


class NotPerformed(Exception):
    """A reference or an input isn't there, so a check can't run. Reported as such, never as a pass."""


@dataclass(frozen=True)
class Fund:
    name: str
    dists: dict[date, Decimal]  # ex-date to EODHD's unadjusted amount
    splits: dict[date, Decimal]  # ex-date to new units per old unit
    periods: list[VehiclePeriod]  # HIO's market return, as ev.analyse builds it
    days: list[date]
    closes: dict[date, Decimal]


@dataclass(frozen=True)
class Fact:
    symbol: str
    start: date
    end: date
    distributions: Decimal | None
    total_return_pct: Decimal | None
    nav_start: Decimal | None
    nav_end: Decimal | None
    filing: str
    section: str


# --- arithmetic shared by the checks


def dec(value: float) -> Decimal:
    """The panel carries twelve decimals, so a float becomes that many and no more."""
    return D(f"{float(value):.12f}")


def share_ok(within: int, total: int, share: tuple[int, int]) -> bool:
    """`within / total >= share`, in integers, so a share exactly at the bar passes and nothing rounds."""
    return total > 0 and within * share[1] >= share[0] * total


def within_bar(gap: Decimal, bar: Decimal) -> bool:
    return abs(gap) <= bar


def verdict(passes: bool) -> str:
    return "pass" if passes else "fail"


def window_mask(months: Sequence[date], window: tuple[date, date]) -> list[bool]:
    """Which monthly returns lie inside a window, as E-0003's evaluation counts them."""
    start, end = window
    return [start <= months[i] and months[i + 1] <= end for i in range(len(months) - 1)]


def compounded(values: Sequence[Decimal]) -> Decimal:
    wealth = D(1)
    for value in values:
        wealth = CTX.multiply(wealth, CTX.add(D(1), value))
    return CTX.subtract(wealth, D(1))


def annualised(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise NotPerformed("no months to annualise")
    wealth = CTX.add(D(1), compounded(values))
    return CTX.subtract(CTX.power(wealth, CTX.divide(D(12), D(len(values)))), D(1))


def picked(values: Sequence[Any], mask: Sequence[bool]) -> list[Any]:
    return [v for v, keep in zip(values, mask, strict=True) if keep]


def gap_2008(ours: Sequence[Decimal], theirs: Sequence[Decimal], in_2008: Sequence[bool]) -> Decimal:
    """The two returns compounded over 2008, and the gap. All twelve months must be there."""
    if sum(in_2008) != MONTHS_IN_2008:
        raise NotPerformed("2008 isn't fully in the panel")
    return abs(compounded(picked(ours, in_2008)) - compounded(picked(theirs, in_2008)))


def gap_annual(ours: Sequence[Decimal], theirs: Sequence[Decimal]) -> Decimal:
    return abs(annualised(ours) - annualised(theirs))


def correlation(ours: Sequence[Decimal], theirs: Sequence[Decimal]) -> Decimal | None:
    """None where it isn't defined, such as a constant series; that fails a bar."""
    if len(ours) < 3:
        raise NotPerformed("fewer than three months to correlate")
    with np.errstate(all="ignore"):
        value = float(np.corrcoef([float(x) for x in ours], [float(x) for x in theirs])[0, 1])
    return dec(value) if np.isfinite(value) else None


def corr_ok(value: Decimal | None) -> bool:
    return value is not None and value >= C4_CORRELATION


def pts(value: Decimal) -> str:
    return f"{value * 100:.4f}"


# --- the five checks, each on numbers it is given


def check_c1(
    rows: Sequence[tuple[date, Decimal | None, Decimal | None]], bar: Decimal, in_2008: Sequence[bool]
) -> dict[str, Any]:
    """`rows`: month end, close, NAV. A month end without a NAV is outside the bar."""
    gaps = [
        None if close is None or nav is None else abs(CTX.subtract(CTX.divide(close, nav), D(1)))
        for _, close, nav in rows
    ]
    flags = [g is not None and g <= bar for g in gaps]
    if sum(in_2008) != MONTHS_IN_2008:
        raise NotPerformed("2008 isn't fully in the panel")
    within = sum(flags)
    every_2008 = all(picked(flags, in_2008))
    known = [g for g in gaps if g is not None]
    passes = share_ok(within, len(rows), C1_SHARE) and every_2008
    return {
        "status": verdict(passes),
        "counts": {
            "month_ends": len(rows),
            "within": within,
            "no_nav": len(rows) - len(known),
            "in_2008": MONTHS_IN_2008,
            "in_2008_within": sum(picked(flags, in_2008)),
        },
        "values": {
            "share within": f"{within / len(rows):.4f}" if rows else "n/a",
            "worst gap (%)": f"{max(known) * 100:.4f}" if known else "n/a",
            "bar (%)": f"{bar * 100:.2f}",
        },
    }


def check_c2(
    ours: Sequence[Decimal], theirs: Sequence[Decimal], in_2008: Sequence[bool], month_bar: Decimal
) -> dict[str, Any]:
    gaps = [abs(a - b) for a, b in zip(ours, theirs, strict=True)]
    within = sum(1 for g in gaps if g <= month_bar)
    window = gap_2008(ours, theirs, in_2008)
    annual = gap_annual(ours, theirs)
    parts = (
        share_ok(within, len(gaps), C2_SHARE),
        within_bar(window, C2_2008_BAR),
        within_bar(annual, C2_ANNUAL_BAR),
    )
    return {
        "status": verdict(all(parts)),
        "counts": {"months": len(gaps), "within": within},
        "values": {
            "monthly bar (points)": pts(month_bar),
            "share within": f"{within / len(gaps):.4f}" if gaps else "n/a",
            "worst month (points)": pts(max(gaps)) if gaps else "n/a",
            "2008 gap (points)": pts(window),
            "annual gap (points)": pts(annual),
        },
    }


def check_c3(ours: Sequence[Decimal], theirs: Sequence[Decimal], in_2008: Sequence[bool]) -> dict[str, Any]:
    window = gap_2008(ours, theirs, in_2008)
    annual = gap_annual(ours, theirs)
    passes = within_bar(window, C3_2008_BAR) and within_bar(annual, C3_ANNUAL_BAR)
    return {
        "status": verdict(passes),
        "counts": {"months": len(ours)},
        "values": {"2008 gap (points)": pts(window), "annual gap (points)": pts(annual)},
    }


def check_c4(
    ours: Sequence[Decimal],
    theirs: Sequence[Decimal],
    in_2008: Sequence[bool],
    in_2008_2009: Sequence[bool],
) -> dict[str, Any]:
    full = correlation(ours, theirs)
    crisis = correlation(picked(ours, in_2008_2009), picked(theirs, in_2008_2009))
    window = gap_2008(ours, theirs, in_2008)

    passes = corr_ok(full) and corr_ok(crisis) and within_bar(window, C4_2008_BAR)
    return {
        "status": verdict(passes),
        "counts": {"months": len(ours), "months_2008_2009": sum(in_2008_2009)},
        "values": {
            "correlation, full": "undefined" if full is None else f"{full:.4f}",
            "correlation, 2008-2009": "undefined" if crisis is None else f"{crisis:.4f}",
            "2008 gap (points)": pts(window),
        },
    }


def covers_2008(fact: Fact) -> bool:
    return fact.start <= WINDOW_2008[1] and fact.end >= date(2008, 1, 1)


def anchor(days: Sequence[date], day: date, *, before: bool) -> date:
    """The last observed day before `day`, or on or before it. Too stale isn't performed."""
    index = (bisect_left if before else bisect_right)(days, day) - 1
    if index < 0 or (day - days[index]).days > base.MAX_STALE_DAYS:
        raise NotPerformed(f"no observed day within {base.MAX_STALE_DAYS} days of {day}")
    return days[index]


def period_return(periods: Sequence[VehiclePeriod], start: date, end: date) -> Decimal:
    chain = [p for p in periods if p.start >= start and p.end <= end]
    if not chain or chain[0].start != start or chain[-1].end != end:
        raise NotPerformed(f"HIO's periods don't run from {start} to {end}")
    return compounded([p.total_return for p in chain])


def _unperformed(why: str) -> dict[str, Any]:
    return {"status": f"not performed: {why}", "values": {}}


def check_c5_fact(fact: Fact, fund: Fund, nav: Mapping[date, Decimal] | None) -> dict[str, dict[str, Any]]:
    """One audited fiscal year: distributions per share, total return, and NAV at both ends."""
    out: dict[str, dict[str, Any]] = {}
    if fact.distributions is None:
        out["distributions"] = _unperformed("the report's distributions per share weren't recorded")
    else:
        paid = sum((a for d, a in fund.dists.items() if fact.start <= d <= fact.end), D(0))
        gap = paid - fact.distributions
        out["distributions"] = {
            "status": verdict(within_bar(gap, C5_PER_SHARE_BAR)),
            "values": {"EODHD": f"{paid:.4f}", "audited": f"{fact.distributions:.4f}", "gap": f"{gap:.4f}"},
        }
    if fact.total_return_pct is None:
        out["total_return"] = _unperformed("the report's total return wasn't recorded")
    else:
        try:
            first = anchor(fund.days, fact.start, before=True)
            last = anchor(fund.days, fact.end, before=False)
            hio = period_return(fund.periods, first, last)
        except NotPerformed as exc:
            out["total_return"] = _unperformed(str(exc))
        else:
            gap = hio * 100 - fact.total_return_pct
            out["total_return"] = {
                "status": verdict(within_bar(gap, C5_TOTAL_POINTS_BAR)),
                "values": {
                    "HIO (%)": f"{hio * 100:.4f}",
                    "audited (%)": f"{fact.total_return_pct:.4f}",
                    "gap (points)": f"{gap:.4f}",
                },
            }
    if nav is None:
        out["nav"] = _unperformed("no NAV file for this fund")
    elif fact.nav_start is None or fact.nav_end is None:
        out["nav"] = _unperformed("the report's NAV at one end wasn't recorded")
    else:
        try:
            days = sorted(nav)
            first = nav[anchor(days, fact.start, before=True)]
            last = nav[anchor(days, fact.end, before=False)]
        except NotPerformed as exc:
            out["nav"] = _unperformed(str(exc))
        else:
            gaps = (first - fact.nav_start, last - fact.nav_end)
            out["nav"] = {
                "status": verdict(all(within_bar(g, C5_NAV_BAR) for g in gaps)),
                "values": {"start gap": f"{gaps[0]:.4f}", "end gap": f"{gaps[1]:.4f}"},
            }
    return out


def combine(statuses: Sequence[str]) -> str:
    """A failed bar is a result and wins; otherwise anything unperformed keeps it from being a pass."""
    if any(s == "fail" for s in statuses):
        return "fail"
    unperformed = [s for s in statuses if s.startswith("not performed")]
    return unperformed[0] if unperformed else "pass"


def check_c5(facts: Sequence[Fact], fund: Fund, nav: Mapping[date, Decimal] | None) -> dict[str, Any]:
    chosen = [f for f in facts if f.symbol == fund.name and covers_2008(f)]
    if not chosen:
        raise NotPerformed("no audited fiscal year covering 2008 for this fund")
    rows, statuses = [], []
    for fact in chosen:
        parts = check_c5_fact(fact, fund, nav)
        statuses += [p["status"] for p in parts.values()]
        row = {
            "fiscal year": f"{fact.start} to {fact.end}",
            "filing": fact.filing,
            "section": fact.section,
        }
        for name, part in parts.items():
            row[name] = part["status"]
            row |= {f"{name}: {k}": v for k, v in part["values"].items()}
        rows.append(row)
    return {
        "status": combine(statuses),
        "counts": {
            "fiscal_years": len(chosen),
            "sub_checks": len(statuses),
            "sub_checks_passed": statuses.count("pass"),
            "sub_checks_failed": statuses.count("fail"),
            "sub_checks_not_performed": sum(1 for s in statuses if s.startswith("not performed")),
        },
        "values": {},
        "rows": rows,
    }


# --- inputs


def distributions_of(records: Sequence[Mapping[str, Any]]) -> dict[date, Decimal]:
    out: dict[date, Decimal] = {}
    for record in records:
        raw = record.get("unadjustedValue")
        if raw is None:
            raise ev.Stop("a distribution has no unadjusted amount")
        day = date.fromisoformat(str(record["date"]))
        out[day] = out.get(day, D(0)) + D(raw)
    return out


def splits_of(records: Sequence[Mapping[str, Any]]) -> dict[date, Decimal]:
    out: dict[date, Decimal] = {}
    for record in records:
        try:
            factor = ev.parse_split(record["split"])
        except (ValueError, ArithmeticError, KeyError):
            raise ev.Stop("a split can't be read") from None
        day = date.fromisoformat(str(record["date"]))
        out[day] = CTX.multiply(out.get(day, D(1)), factor)
    return out


def load_funds(e0002: Path, manifest: Mapping[str, Any]) -> dict[str, Fund]:
    """Each fund as the panel built it: ev.analyse over the raw snapshot, which must qualify."""
    listing = ev._read(e0002, manifest, "EXCHANGE.US", "symbols")
    out = {}
    for name, (_, symbol) in FUNDS.items():
        eod = ev._read(e0002, manifest, symbol, "eod")
        dividends = ev._read(e0002, manifest, symbol, "div")
        splits = ev._read(e0002, manifest, symbol, "splits")
        series = ev.analyse(
            symbol, ev.ETFS[symbol], ev.quote_currency(listing, symbol), eod, dividends, splits
        )
        if not all(series.qualified.values()):
            raise ev.Stop(f"{symbol} didn't qualify")
        closes = {date.fromisoformat(str(r["date"])): D(r["close"]) for r in eod}
        out[name] = Fund(
            name, distributions_of(dividends), splits_of(splits), series.periods, series.days, closes
        )
    return out


def load_nav(path: Path) -> dict[date, Decimal] | None:
    """date,nav rows, or None when the file isn't there."""
    if not path.is_file():
        return None
    reader = csv.DictReader(path.read_text().splitlines())
    if reader.fieldnames is None or {"date", "nav"} - set(reader.fieldnames):
        raise ev.Stop(f"{path.name} lacks the date and nav columns")
    out: dict[date, Decimal] = {}
    for row in reader:
        try:
            day, value = date.fromisoformat(row["date"]), D(row["nav"])
        except (ValueError, ArithmeticError):
            raise ev.Stop(f"{path.name}: an unreadable row") from None
        if not value.is_finite() or value <= 0:
            raise ev.Stop(f"{path.name}: an impossible NAV on {day}")
        if day in out:
            raise ev.Stop(f"{path.name}: {day} repeated")
        out[day] = value
    if not out:
        raise ev.Stop(f"{path.name} holds no rows")
    return out


def _optional(text: str) -> Decimal | None:
    if not text.strip():
        return None
    try:
        value = D(text)
    except ArithmeticError:
        raise ev.Stop("an unreadable number in the audited facts") from None
    if not value.is_finite():
        raise ev.Stop("an unreadable number in the audited facts")
    return value


def load_facts(path: Path) -> list[Fact] | None:
    """The audited reports' figures, read by hand into audited-facts.csv; None when it isn't there."""
    if not path.is_file():
        return None
    reader = csv.DictReader(path.read_text().splitlines())
    if reader.fieldnames is None or set(FACT_COLUMNS) - set(reader.fieldnames):
        raise ev.Stop("audited-facts.csv lacks a declared column")
    out, seen = [], set()
    for row in reader:
        if row["symbol"] not in FUNDS:
            raise ev.Stop("audited-facts.csv names a fund this tool doesn't check")
        try:
            start, end = date.fromisoformat(row["fiscal_start"]), date.fromisoformat(row["fiscal_end"])
        except ValueError:
            raise ev.Stop("audited-facts.csv has an unreadable fiscal date") from None
        if end < start or (row["symbol"], start, end) in seen:
            raise ev.Stop("audited-facts.csv has a backwards or repeated fiscal year")
        seen.add((row["symbol"], start, end))
        out.append(
            Fact(
                row["symbol"],
                start,
                end,
                _optional(row["distributions_per_share"]),
                _optional(row["total_return_pct"]),
                _optional(row["nav_start"]),
                _optional(row["nav_end"]),
                row["filing"],
                row["section"],
            )
        )
    return out


def parse_par(body: bytes, fields: Sequence[str] = PAR_FIELDS) -> dict[str, dict[date, Decimal]]:
    """Par yields by date, read as E-0001 reads its feed: blank, null or N/A is absent; other bad stops."""
    out: dict[str, dict[date, Decimal]] = {f: {} for f in fields}
    for element in ET.fromstring(body).iter():
        if not element.tag.endswith("}properties"):
            continue
        values = {child.tag.rsplit("}", 1)[-1]: child for child in element}
        stamp = values.get("NEW_DATE")
        if stamp is None or not (stamp.text or "").strip():
            raise ev.Stop("a par row has no date")
        day = date.fromisoformat((stamp.text or "").strip()[:10])
        for field in fields:
            cell = values.get(field)
            text = (cell.text or "").strip() if cell is not None else ""
            if cell is None or cell.get(f"{e1.METADATA}null") == "true" or text in {"", "N/A"}:
                continue
            try:
                value = D(text)
            except ArithmeticError:
                raise ev.Stop(f"{day}: a non-numeric value in {field}") from None
            if not value.is_finite() or not e1.LOW <= value <= e1.HIGH:
                raise ev.Stop(f"{day}: a value out of range in {field}")
            if out[field].get(day, value) != value:
                raise ev.Stop(f"{day}: conflicting rows in {field}")
            out[field][day] = value
    return out


def load_par(e0001: Path) -> dict[str, dict[date, Decimal]]:
    try:
        manifest = e1.verify_retained(e0001)
    except e1.Stop as exc:
        raise ev.Stop(str(exc)) from None
    out: dict[str, dict[date, Decimal]] = {f: {} for f in PAR_FIELDS}
    for entry in manifest["files"]:
        for field, rates in parse_par((e0001 / entry["path"]).read_bytes()).items():
            for day, value in rates.items():
                if out[field].get(day, value) != value:
                    raise ev.Stop(f"{day}: conflicting rows in {field} across files")
                out[field][day] = value
    return out


def load_v1(e0001: Path) -> tuple[list[tuple[date, date, Decimal]], str]:
    """V1's column r, from the release variant-summary.json names, checked against that release's manifest."""
    release = json.loads((e0001 / "variant-summary.json").read_text())["release"]
    folder = e0001 / "store-variant" / "releases" / e1.DATASET_ID / release
    data = (folder / "data.csv").read_bytes()
    entries = {f["path"]: f["sha256"] for f in json.loads((folder / "manifest.json").read_text())["files"]}
    digest = hashlib.sha256(data).hexdigest()
    if entries.get("data.csv") != digest:
        raise ev.Stop("V1's data.csv doesn't match its release manifest")
    rows = csv.DictReader(data.decode().splitlines())
    periods = [
        (date.fromisoformat(r["period_start"]), date.fromisoformat(r["period_end"]), D(r["r"])) for r in rows
    ]
    if not periods:
        raise ev.Stop("V1 holds no periods")
    return periods, digest


# --- NAV returns


def nav_periods(
    nav: Mapping[date, Decimal], dists: Mapping[date, Decimal], splits: Mapping[date, Decimal]
) -> tuple[list[VehiclePeriod], dict[str, int]]:
    """A return from NAV in place of close, with EODHD's distributions and splits placed on the first NAV day
    on or after their ex-dates, as ev.analyse places them on traded days.

    A split changes the NAV per share only if the NAV history is unadjusted. On each split day the NAV jump
    is tested: if it follows 1/f, the factor is applied as vehicle_series does; if there is no jump, the NAV
    history is already adjusted, so no factor applies and the earlier distributions are put in new units.
    A jump that fits neither stops.
    """
    days = sorted(nav)
    if len(days) < 2:
        raise ev.Stop("a NAV file with fewer than two days")
    counts: Counter = Counter()

    def place(
        actions: Mapping[date, Decimal], join: Callable[[Decimal, Decimal], Decimal]
    ) -> dict[date, Decimal]:
        out: dict[date, Decimal] = {}
        for day, amount in sorted(actions.items()):
            index = bisect_left(days, day)
            if index == len(days):
                counts["actions_after_last_nav_day"] += 1
            elif index == 0:
                counts["actions_before_the_first_period"] += 1
            else:
                target = days[index]
                counts["actions_moved_to_next_nav_day"] += int(target != day)
                out[target] = join(out[target], amount) if target in out else amount
        return out

    paid = place(dists, CTX.add)
    raw_factors = place(splits, CTX.multiply)
    factors: dict[date, Decimal] = {}
    adjusted: dict[date, Decimal] = {}
    for day, factor in sorted(raw_factors.items()):
        if factor == 1:
            continue
        ratio = CTX.divide(nav[day], nav[days[bisect_left(days, day) - 1]])
        unadjusted_fit = abs(CTX.subtract(CTX.multiply(ratio, factor), D(1)))
        adjusted_fit = abs(CTX.subtract(ratio, D(1)))
        if min(unadjusted_fit, adjusted_fit) > SPLIT_FIT:
            raise ev.Stop(f"the NAV jump on {day} fits neither basis of its split")
        if adjusted_fit < unadjusted_fit:
            adjusted[day] = factor
            counts["splits_nav_already_adjusted"] += 1
        else:
            factors[day] = factor
            counts["splits_nav_unadjusted"] += 1
    for day in list(paid):
        later = [f for s, f in adjusted.items() if s > day]
        for factor in later:
            paid[day] = CTX.divide(paid[day], factor)
    bars = [VehicleDay(d, nav[d], paid.get(d, D(0)), factors.get(d, D(1))) for d in days]
    periods = vehicle_series(bars)
    counts["nav_days"] = len(days)
    counts["distributions_applied"] = len(paid)
    return periods, dict(counts)


def compound_months(periods: Sequence[tuple[date, date, Decimal]], months: Sequence[date]) -> fa.Floats:
    """Periods compounded between the panel's month ends. A gap or a short end isn't performed."""
    try:
        return common.compound_between([(a, b, float(r)) for a, b, r in periods], months)
    except ev.Stop as exc:
        raise NotPerformed(str(exc)) from None


def par_months(rates: Mapping[date, Decimal], months: Sequence[date]) -> fa.Floats:
    """The 1-month par yield accrued simple ACT/365 on each published date, between the panel's month ends."""
    if not rates:
        raise NotPerformed("no 1-month par yields")
    last = max(rates)
    until = months[-1] if 0 < (months[-1] - last).days <= base.MAX_STALE_DAYS else None
    try:
        return base.cash_returns(months, ext.accrue(rates, until=until))
    except ev.Stop as exc:
        raise NotPerformed(str(exc)) from None


def decimals(values: Sequence[float]) -> list[Decimal]:
    return [dec(v) for v in values]


# --- sensitivities


def sensitivity(
    panel: common.FrozenPanel, frozen: Mapping[str, Any], changes: Mapping[str, fa.Floats]
) -> dict[str, Any]:
    """The comparison rerun with named USD sleeves replaced. The bar: no class changes."""
    moved = common.class_changes(frozen, common.classes_of(common.with_changes(panel, usd=changes)))
    return {"status": verdict(not moved), "changes": moved}


# --- the run


@dataclass
class Source:
    """A monthly series, or why it can't be had."""

    values: fa.Floats | None
    why: str = ""


def attempt(build: Callable[[], fa.Floats]) -> Source:
    try:
        return Source(build())
    except NotPerformed as exc:
        return Source(None, str(exc))


def guarded(run: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return run()
    except NotPerformed as exc:
        return {"status": f"not performed: {exc}", "counts": {}, "values": {}}


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def run_checks(
    panel: common.FrozenPanel,
    funds: Mapping[str, Fund],
    navs: Mapping[str, Mapping[date, Decimal] | None],
    par: Mapping[str, Mapping[date, Decimal]],
    v1: Sequence[tuple[date, date, Decimal]],
    facts: Sequence[Fact] | None,
) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, Source], dict[str, Any]]:
    months = panel.months
    usd = common.usd_columns(panel)
    ours = {name: decimals(usd[column]) for name, (column, _) in FUNDS.items()}
    in_2008 = window_mask(months, WINDOW_2008)
    in_2008_2009 = window_mask(months, WINDOW_2008_2009)
    month_ends_2008 = [WINDOW_2008[0] < d <= WINDOW_2008[1] for d in months]
    checks: dict[str, dict[str, dict[str, Any]]] = {c: {} for c in CHECKS}
    sources: dict[str, Source] = {}
    nav_counts: dict[str, Any] = {}

    for name, fund in funds.items():
        nav = navs[name]
        if nav is None:
            why = f"no nav-{name.lower()}.csv"
            checks["C1"][name] = checks["C2"][name] = _unperformed(why) | {"counts": {}}
            sources[f"nav_{name}"] = Source(None, why)
        else:
            rows = [(d, fund.closes.get(d), nav.get(d)) for d in months]
            bar = C1_CLOSE_BAR[name]
            checks["C1"][name] = guarded(lambda rows=rows, bar=bar: check_c1(rows, bar, month_ends_2008))
            built, nav_counts[name] = nav_periods(nav, fund.dists, fund.splits)
            periods = [(p.start, p.end, p.total_return) for p in built]
            source = sources[f"nav_{name}"] = attempt(
                lambda periods=periods: compound_months(periods, months)
            )
            if source.values is None:
                checks["C2"][name] = _unperformed(source.why) | {"counts": {}}
            else:
                theirs = decimals(source.values)
                checks["C2"][name] = guarded(
                    lambda name=name, theirs=theirs: check_c2(ours[name], theirs, in_2008, C2_MONTH_BAR[name])
                )

    sources["par_BIL"] = attempt(lambda: par_months(par["BC_1MONTH"], months))
    if sources["par_BIL"].values is None:
        checks["C3"]["BIL"] = _unperformed(sources["par_BIL"].why) | {"counts": {}}
    else:
        accrued = decimals(sources["par_BIL"].values)
        checks["C3"]["BIL"] = guarded(lambda: check_c3(ours["BIL"], accrued, in_2008))
    sources["v1_IEF"] = attempt(lambda: compound_months(v1, months))
    if sources["v1_IEF"].values is None:
        checks["C4"]["IEF"] = _unperformed(sources["v1_IEF"].why) | {"counts": {}}
    else:
        construction = decimals(sources["v1_IEF"].values)
        checks["C4"]["IEF"] = guarded(lambda: check_c4(ours["IEF"], construction, in_2008, in_2008_2009))

    for name, fund in funds.items():
        if facts is None:
            checks["C5"][name] = _unperformed("no audited-facts.csv") | {"counts": {}}
        else:
            checks["C5"][name] = guarded(lambda fund=fund, name=name: check_c5(facts, fund, navs[name]))
    return checks, sources, nav_counts


def run_sensitivities(panel: common.FrozenPanel, sources: Mapping[str, Source]) -> dict[str, dict[str, Any]]:
    frozen = common.classes_of(panel)
    out: dict[str, dict[str, Any]] = {}
    for key, (label, wanted) in SENSITIVITIES.items():
        missing = [f"{sources[s].why}" for s in wanted.values() if sources[s].values is None]
        if missing:
            out[key] = {"label": label, "status": f"not performed: {missing[0]}", "changes": []}
            continue
        changes = {column: sources[s].values for column, s in wanted.items()}
        out[key] = {"label": label, **sensitivity(panel, frozen, changes)}
    return out


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return lines


def render(
    checks: Mapping[str, Mapping[str, Mapping[str, Any]]],
    sensitivities: Mapping[str, Mapping[str, Any]],
    panel_id: str,
    commit: str,
) -> str:
    lines = [
        "# T-0023 step 3: the three sleeves against references. For the owner: licensed-derived values; "
        "don't commit or share.",
        "",
        f"Panel `{panel_id}`, code `{commit}`. Bars are the preregistration's, unchanged. A failed bar is a "
        "result and narrows the claim. A NAV isn't a traded close and holds no distributions. Nothing here "
        "validates a factor.",
    ]
    for check, label in CHECKS.items():
        lines += ["", f"## {check}: {label}", "", f"Bar: {BAR_TEXT[check]}.", ""]
        sleeves = checks[check]
        if not sleeves:
            lines.append("No sleeve.")
            continue
        flat = {s: r for s, r in sleeves.items() if not r.get("rows")}
        keys = list(dict.fromkeys(k for r in flat.values() for k in r.get("values", {})))
        if flat:
            lines += table(
                ["Sleeve", "Status", *keys],
                [[s, r["status"], *(r.get("values", {}).get(k, "") for k in keys)] for s, r in flat.items()],
            )
        for sleeve, result in sleeves.items():
            if result.get("rows"):
                columns = list(dict.fromkeys(k for row in result["rows"] for k in row))
                lines += ["", f"{sleeve}: {result['status']}", ""]
                lines += table(columns, [[row.get(c, "") for c in columns] for row in result["rows"]])
    lines += ["", "## Sensitivities", "", "Bar: no change of class in any effect and metric pair.", ""]
    lines += table(
        ["Id", "Change", "Status", "Class changes"],
        [[k, v["label"], v["status"], "; ".join(v["changes"]) or "none"] for k, v in sensitivities.items()],
    )
    return "\n".join(lines) + "\n"


def run(
    root: Path, e0002: Path, e0001: Path, *, gate: RightsGate, code: Mapping[str, str], now: Any = None
) -> dict[str, Any]:
    for path in (root, e0002, e0001):
        ev.check_root(path)
    gate.authorise(Operation.BUILD, [ev.SOURCE_ID, e1.SOURCE_ID])
    panel, run_dir = common.load_frozen(root)
    record = json.loads((run_dir / "run.json").read_text())
    manifest = ev.load_snapshot(e0002, panel_tool.SNAPSHOT)
    funds = load_funds(e0002, manifest)
    reference = root / "reference"
    navs = {name: load_nav(reference / f"nav-{name.lower()}.csv") for name in FUNDS}
    facts = load_facts(reference / "audited-facts.csv")
    par = load_par(e0001)
    v1, v1_sha = load_v1(e0001)

    checks, sources, nav_counts = run_checks(panel, funds, navs, par, v1, facts)
    sensitivities = run_sensitivities(panel, sources)
    out = common.new_output(root, "step3", code["commit"], now)
    report = render(checks, sensitivities, record["panel_id"], code["commit"])
    summary = {
        "panel_id": record["panel_id"],
        "code": dict(code),
        "inputs": {
            "panel_sha256": record["panel_sha256"],
            "snapshot": panel_tool.SNAPSHOT,
            "v1_data_sha256": v1_sha,
            **{f"nav_{n.lower()}_sha256": sha256_file(reference / f"nav-{n.lower()}.csv") for n in FUNDS},
            "audited_facts_sha256": sha256_file(reference / "audited-facts.csv"),
        },
        "checks": {
            c: {s: {"status": r["status"], "counts": r.get("counts", {})} for s, r in rows.items()}
            for c, rows in checks.items()
        },
        "nav_counts": nav_counts,
        "sensitivities": {
            k: {"status": v["status"], "class_changes": len(v["changes"]), "changes": v["changes"]}
            for k, v in sensitivities.items()
        },
        "report_sha256": hashlib.sha256(report.encode()).hexdigest(),
        "output": out.name,
    }
    common.write_outputs(out, report, summary)
    return summary


def stdout_view(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "panel_id": summary["panel_id"],
        "checks": {c: {s: r["status"] for s, r in rows.items()} for c, rows in summary["checks"].items()},
        "sensitivities": {k: v["status"] for k, v in summary["sensitivities"].items()},
        "class_changes": {k: v["changes"] for k, v in summary["sensitivities"].items() if v["changes"]},
        "report_sha256": summary["report_sha256"],
        "output": summary["output"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    research = Path.home() / ".hio-research"
    parser.add_argument("--root", type=Path, default=research / "T-0023")
    parser.add_argument("--e0002", type=Path, default=research / "E-0002-eodhd")
    parser.add_argument("--e0001", type=Path, default=research / "E-0001")
    args = parser.parse_args(argv)
    try:
        summary = run(args.root, args.e0002, args.e0001, gate=ev.make_gate(), code=ev.code_commit())
    except ev.Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # the type only: a message could hold a value
        print(f"stopped: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(stdout_view(summary), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
