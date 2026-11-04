"""E-0001's variant V1 (OD-0163): zero-curve valuation primary, flat as comparison, interpolation sensitivity.

Post-hoc and UNREFERENCED, from the same retained bytes. It doesn't reverse E-0001's verdict, and agreement
between any of these models from one source validates none of them. Values stay under --root;
variant-summary.json holds counts, hashes and pass or fail. It writes a separate local release, spec 0.2.0.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import e0001_run as base
from hio.contracts.canonical import instant_str
from hio.contracts.rights import Operation
from hio.contracts.status import Status
from hio.library.cmt import CurveObservation, PeriodTooLong, cmt_period
from hio.library.numeric import CTX
from hio.library.zero_curve import (
    MissingKnot,
    NonPositiveDiscount,
    ZeroCurve,
    bootstrap,
    bootstrap_grid,
    pchip_grid,
    value_on_curve,
)
from hio.publish.release import make_release, render_csv, write_release
from hio.publish.status import append_status
from hio.rights.gate import RightsGate
from hio.rights.model import propagate
from hio.rights.register import load_genuine
from hio.storage.objectstore import LocalObjectStore

SPEC_REF = f"{base.DATASET_ID}@0.2.0"
COLUMNS = ["period_start", "period_end", "r", "flat_r", "cubic_r", "coupon_pct", "long_gap"]


def _return(start: date, end: date, coupon: Decimal, then: ZeroCurve, now: ZeroCurve) -> Decimal:
    v0, _ = value_on_curve(start, start, coupon, then)
    v1, cash = value_on_curve(start, end, coupon, now)
    return CTX.subtract(CTX.divide(CTX.add(v1, cash), v0), Decimal(1))


def _bars(pairs: Sequence[tuple[Decimal, Decimal, int]]) -> dict[str, Any]:
    gaps = sorted(abs(a - b) for a, b, _ in pairs)
    share = Decimal(sum(1 for g in gaps if g <= base.BP)) / Decimal(len(gaps))
    annual = base._annualised_gap(pairs)
    return {
        "within_1bp_on_99pct": share >= Decimal("0.99"),
        "max_within_5bp": gaps[-1] <= 5 * base.BP,
        "annual_within_10bp": abs(annual) <= 10 * base.BP,
        "share_within_1bp": str(share),
        "max_bp": str(CTX.divide(gaps[-1], base.BP)),
        "annual_bp": str(CTX.divide(annual, base.BP)),
    }


def build(rows: Sequence[base.Row]) -> tuple[list[list[str]], dict[str, Any]]:
    linear: dict[date, ZeroCurve] = {}
    cubic: dict[date, ZeroCurve] = {}
    observations, skipped = [], {"missing_tenor": 0, "missing_knot": 0, "non_positive": 0}
    for row in rows:
        if row.knots[base.SEVEN] is None or row.knots[base.TEN] is None:
            skipped["missing_tenor"] += 1
            continue
        observations.append(CurveObservation(row.day, row.knots[base.SEVEN], row.knots[base.TEN]))
        try:
            linear[row.day] = bootstrap(row.knots)
            cubic[row.day] = bootstrap_grid(pchip_grid(row.knots))
        except MissingKnot:
            skipped["missing_knot"] += 1
        except NonPositiveDiscount:
            skipped["non_positive"] += 1
    out, flat_pairs, cubic_pairs, refused, uncovered = [], [], [], 0, 0
    for previous, current in pairwise(observations):
        try:
            period = cmt_period(previous, current)
        except PeriodTooLong:
            refused += 1
            continue
        a, b = previous.day, current.day
        if a not in linear or b not in linear or a not in cubic or b not in cubic:
            uncovered += 1
            continue
        rz = _return(a, b, period.coupon_pct, linear[a], linear[b])
        rc = _return(a, b, period.coupon_pct, cubic[a], cubic[b])
        days = (b - a).days
        flat_pairs.append((rz, period.r, days))
        cubic_pairs.append((rc, rz, days))
        out.append(
            [
                a.isoformat(),
                b.isoformat(),
                str(rz),
                str(period.r),
                str(rc),
                str(period.coupon_pct),
                "true" if period.long_gap else "false",
            ]
        )
    report = {
        "periods": len(out),
        "uncovered": uncovered,
        "refused_too_long": refused,
        **skipped,
        "zero_against_flat": _bars(flat_pairs),
        "cubic_against_linear": _bars(cubic_pairs),
    }
    return out, report


def run(root: Path, *, gate: RightsGate, code: dict[str, str]) -> dict[str, Any]:
    manifest = base.verify_retained(root)
    parsed: list[base.Row] = []
    for entry in manifest["files"]:
        parsed += base.parse_feed((root / entry["path"]).read_bytes())
    rows, _ = base.dedupe(parsed)
    gate.authorise(Operation.BUILD, [base.SOURCE_ID])
    table, report = build(rows)
    store_dir = root / "store-variant"
    if store_dir.exists():
        shutil.rmtree(store_dir)
    store = LocalObjectStore(store_dir)
    receipts, cutoff = base.write_store(root, store, manifest)
    release = make_release(
        {
            "dataset_id": base.DATASET_ID,
            "version": "e0001-v1",
            "spec_ref": SPEC_REF,
            "code_ref": code,
            "inputs": [{"series_id": "us_treasury.par_yield", "receipts": sorted(receipts)}],
            "knowledge_mode": "latest",
            "knowledge_cutoff": instant_str(cutoff),
            "weakest_knowable_basis": "rule_inferred",
            "rights": propagate([gate.records[base.SOURCE_ID]]),
            "invariant_results": {"ZC-INV-1 to 3": "pass; tests at this commit"},
            "quality_summary": {
                "periods": len(table),
                "notices": [base.NOTICE],
                "limitations": base.LIMITATION
                + " Post-hoc variant V1: a construction convention, not a better fit.",
            },
            "supersedes": None,
        },
        {"data.csv": render_csv(COLUMNS, table)},
    )
    write_release(store, gate, release)
    append_status(store, release.content_sha256, Status.EXPLORATORY, "job:e0001", "variant V1", cutoff)
    summary = {
        "bars": {
            k: {b: v[b] for b in ("within_1bp_on_99pct", "max_within_5bp", "annual_within_10bp")}
            for k, v in report.items()
            if isinstance(v, dict)
        },
        "counts": {k: v for k, v in report.items() if not isinstance(v, dict)},
        "release": release.content_sha256,
        "code": code,
    }
    (root / "variant-results.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    (root / "variant-summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    gate = RightsGate(load_genuine(base.REPO / "registers" / "sources.yaml"))
    try:
        report = run(args.root, gate=gate, code=base.code_identity())
    except base.Stop as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
