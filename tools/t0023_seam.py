"""T-0023 step 4 (OD-0178): the cash seam, checked against the RBA's own target. Checks M1, M2, R1, R2, R3 and
sensitivities S6 and S7 of docs/evidence/t0023/preregistration-1.md, with its bars as constants. Values go to
report.md and summary.json under the output directory; stdout holds hashes, counts, passes and classes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

import e0003_aud_cash as base
import e0003_extended as ext
import e0003_panel as panel_tool
import eodhd_eval as ev
import t0023_common as common
from hio.contracts.rights import Operation
from hio.library.numeric import CTX
from hio.rights.gate import RightsGate
from hio.sources.datasets import parse_rba_f1

TRI_START = date(2011, 1, 4)
TRI_ID, AONIA_ID, TARGET_ID = "FIRMMCTRI", "FIRMMCRID", "FIRMMCRTD"
SERIES = {TRI_ID: "tri", AONIA_ID: "aonia", TARGET_ID: "target"}
PAGE = Path("raw") / "rba-cash-rate.html"
M1_BP = Decimal("0.0001")
M1_SHARE = Decimal("0.95")
M2_DRIFT = Decimal("0.001")
R1_PCT_POINTS = Decimal("0.05")  # 5 bp, in the rates' own unit (percent)
R1_SHARE = Decimal("0.95")
R2_BP = Decimal("0.0001")
R2_SHARE = Decimal("0.95")
R1_YEARS = (2007, 2008, 2009, 2010)
REBUILD_TOLERANCE = 1e-9
WORDS = (
    "M1 and M2 test the method only. R1 and R2 test consistency with the RBA's own target, not the rates' "
    "accuracy against a third party. A benchmark accrual isn't an investable deposit return, and nothing "
    "here changes that."
)


class _Rows(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


_DAY = re.compile(r"^\d{1,2} [A-Za-z]{3,9} \d{4}$")
_NUMBER = re.compile(r"^\d+(\.\d+)?$")


def _effective(cell: str) -> date | None:
    if not _DAY.match(cell):
        return None
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(cell, fmt).date()  # noqa: DTZ007 -- a calendar label
        except ValueError:
            continue
    return None


def parse_target_page(text: str, window_start: date) -> tuple[dict[date, Decimal], list[str]]:
    """Effective date to target percent, from the page's table rows, and the rows that couldn't be read.
    A row is data when its first cell holds a digit. One with no readable date or target number (a range,
    text) is counted and listed, never guessed. Such a row dated on or after `window_start` stops."""
    parser = _Rows()
    parser.feed(text)
    steps: dict[date, Decimal] = {}
    unreadable: list[str] = []
    for cells in parser.rows:
        if not cells or not any(ch.isdigit() for ch in cells[0]):
            continue  # a header or a spacer
        day = _effective(cells[0])
        target = cells[-1].replace("%", "").replace("\xa0", " ").strip() if len(cells) >= 2 else ""
        if day is None or not _NUMBER.match(target):
            unreadable.append(" | ".join(cells))
            if day is not None and day >= window_start:
                raise ev.Stop(f"no readable target for {day}, inside the panel's window")
            continue
        try:
            value = Decimal(target)
        except InvalidOperation:  # pragma: no cover -- _NUMBER already matched
            unreadable.append(" | ".join(cells))
            continue
        if steps.get(day, value) != value:
            raise ev.Stop(f"two different targets effective {day}")
        steps[day] = value
    if not steps:
        raise ev.Stop("no readable target rows")
    return steps, unreadable


def target_on(steps: Mapping[date, Decimal], day: date) -> Decimal | None:
    """The target in force on `day`: from its effective date until the next. None before the first row."""
    ordered = sorted(steps)
    index = bisect_right(ordered, day) - 1
    return None if index < 0 else steps[ordered[index]]


def _target_rates(steps: Mapping[date, Decimal], days: Sequence[date]) -> dict[date, Decimal]:
    out = {}
    for day in days:
        value = target_on(steps, day)
        if value is None:
            raise ev.Stop(f"no target in force on {day}")
        out[day] = value
    return out


def pre_2011(history: Mapping[date, Decimal], first_month: date) -> dict[date, Decimal]:
    """The historical rates a pre-2011 comparison covers: from the panel's first month to the TRI."""
    start = date(first_month.year, first_month.month, 1)
    return {d: v for d, v in history.items() if start <= d < TRI_START}


def _month_returns(months: Sequence[date], levels: Mapping[date, Decimal]) -> list[Decimal]:
    ordered = sorted(levels)
    marks = [base.level_on(levels, ordered, m) for m in months]
    return [CTX.divide(b, a) - 1 for a, b in pairwise(marks)]


def check_m1(
    months: Sequence[date], aonia: Mapping[date, Decimal], tri: Mapping[date, Decimal]
) -> dict[str, Any]:
    """The accrual against the TRI, monthly, from 2011. At least 95% of months within 1 bp."""
    seam = ext.seam_check(months, aonia, tri)
    if not seam["months"]:
        return {"performed": False, "why": "fewer than two panel months where both exist", "passes": False}
    share = Decimal(seam["within_1bp"]) / Decimal(seam["months"])
    return {
        "performed": True,
        "months": seam["months"],
        "within_1bp": seam["within_1bp"],
        "passes": share >= M1_SHARE,
    }


def check_m2(
    months: Sequence[date], aonia: Mapping[date, Decimal], tri: Mapping[date, Decimal]
) -> dict[str, Any]:
    """Cumulative drift of the accrual on F1's FIRMMCRID over the TRI, each rebased at the first common date,
    at the panel's last month. Within 0.10%."""
    common_days = sorted(set(aonia) & set(tri))
    if not common_days or months[-1] <= common_days[0]:
        return {"performed": False, "why": "no common date before the panel's last month", "passes": False}
    first = common_days[0]
    accrued = ext.accrue({d: v for d, v in aonia.items() if d >= first})
    ours = CTX.divide(base.level_on(accrued, sorted(accrued), months[-1]), accrued[first])
    theirs = CTX.divide(base.level_on(tri, sorted(tri), months[-1]), tri[first])
    drift = abs(CTX.divide(ours, theirs) - 1)
    return {"performed": True, "rebased_at": first.isoformat(), "passes": drift <= M2_DRIFT}


def check_r1(
    history: Mapping[date, Decimal], steps: Mapping[date, Decimal], first_month: date
) -> dict[str, Any]:
    """Each published pre-2011 FIRMMCRID day against the target in force, per calendar year 2007 to 2010:
    within 5 bp on at least 95% of days, each year."""
    days = pre_2011(history, first_month)
    target = _target_rates(steps, sorted(days))
    years: dict[str, Any] = {}
    for year in R1_YEARS:
        in_year = [d for d in sorted(days) if d.year == year]
        if not in_year:
            years[str(year)] = {"performed": False, "why": "no published days", "passes": False}
            continue
        within = sum(abs(days[d] - target[d]) <= R1_PCT_POINTS for d in in_year)
        years[str(year)] = {
            "days": len(in_year),
            "within_5bp": within,
            "passes": Decimal(within) / Decimal(len(in_year)) >= R1_SHARE,
        }
    return {"years": years, "passes": all(y["passes"] for y in years.values())}


def pre_2011_levels(rates: Mapping[date, Decimal]) -> dict[date, Decimal]:
    return ext.accrue(rates, until=TRI_START)


def check_r2(
    months: Sequence[date], history: Mapping[date, Decimal], steps: Mapping[date, Decimal]
) -> dict[str, Any]:
    """Pre-2011 accrual on the target against the accrual on FIRMMCRID, monthly: 95% of months within 1 bp."""
    rid = pre_2011(history, months[0])
    if not rid:
        return {"performed": False, "why": "no pre-2011 rates", "passes": False}
    ours = pre_2011_levels(_target_rates(steps, sorted(rid)))
    theirs = pre_2011_levels(rid)
    span = [m for m in months if min(rid) <= m <= max(theirs)]
    if len(span) < 2:
        return {"performed": False, "why": "fewer than two pre-2011 months", "passes": False}
    pairs = zip(_month_returns(span, ours), _month_returns(span, theirs), strict=True)
    within = sum(abs(a - b) <= R2_BP for a, b in pairs)
    total = len(span) - 1
    return {
        "performed": True,
        "months": total,
        "within_1bp": within,
        "passes": Decimal(within) / Decimal(total) >= R2_SHARE,
    }


def check_r3(steps: Mapping[date, Decimal], published: Mapping[date, Decimal]) -> dict[str, Any]:
    """The page's target against F1's FIRMMCRTD from 2011: every published day equal."""
    days = sorted(d for d in published if d >= TRI_START)
    if not days:
        return {"performed": False, "why": "F1 holds no FIRMMCRTD from 2011", "passes": False}
    equal = sum(target_on(steps, d) == published[d] for d in days)
    return {"performed": True, "days": len(days), "equal": equal, "passes": equal == len(days)}


def build_cash(
    panel: common.FrozenPanel,
    rates: Mapping[date, Decimal],
    tri: Mapping[date, Decimal] | None,
    later: Mapping[date, Decimal] | None = None,
) -> np.ndarray:
    """Monthly AUD cash returns. Pre-2011 `rates` accrue and, with a TRI, join to it as V1 does. Without a TRI
    the `later` rates (F1's FIRMMCRID) carry on from 2011."""
    if tri is not None:
        levels = ext.joined_levels(pre_2011_levels(rates), tri)
    else:
        levels = ext.accrue({**rates, **(later or {})}, until=panel.months[-1])
    return base.cash_returns(panel.months, levels)


def s6_panel(
    panel: common.FrozenPanel,
    history: Mapping[date, Decimal],
    steps: Mapping[date, Decimal],
    tri: Mapping[date, Decimal],
) -> common.FrozenPanel:
    """Only pre-2011 rates become the target, joined to the TRI as V1 does. Only AUD cash changes."""
    wanted = pre_2011(history, panel.months[0])
    cash = build_cash(panel, _target_rates(steps, sorted(wanted)), tri)
    return common.with_changes(panel, cash=cash)


def s7_panel(
    panel: common.FrozenPanel, history: Mapping[date, Decimal], aonia: Mapping[date, Decimal]
) -> common.FrozenPanel:
    """AUD cash on the accrual of the historical file then F1's FIRMMCRID, throughout, no TRI."""
    wanted = pre_2011(history, panel.months[0])
    later = {d: v for d, v in aonia.items() if d >= TRI_START}
    return common.with_changes(panel, cash=build_cash(panel, wanted, None, later))


def sensitivity(
    frozen_classes: Mapping[str, Any], changed: common.FrozenPanel, rebuilt: bool, why: str
) -> dict[str, Any]:
    """The bar for a sensitivity is no change of class in any effect and metric pair."""
    if not rebuilt:
        return {"performed": False, "why": why, "passes": False}
    changes = common.class_changes(frozen_classes, common.classes_of(changed))
    return {"performed": True, "class_changes": changes, "passes": not changes}


def baseline_rebuilds(
    panel: common.FrozenPanel, history: Mapping[date, Decimal], tri: Mapping[date, Decimal]
) -> bool:
    """The frozen cash column is reproduced from the historical file and the TRI, so a sensitivity differs
    only by what it names."""
    cash = build_cash(panel, pre_2011(history, panel.months[0]), tri)
    frozen = panel.returns[:, base.SLEEVES.index("cash")]
    return cash.shape == frozen.shape and bool(np.max(np.abs(cash - frozen)) <= REBUILD_TOLERANCE)


def render(summary: Mapping[str, Any]) -> str:
    def word(check: Mapping[str, Any]) -> str:
        if check["passes"]:
            return "passed"
        return "**failed**" if check.get("performed", True) else f"not performed: {check['why']}"

    lines = ["# T-0023 step 4: the cash seam", "", WORDS, ""]
    lines += ["| Check | Result |", "|---|---|"]
    for key in ("M1", "M2", "R2", "R3"):
        lines.append(f"| {key} | {word(summary['checks'][key])} |")
    for year, entry in summary["checks"]["R1"]["years"].items():
        lines.append(f"| R1 {year} | {word(entry)} |")
    for key, entry in summary["sensitivities"].items():
        lines.append(f"| {key} | {word(entry)} |")
    page = summary["page"]
    lines += [
        "",
        f"The target page gave {page['steps']} readable rows; {page['unreadable']} rows couldn't be read and "
        "were left out, not guessed.",
    ]
    for key, entry in summary["sensitivities"].items():
        for change in entry.get("class_changes", []):
            lines.append(f"- {key}: {change}")
    return "\n".join(lines) + "\n"


def jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, bool | int | str) or value is None:
        return value
    return str(value)


def run(
    root: Path,
    e0003: Path,
    history_root: Path,
    reference: Path,
    *,
    gate: RightsGate,
    panel_id: str | None = panel_tool.FROZEN_PANEL_ID,
) -> tuple[dict[str, Any], Path]:
    ev.check_root(root)
    ev.check_root(e0003)
    for source in (ext.HISTORY_SOURCE, base.RBA_SOURCE):
        gate.authorise(Operation.BUILD, [source])
    panel, run_dir = common.load_frozen(root, panel_id)
    manifest = json.loads((e0003 / "raw" / "manifest.json").read_text())
    body = (e0003 / "raw" / "rba_f1.csv").read_bytes()
    if hashlib.sha256(body).hexdigest() != manifest["receipt_id"]:
        raise ev.Stop("the retained F1 bytes don't match their manifest")
    try:
        parsed = parse_rba_f1(SERIES)(body)
    except Exception as exc:
        raise ev.Stop("the F1 receipt lacks a series this check needs") from exc
    by_series: dict[str, dict[date, Decimal]] = {name: {} for name in SERIES.values()}
    for row in parsed.rows:
        by_series[row.series_id][row.valid_time] = row.value
    tri, aonia, published = by_series["tri"], by_series["aonia"], by_series["target"]
    if not tri or min(tri.values()) <= 0:
        raise ev.Stop("no usable TRI level")
    history = ext.load_history(history_root)
    steps, unreadable = parse_target_page(
        (reference / PAGE).read_text(encoding="utf-8"), date(panel.months[0].year, panel.months[0].month, 1)
    )
    months = panel.months
    checks = {
        "M1": check_m1(months, aonia, tri),
        "M2": check_m2(months, aonia, tri),
        "R1": check_r1(history, steps, months[0]),
        "R2": check_r2(months, history, steps),
        "R3": check_r3(steps, published),
    }
    rebuilt = baseline_rebuilds(panel, history, tri)
    why = "the frozen cash column isn't reproduced from the historical file and the TRI"
    frozen_classes = common.classes_of(panel)
    sensitivities = {
        "S6": sensitivity(frozen_classes, s6_panel(panel, history, steps, tri), rebuilt, why),
        "S7": sensitivity(frozen_classes, s7_panel(panel, history, aonia), rebuilt, why),
    }
    summary = {
        "panel_id": run_dir.name,
        "f1_receipt": manifest["receipt_id"],
        "page_sha256": hashlib.sha256((reference / PAGE).read_bytes()).hexdigest(),
        "page": {"steps": len(steps), "unreadable": len(unreadable)},
        "baseline_rebuilt": rebuilt,
        "checks": checks,
        "sensitivities": sensitivities,
    }
    return jsonable(summary), run_dir


def stdout_line(summary: Mapping[str, Any]) -> dict[str, Any]:
    checks = summary["checks"]
    passes = {k: checks[k]["passes"] for k in ("M1", "M2", "R2", "R3")}
    passes["R1"] = {y: e["passes"] for y, e in checks["R1"]["years"].items()}
    passes |= {k: v["passes"] for k, v in summary["sensitivities"].items()}
    return {
        "f1_receipt": summary["f1_receipt"],
        "page_sha256": summary["page_sha256"],
        "page": summary["page"],
        "baseline_rebuilt": summary["baseline_rebuilt"],
        "passes": passes,
        "not_performed": sorted(
            [k for k, v in {**checks, **summary["sensitivities"]}.items() if v.get("performed") is False]
            + [f"R1.{y}" for y, e in checks["R1"]["years"].items() if e.get("performed") is False]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hio-research" / "T-0023")
    parser.add_argument("--e0003", type=Path, default=Path.home() / ".hio-research" / "E-0003")
    parser.add_argument("--history", type=Path, default=Path.home() / ".hio-research" / "RBA-F1-history")
    parser.add_argument("--reference", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        commit = ev.code_commit()["commit"]
        summary, _ = run(
            args.root,
            args.e0003,
            args.history,
            args.reference or args.root / "reference",
            gate=ev.make_gate(),
        )
        out = common.new_output(args.root, "t0023_seam", commit)
        common.write_outputs(out, render(summary), summary)
    except Exception as exc:
        print(f"stopped: {type(exc).__name__}: {exc if isinstance(exc, ev.Stop) else ''}", file=sys.stderr)
        return 2
    print(json.dumps(stdout_line(summary), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
