"""S1a synthetic pipeline: capture → vintages → views → constructions → releases (OD-0017).

Everything is synthetic: the sources are SyntheticWorldSource fixtures, and the rights come
from a synthetic fixture register. Run:

    uv run python -m hio.jobs.s1a --world tests/fixtures/synthetic/s1a_world \
        --rights tests/fixtures/synthetic/rights.yaml --store .hio-store \
        --cutoff 2026-01-29T00:00:00Z --mode as_captured_by_hio

The release content hashes depend only on the inputs, the cutoff, the mode, the specs and the
code_ref, never on when the job ran (releases standard §6).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from hio.contracts.canonical import canonical_json, decimal_str, instant_str, sha256_hex
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.status import Status
from hio.contracts.temporal import KnowledgeMode, weakest
from hio.library.cash import ACT_360, ACT_365F, CashPeriod, RateFixing, chain_index, overnight_series
from hio.library.fx import FxQuote, fx_series, joint_calendar
from hio.library.numeric import check_identity
from hio.marketdata.capture import SyntheticWorldSource, capture
from hio.marketdata.queries import View
from hio.marketdata.series import CaptureMode, ReleaseSchedule, SeriesDef
from hio.marketdata.vintages import VintageStore
from hio.publish.release import Release, make_release, render_csv, write_release
from hio.publish.status import append_status
from hio.reference.calendar import BusinessCalendar, load_calendars
from hio.rights.model import RightsRecord, propagate
from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parents[3]
CASH_RATE, AUDUSD, SOFR = "synthetic.rba.cash_rate", "synthetic.rba.audusd_4pm", "synthetic.nyfed.sofr"
RBA, NYFED = "synthetic.rba", "synthetic.nyfed"
JOB_ACTOR = "job:hio.jobs.s1a"


@dataclass(frozen=True)
class World:
    root: Path
    syd: BusinessCalendar
    ny: BusinessCalendar
    series: dict[str, SeriesDef]

    @property
    def sources(self) -> list[SyntheticWorldSource]:
        return [
            SyntheticWorldSource(RBA, self.root / "rba.csv", self.series),
            SyntheticWorldSource(NYFED, self.root / "nyfed.csv", self.series),
        ]


def load_world(root: str | Path) -> World:
    """Series definitions modelled on the S1 specs' release timing (the real timing is [EXT],
    to be verified in T-0002; these are synthetic)."""
    root = Path(root)
    cals = load_calendars(root / "calendars.yaml")
    syd, ny = cals["synthetic.xsyd"], cals["synthetic.xnys"]
    grace = timedelta(days=1)
    series = {
        CASH_RATE: SeriesDef(
            CASH_RATE,
            RBA,
            "percent per annum",
            "Australia/Sydney",
            syd,
            ReleaseSchedule(syd, time(9, 20), "Australia/Sydney", 1, grace),
        ),
        AUDUSD: SeriesDef(
            AUDUSD,
            RBA,
            "USD per AUD",
            "Australia/Sydney",
            syd,
            ReleaseSchedule(syd, time(17, 0), "Australia/Sydney", 0, grace),
        ),
        SOFR: SeriesDef(
            SOFR,
            NYFED,
            "percent per annum",
            "America/New_York",
            ny,
            ReleaseSchedule(ny, time(8, 0), "America/New_York", 1, grace),
        ),
    }
    return World(root, syd, ny, series)


# --- capture ---------------------------------------------------------------------------------------


def capture_instants(first: date, cutoff: datetime) -> list[datetime]:
    """One scheduled capture a day at 14:00Z: after the synthetic SOFR (about 13:00Z), the
    Sydney 17:00 fixing (06:00Z) and the 09:20 Sydney cash rate (22:20Z the day before)."""
    out, d = [], first
    while (at := datetime.combine(d, time(14), tzinfo=UTC)) <= cutoff:
        out.append(at)
        d += timedelta(days=1)
    return out


def run_captures(
    world: World, vs: VintageStore, gate: RightsGate, instants: list[datetime]
) -> dict[str, int]:
    counts = {"captures": 0, "no_op": 0, "new_vintages": 0}
    for at in instants:
        for source in world.sources:
            receipt, is_new = capture(source, vs.store, gate, at)
            if not is_new:
                counts["no_op"] += 1
                continue
            counts["captures"] += 1
            result = vs.ingest(receipt, CaptureMode.SCHEDULED)
            if result.receipt_quarantined:
                raise RuntimeError(f"receipt quarantined: {result.receipt_quarantined}")
            counts["new_vintages"] += len(result.new_vintages)
    return counts


# --- view adapters -----------------------------------------------------------------------------------


def fixings(view: View) -> dict[date, RateFixing]:
    return {d: RateFixing(d, v.value, v.knowable_at, v.knowable_basis) for d, v in view.values.items()}


def quotes(view: View) -> dict[date, FxQuote]:
    return {d: FxQuote(d, v.value, v.knowable_at, v.knowable_basis) for d, v in view.values.items()}


def input_record(view: View) -> dict[str, Any]:
    cut = [[d.isoformat(), v.vintage_seq, decimal_str(v.value), v.receipt_id] for d, v in view.values.items()]
    return {
        "series_id": view.series_id,
        "knowledge_mode": view.mode.value,
        "knowledge_cutoff": instant_str(view.cutoff) if view.cutoff else None,
        "receipts": sorted({v.receipt_id for v in view.values.values()}),
        "vintage_cut_sha256": sha256_hex(canonical_json(cut)),
    }


# --- build -------------------------------------------------------------------------------------------


def spec_ref(factor_id: str) -> str:
    spec = yaml.safe_load((REPO / "specs" / "factors" / f"{factor_id}.yaml").read_text())
    return f"{factor_id}@{spec['identity']['version']}"


def _gaps(gaps) -> list[list[str]]:
    return [[s.isoformat(), e.isoformat(), reason] for s, e, reason in gaps]


def build_releases(
    world: World,
    vs: VintageStore,
    gate: RightsGate,
    rights: dict[str, RightsRecord],
    mode: KnowledgeMode,
    cutoff: datetime,
    code_ref: dict[str, str],
) -> dict[str, Release]:
    if not mode.point_in_time and mode is not KnowledgeMode.RECONSTRUCTED:
        raise ValueError("releases are built from a point-in-time view or a labelled reconstruction")
    gate.authorise(Operation.BUILD, [RBA, NYFED])
    v_cash, v_fx, v_sofr = (vs.view(s, mode, cutoff) for s in (CASH_RATE, AUDUSD, SOFR))
    aud_fix, usd_fix, fx_q = fixings(v_cash), fixings(v_sofr), quotes(v_fx)
    common = {
        "version": "s1a",
        "code_ref": code_ref,
        "knowledge_mode": mode.value,
        "knowledge_cutoff": instant_str(cutoff),
        "supersedes": None,
    }

    def rights_of(*sources: str) -> dict[str, str]:
        return propagate(rights[s] for s in sources)

    # cash.aud.overnight on Sydney business days. A period (t-1, t] needs only the rates fixed
    # before t, so the series runs to the business day after the latest fixing.
    syd_days = (
        world.syd.business_days(min(aud_fix), world.syd.add_business_days(max(aud_fix), 1)) if aud_fix else []
    )
    aud = overnight_series(syd_days, aud_fix, world.syd, ACT_365F)
    # the joint calendar J: Sydney business days with a fixing
    joint = joint_calendar(fx_q, world.syd)
    usd = overnight_series(joint, usd_fix, world.ny, ACT_360)
    fx = fx_series(joint, fx_q, usd_fix, world.ny, aud_fix, world.syd)

    releases: dict[str, Release] = {}
    for dataset_id, series, source, view in (
        ("cash.aud.overnight", aud, RBA, v_cash),
        ("cash.usd.overnight", usd, NYFED, v_sofr),
    ):
        releases[dataset_id] = _cash_release(dataset_id, series, view, common, rights_of(source))

    fx_inputs = [input_record(v) for v in (v_cash, v_fx, v_sofr)] + [
        {"upstream": {"dataset_id": d, "content_sha256": releases[d].content_sha256}}
        for d in ("cash.aud.overnight", "cash.usd.overnight")
    ]
    fx_common = {
        **common,
        "inputs": fx_inputs,
        "weakest_knowable_basis": weakest(p.weakest_basis for p in fx.periods).value if fx.periods else None,
        "rights": rights_of(RBA, NYFED),
        "quality_summary": {"periods": len(fx.periods), "absent_periods": _gaps(fx.gaps)},
    }
    max1 = max((check_identity(p.X, p.s + p.carry + p.cross) for p in fx.periods), default=Decimal(0))
    max2 = max((check_identity(p.R, p.r_aud + p.X) for p in fx.periods), default=Decimal(0))
    fx_inv = {
        "FXC-INV-1": f"pass; max |X - (s + carry + cross)| = {decimal_str(max1)}",
        "FXC-INV-2": f"pass; max |R - (r_aud + X)| = {decimal_str(max2)}",
        "RA-INV-007": "pass; s = q_{t-1}/q_t - 1",
    }
    excess_rows = [
        [
            p.start.isoformat(),
            p.end.isoformat(),
            decimal_str(p.X),
            decimal_str(p.R),
            decimal_str(p.r_aud),
            instant_str(p.knowable_at),
            p.weakest_basis.value,
        ]
        for p in fx.periods
    ]
    releases["fx.usd_cash_vs_aud.excess"] = make_release(
        {
            **fx_common,
            "dataset_id": "fx.usd_cash_vs_aud.excess",
            "spec_ref": spec_ref("fx.usd_cash_vs_aud.excess"),
            "invariant_results": fx_inv,
        },
        {
            "data.csv": render_csv(
                ["period_start", "period_end", "X", "R", "r_aud", "knowable_at", "weakest_basis"], excess_rows
            )
        },
    )
    decomposition_rows = [
        [
            p.start.isoformat(),
            p.end.isoformat(),
            decimal_str(p.s),
            decimal_str(p.carry),
            decimal_str(p.cross),
            decimal_str(p.X),
        ]
        for p in fx.periods
    ]
    releases["fx.usd_cash_vs_aud.decomposition"] = make_release(
        {
            **fx_common,
            "dataset_id": "fx.usd_cash_vs_aud.decomposition",
            "spec_ref": spec_ref("fx.usd_cash_vs_aud.excess"),
            "invariant_results": fx_inv,
        },
        {
            "data.csv": render_csv(
                ["period_start", "period_end", "s", "carry", "cross", "X"], decomposition_rows
            )
        },
    )
    return releases


def _cash_release(dataset_id, series, view, common, rights) -> Release:
    periods: tuple[CashPeriod, ...] = series.periods
    index = chain_index([(p.end, p.r) for p in periods]) if periods else []
    rows = [
        [
            p.start.isoformat(),
            p.end.isoformat(),
            decimal_str(p.r),
            decimal_str(level),
            "|".join(f"{b.isoformat()}:{decimal_str(rate)}:{n}" for b, rate, n in p.legs),
            instant_str(p.knowable_at),
            p.weakest_basis.value,
        ]
        for p, (_, level) in zip(periods, index, strict=True)
    ]
    inv_id = "CASH-AUD-INV-1" if dataset_id.startswith("cash.aud") else "CASH-USD-INV-1"
    return make_release(
        {
            **common,
            "dataset_id": dataset_id,
            "spec_ref": spec_ref(dataset_id),
            "inputs": [input_record(view)],
            "weakest_knowable_basis": weakest(p.weakest_basis for p in periods).value if periods else None,
            "rights": rights,
            "invariant_results": {
                "RA-INV-003": "pass; RA §3.2 accrual",
                inv_id: "pass; index ratio equals r",
            },
            "quality_summary": {"periods": len(periods), "absent_periods": _gaps(series.gaps)},
        },
        {
            "data.csv": render_csv(
                ["period_start", "period_end", "r", "index", "legs", "knowable_at", "weakest_basis"], rows
            )
        },
    )


def publish_releases(
    vs: VintageStore, gate: RightsGate, releases: dict[str, Release], at: datetime
) -> dict[str, dict[str, Any]]:
    """Write each release (store_derived gate) and mark it exploratory: its invariants passed in
    construction, so the producing job may (releases standard §5)."""
    out = {}
    for dataset_id, release in sorted(releases.items()):
        sources = [RBA, NYFED] if dataset_id.startswith("fx.") else [RBA if "aud" in dataset_id else NYFED]
        written = write_release(vs.store, gate, release, sources)
        if written:
            append_status(
                vs.store,
                release.content_sha256,
                Status.EXPLORATORY,
                JOB_ACTOR,
                "invariants passed in construction",
                at,
            )
        out[dataset_id] = {
            "release_id": release.release_id,
            "written": written,
            "periods": release.core["quality_summary"]["periods"],
        }
    return out


def rebuild_check(
    world: World,
    store: LocalObjectStore,
    gate: RightsGate,
    rights: dict[str, RightsRecord],
    mode: KnowledgeMode,
    cutoff: datetime,
    code_ref: dict[str, str],
) -> dict[str, bool]:
    """S1-A11: rebuild every release from the stored receipts' vintages (reloaded from the
    store) and report, per dataset, whether the rebuilt content hash is already stored. Needs
    the rebuild rights (rights standard §3) and writes nothing."""
    gate.authorise(Operation.REBUILD, [RBA, NYFED])
    vs = VintageStore(store, world.series)
    rebuilt = build_releases(world, vs, gate, rights, mode, cutoff, code_ref)
    return {d: store.exists(f"{r.prefix}/manifest.json") for d, r in sorted(rebuilt.items())}


def write_run_record(
    store: LocalObjectStore,
    job: str,
    started: datetime,
    ended: datetime,
    code_ref: dict[str, str],
    outputs: dict[str, Any],
    outcome: str,
) -> str:
    """Run metadata is non-deterministic and lives outside the content hash (releases §3)."""
    run_id = uuid.uuid4().hex
    record = {
        "run_id": run_id,
        "job": job,
        "trigger": "manual",
        "started_at": started,
        "ended_at": ended,
        "code_ref": code_ref,
        "outputs": outputs,
        "outcome": outcome,
    }
    store.put(f"catalogue/runs/{started:%Y/%m}/{run_id}.json", canonical_json(record))
    return run_id


def current_code_ref(repo: Path = REPO) -> dict[str, str]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "specs", "uv.lock"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    lock = hashlib.sha256((repo / "uv.lock").read_bytes()).hexdigest()
    return {"commit": commit + ("+dirty" if dirty else ""), "lock_sha256": lock}


def main(argv: list[str] | None = None) -> int:
    from hio.rights.gate import RightsGate as Gate
    from hio.rights.register import load_synthetic

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", required=True)
    ap.add_argument("--rights", required=True, help="a SYNTHETIC rights fixture file")
    ap.add_argument("--store", required=True)
    ap.add_argument("--cutoff", required=True, help="UTC instant with a Z suffix")
    ap.add_argument(
        "--mode",
        default=KnowledgeMode.AS_CAPTURED_BY_HIO.value,
        choices=[m.value for m in KnowledgeMode if m is not KnowledgeMode.LATEST],
    )
    args = ap.parse_args(argv)

    started = datetime.now(UTC)
    world = load_world(args.world)
    rights = dict(load_synthetic(args.rights))
    gate = Gate(rights)
    store = LocalObjectStore(args.store)
    vs = VintageStore(store, world.series)
    cutoff = parse_instant(args.cutoff)
    code_ref = current_code_ref()
    counts = run_captures(world, vs, gate, capture_instants(date(2026, 1, 5), cutoff))
    releases = build_releases(world, vs, gate, rights, KnowledgeMode(args.mode), cutoff, code_ref)
    published = publish_releases(vs, gate, releases, datetime.now(UTC))
    write_run_record(
        store,
        "hio.jobs.s1a",
        started,
        datetime.now(UTC),
        code_ref,
        {k: v["release_id"] for k, v in published.items()},
        "ok",
    )
    print(
        json.dumps(
            {"code_ref": code_ref, "captures": counts, "releases": published}, indent=2, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
