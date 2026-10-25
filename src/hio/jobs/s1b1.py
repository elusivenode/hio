"""S1b-1.0: exploratory cash-return releases and publisher-index comparisons from captured receipts
(T-0009 section 2.8; OD-0062, OD-0063). No fetch happens here: this job reads receipts already in
the store. Every vintage is placed by HIO-ADR-0012 P3 (`schedule_only`), so nothing here is
eligible for `as_known_by_market`, and every release is exploratory, never final.

Calendars: AUD rates are selected on RITS days and USD rates on the days NY Fed actually published
(`calendar_from_observations`), with period ends on NSW days (the joint calendar until S1b-2).
Release instants for P3 use weekdays for SOFR, which is a known limitation: across a US-only holiday
the documented instant is a day early. That can only make a `schedule_only` label optimistic, and
such labels never support a market-knowledge claim.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal

from hio.contracts.canonical import decimal_str, instant_str
from hio.contracts.layout import CAPTURES_PREFIX
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.temporal import KnowledgeMode, weakest
from hio.jobs.s1a import _cash_release, input_record, spec_ref
from hio.library.cash import ACT_360, ACT_365F, chain_index, overnight_series
from hio.library.numeric import CTX
from hio.marketdata.capture import load_receipt_record, receipt_bytes
from hio.marketdata.parse import MalformedReceipt, RawRow
from hio.marketdata.series import CaptureMode, ReleaseSchedule, SeriesDef
from hio.marketdata.vintages import VintageStore, _processed_key
from hio.publish.release import Release, make_release, render_csv
from hio.reference.calendar import BusinessCalendar, calendar_from_observations
from hio.rights.model import RightsRecord, propagate
from hio.sources.datasets import AONIA, DATASETS, PUBLICATIONS, SOFR, SOFR_INDEX, TRI, MalformedPayload
from hio.storage.objectstore import LocalObjectStore

VERSION = "s1b1-0"
SYD, NY = "Australia/Sydney", "America/New_York"
LIMITATIONS = (
    "benchmark accrual; not an achievable deposit or fund return; replicable only with a basis. "
    "Exploratory: placed schedule_only (HIO-ADR-0012 P3), not final, no as_known_by_market claim"
)
# The published file each series is read from, and the dataset (the rights subject) it belongs to.
PUBLICATION_OF = {AONIA: "rba.f1", TRI: "rba.f1", SOFR: "nyfed.sofr", SOFR_INDEX: "nyfed.sofr_index"}
DATASET_OF = {
    AONIA: "rba.cash_rate",
    TRI: "rba.cash_rate_tri",
    SOFR: "nyfed.sofr",
    SOFR_INDEX: "nyfed.sofr_index",
}
UNIT = {AONIA: "percent per annum", SOFR: "percent per annum", TRI: "index", SOFR_INDEX: "index"}


@dataclass(frozen=True)
class Calendars:
    rits: BusinessCalendar  # AONIA selection and AUD period ends (cited reference data)
    nsw: BusinessCalendar  # period ends for cash.usd until S1b-2 supplies fixings
    ny: BusinessCalendar  # derived from published SOFR dates, for rate selection


def sofr_calendar(store: LocalObjectStore, cutoff: datetime) -> BusinessCalendar:
    """The US observation calendar from the SOFR receipts captured at or before the cutoff."""
    spec = DATASETS["nyfed.sofr"]
    observations = []
    for key in store.list(f"{CAPTURES_PREFIX}nyfed.sofr/"):
        receipt = load_receipt_record(store, key)
        if receipt.captured_at <= cutoff:
            observations.append({r.valid_time for r in spec.parse(receipt_bytes(store, receipt)).rows})
    return calendar_from_observations("nyfed.observed", observations)


def _series(sid: str, tz: str, calendar: BusinessCalendar, schedule: ReleaseSchedule) -> SeriesDef:
    shared = PUBLICATION_OF[sid] != DATASET_OF[sid]
    return SeriesDef(
        sid,
        PUBLICATION_OF[sid],
        UNIT[sid],
        tz,
        calendar,
        schedule,
        dataset_id=DATASET_OF[sid] if shared else None,
    )


def series_defs(cals: Calendars) -> dict[str, SeriesDef]:
    """P3 uses the documented release instant, so the schedules carry the documented rules only:
    AONIA and SOFR are released on the next business day, the TRI and the SOFR Index on their label
    day. The capture grace is irrelevant to P3."""
    weekdays = BusinessCalendar("weekdays")
    grace = timedelta(days=1)
    return {
        AONIA: _series(AONIA, SYD, cals.rits, ReleaseSchedule(cals.rits, time(9, 20), SYD, 1, grace)),
        TRI: _series(TRI, SYD, cals.rits, ReleaseSchedule(cals.rits, time(9, 20), SYD, 0, grace)),
        SOFR: _series(SOFR, NY, cals.ny, ReleaseSchedule(weekdays, time(8, 0), NY, 1, grace)),
        SOFR_INDEX: _series(SOFR_INDEX, NY, cals.ny, ReleaseSchedule(weekdays, time(8, 0), NY, 0, grace)),
    }


def _parser(publication_id: str) -> Callable[[bytes], list[RawRow]]:
    spec = PUBLICATIONS[publication_id]

    def parse(data: bytes) -> list[RawRow]:
        try:
            return list(spec.parse(data).rows)
        except MalformedPayload as exc:
            raise MalformedReceipt(str(exc)) from exc

    return parse


def vintage_store(
    store: LocalObjectStore, cals: Calendars, clock: Callable[[], datetime] | None = None
) -> VintageStore:
    parsers = {pid: _parser(pid) for pid in PUBLICATIONS}
    return VintageStore(store, series_defs(cals), clock, parsers)


def ingest_pending(vs: VintageStore, cutoff: datetime) -> int:
    """Process every captured, not yet processed receipt of the five datasets in capture order, under
    P3. Returns the number of receipts processed."""
    n = 0
    for publication_id in sorted(PUBLICATIONS):
        for key in vs.store.list(f"{CAPTURES_PREFIX}{publication_id}/"):
            receipt = load_receipt_record(vs.store, key)
            if receipt.captured_at > cutoff or vs.store.exists(_processed_key(receipt)):
                continue
            result = vs.ingest(receipt, CaptureMode.SCHEDULED_P3)
            if result.receipt_quarantined:
                raise RuntimeError(f"receipt quarantined: {result.receipt_quarantined}")
            n += 1
    return n


def _fixings(view):
    from hio.jobs.s1a import fixings

    return fixings(view)


def _places(value: Decimal) -> int:
    """Decimal places of the canonical rendering. Never read a Decimal's exponent: a value parsed
    from a payload ('100.1200') and the same value reloaded from the store ('100.12') differ there,
    and a release must not depend on which one it was built from."""
    text = decimal_str(value)
    return len(text.split(".")[1]) if "." in text else 0


def _decimals(view) -> int:
    """The finest precision seen in a series: the best available estimate of its publisher rounding
    (values are stored without trailing zeros, so this is a lower bound on the published precision)."""
    return max((_places(v.value) for v in view.values.values()), default=0)


CASH = {
    # dataset id: (series, rate calendar, period-end calendar, day-count base)
    "cash.aud.overnight": (AONIA, "rits", "rits", ACT_365F),
    "cash.usd.overnight": (SOFR, "ny", "nsw", ACT_360),
}
COMPARISON = {
    # output id: (the cash release it compares, the publisher's index series, the series' day-count base)
    "cash.aud.overnight.vs_tri": ("cash.aud.overnight", TRI, 365),
    "cash.usd.overnight.vs_sofr_index": ("cash.usd.overnight", SOFR_INDEX, 360),
}
OUTPUTS = (*CASH, *COMPARISON)


def build_releases(
    vs: VintageStore,
    gate: RightsGate,
    rights: Mapping[str, RightsRecord],
    cals: Calendars,
    cutoff: datetime,
    code_ref: dict[str, str],
    outputs: Iterable[str] | None = None,
) -> dict[str, Release]:
    """Build the requested outputs (default: all four). Each output is authorised on the datasets
    it actually uses, evaluated one by one: the AUD cash release needs only `rba.cash_rate`, while
    its TRI comparison also needs `rba.cash_rate_tri`. A refusal writes nothing."""
    wanted = frozenset(outputs) if outputs is not None else frozenset(OUTPUTS)
    if wanted - set(OUTPUTS):
        raise ValueError(f"unknown outputs: {sorted(wanted - set(OUTPUTS))}")
    mode = KnowledgeMode.AS_CAPTURED_BY_HIO
    common = {
        "version": VERSION,
        "code_ref": code_ref,
        "knowledge_mode": mode.value,
        "knowledge_cutoff": instant_str(cutoff),
        "supersedes": None,
    }
    calendars = {"rits": cals.rits, "nsw": cals.nsw, "ny": cals.ny}
    views: dict[str, object] = {}

    def view(sid: str):
        if sid not in views:
            v = vs.view(sid, mode, cutoff, None)
            if any(x.knowable_basis.supports_market_knowledge for x in v.values.values()):
                raise RuntimeError(f"{sid}: a vintage is placed above schedule_only; P3 only here")
            views[sid] = v
        return views[sid]

    def authorised(*sids: str) -> frozenset[str]:
        subjects = frozenset().union(*(vs.sources_of(view(s)) for s in sids))
        gate.authorise(Operation.BUILD, subjects)
        return subjects

    releases: dict[str, Release] = {}
    series = {}
    for dataset_id in OUTPUTS:
        if dataset_id in CASH and (
            dataset_id in wanted or any(COMPARISON[o][0] == dataset_id for o in wanted & set(COMPARISON))
        ):
            sid, rate_key, end_key, base = CASH[dataset_id]
            subjects = authorised(sid)
            fix = _fixings(view(sid))
            rate_cal, end_cal = calendars[rate_key], calendars[end_key]
            if fix:
                last = rate_cal.add_business_days(rate_cal.latest_on_or_before(max(fix)), 1)
                ends = [d for d in end_cal.business_days(min(fix), last) if d <= last]
            else:
                ends = []
            series[dataset_id] = overnight_series(ends, fix, rate_cal, base)
            built = _cash_release(
                dataset_id, series[dataset_id], view(sid), common, propagate([rights[s] for s in subjects])
            )
            core = {k: v for k, v in built.core.items() if k != "files"}
            core["quality_summary"] = {**core["quality_summary"], "limitations": LIMITATIONS}
            releases[dataset_id] = make_release(core, built.files)
        elif dataset_id in COMPARISON and dataset_id in wanted:
            cash_id, ref_sid, base = COMPARISON[dataset_id]
            subjects = authorised(CASH[cash_id][0], ref_sid)
            releases[dataset_id] = _comparison(
                releases[cash_id], series[cash_id], view(ref_sid), dataset_id, common, base,
                propagate([rights[s] for s in subjects]),
            )  # fmt: skip
    return {k: v for k, v in releases.items() if k in wanted}


def _comparison(cash: Release, cash_series, ref_view, out_id: str, common, base: int, rights) -> Release:
    """Our compounded index against the publisher's index over each consecutive period: ratios,
    the difference, the expected bound from the publishers' own rounding, and a classification.
    The classification is a record, never a pass or fail on agreement (HIO-ADR-0012 4.4)."""
    periods = cash_series.periods
    levels = dict(chain_index([(p.end, p.r) for p in periods])) if periods else {}
    ref = {d: v.value for d, v in ref_view.values.items()}
    ref_dp = _decimals(ref_view)
    rows = []
    for p in periods:
        s, t = p.start, p.end
        if s not in levels or t not in ref or s not in ref:
            continue
        ours = CTX.divide(levels[t], levels[s])
        theirs = CTX.divide(ref[t], ref[s])
        diff = CTX.subtract(ours, theirs)
        ulp = Decimal(1).scaleb(-ref_dp) / 2
        rate_dp = max((_places(r) for _, r, _ in p.legs), default=0)
        rate_ulp = Decimal(1).scaleb(-rate_dp) / 2 / 100 / base
        bound = ulp / ref[s] + ulp / ref[t] + sum((rate_ulp * n for _, _, n in p.legs), Decimal(0))
        klass = "within_expected_bound" if abs(diff) <= bound else "outside_expected_bound"
        rows.append([s.isoformat(), t.isoformat(), decimal_str(ours), decimal_str(theirs),
                     decimal_str(diff), decimal_str(bound), klass])  # fmt: skip
    counts = {
        k: sum(1 for r in rows if r[6] == k) for k in ("within_expected_bound", "outside_expected_bound")
    }
    basis = [p.weakest_basis for p in periods] + ([ref_view.weakest_basis] if ref_view.weakest_basis else [])
    spec = "cash.aud.overnight" if out_id.startswith("cash.aud") else "cash.usd.overnight"
    columns = [
        "period_start",
        "period_end",
        "ours",
        "reference",
        "difference",
        "expected_bound",
        "classification",
    ]
    return make_release(
        {
            **common,
            "dataset_id": out_id,
            "spec_ref": spec_ref(spec),
            "inputs": [
                input_record(ref_view),
                {"upstream": {"dataset_id": cash.core["dataset_id"], "content_sha256": cash.content_sha256}},
            ],
            "weakest_knowable_basis": weakest(basis).value if periods else None,
            "rights": rights,
            "invariant_results": {
                "comparison": "recorded; not an identity invariant; no pass or fail on agreement"
            },
            "quality_summary": {
                "periods": len(rows),
                "periods_compared": len(rows),
                **counts,
                "limitations": LIMITATIONS,
            },
        },
        {"data.csv": render_csv(columns, rows)},
    )


def all_series_ids() -> Iterable[str]:
    return (AONIA, TRI, SOFR, SOFR_INDEX)
