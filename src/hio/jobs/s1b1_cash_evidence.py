"""T-0014 P-1: the cash evidence report (base-camp criterion 3), non-live.

For a cutoff, from the cash releases and index comparisons `hio.jobs.s1b1` already built, reconcile
every eligible period of both currencies' accruals against the publisher index (Cash Rate TRI, SOFR
Index) and classify it. The report states what was found and leaves a written disposition slot for
every non-agreeing class. It reports; it does not pass or fail, and it approves nothing. It reads
releases only: it does not rebuild, re-round or change any return mathematics.

Classes (each eligible period appears in exactly one):

- `agrees within bound`: the comparison row is within the pre-registered publisher-rounding bound.
- `differs: precision`: an observed value has more places than the spec's rounding model declares.
- `differs: date alignment`: no comparison row has this period's dates, but one shares its start or
  its end, so the two sides disagree about the period itself.
- `missing comparison`: no comparison was made (no row, or a row that could not be compared).
- `unexplained residual`: outside the bound, or the comparison's accrual is not the cash release's.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from hio.contracts.canonical import canonical_json, decimal_str
from hio.jobs.s1b1 import COMPARISON
from hio.library.numeric import CTX
from hio.publish.release import Release

REPORT_ID = "t0014-cash-evidence"
REPORT_VERSION = "1"
STATEMENT = (
    "This report states observations and leaves dispositions to be written. It does not pass or "
    "fail, approve a specification or a release, or establish base-camp criterion 3."
)

AGREES = "agrees within bound"
PRECISION = "differs: precision"
ALIGNMENT = "differs: date alignment"
MISSING = "missing comparison"
RESIDUAL = "unexplained residual"
CLASSES = (AGREES, PRECISION, ALIGNMENT, MISSING, RESIDUAL)
NON_AGREEING = CLASSES[1:]

_ROW_CLASS = {
    "within_expected_bound": AGREES,
    "precision_exceeds_declared": PRECISION,
    "outside_expected_bound": RESIDUAL,
    "not_compared": MISSING,
}
_Key = tuple[str, str]


def _read(release: Release) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(release.files["data.csv"].decode("utf-8"))))


def _index(rows: list[dict[str, str]], what: str) -> dict[_Key, dict[str, str]]:
    out: dict[_Key, dict[str, str]] = {}
    for row in rows:
        key = (row["period_start"], row["period_end"])
        if key in out:
            raise ValueError(f"{what}: period {key} appears more than once")
        out[key] = row
    return out


@dataclass(frozen=True)
class _Pair:
    cash: Release
    comparison: Release


def _pair(releases: Mapping[str, Release], cash_id: str, out_id: str) -> _Pair:
    missing = [i for i in (cash_id, out_id) if i not in releases]
    if missing:
        raise ValueError(f"cash evidence needs {missing}")
    cash, comparison = releases[cash_id], releases[out_id]
    if cash.core["dataset_id"] != cash_id or comparison.core["dataset_id"] != out_id:
        raise ValueError(f"{cash_id}/{out_id}: a release is filed under the wrong dataset id")
    upstream = [i["upstream"] for i in comparison.core["inputs"] if "upstream" in i]
    if {(u["dataset_id"], u["content_sha256"]) for u in upstream} != {(cash_id, cash.content_sha256)}:
        raise ValueError(f"{out_id} was not built from the supplied {cash_id}")
    if cash.core["knowledge_cutoff"] != comparison.core["knowledge_cutoff"]:
        raise ValueError(f"{out_id}: cash and comparison cutoffs differ")
    return _Pair(cash, comparison)


def _period(
    key: _Key,
    cash_row: dict[str, str] | None,
    absent: str | None,
    row: dict[str, str] | None,
    near: _Key | None,
) -> dict[str, Any]:
    """One eligible period: its class, cause and the numbers on both sides, as strings."""
    out: dict[str, Any] = {
        "period_start": key[0],
        "period_end": key[1],
        "accrual": cash_row["r"] if cash_row else "",
        "ours": "",
        "reference": "",
        "difference": "",
        "expected_bound": "",
        "class": MISSING,
        "cause": "",
    }
    if row is None:
        if near is not None:
            out["class"] = ALIGNMENT
            out["cause"] = f"comparison row is for {near[0]}..{near[1]}"
        else:
            out["cause"] = "no_comparison_row"
        return out
    for column in ("ours", "reference", "difference", "expected_bound"):
        out[column] = row[column]
    out["class"] = _ROW_CLASS[row["classification"]]
    out["cause"] = row["cause"]
    if cash_row is None:
        out["cause"] = "; ".join(x for x in (row["cause"], absent and f"cash absent: {absent}") if x)
    elif row["ours"] and row["ours"] != decimal_str(CTX.add(Decimal(1), Decimal(cash_row["r"]))):
        out["class"] = RESIDUAL
        out["cause"] = "comparison accrual is not 1 + the cash release's r"
    return out


def _currency(releases: Mapping[str, Release], cash_id: str, out_id: str) -> dict[str, Any]:
    pair = _pair(releases, cash_id, out_id)
    cash_rows = _index(_read(pair.cash), cash_id)
    cmp_rows = _index(_read(pair.comparison), out_id)
    absent = {k: "" for k, r in cmp_rows.items() if r["cause"] == "cash_period_absent"}
    absent |= {(s, e): reason for s, e, reason in pair.cash.core["quality_summary"]["absent_periods"]}
    eligible = sorted(cash_rows.keys() | absent.keys())

    unmatched = {k for k in cmp_rows if k not in cash_rows and k not in absent}
    periods = []
    for key in eligible:
        row, near = cmp_rows.get(key), None
        if row is None:
            near = next((k for k in sorted(unmatched) if k[0] == key[0] or k[1] == key[1]), None)
            unmatched.discard(near)
        periods.append(_period(key, cash_rows.get(key), absent.get(key), row, near))
    if len({(p["period_start"], p["period_end"]) for p in periods}) != len(periods):
        raise AssertionError("an eligible period appears more than once")  # pragma: no cover

    counts = {c: sum(1 for p in periods if p["class"] == c) for c in CLASSES}
    return {
        "cash_dataset_id": cash_id,
        "cash_release_id": pair.cash.release_id,
        "cash_content_sha256": pair.cash.content_sha256,
        "comparison_dataset_id": out_id,
        "comparison_release_id": pair.comparison.release_id,
        "comparison_content_sha256": pair.comparison.content_sha256,
        "reference_series": COMPARISON[out_id][1],
        "rounding_model": pair.comparison.core["quality_summary"]["rounding_model"],
        "periods": periods,
        "counts": counts,
        "comparison_rows_without_a_cash_period": [
            {"period_start": s, "period_end": e} for s, e in sorted(unmatched)
        ],
        "dispositions": [
            {
                "class": c,
                "periods": counts[c],
                "required": counts[c] > 0,
                "disposition": None,
                "written_by": None,
                "evidence_refs": [],
            }
            for c in NON_AGREEING
        ],
    }


def build_report(releases: Mapping[str, Release]) -> dict[str, Any]:
    """The evidence report for both currencies from `build_releases` outputs. Deterministic: it holds
    no clock reading, and every list is sorted."""
    currencies = {
        COMPARISON[out_id][0]: _currency(releases, COMPARISON[out_id][0], out_id)
        for out_id in sorted(COMPARISON)
    }
    cutoffs = {releases[c].core["knowledge_cutoff"] for c in currencies}
    if len(cutoffs) != 1:
        raise ValueError(f"the cash releases have different cutoffs: {sorted(cutoffs)}")
    return {
        "report": REPORT_ID,
        "version": REPORT_VERSION,
        "statement": STATEMENT,
        "cutoff": cutoffs.pop(),
        "classes": list(CLASSES),
        "currencies": currencies,
    }


def render_json(report: Mapping[str, Any]) -> bytes:
    return canonical_json(report) + b"\n"


def render_markdown(report: Mapping[str, Any]) -> str:
    """A template a reviewer fills in: the counts, then one disposition section per non-agreeing class."""
    lines = [
        f"# Cash evidence report ({report['report']} v{report['version']})",
        "",
        f"Cutoff: `{report['cutoff']}`",
        "",
        f"> {report['statement']}",
        "",
    ]
    for cash_id, cur in report["currencies"].items():
        lines += [
            f"## {cash_id} against {cur['reference_series']}",
            "",
            f"- Cash release: `{cur['cash_release_id']}` (`{cur['cash_content_sha256']}`)",
            f"- Comparison release: `{cur['comparison_release_id']}` (`{cur['comparison_content_sha256']}`)",
            "",
            "| Class | Periods |",
            "|---|---|",
            *(f"| {c} | {cur['counts'][c]} |" for c in CLASSES),
            "",
        ]
        if cur["comparison_rows_without_a_cash_period"]:
            n = len(cur["comparison_rows_without_a_cash_period"])
            lines += [f"Comparison rows with no cash period: {n} (listed in the JSON).", ""]
        for slot in cur["dispositions"]:
            lines += [f"### {cash_id}: {slot['class']} ({slot['periods']} periods)", ""]
            listed = [p for p in cur["periods"] if p["class"] == slot["class"]]
            if listed:
                lines += ["| Start | End | Cause |", "|---|---|---|"]
                lines += [f"| {p['period_start']} | {p['period_end']} | {p['cause']} |" for p in listed]
                lines.append("")
            lines += [
                "Disposition (written, with evidence references): _not yet written_" if slot["required"]
                else "Disposition: none required (no periods in this class).",
                "",
                "Written by: _unset_",
                "",
            ]  # fmt: skip
    return "\n".join(lines)
