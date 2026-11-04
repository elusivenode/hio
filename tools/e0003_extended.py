"""E-0003's variant V1 (OD-0173): the same comparison back to May 2007, so 2008 is a named window.

AUD cash before 2011 is HIO's accrual of the RBA's FIRMMCRID; from 2011-01-04 it's the RBA's Cash Rate TRI, by
level, with the seam stated. The seam check tests the accrual against the TRI where both exist. Values go only
to reports/ for the owner; stdout and summary-v1.json hold counts and pass or fail. Descriptive: one more
crisis isn't statistical power, and the US funds' 2008 inputs have no independent check.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import e0002_aud as aud_tool
import e0003_aud_cash as base
import eodhd_eval as ev
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation
from hio.contracts.temporal import KnowledgeMode
from hio.library.numeric import CTX
from hio.portfolio import fixed_allocation as fa
from hio.rights.gate import RightsGate
from hio.sources.datasets import parse_rba_f1
from hio.storage.objectstore import LocalObjectStore
from research_reader import Pin, read_panel

HISTORY_SOURCE = "rba.f1_historical"
AONIA = "FIRMMCRID"
TRI_START = date(2011, 1, 4)
WINDOWS = {
    "full": (date.min, date.max),
    "before_2011": (date.min, date(2010, 12, 31)),
    "from_2011": (date(2010, 12, 31), date.max),
    "2008": (date(2007, 12, 31), date(2008, 12, 31)),
    "q1_2020": (date(2019, 12, 31), date(2020, 3, 31)),
    "2022": (date(2021, 12, 31), date(2022, 12, 31)),
}
SEAM_BP = Decimal("0.0001")
SEAM_SHARE = Decimal("0.95")
DAY_BASIS = Decimal(365)


def accrue(rates: Mapping[date, Decimal], until: date | None = None) -> dict[date, Decimal]:
    """A level at each published date, from 1. Each rate accrues simple ACT/365 to the next date, and the last
    to `until` if given. A published rate is never interpolated."""
    days = sorted(rates)
    if until is not None and until > days[-1]:
        days = [*days, until]
    levels = {days[0]: Decimal(1)}
    for a, b in pairwise(days):
        interest = CTX.divide(CTX.multiply(rates[a], Decimal((b - a).days)), 100 * DAY_BASIS)
        levels[b] = CTX.multiply(levels[a], CTX.add(Decimal(1), interest))
    return levels


def joined_levels(accrued: Mapping[date, Decimal], tri: Mapping[date, Decimal]) -> dict[date, Decimal]:
    """The accrual up to the TRI's first level, then the TRI scaled to continue it."""
    start = min(tri)
    if start not in accrued:
        raise ev.Stop(f"the accrual doesn't reach {start}")
    scale = CTX.divide(accrued[start], tri[start])
    joined = {d: v for d, v in accrued.items() if d < start}
    joined |= {d: CTX.multiply(v, scale) for d, v in tri.items()}
    return joined


def seam_check(
    months: Sequence[date], aonia: Mapping[date, Decimal], tri: Mapping[date, Decimal]
) -> dict[str, Any]:
    """The accrual against the TRI, monthly, where both exist. It tests the method, not historical rates."""
    start = max(min(aonia), min(tri))
    span = [m for m in months if m >= start]
    if len(span) < 2:
        return {"months": 0, "passes": False}
    accrued = accrue({d: v for d, v in aonia.items() if d >= start})
    ordered_a, ordered_t = sorted(accrued), sorted(tri)
    within, total = 0, 0
    for a, b in pairwise(span):
        ours = CTX.divide(base.level_on(accrued, ordered_a, b), base.level_on(accrued, ordered_a, a))
        theirs = CTX.divide(base.level_on(tri, ordered_t, b), base.level_on(tri, ordered_t, a))
        total += 1
        within += int(abs(ours - theirs) <= SEAM_BP)
    return {"months": total, "within_1bp": within, "passes": Decimal(within) / Decimal(total) >= SEAM_SHARE}


def load_history(root: Path) -> dict[date, Decimal]:
    meta = json.loads((root / "extract-manifest.json").read_text())
    body = (root / "firmmcrid.csv").read_bytes()
    if hashlib.sha256(body).hexdigest() != meta["sha256"]:
        raise ev.Stop("the extracted series doesn't match its manifest")
    with (root / "firmmcrid.csv").open() as handle:
        rates = {date.fromisoformat(r["date"]): Decimal(r["rate_pct"]) for r in csv.DictReader(handle)}
    if not rates:
        raise ev.Stop("no historical rates")
    return rates


def render(results: Mapping[str, Any], seam: Mapping[str, Any]) -> str:
    text = base.render(results)
    text = text.replace("# E-0003:", "# E-0003 V1 (from May 2007):", 1)
    text = text.replace(
        "**2008 isn't in the sample:** retained RBA cash data starts in 2011.",
        "**2008 is in this sample:** AUD cash before 2011 is HIO's accrual of the RBA's "
        "overnight rate, and the "
        "RBA's index after, with a seam at 2011-01-04.",
    )
    text = text.replace(
        "anything about 2008, a forecast, or a recommendation. About five",
        "a forecast or a recommendation. 2008 is one crisis. About six",
    )
    text = text.replace(
        "what these hypothetical sleeves did from 2011,", "what these hypothetical sleeves did from May 2007,"
    )
    text = text.replace(
        "SPY, IEF and BIL have no independent check;",
        "SPY, IEF and BIL before 2016 have no independent check;",
    )
    text = text[: text.index("- **Earlier AUD cash history:**")].rstrip() + "\n"
    verdict = "passed" if seam["passes"] else "**failed**"
    return text + (
        f"- **Seam check:** {verdict}: the accrual is within 1 bp of the RBA's index in "
        f"{seam.get('within_1bp', 0)} of {seam['months']} months from 2011. It tests the method, not the "
        "historical rates.\n"
        "- **The US funds' 2008 inputs have no independent check:** the issuer check starts in 2016.\n"
    )


@dataclass(frozen=True)
class Assembled:
    """The aligned monthly panel: what every allocation and block length reads."""

    months: list[date]
    returns: fa.Floats  # in AUD, columns as base.SLEEVES
    usd_bills: fa.Floats
    s: fa.Floats
    history_rates_used: int
    facts: dict[str, int]
    seam: dict[str, Any]


def assemble(
    panel: fa.Panel,
    rates: Mapping[date, Decimal],
    aonia: Mapping[date, Decimal],
    tri: Mapping[date, Decimal],
    fx: Mapping[date, Decimal],
) -> Assembled:
    months, usd = aud_tool.monthly_usd(panel)
    first = months[0]
    wanted = {d: v for d, v in rates.items() if d >= date(first.year, first.month, 1)}
    levels = joined_levels(accrue(wanted, until=TRI_START), tri)
    _, s, facts = aud_tool.translate(months, usd, fx)
    cash = base.cash_returns(months, levels)
    return Assembled(
        months,
        base.matrix(usd, panel.sleeves, s, cash),
        usd[:, panel.sleeves.index("cash")],
        s,
        len(wanted),
        facts,
        seam_check(months, aonia, tri),
    )


def run(
    root: Path, e0002_root: Path, h10_root: Path, history: Path, snapshot: str, *, gate: RightsGate
) -> dict[str, Any]:
    ev.check_root(root)
    ev.check_root(e0002_root)
    for source in (HISTORY_SOURCE, base.RBA_SOURCE, aud_tool.H10_SOURCE, ev.SOURCE_ID):
        gate.authorise(Operation.BUILD, [source])
    manifest = json.loads((root / "raw" / "manifest.json").read_text())
    body = (root / "raw" / "rba_f1.csv").read_bytes()
    if hashlib.sha256(body).hexdigest() != manifest["receipt_id"]:
        raise ev.Stop("the retained F1 bytes don't match their manifest")
    tri = base.parse_tri(body)
    aonia = {row.valid_time: row.value for row in parse_rba_f1({AONIA: "aonia"})(body).rows}
    rates = load_history(history)
    summary = json.loads((e0002_root / "summary.json").read_text())
    if summary.get("snapshot") != snapshot or not summary.get("comparison_ran"):
        raise ev.Stop("the USD run for this snapshot hasn't passed")
    hashes = summary["releases"]
    release = e0002_root / "store" / "releases" / ev.SLEEVES["equity"][1] / hashes["equity"]
    core = json.loads((release / "manifest.json").read_text())
    panel, _ = read_panel(
        LocalObjectStore(e0002_root / "store"),
        [Pin(s, ev.SLEEVES[s][1], sha) for s, sha in hashes.items()],
        mode=KnowledgeMode.LATEST,
        cutoff=parse_instant(core["knowledge_cutoff"]),
        gate=gate,
    )
    with zipfile.ZipFile(h10_root / "FRB_h10_xml.zip") as archive:
        fx, _ = aud_tool.parse_h10(archive.read("H10_data.xml"))
    built = assemble(panel, rates, aonia, tri, fx)
    months, returns, s = built.months, built.returns, built.s
    results = base.evaluate(months, returns, built.usd_bills, s, WINDOWS)
    seam, facts, wanted = built.seam, built.facts, built.history_rates_used
    reports = root / "reports"
    reports.mkdir(mode=0o700, exist_ok=True)
    ev.private_write(reports / "owner-report-v1.md", render(results, seam).encode())
    values = json.dumps(results, indent=1, sort_keys=True) + "\n"
    ev.private_write(reports / "owner-values-v1.json", values.encode())
    out = {
        "first_month": months[0].isoformat(),
        "last_month": months[-1].isoformat(),
        "months": int(returns.shape[0]),
        "history_rates_used": wanted,
        **{k: facts[k] for k in ("rates_not_on_the_day", "oldest_rate_days")},
        "windows_available": {k: v["available"] for k, v in results["windows"].items()},
        "interval_classes": base.interval_classes(results),
        "seam_check": seam,
    }
    ev.private_write(root / "summary-v1.json", (json.dumps(out, indent=1, sort_keys=True) + "\n").encode())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "E-0003")
    parser.add_argument("--e0002", type=Path, default=Path.home() / ".hio-research" / "E-0002-eodhd")
    parser.add_argument("--h10", type=Path, default=Path.home() / ".hio-research" / "H10")
    parser.add_argument("--history", type=Path, default=Path.home() / ".hio-research" / "RBA-F1-history")
    parser.add_argument("--snapshot", default="s2")
    args = parser.parse_args(argv)
    try:
        ev.code_commit()
        out = run(args.root, args.e0002, args.h10, args.history, args.snapshot, gate=ev.make_gate())
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
