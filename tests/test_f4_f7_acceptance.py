"""Acceptance tests for F-REVIEW-2026-10-24-s1a-1-4 and -7 (OD-0030), per the approved
OBS-AMEND-Q001 revision 4 (blob 419992f2) and OBS-AMEND-Q002 revision 5 (blob d0a25b3b).

Each test names the acceptance test (AT-Q1-n, AT-Q2-n) and the invariants it covers. Codex's
original counterexamples for findings 4 and 7 (REVIEW-2026-10-24-s1a-1) are AT-Q1-1 and AT-Q2-1.
Everything here is synthetic.
"""

import itertools
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hio.contracts.observation import Vintage
from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus
from hio.jobs import s1a
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.queries import (
    InadmissibleForPredictivePointInTime,
    Resolution,
    require_predictive_pit,
    select,
)
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import DecisionRefused, IncompleteProcessing, VintageStore
from hio.rights.gate import RightsGate
from hio.rights.register import load_synthetic
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES, SERIES, AllowAllGate, receipt_text, utc

RATE, SRC = "synthetic.rate", "synthetic.daily_source"
D1, D2, D3 = date(2026, 1, 12), date(2026, 1, 13), date(2026, 1, 14)
CLOCK = lambda: utc(2026, 1, 1)  # noqa: E731 - the recording clock: decisions dated later are allowed
HEADER = "series_id,valid_time,value,published_at"


def store_at(path):
    return VintageStore(LocalObjectStore(path), SERIES, clock=CLOCK)


def capture_only(vs, tmp, text, at):
    path = tmp / f"{SRC}.csv"
    path.write_text(text)
    receipt, is_new = capture(SyntheticSource(SRC, path), vs.store, AllowAllGate(), at)
    assert is_new
    return receipt


def published(value, key="2026-01-12", stamp="2026-01-12T00:00:00Z"):
    return receipt_text(value, [f"{RATE},{key},{value},{stamp}"], HEADER)


def values(view):
    return {k: v.value for k, v in view.values.items()}


def effects(view):
    return sorted((r.conflict.rank_clock, r.effect) for r in view.conflicts)


# --- AT-Q1-1: Codex's F4 counterexample, both directions (OBS-INV-009) ------------------------------

JUMP_ROWS = [
    f"{RATE},2026-01-12,3.60,2026-01-11T22:00:00Z",
    f"{RATE},2026-01-13,9.99,2026-01-12T22:00:00Z",  # a jump: quarantined by the gate
    f"{RATE},2026-01-14,3.62,2026-01-13T22:00:00Z",
]
E1, E2 = utc(2026, 1, 16, 10), utc(2026, 1, 20, 10)


@pytest.fixture
def jumped(tmp_path):
    vs = store_at(tmp_path / "s")
    r = capture_only(vs, tmp_path, receipt_text("jump", JUMP_ROWS, HEADER), utc(2026, 1, 15, 9))
    result = vs.ingest(r, CaptureMode.SCHEDULED)
    assert [v.valid_time for v in result.quarantined] == [D2]
    return vs


def test_at_q1_1_codex_f4_a_later_release_never_changes_an_earlier_point_in_time_view(jumped):
    vs = jumped
    t15 = utc(2026, 1, 15, 12)
    before = vs.as_captured_by_hio(RATE, t15)
    assert D2 not in before.values
    vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "checked against the source", E1)
    vs.set_quality(RATE, D2, 1, QualityStatus.QUARANTINED, "owner", "re-quarantined", E2)
    # Codex: "after an owner release event dated 16 Jan, the same 15 Jan query included it".
    assert vs.as_captured_by_hio(RATE, t15) == before  # byte-for-byte the same view
    assert D2 in vs.as_captured_by_hio(RATE, utc(2026, 1, 17)).values  # E1 in force at Q = T
    assert D2 not in vs.as_captured_by_hio(RATE, utc(2026, 1, 21)).values  # E2 in force
    # The same holds for a reloaded store (the decisions are durable).
    again = store_at(vs.store.root)
    assert again.as_captured_by_hio(RATE, t15) == before


def test_at_q1_1_market_and_latest_rows_of_the_worked_example(jumped):
    vs = jumped
    vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "checked", E1)
    vs.set_quality(RATE, D2, 1, QualityStatus.QUARANTINED, "owner", "re-quarantined", E2)
    t15 = utc(2026, 1, 15, 12)
    assert D2 not in vs.as_known_by_market(RATE, t15, t15).values
    later = vs.as_known_by_market(RATE, t15, utc(2026, 1, 17))
    assert values(later)[D2] == Decimal("9.99")
    assert later.quality_after_cutoff and not later.predictive_pit_admissible
    assert later.eligibility_decided_at[D2] == E1 and later.validated_after_cutoff(D2)
    assert not later.validated_after_cutoff(D1)  # D1's eligibility is the gate's verdict at capture
    latest = vs.latest(RATE, utc(2026, 1, 21))
    assert D2 not in latest.values
    assert (latest.label, latest.restated_quality, latest.predictive_pit_admissible) == (
        "descriptive",
        True,
        False,
    )


# --- AT-Q1-2 and OBS-INV-008 / OBS-INV-013: later evidence and decisions never change a result -------

T0 = datetime(2026, 1, 1, tzinfo=UTC)
hours = st.integers(min_value=0, max_value=120)


@st.composite
def worlds(draw):
    out, seq = [], {}
    for _ in range(draw(st.integers(min_value=0, max_value=14))):
        key = date(2026, 1, 5) + timedelta(days=draw(st.integers(0, 2)))
        seq[key] = seq.get(key, 0) + 1
        out.append(
            Vintage(
                "synthetic.p",
                key,
                seq[key],
                Decimal(draw(st.integers(0, 3))),
                f"{draw(st.integers(0, 5)):064x}",
                T0 + timedelta(hours=draw(hours)),
                T0 + timedelta(hours=draw(hours)),
                draw(st.sampled_from(list(KnowableBasis))),
                "UTC",
                draw(st.sampled_from([QualityStatus.VALID, QualityStatus.QUARANTINED])),
            )
        )
    return out


@settings(max_examples=250, deadline=None)
@given(worlds(), worlds(), hours, hours, st.sampled_from(list(KnowledgeMode)))
def test_at_q1_2_appending_anything_dated_after_q_leaves_every_result_at_q_unchanged(held, extra, t, q, mode):
    cutoff = None if mode is KnowledgeMode.LATEST else T0 + timedelta(hours=t)
    qq = None if mode is KnowledgeMode.AS_CAPTURED_BY_HIO else T0 + timedelta(hours=q)
    Q = cutoff if mode is KnowledgeMode.AS_CAPTURED_BY_HIO else qq
    before = select(held, {}, "synthetic.p", mode, cutoff, qq)
    # Later evidence: every extra vintage is captured after Q (new receipt ids keep it distinct).
    later_vintages = [
        Vintage(
            v.series_id,
            v.valid_time,
            100 + i,
            v.value,
            f"{0xF00 + i:064x}",
            Q + timedelta(hours=1 + i),
            v.knowable_at,
            v.knowable_basis,
            "UTC",
            v.quality_status,
        )
        for i, v in enumerate(extra)
    ]
    # Later decisions: a release and a re-quarantine of every held vintage, both after Q.
    later_decisions = {
        (v.series_id, v.valid_time, v.vintage_seq): [
            (Q + timedelta(minutes=1), QualityStatus.VALID),
            (Q + timedelta(minutes=2), QualityStatus.QUARANTINED),
        ]
        for v in held
    }
    later_resolutions = [
        Resolution(
            "synthetic.p",
            r.conflict.conflict_id,
            "reject_all",
            None,
            "x",
            "owner",
            "x",
            Q + timedelta(minutes=3),
            Q,
        )
        for r in before.conflicts
    ]
    after = select(held + later_vintages, later_decisions, "synthetic.p", mode, cutoff, qq, later_resolutions)
    assert after == before


# --- AT-Q1-3 and OBS-INV-010 / OBS-INV-014: labels, admissibility, eligibility fields ---------------


@pytest.mark.parametrize("q_offset", [-1, 0, 1])
def test_at_q1_3_labels_and_admissibility_for_every_mode(tmp_path, q_offset):
    vs = store_at(tmp_path / "s")
    vs.ingest(capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1)), CaptureMode.SCHEDULED)
    t = utc(2026, 1, 12, 12)
    q = t + timedelta(hours=q_offset)
    views = {
        KnowledgeMode.AS_CAPTURED_BY_HIO: vs.as_captured_by_hio(RATE, t),
        KnowledgeMode.AS_KNOWN_BY_MARKET: vs.as_known_by_market(RATE, t, q),
        KnowledgeMode.RECONSTRUCTED: vs.reconstructed(RATE, t, q),
        KnowledgeMode.LATEST: vs.latest(RATE, q),
    }
    later = q_offset > 0
    expected = {
        KnowledgeMode.AS_CAPTURED_BY_HIO: ("point_in_time", False, False, True),
        KnowledgeMode.AS_KNOWN_BY_MARKET: ("point_in_time", later, False, not later),
        KnowledgeMode.RECONSTRUCTED: ("reconstructed", False, later, False),
        KnowledgeMode.LATEST: ("descriptive", False, True, False),
    }
    for mode, view in views.items():
        got = (view.label, view.quality_after_cutoff, view.restated_quality, view.predictive_pit_admissible)
        assert got == expected[mode], mode
        assert view.quality_as_of == (t if mode is KnowledgeMode.AS_CAPTURED_BY_HIO else q)
        for key, v in view.values.items():  # per-value market claim and HIO validation, distinguishable
            assert (v.knowable_at, v.knowable_basis, v.captured_at) == (
                utc(2026, 1, 12),
                KnowableBasis.PUBLISHER_TIMESTAMP,
                utc(2026, 1, 12, 1),
            )
            assert view.eligibility_decided_at[key] == v.captured_at


def test_at_q1_3_obs_inv_014_no_override_and_the_guard_refuses_inadmissible_results(tmp_path):
    vs = store_at(tmp_path / "s")
    vs.ingest(capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1)), CaptureMode.SCHEDULED)
    t = utc(2026, 1, 12, 12)
    require_predictive_pit(vs.as_captured_by_hio(RATE, t))
    require_predictive_pit(vs.as_known_by_market(RATE, t, t))
    for view in (
        vs.as_known_by_market(RATE, t, t + timedelta(hours=1)),
        vs.reconstructed(RATE, t, t),
        vs.latest(RATE, t),
    ):
        with pytest.raises(InadmissibleForPredictivePointInTime):
            require_predictive_pit(view)
    with pytest.raises(ValueError):  # Q cannot be overridden for as_captured_by_hio
        vs.view(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, t, t + timedelta(hours=1))
    with pytest.raises(AttributeError):  # admissibility is computed, not settable
        vs.as_known_by_market(RATE, t, t + timedelta(hours=1)).predictive_pit_admissible = True  # type: ignore[misc]


# --- AT-Q1-4 and OBS-INV-012: decision-clock refusals, store unchanged -------------------------------


def test_at_q1_4_backdated_or_out_of_order_quality_decisions_are_refused(jumped):
    vs = jumped
    before = vs.store.snapshot()
    late_clock = store_at(vs.store.root)
    late_clock._clock = lambda: utc(2026, 1, 18)
    with pytest.raises(DecisionRefused, match="backdated"):  # decided before it is recorded
        late_clock.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "x", utc(2026, 1, 17))
    with pytest.raises(DecisionRefused, match="previous decision"):  # not after the capture
        vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "x", utc(2026, 1, 15, 9))
    with pytest.raises(PermissionError):  # an agent may propose, not decide
        vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "claude/implementation-agent", "x", E1)
    assert vs.store.snapshot() == before
    vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "x", E1)
    with pytest.raises(DecisionRefused, match="previous decision"):  # not after the previous one
        vs.set_quality(RATE, D2, 1, QualityStatus.QUARANTINED, "owner", "x", E1)


# --- AT-Q1-6 / AT-Q2-9: S1a releases unchanged; the S1a fixtures hold no conflicts ------------------

# data.csv SHA-256 at the reviewed heads (98e6a8e, 18c80f2, d9fa276; VERIFY-2026-10-24-s1a-1-1).
S1A_DATA_SHA256 = {
    "cash.aud.overnight": "9e3a03e9c5f5e6bca5bd97ffd8786451439f65ec9602a8abb2460fda172fe73c",
    "cash.usd.overnight": "97faf4e8eaba6be8b17a35d34b539ddafafe120e667ef60e78187f13acf8c6b2",
    "fx.usd_cash_vs_aud.decomposition": "6e6284932674e81cd8969f8bda3672e4a6e9ce75bbaa019ca9c6006bba125a95",
    "fx.usd_cash_vs_aud.excess": "b8ea0d6f293dbefc6e3bfd6e9da99b2751d640486b5d90bd69663e8cbeb46587",
}


def test_at_q1_6_and_at_q2_9_s1a_financial_outputs_are_unchanged_and_conflict_free(tmp_path):
    from hio.contracts.canonical import sha256_hex

    world = s1a.load_world(FIXTURES / "s1a_world")
    rights = dict(load_synthetic(FIXTURES / "rights.yaml"))
    cutoff = datetime(2026, 1, 29, tzinfo=UTC)
    vs = VintageStore(LocalObjectStore(tmp_path / "s"), world.series)
    gate = RightsGate(rights)
    s1a.run_captures(world, vs, gate, s1a.capture_instants(date(2026, 1, 5), cutoff))
    releases = s1a.build_releases(
        world,
        vs,
        gate,
        rights,
        KnowledgeMode.AS_CAPTURED_BY_HIO,
        cutoff,
        {"commit": "0" * 40, "lock_sha256": "1" * 64},
    )
    assert {d: sha256_hex(r.files["data.csv"]) for d, r in releases.items()} == S1A_DATA_SHA256
    for series_id in (s1a.CASH_RATE, s1a.AUDUSD, s1a.SOFR):
        assert vs.as_captured_by_hio(series_id, cutoff).conflicts == ()
        assert vs.conflicts(series_id, cutoff) == {}


# --- AT-Q2-1: Codex's F7 counterexample (OBS-INV-011) ------------------------------------------------


def test_at_q2_1_codex_f7_same_captures_processed_in_opposite_orders_give_identical_results(tmp_path):
    """Codex: 3.60 and 3.61 with identical publisher_timestamp, in opposite orders; the old code
    returned 3.61 in one store and 3.60 in the other."""
    views = []
    for name, first_then in (("ab", (0, 1)), ("ba", (1, 0))):
        vs = store_at(tmp_path / name)
        rs = [
            capture_only(vs, tmp_path / name, published("3.60"), utc(2026, 1, 12, 1)),
            capture_only(vs, tmp_path / name, published("3.61"), utc(2026, 1, 12, 2)),
        ]
        if first_then == (1, 0):
            with pytest.raises(IncompleteProcessing):  # out of capture order: refused, nothing written
                vs.ingest(rs[1], CaptureMode.SCHEDULED)
        for i in (0, 1):
            vs.ingest(rs[i], CaptureMode.SCHEDULED)
        views.append(vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13)))
    assert views[0] == views[1]
    assert values(views[0]) == {} and effects(views[0]) == [("knowable_at", "suppresses_key")]


def test_at_q2_1_codex_f7_opposite_capture_orders_agree_once_both_are_held(tmp_path):
    """Codex's literal case: values captured in opposite orders (two acquisition histories).
    Intermediate results may differ (OBS-INV-017); with both held they are identical."""
    final = []
    for name, order in (("x", ("3.60", "3.61")), ("y", ("3.61", "3.60"))):
        vs = store_at(tmp_path / name)
        for hour, value in zip((1, 2), order, strict=True):
            vs.ingest(
                capture_only(vs, tmp_path / name, published(value), utc(2026, 1, 12, hour)),
                CaptureMode.SCHEDULED,
            )
        mid = vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 12, 1, 30))
        assert values(mid) == {D1: Decimal(order[0])}  # only the first capture held
        final.append(vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13)))
    assert [r.conflict for r in final[0].conflicts] == [r.conflict for r in final[1].conflicts]
    assert values(final[0]) == values(final[1]) == {}


# --- AT-Q2-2: the §4(a) table, including C' ending R's effect (OBS-INV-013, OBS-INV-015) -------------


def test_at_q2_2_resolution_in_force_and_chain_extension(tmp_path):
    vs = store_at(tmp_path / "s")
    t = utc(2026, 1, 12, 12)
    r1 = capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1))
    vs.ingest(r1, CaptureMode.SCHEDULED)
    vs.ingest(capture_only(vs, tmp_path, published("3.61"), utc(2026, 1, 13, 1)), CaptureMode.SCHEDULED)
    c = vs.as_known_by_market(RATE, t, utc(2026, 1, 13, 12)).conflicts
    (report,) = [r for r in c if r.conflict.rank_clock == "knowable_at"]
    cid = report.conflict.conflict_id
    assert report.conflict.detected_at == utc(2026, 1, 13, 1)
    vs.resolve_conflict(
        RATE, cid, "select", (r1.receipt_id, "3.60"), "", "owner", "checked", utc(2026, 1, 14, 9)
    )
    vs.ingest(capture_only(vs, tmp_path, published("3.62"), utc(2026, 1, 16, 1)), CaptureMode.SCHEDULED)

    def row(q):
        view = vs.as_known_by_market(RATE, t, q)
        return values(view), [
            (r.conflict.conflict_id == cid, r.effect)
            for r in view.conflicts
            if r.conflict.rank_clock == "knowable_at"
        ]

    assert row(utc(2026, 1, 12, 12)) == ({D1: Decimal("3.60")}, [])
    assert row(utc(2026, 1, 13, 12)) == ({}, [(True, "suppresses_key")])
    assert row(utc(2026, 1, 15)) == ({D1: Decimal("3.60")}, [(True, "resolved")])
    assert row(utc(2026, 1, 17)) == (
        {},
        [(False, "suppresses_key")],
    )  # C' = {r1, r2, r3}; R does not carry over
    captured = vs.as_captured_by_hio(RATE, utc(2026, 1, 13, 12))
    assert values(captured) == {D1: Decimal("3.61")}
    assert effects(captured) == [("knowable_at", "not_eligible_in_mode")]
    diag = vs.conflicts(RATE, utc(2026, 1, 17))
    (entry,) = diag.values()
    assert entry["chain"][0] == cid and len(entry["chain"]) == 2  # history: C then C'


# --- AT-Q2-3 / AT-Q2-4: processing order, the A, B, C case and the refused midway state ------------


def test_at_q2_3_and_4_every_processing_order_reaches_the_same_results(tmp_path):
    texts = [published("3.60"), published("3.61"), published("3.62"), published("3.70", key="2026-01-13")]
    hours_ = [1, 2, 3, 4]
    baseline = None
    for n, order in enumerate(itertools.permutations(range(4))):
        root = tmp_path / f"p{n}"
        vs = store_at(root)
        rs = [capture_only(vs, root, txt, utc(2026, 1, 12, h)) for txt, h in zip(texts, hours_, strict=True)]
        processed = set()
        for i in order:
            if any(j not in processed for j in range(i)):
                before = vs.store.snapshot()
                with pytest.raises(IncompleteProcessing):  # a midway, out-of-order step is refused
                    vs.ingest(rs[i], CaptureMode.SCHEDULED)
                assert vs.store.snapshot() == before
                with pytest.raises(IncompleteProcessing):  # and so is a query at a Q past the gap
                    vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13))
        for i in range(4):  # the refused steps are then completed in capture order
            if i not in processed:
                vs.ingest(rs[i], CaptureMode.SCHEDULED)
                processed.add(i)
        assert not any(
            k.startswith(("catalogue/resolutions/", "catalogue/conflicts/")) for k in vs.store.list()
        )
        got = (
            [vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 12, h, 30)) for h in hours_],
            vs.conflicts(RATE, utc(2026, 1, 13)),
        )
        baseline = baseline or got
        assert got == baseline
    views, diag = baseline
    assert values(views[0]) == {D1: Decimal("3.60")}  # A only
    assert values(views[1]) == {}  # {A, B}
    assert values(views[3]) == {D2: Decimal("3.70")}  # {A, B, C} suppresses D1
    (entry,) = diag.values()
    assert len(entry["chain"]) == 2  # {A,B} then {A,B,C}


# --- AT-Q2-5: genuinely different acquisition histories (OBS-INV-017) ------------------------------


def test_at_q2_5_two_capture_histories_differ_midway_and_agree_finally(tmp_path):
    finals, mids = [], []
    for name, order in (("x", ("3.61", "3.62")), ("y", ("3.62", "3.61"))):
        vs = store_at(tmp_path / name)
        vs.ingest(
            capture_only(vs, tmp_path / name, published("3.60"), utc(2026, 1, 12, 1)), CaptureMode.SCHEDULED
        )
        for hour, value in zip((2, 3), order, strict=True):
            vs.ingest(
                capture_only(vs, tmp_path / name, published(value), utc(2026, 1, 12, hour)),
                CaptureMode.SCHEDULED,
            )
        mids.append(vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 12, 2, 30)).conflicts)
        finals.append(vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13)))
    assert mids[0][0].conflict.members != mids[1][0].conflict.members  # {A,B} versus {A,C}
    assert finals[0].conflicts[0].conflict == finals[1].conflicts[0].conflict  # {A,B,C}, same id
    assert values(finals[0]) == values(finals[1]) == {}


# --- AT-Q2-6 and OBS-INV-016: diagnostics, one fixture per effect -----------------------------------


def test_at_q2_6_every_effect_and_the_two_way_comparison(tmp_path):
    vs = store_at(tmp_path / "s")
    t = utc(2026, 1, 20)
    rows = lambda *r: receipt_text("d", list(r), HEADER)  # noqa: E731
    # D1: a conflict outranked by a later instant. D2: a schedule-only conflict (not market evidence).
    vs.ingest(
        capture_only(vs, tmp_path, rows(f"{RATE},2026-01-12,3.60,2026-01-12T00:00:00Z"), utc(2026, 1, 15, 1)),
        CaptureMode.SCHEDULED,
    )
    vs.ingest(
        capture_only(vs, tmp_path, rows(f"{RATE},2026-01-12,3.61,2026-01-12T00:00:00Z"), utc(2026, 1, 15, 2)),
        CaptureMode.SCHEDULED,
    )
    vs.ingest(
        capture_only(vs, tmp_path, rows(f"{RATE},2026-01-12,3.65,2026-01-14T00:00:00Z"), utc(2026, 1, 15, 3)),
        CaptureMode.SCHEDULED,
    )
    plain = "series_id,valid_time,value"
    for hour, value in ((4, "3.66"), (5, "3.67")):  # within the jump threshold: both valid
        vs.ingest(
            capture_only(
                vs,
                tmp_path,
                receipt_text("late", [f"{RATE},2026-01-13,{value}"], plain),
                utc(2026, 1, 17, hour),
            ),
            CaptureMode.BACKFILL,
        )  # a backfill has only the schedule: schedule_only, both at the scheduled release instant
    market = vs.as_known_by_market(RATE, t, t)
    rec = vs.reconstructed(RATE, t, t)
    assert values(market) == {D1: Decimal("3.65")}
    eff = {(r.conflict.key, r.conflict.rank_clock): r.effect for r in market.conflicts}
    assert eff[(D1, "knowable_at")] == "outranked"
    assert eff[(D2, "knowable_at")] == "not_eligible_in_mode"
    assert {(r.conflict.key, r.effect) for r in rec.conflicts if r.conflict.rank_clock == "knowable_at"} == {
        (D1, "outranked"),
        (D2, "suppresses_key"),
    }
    # Two-way comparison: each view's conflicts are exactly the diagnostics' conflicts in force.
    diag = vs.conflicts(RATE, t)
    for view in (market, rec, vs.as_captured_by_hio(RATE, t), vs.latest(RATE, t)):
        assert {r.conflict.conflict_id for r in view.conflicts} == set(diag)
    # Resolved: the owner rejects the schedule-only pair; reconstructed then reports it resolved.
    (sched,) = [r for r in rec.conflicts if r.conflict.key == D2 and r.conflict.rank_clock == "knowable_at"]
    vs.resolve_conflict(
        RATE, sched.conflict.conflict_id, "reject_all", None, "contradictory", "owner", "x", utc(2026, 1, 21)
    )
    after = vs.reconstructed(RATE, t, utc(2026, 1, 22))
    assert D2 not in after.values
    assert any(r.conflict.key == D2 and r.effect == "resolved" for r in after.conflicts)


# --- AT-Q2-7 and OBS-INV-018: reproducibility pins ----------------------------------------------------


def test_at_q2_7_results_carry_pins_and_reproduce_from_them(tmp_path):
    vs = store_at(tmp_path / "s")
    vs.ingest(capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1)), CaptureMode.SCHEDULED)
    vs.ingest(capture_only(vs, tmp_path, published("3.61"), utc(2026, 1, 12, 2)), CaptureMode.SCHEDULED)
    t = utc(2026, 1, 13)
    view = vs.as_known_by_market(RATE, t, t)
    assert view.evidence_digest == vs.evidence_digest(RATE, t)
    # hio-obs-select/3 since OBS-AMEND-Q002-R1 (OD-0035) added quality_digest to every result.
    assert view.algorithm_revision == "hio-obs-select/3" and len(view.resolution_digest) == 64
    # Recompute from the pinned evidence in a fresh store (same receipts, same order): identical.
    again = store_at(tmp_path / "s")
    assert again.as_known_by_market(RATE, t, t) == view
    # A later capture changes the evidence pin only for Q at or after it.
    vs.ingest(capture_only(vs, tmp_path, published("3.62"), utc(2026, 1, 14)), CaptureMode.SCHEDULED)
    assert vs.as_known_by_market(RATE, t, t) == view
    assert vs.as_known_by_market(RATE, t, utc(2026, 1, 15)).evidence_digest != view.evidence_digest


def test_at_q2_7_a_broken_evidence_pin_is_refused(tmp_path):
    from hio.marketdata.vintages import ReceiptIntegrityError

    vs = store_at(tmp_path / "s")
    r = capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1))
    vs.ingest(r, CaptureMode.SCHEDULED)
    from hio.contracts.layout import receipt_key

    path = vs.store.root / receipt_key(SRC, r.captured_at, r.receipt_id)
    path.chmod(0o644)
    path.write_bytes(b"# SYNTHETIC altered\n")
    with pytest.raises(ReceiptIntegrityError):
        store_at(tmp_path / "s").as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13))


# --- OBS-INV-019: completeness by observation identity and content, not counts ----------------------


def test_obs_inv_019_a_captured_but_unprocessed_receipt_refuses_queries_and_resolutions(tmp_path):
    vs = store_at(tmp_path / "s")
    vs.ingest(capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1)), CaptureMode.SCHEDULED)
    capture_only(vs, tmp_path, published("3.61"), utc(2026, 1, 12, 2))  # captured, never processed
    t = utc(2026, 1, 13)
    assert values(vs.as_known_by_market(RATE, t, utc(2026, 1, 12, 1, 30))) == {D1: Decimal("3.60")}
    with pytest.raises(IncompleteProcessing):
        vs.as_known_by_market(RATE, t, t)
    with pytest.raises(IncompleteProcessing):
        vs.conflicts(RATE, t)


def test_obs_inv_019_same_count_wrong_content_is_detected(tmp_path):
    """One receipt, one vintage: the count matches, but the stored value is not the receipt's."""
    import json

    from hio.contracts.canonical import canonical_json

    vs = store_at(tmp_path / "s")
    r = capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1))
    vs.ingest(r, CaptureMode.SCHEDULED)
    (key,) = [k for k in vs.store.list("catalogue/vintages/")]
    record = json.loads(vs.store.get(key))
    record["value"] = "3.99"  # a forged vintage: same receipt id, same count, wrong content
    path = vs.store.root / key
    path.chmod(0o644)
    path.write_bytes(canonical_json(record))
    with pytest.raises(IncompleteProcessing):
        store_at(tmp_path / "s").as_captured_by_hio(RATE, utc(2026, 1, 13))


# --- AT-Q2-8: resolutions are append-only and refused when invalid ----------------------------------


def test_at_q2_8_resolution_refusals_leave_the_store_unchanged_and_events_are_append_only(tmp_path):
    vs = store_at(tmp_path / "s")
    r1 = capture_only(vs, tmp_path, published("3.60"), utc(2026, 1, 12, 1))
    vs.ingest(r1, CaptureMode.SCHEDULED)
    vs.ingest(capture_only(vs, tmp_path, published("3.61"), utc(2026, 1, 12, 2)), CaptureMode.SCHEDULED)
    t = utc(2026, 1, 13)
    (c,) = [
        r.conflict
        for r in vs.as_known_by_market(RATE, t, t).conflicts
        if r.conflict.rank_clock == "knowable_at"
    ]
    before = vs.store.snapshot()
    refusals = [
        (PermissionError, dict(actor="gate")),
        (PermissionError, dict(actor="claude/implementation-agent")),
        (DecisionRefused, dict(conflict_id="0" * 64)),  # not the conflict in force
        (DecisionRefused, dict(member=("f" * 64, "3.6"))),  # not a member
        (DecisionRefused, dict(decided_at=utc(2026, 1, 12, 1, 30))),  # before the conflict existed
    ]
    for exc, override in refusals:
        args = (
            dict(
                series_id=RATE,
                conflict_id=c.conflict_id,
                outcome="select",
                member=(r1.receipt_id, "3.6"),
                reason="",
                actor="owner",
                evidence="x",
                decided_at=t,
            )
            | override
        )
        with pytest.raises(exc):
            vs.resolve_conflict(**args)
    backdating = store_at(tmp_path / "s")
    backdating._clock = lambda: utc(2026, 1, 14)
    with pytest.raises(DecisionRefused, match="backdated"):
        backdating.resolve_conflict(RATE, c.conflict_id, "reject_all", None, "", "owner", "x", t)
    assert vs.store.snapshot() == before
    first = vs.resolve_conflict(RATE, c.conflict_id, "select", (r1.receipt_id, "3.60"), "", "owner", "x", t)
    snapshot = vs.store.snapshot()
    with pytest.raises(DecisionRefused):  # a later resolution must be strictly later
        vs.resolve_conflict(RATE, c.conflict_id, "reject_all", None, "", "owner", "x", t)
    vs.resolve_conflict(RATE, c.conflict_id, "reject_all", None, "", "owner", "x", t + timedelta(hours=1))
    after = vs.store.snapshot()
    assert all(after[k] == v for k, v in snapshot.items())  # earlier events untouched: append-only
    assert first.member == (r1.receipt_id, "3.6")  # canonical value
    reloaded = store_at(tmp_path / "s")
    assert values(reloaded.as_known_by_market(RATE, t, t + timedelta(minutes=30))) == {D1: Decimal("3.60")}
    assert values(reloaded.as_known_by_market(RATE, t, t + timedelta(hours=2))) == {}
