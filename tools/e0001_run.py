"""E-0001: the Treasury par-curve construction experiment, from the retained one-off download (T-0020).

It verifies the retained bytes against their manifest, parses them, builds
rates.us.cmt_10y.total_return 0.1.3 and the same-source zero-curve sensitivity, evaluates the pre-registered
bars in registers/experiments.yaml, and writes a local exploratory release. Nothing here downloads. The
strongest result it can report is "construction diagnostics completed; UNREFERENCED", never "factor
validated". Values stay under --root, outside the repository; summary.json holds only counts, hashes and pass
or fail, and is what the repository may record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

from hio.contracts.canonical import canonical_json, instant_str
from hio.contracts.layout import capture_record_key, receipt_key
from hio.contracts.observation import Receipt
from hio.contracts.rights import Operation
from hio.contracts.status import Status
from hio.library.cmt import CmtPeriod, CurveObservation, PeriodTooLong, cmt_period
from hio.library.numeric import CTX
from hio.library.zero_curve import MissingKnot, NonPositiveDiscount, ZeroCurve, bootstrap, value_on_curve
from hio.publish.release import make_release, render_csv, write_release
from hio.publish.status import append_status
from hio.rights.gate import RightsGate
from hio.rights.model import propagate
from hio.rights.register import load_genuine
from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parent.parent
SOURCE_ID = "us_treasury.par_yield_curve"
DATASET_ID = "rates.us.cmt_10y.total_return"
SPEC_REF = f"{DATASET_ID}@0.1.3"
NOTICE = "Source: US Department of the Treasury. No endorsement by the Treasury is implied."
LIMITATION = (
    "Exploratory and UNREFERENCED: reconstructed(T), gross and frictionless, a synthetic daily re-strike and "
    "not a traded return. Not validated; the zero-curve check repeats the same source. Not for any consumer."
)
FIELDS = {
    "BC_6MONTH": Decimal("0.5"),
    "BC_1YEAR": Decimal(1),
    "BC_2YEAR": Decimal(2),
    "BC_3YEAR": Decimal(3),
    "BC_5YEAR": Decimal(5),
    "BC_7YEAR": Decimal(7),
    "BC_10YEAR": Decimal(10),
}
SEVEN, TEN = Decimal(7), Decimal(10)
LOW, HIGH = Decimal(-5), Decimal(25)
METHOD_CHANGE = date(2021, 12, 6)  # Treasury's methodology page, read 2026-11-04
BP = Decimal("0.0001")
RELATIVE_BOUND = Decimal("1e-10")
DAYS_PER_YEAR = Decimal("365.25")
METADATA = "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}"


class Stop(ValueError):
    """A pre-registered stop: no output until the owner has seen the count."""


@dataclass(frozen=True)
class Row:
    day: date
    knots: dict[Decimal, Decimal | None]


def parse_feed(body: bytes) -> list[Row]:
    """One row per m:properties. Blank, null or N/A is absent. Other bad values stop."""
    rows = []
    for element in ET.fromstring(body).iter():
        if not element.tag.endswith("}properties"):
            continue
        values = {child.tag.rsplit("}", 1)[-1]: child for child in element}
        if "NEW_DATE" not in values or not (values["NEW_DATE"].text or "").strip():
            raise Stop("a row has no date")
        day = date.fromisoformat(values["NEW_DATE"].text.strip()[:10])
        knots: dict[Decimal, Decimal | None] = {}
        for name, maturity in FIELDS.items():
            cell = values.get(name)
            text = (cell.text or "").strip() if cell is not None else ""
            if cell is None or cell.get(f"{METADATA}null") == "true" or text in {"", "N/A"}:
                knots[maturity] = None
                continue
            try:
                value = Decimal(text)
            except ArithmeticError as exc:
                raise Stop(f"{day}: a non-numeric value in {name}") from exc
            if not value.is_finite() or not LOW <= value <= HIGH:
                raise Stop(f"{day}: a value out of range in {name}")
            knots[maturity] = value
        rows.append(Row(day, knots))
    return rows


def dedupe(rows: Sequence[Row]) -> tuple[list[Row], int]:
    """Identical duplicates keep one row and are counted. Conflicting ones stop."""
    seen: dict[date, Row] = {}
    duplicates = 0
    for row in rows:
        kept = seen.get(row.day)
        if kept is None:
            seen[row.day] = row
        elif kept.knots == row.knots:
            duplicates += 1
        else:
            raise Stop(f"conflicting duplicate rows for one date; count so far {duplicates + 1}")
    return [seen[d] for d in sorted(seen)], duplicates


def _annualised_gap(pairs: Sequence[tuple[Decimal, Decimal, int]]) -> Decimal:
    """(prod(1 + Rz) / prod(1 + R)) ^ (365.25 / days) - 1, over the periods given."""
    if not pairs:
        return Decimal(0)  # an empty sub-sample has nothing to fail
    ratio, days = Decimal(1), 0
    for rz, r, span in pairs:
        ratio = CTX.multiply(ratio, CTX.divide(CTX.add(Decimal(1), rz), CTX.add(Decimal(1), r)))
        days += span
    return CTX.subtract(CTX.power(ratio, CTX.divide(DAYS_PER_YEAR, Decimal(days))), Decimal(1))


def _quantile(ordered: Sequence[Decimal], share: Decimal) -> Decimal:
    return ordered[min(len(ordered) - 1, int(share * len(ordered)))]


@dataclass
class Build:
    periods: list[CmtPeriod]
    zero_returns: dict[date, Decimal]
    counts: Counter
    zero_failures: int
    par_failures: int


def build(rows: Sequence[Row]) -> Build:
    counts: Counter = Counter()
    observations = []
    curves: dict[date, ZeroCurve] = {}
    zero_failures = 0
    for row in rows:
        if row.knots[SEVEN] is None or row.knots[TEN] is None:
            counts["excluded_missing_tenor"] += 1
            continue
        observations.append(CurveObservation(row.day, row.knots[SEVEN], row.knots[TEN]))
        try:
            curves[row.day] = bootstrap(row.knots)
        except MissingKnot:
            counts["dates_missing_knot"] += 1
        except NonPositiveDiscount:
            zero_failures += 1
    periods, zero_returns, par_failures = [], {}, 0
    for previous, current in pairwise(observations):
        try:
            period = cmt_period(previous, current)
        except PeriodTooLong:
            counts["refused_period_too_long"] += 1
            continue
        periods.append(period)
        counts["long_gaps"] += int(period.long_gap)
        counts["moves_over_50bp"] += int(abs(current.y10_pct - previous.y10_pct) > Decimal("0.5"))
        then, now = curves.get(previous.day), curves.get(current.day)
        if then is None or now is None:
            counts["periods_uncovered"] += 1
            continue
        start, _ = value_on_curve(previous.day, previous.day, period.coupon_pct, then)
        if abs(CTX.divide(start, Decimal(100)) - 1) > RELATIVE_BOUND:
            par_failures += 1
        end, cash = value_on_curve(previous.day, current.day, period.coupon_pct, now)
        zero_returns[period.end] = CTX.subtract(CTX.divide(CTX.add(end, cash), start), Decimal(1))
    return Build(periods, zero_returns, counts, zero_failures, par_failures)


def diagnostics(result: Build) -> dict[str, Any]:
    """The bars real data decides: B2, B3, B6 to B9. The caller decides B4 and B5; tests decide B1."""
    breaches, worst_residual = 0, Decimal(0)
    for p in result.periods:
        size = abs(p.residual)
        worst_residual = max(worst_residual, size)
        if abs(p.yield_pct - p.coupon_pct) < Decimal("0.25") and size >= BP:
            breaches += 1
    covered = [p for p in result.periods if p.end in result.zero_returns]
    if not covered:
        raise Stop("no period is covered by the sensitivity")
    gaps = sorted(abs(result.zero_returns[p.end] - p.r) for p in covered)
    triples = [(result.zero_returns[p.end], p.r, (p.end - p.start).days) for p in covered]
    before = [t for t, p in zip(triples, covered, strict=True) if p.end < METHOD_CHANGE]
    after = [t for t, p in zip(triples, covered, strict=True) if p.start >= METHOD_CHANGE]
    crossing = [p for p in covered if p.start < METHOD_CHANGE <= p.end]
    within = sum(1 for g in gaps if g <= BP)
    annual = {
        "full": _annualised_gap(triples),
        "before": _annualised_gap(before),
        "after": _annualised_gap(after),
    }
    coverage = Decimal(len(covered)) / Decimal(len(result.periods))
    share = Decimal(within) / Decimal(len(gaps))
    bars = {
        "B2": breaches == 0,
        "B3": result.zero_failures == 0 and result.par_failures == 0,
        "B6": share >= Decimal("0.99"),
        "B7": gaps[-1] <= 5 * BP,
        "B8": all(abs(v) <= 10 * BP for v in annual.values()),
        "B9": coverage >= Decimal("0.95"),
    }
    return {
        "bars": bars,
        "values": {
            "residual_max_abs_bp": str(CTX.divide(worst_residual, BP)),
            "residual_breaches": breaches,
            "d_abs_p50_bp": str(CTX.divide(_quantile(gaps, Decimal("0.5")), BP)),
            "d_abs_p99_bp": str(CTX.divide(_quantile(gaps, Decimal("0.99")), BP)),
            "d_abs_max_bp": str(CTX.divide(gaps[-1], BP)),
            "share_within_1bp": str(share),
            "d_annualised_bp": {k: str(CTX.divide(v, BP)) for k, v in annual.items()},
            "crossing_d_abs_bp": [
                str(CTX.divide(abs(result.zero_returns[p.end] - p.r), BP)) for p in crossing
            ],
            "coverage": str(coverage),
        },
        "counts": {
            "periods": len(result.periods),
            "covered": len(covered),
            "before": len(before),
            "after": len(after),
            "crossing": len(crossing),
            "zero_curve_failures": result.zero_failures,
            "par_failures": result.par_failures,
            **{k: result.counts[k] for k in sorted(result.counts)},
        },
    }


def verify_retained(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["stopped"] is not None or manifest["source_id"] != SOURCE_ID:
        raise Stop("the manifest doesn't describe one complete download of this source")
    for entry in manifest["files"]:
        if hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise Stop(f"retained bytes don't match the manifest: {entry['path']}")
    return manifest


def write_store(root: Path, store: LocalObjectStore, manifest: dict[str, Any]) -> tuple[list[str], datetime]:
    """Each retained file becomes a receipt, with its capture record, so the release has real lineage."""
    receipts = []
    latest = None
    for entry in manifest["files"]:
        data = (root / entry["path"]).read_bytes()
        at = datetime.fromisoformat(entry["retrieved_at"]).astimezone(UTC)
        receipt = Receipt(entry["sha256"], SOURCE_ID, at, {"url": entry["url"]}, len(data))
        store.put(receipt_key(SOURCE_ID, at, entry["sha256"]), data)
        store.put(capture_record_key(SOURCE_ID, at, entry["sha256"]), canonical_json(receipt.as_record()))
        receipts.append(entry["sha256"])
        latest = at if latest is None or at > latest else latest
    return receipts, latest


def release_rows(result: Build) -> list[list[str]]:
    return [
        [
            p.start.isoformat(),
            p.end.isoformat(),
            str(p.r),
            str(p.coupon_pct),
            str(p.yield_pct),
            str(p.dirty),
            str(p.coupon_cash),
            str(p.carry),
            str(p.roll_down),
            str(p.curve_change),
            str(p.convexity),
            str(p.residual),
            "true" if p.long_gap else "false",
            str(result.zero_returns[p.end]) if p.end in result.zero_returns else "",
        ]
        for p in result.periods
    ]


COLUMNS = [
    "period_start",
    "period_end",
    "r",
    "coupon_pct",
    "yield_pct",
    "dirty",
    "coupon_cash",
    "carry",
    "roll_down",
    "curve_change",
    "convexity",
    "residual",
    "long_gap",
    "zero_curve_r",
]


def run_once(root: Path, store_dir: Path, gate: RightsGate, code: dict[str, str]) -> dict[str, Any]:
    manifest = verify_retained(root)
    parsed: list[Row] = []
    for entry in manifest["files"]:
        parsed += parse_feed((root / entry["path"]).read_bytes())
    rows, duplicates = dedupe(parsed)
    gate.authorise(Operation.BUILD, [SOURCE_ID])
    result = build(rows)
    report = diagnostics(result)
    included = len(rows) - result.counts["excluded_missing_tenor"]
    accounted = included + result.counts["excluded_missing_tenor"] + duplicates == len(parsed)

    store = LocalObjectStore(store_dir)
    receipts, cutoff = write_store(root, store, manifest)
    rights = propagate([gate.records[SOURCE_ID]])
    release = make_release(
        {
            "dataset_id": DATASET_ID,
            "version": "e0001-0",
            "spec_ref": SPEC_REF,
            "code_ref": code,
            "inputs": [{"series_id": "us_treasury.par_yield", "receipts": sorted(receipts)}],
            "knowledge_mode": "latest",
            "knowledge_cutoff": instant_str(cutoff),
            "weakest_knowable_basis": "rule_inferred",
            "rights": rights,
            "invariant_results": {"RA-INV-013": "pass; tests at this commit", "E-0001": "see the experiment"},
            "quality_summary": {
                "periods": len(result.periods),
                "notices": [NOTICE],
                "limitations": LIMITATION,
                "reconstructed": "reconstructed(T): one one-off download; no publication instant is claimed",
            },
            "supersedes": None,
        },
        {"data.csv": render_csv(COLUMNS, release_rows(result))},
    )
    write_release(store, gate, release)
    append_status(
        store, release.content_sha256, Status.EXPLORATORY, "job:e0001", "bars evaluated by E-0001", cutoff
    )
    days = [p.end for p in result.periods]
    return {
        "report": report,
        "parsed_rows": len(parsed),
        "included_dates": included,
        "duplicates": duplicates,
        "accounted": accounted,
        "first_date": result.periods[0].start.isoformat(),
        "last_date": days[-1].isoformat(),
        "release": release.content_sha256,
        "data_sha256": release.core["files"][0]["sha256"],
    }


def code_identity() -> dict[str, str]:
    git = ("git", "-C", str(REPO))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    commit = subprocess.run((*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True)
    return {
        "commit": commit.stdout.strip(),
        "lock_sha256": hashlib.sha256((REPO / "uv.lock").read_bytes()).hexdigest(),
    }


def outcome(first: dict[str, Any], identical: bool) -> dict[str, Any]:
    bars = {"B4": identical, "B5": first["accounted"], **first["report"]["bars"]}
    implementation = all(bars[b] for b in ("B2", "B3", "B4", "B5"))
    approximation = all(bars[b] for b in ("B6", "B7", "B8"))
    if not implementation:
        verdict = "implementation rejected until corrected"
    elif not bars["B9"]:
        verdict = "approximation inconclusive: coverage below the bar"
    elif not approximation:
        verdict = "approximation not adequate for this purpose"
    else:
        verdict = "construction diagnostics completed; UNREFERENCED"
    return {"bars": bars, "verdict": verdict}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    gate = RightsGate(load_genuine(REPO / "registers" / "sources.yaml"))
    code = code_identity()
    stores = [args.root / "store", args.root / "store-rebuild"]
    for path in stores:
        if path.exists():
            shutil.rmtree(path)
    try:
        first = run_once(args.root, stores[0], gate, code)
        second = run_once(args.root, stores[1], gate, code)
    except Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    identical = first["release"] == second["release"] and first["data_sha256"] == second["data_sha256"]
    decided = outcome(first, identical)
    (args.root / "results.json").write_text(json.dumps({**first, **decided}, indent=1, sort_keys=True) + "\n")
    report = first["report"]
    summary = {
        "bars": decided["bars"],
        "verdict": decided["verdict"],
        "counts": report["counts"],
        "parsed_rows": first["parsed_rows"],
        "included_dates": first["included_dates"],
        "duplicates": first["duplicates"],
        "first_date": first["first_date"],
        "last_date": first["last_date"],
        "release": first["release"],
        "data_sha256": first["data_sha256"],
        "code": code,
    }
    (args.root / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdict": decided["verdict"], "bars": decided["bars"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
