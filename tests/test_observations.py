"""Observations, vintages and the knowledge query modes (observations standard; OD-0020 item 1).

Covers OBS-INV-001…007, same-time vintages, revision sequences, quarantine, late capture,
evidence insufficiency and schedule-only backfills. OBS-INV-007 is a mandatory regression
fixture: tests/fixtures/synthetic/obs_inv_007_*.csv.
"""

from datetime import date
from decimal import Decimal

import pytest

from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus
from hio.marketdata.capture import SyntheticSource, capture, receipt_bytes
from hio.marketdata.series import CaptureMode
from hio.marketdata.vintages import VintageStore
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import FIXTURES, SERIES, AllowAllGate, ingest_file, ingest_text, receipt_text, utc

X, RATE, LAGGED = "synthetic.x", "synthetic.rate", "synthetic.lagged"
MONTHLY_SRC, DAILY_SRC = "synthetic.monthly_source", "synthetic.daily_source"
KEY = date(2020, 2, 28)
D1, D2, D3 = date(2026, 1, 12), date(2026, 1, 13), date(2026, 1, 14)


# Every decision in these tests is recorded at 2026-01-01; decisions dated later are allowed
# (OBS-INV-012 forbids only backdating).
CLOCK = lambda: utc(2026, 1, 1)  # noqa: E731
Q_LATE = utc(2026, 2, 1)  # an HIO decision cutoff after every capture in these tests


@pytest.fixture
def vs(tmp_path):
    return VintageStore(LocalObjectStore(tmp_path / "store"), SERIES, clock=CLOCK)


def values(view):
    return {k: v.value for k, v in view.values.items()}


# --- OBS-INV-007: the §4.1 fixture (mandatory regression) ----------------------------------------


def test_obs_inv_007_case_a_backfill_alone(vs):
    ingest_file(
        vs, MONTHLY_SRC, FIXTURES / "obs_inv_007_backfill.csv", utc(2026, 1, 10), CaptureMode.BACKFILL
    )
    (v,) = vs.all_vintages()
    assert (v.value, v.knowable_basis) == (Decimal(110), KnowableBasis.SCHEDULE_ONLY)
    assert values(vs.as_known_by_market(X, utc(2021, 1, 1), Q_LATE)) == {}  # absent, not filled
    reconstructed = vs.reconstructed(X, utc(2021, 1, 1), Q_LATE)
    assert values(reconstructed) == {KEY: Decimal(110)}
    assert reconstructed.label == "reconstructed"  # never described as point-in-time evidence
    assert values(vs.as_captured_by_hio(X, utc(2021, 1, 1))) == {}
    assert values(vs.as_captured_by_hio(X, utc(2026, 2, 1))) == {KEY: Decimal(110)}


@pytest.mark.parametrize("archive_first", [False, True])
def test_obs_inv_007_case_b_with_publisher_vintages(vs, archive_first):
    files = [
        ("obs_inv_007_backfill.csv", CaptureMode.BACKFILL),
        ("obs_inv_007_archive.csv", CaptureMode.BACKFILL),
    ]
    for day, (name, mode) in enumerate(reversed(files) if archive_first else files, start=10):
        ingest_file(vs, MONTHLY_SRC, FIXTURES / name, utc(2026, 1, day), mode)
    # OBS-INV-007 as amended by OBS-AMEND-Q001: Q after the archive was ingested gives 100 and
    # 110, labelled and not admissible; at Q = 2021-01-01 HIO did not hold the archive.
    early = vs.as_known_by_market(X, utc(2021, 1, 1), Q_LATE)
    assert values(early) == {KEY: Decimal(100)}
    assert early.quality_after_cutoff and not early.predictive_pit_admissible
    assert values(vs.as_known_by_market(X, utc(2025, 7, 1), Q_LATE)) == {KEY: Decimal(110)}
    assert values(vs.as_known_by_market(X, utc(2021, 1, 1), utc(2021, 1, 1))) == {}
    # reconstructed(T) is "the latest valid vintage with knowable_at <= T under any basis" (§4).
    # The schedule-only 110 is placed at its scheduled release (2020-03-16T00:30Z), after the
    # archive's 100 (2020-03-15T00:30Z), so the standard's definition gives 110, whatever the
    # ingestion order. (Flagged for review: schedule-only placement can contradict publisher
    # evidence; the standard does not say that evidence should override it.)
    assert values(vs.reconstructed(X, utc(2021, 1, 1), Q_LATE)) == {KEY: Decimal(110)}


# --- OBS-INV-001 and OBS-INV-004 -------------------------------------------------------------------


def test_obs_inv_001_identical_refetch_makes_no_vintage_and_a_change_makes_the_next(vs, tmp_path):
    first = receipt_text("day 1", ["synthetic.rate,2026-01-12,3.60"])
    r1 = ingest_text(vs, tmp_path, DAILY_SRC, first, utc(2026, 1, 12, 0), CaptureMode.SCHEDULED)
    r2 = ingest_text(vs, tmp_path, DAILY_SRC, first, utc(2026, 1, 12, 1), CaptureMode.SCHEDULED)
    assert len(r1.new_vintages) == 1 and r2 is None  # identical bytes: a no-op before ingest
    # Different bytes carrying the same value: ingested, but no new vintage.
    same_value = receipt_text("re-issued file", ["synthetic.rate,2026-01-12,3.60"])
    r2b = ingest_text(vs, tmp_path, DAILY_SRC, same_value, utc(2026, 1, 12, 2), CaptureMode.SCHEDULED)
    assert (len(r2b.new_vintages), r2b.redundant) == (0, 1)
    changed = receipt_text("revised", ["synthetic.rate,2026-01-12,3.65"])
    r3 = ingest_text(vs, tmp_path, DAILY_SRC, changed, utc(2026, 1, 12, 5), CaptureMode.SCHEDULED)
    assert [v.vintage_seq for v in r3.new_vintages] == [2]
    assert [v.value for v in vs.all_vintages()] == [Decimal("3.60"), Decimal("3.65")]  # both retrievable
    assert r3.revisions == [(RATE, D1, Decimal("3.60"), Decimal("3.65"))]  # logged, not quarantined


def test_identical_consecutive_refetch_is_a_no_op(vs, tmp_path):
    path = tmp_path / "dup.csv"
    path.write_text(receipt_text("dup", ["synthetic.rate,2026-01-12,3.60"]))
    src, gate = SyntheticSource(DAILY_SRC, path), AllowAllGate()
    _, new1 = capture(src, vs.store, gate, utc(2026, 1, 12))
    before = vs.store.snapshot()
    receipt, new2 = capture(src, vs.store, gate, utc(2026, 1, 13))
    assert (new1, new2) == (True, False)
    assert receipt.captured_at == utc(2026, 1, 12)  # the first capture stands
    assert vs.store.snapshot() == before


def test_obs_inv_004_every_vintage_references_a_verifying_receipt(vs, tmp_path):
    ingest_text(
        vs,
        tmp_path,
        DAILY_SRC,
        receipt_text("a", ["synthetic.rate,2026-01-12,3.60"]),
        utc(2026, 1, 12),
        CaptureMode.SCHEDULED,
    )
    from hio.marketdata.capture import load_receipt

    for v in vs.all_vintages():
        source = SERIES[v.series_id].source_id
        receipt_bytes(
            vs.store, load_receipt(vs.store, source, v.captured_at, v.receipt_id)
        )  # verifies the hash


# --- scheduled capture, late capture, revisions -------------------------------------------------------


def test_scheduled_capture_on_time_is_captured_on_schedule(vs, tmp_path):
    ingest_text(
        vs,
        tmp_path,
        DAILY_SRC,
        receipt_text("d1", ["synthetic.rate,2026-01-12,3.60"]),
        utc(2026, 1, 12, 0),
        CaptureMode.SCHEDULED,
    )  # 11:00 Sydney, after the 09:00 release
    (v,) = vs.all_vintages()
    assert v.knowable_basis is KnowableBasis.CAPTURED_ON_SCHEDULE
    assert v.knowable_at == utc(2026, 1, 11, 22)  # 09:00 Sydney (AEDT, UTC+11)
    # knowable_at placement, judged with Q after the capture (the vintage is held).
    after = utc(2026, 1, 12, 1)
    assert values(vs.as_known_by_market(RATE, utc(2026, 1, 11, 21, 59), after)) == {}
    assert values(vs.as_known_by_market(RATE, utc(2026, 1, 11, 22), after)) == {D1: Decimal("3.60")}
    # At Q = T, before the capture, HIO did not hold it (OBS-AMEND-Q001).
    assert values(vs.as_known_by_market(RATE, utc(2026, 1, 11, 22), utc(2026, 1, 11, 22))) == {}


def test_late_capture_is_schedule_only_and_not_market_evidence(vs, tmp_path):
    """Captured beyond the grace: the value may already be a revision, so the schedule is not
    evidence for it."""
    ingest_text(
        vs,
        tmp_path,
        DAILY_SRC,
        receipt_text("late", ["synthetic.rate,2026-01-12,3.60"]),
        utc(2026, 1, 20),
        CaptureMode.SCHEDULED,
    )
    (v,) = vs.all_vintages()
    assert v.knowable_basis is KnowableBasis.SCHEDULE_ONLY
    assert values(vs.as_known_by_market(RATE, utc(2026, 2, 1), utc(2026, 2, 1))) == {}
    assert values(vs.reconstructed(RATE, utc(2026, 2, 1), utc(2026, 2, 1))) == {D1: Decimal("3.60")}
    assert values(vs.as_captured_by_hio(RATE, utc(2026, 1, 19))) == {}
    assert values(vs.as_captured_by_hio(RATE, utc(2026, 1, 20))) == {D1: Decimal("3.60")}


def test_revision_sequence_including_a_revert(vs, tmp_path):
    seq = [("3.60", utc(2026, 1, 12, 0)), ("3.65", utc(2026, 1, 12, 3)), ("3.60", utc(2026, 1, 12, 6))]
    for value, at in seq:
        ingest_text(
            vs,
            tmp_path,
            DAILY_SRC,
            receipt_text(value, [f"synthetic.rate,2026-01-12,{value}"]),
            at,
            CaptureMode.SCHEDULED,
        )
    assert [v.vintage_seq for v in vs.all_vintages()] == [1, 2, 3]  # the revert is a new vintage
    at = lambda h: values(vs.as_captured_by_hio(RATE, utc(2026, 1, 12, h)))  # noqa: E731
    assert (at(1), at(4), at(7)) == ({D1: Decimal("3.60")}, {D1: Decimal("3.65")}, {D1: Decimal("3.60")})
    # A revision is knowable from HIO's capture of it, not from the original release.
    v2 = vs.all_vintages()[1]
    assert (v2.knowable_basis, v2.knowable_at) == (KnowableBasis.CAPTURED_ON_SCHEDULE, utc(2026, 1, 12, 3))
    assert values(vs.as_known_by_market(RATE, utc(2026, 1, 12, 2), utc(2026, 1, 12, 2))) == {
        D1: Decimal("3.60")
    }


# --- same-time vintages ---------------------------------------------------------------------------


def test_same_time_contradictions_are_conflicts_not_ingestion_order(vs, tmp_path):
    """Changed by OBS-AMEND-Q002 (OD-0030). This test previously asserted that the later-recorded
    vintage (3.61) won: the ingestion-order tie-break of F-REVIEW-2026-10-24-s1a-1-7. Equal
    knowable_at and basis with different values are now a derived conflict: the key is absent
    and the conflict is reported, until an owner resolution."""
    header = "series_id,valid_time,value,published_at"
    stamp = "2026-01-12T00:00:00Z"
    for value, at in [("3.60", utc(2026, 1, 12, 1)), ("3.61", utc(2026, 1, 12, 2))]:
        ingest_text(
            vs,
            tmp_path,
            DAILY_SRC,
            receipt_text(value, [f"synthetic.rate,2026-01-12,{value},{stamp}"], header),
            at,
            CaptureMode.SCHEDULED,
        )
    for view in (
        vs.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13)),
        vs.reconstructed(RATE, utc(2026, 1, 13), utc(2026, 1, 13)),
        vs.latest(RATE, utc(2026, 1, 13)),
    ):
        assert values(view) == {}
        assert [r.effect for r in view.conflicts if r.conflict.rank_clock == "knowable_at"] == [
            "suppresses_key"
        ]
    # The capture clock has no tie (captured 01:00 and 02:00): the later capture is HIO's view.
    assert values(vs.as_captured_by_hio(RATE, utc(2026, 1, 13))) == {D1: Decimal("3.61")}
    # A reload from the store gives identical results.
    again = VintageStore(vs.store, SERIES, clock=CLOCK)
    assert again.as_known_by_market(RATE, utc(2026, 1, 13), utc(2026, 1, 13)) == vs.as_known_by_market(
        RATE, utc(2026, 1, 13), utc(2026, 1, 13)
    )
    assert again.all_vintages() == vs.all_vintages()


# --- quarantine -------------------------------------------------------------------------------------


def test_jump_quarantines_until_the_owner_releases_it(vs, tmp_path):
    rows = [
        "synthetic.rate,2026-01-12,3.60",
        "synthetic.rate,2026-01-13,9.99",
        "synthetic.rate,2026-01-14,3.62",
    ]
    result = ingest_text(
        vs, tmp_path, DAILY_SRC, receipt_text("jump", rows), utc(2026, 1, 15), CaptureMode.BACKFILL
    )
    assert [v.valid_time for v in result.quarantined] == [D2]
    view = vs.reconstructed(RATE, utc(2026, 2, 1), Q_LATE)
    assert set(view.values) == {D1, D3}  # the quarantined key is absent, never filled
    with pytest.raises(PermissionError):
        vs.set_quality(
            RATE, D2, 1, QualityStatus.VALID, "claude/implementation-agent", "proposal", utc(2026, 1, 16)
        )
    vs.set_quality(RATE, D2, 1, QualityStatus.VALID, "owner", "checked against the source", utc(2026, 1, 16))
    assert set(vs.reconstructed(RATE, utc(2026, 2, 1), Q_LATE).values) == {D1, D2, D3}
    reloaded = VintageStore(vs.store, SERIES, clock=CLOCK)
    assert set(reloaded.reconstructed(RATE, utc(2026, 2, 1), Q_LATE).values) == {D1, D2, D3}
    # Decided on 16 January: a decision cutoff before then is unchanged (OBS-INV-008).
    assert set(vs.reconstructed(RATE, utc(2026, 2, 1), utc(2026, 1, 15, 12)).values) == {D1, D3}


@pytest.mark.parametrize(
    "body",
    [
        "series_id,valid_time,value\nsynthetic.rate,2026-01-12,3.60\n",  # no SYNTHETIC line
        # an instant where a date belongs
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.rate,2026-01-12T00:00:00Z,3.60\n",
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.rate,2026-01-12,abc\n",
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.rate,2026-01-12,NaN\n",
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.rate,2026-01-12,3.6,extra\n",
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.unknown,2026-01-12,3.6\n",
        "# SYNTHETIC\nseries_id,valid_time,value\nsynthetic.x,2026-01-12,3.6\n",  # another source's series
        # an evidence instant with an offset instead of Z
        "# SYNTHETIC\nseries_id,valid_time,value,published_at\n"
        "synthetic.rate,2026-01-12,3.6,2026-01-12T09:00:00+11:00\n",
    ],
)
def test_malformed_receipt_is_quarantined_whole(vs, tmp_path, body):
    result = ingest_text(vs, tmp_path, DAILY_SRC, body, utc(2026, 1, 12), CaptureMode.SCHEDULED)
    assert result.receipt_quarantined
    assert vs.all_vintages() == []
    assert any(k.startswith("catalogue/quarantine/receipts/") for k in vs.store.list())


# --- evidence insufficiency --------------------------------------------------------------------------


def test_rule_inferred_is_never_market_evidence(vs, tmp_path):
    ingest_text(
        vs,
        tmp_path,
        DAILY_SRC,
        receipt_text("lag", ["synthetic.lagged,2026-01-12,1.5"]),
        utc(2026, 1, 20),
        CaptureMode.BACKFILL,
    )
    (v,) = vs.all_vintages()
    assert v.knowable_basis is KnowableBasis.RULE_INFERRED
    assert values(vs.as_known_by_market(LAGGED, utc(2026, 2, 1), utc(2026, 2, 1))) == {}
    assert values(vs.reconstructed(LAGGED, utc(2026, 2, 1), utc(2026, 2, 1))) == {D1: Decimal("1.5")}


def test_a_capture_before_the_documented_release_is_refused(vs, tmp_path):
    from hio.marketdata.knowability import UnplaceableValue

    with pytest.raises(UnplaceableValue):
        ingest_text(
            vs,
            tmp_path,
            DAILY_SRC,
            receipt_text("early", ["synthetic.rate,2026-01-12,3.60"]),
            utc(2026, 1, 11, 12),
            CaptureMode.SCHEDULED,
        )


# --- monitoring gates -----------------------------------------------------------------------------


def test_calendar_completeness_and_staleness(vs, tmp_path):
    rows = ["synthetic.rate,2026-01-12,3.60", "synthetic.rate,2026-01-14,3.61"]
    ingest_text(vs, tmp_path, DAILY_SRC, receipt_text("gap", rows), utc(2026, 1, 15), CaptureMode.BACKFILL)
    assert vs.missing_business_days(RATE, D1, date(2026, 1, 16)) == [D2, date(2026, 1, 15), date(2026, 1, 16)]
    # Next expected: 2026-01-15, released 09:00 Sydney (22:00Z on the 14th), grace one day.
    assert not vs.is_stale(RATE, utc(2026, 1, 15, 21, 59))
    assert vs.is_stale(RATE, utc(2026, 1, 15, 22, 1))


def test_latest_takes_no_cutoff_and_other_modes_need_one(vs):
    with pytest.raises(ValueError):
        vs.view(RATE, KnowledgeMode.LATEST, utc(2026, 1, 1))
    with pytest.raises(ValueError):
        vs.view(RATE, KnowledgeMode.AS_KNOWN_BY_MARKET)
    with pytest.raises(ValueError):  # Q is required outside as_captured_by_hio
        vs.view(RATE, KnowledgeMode.AS_KNOWN_BY_MARKET, utc(2026, 1, 1))
    with pytest.raises(ValueError):  # and cannot override Q = T in as_captured_by_hio
        vs.view(RATE, KnowledgeMode.AS_CAPTURED_BY_HIO, utc(2026, 1, 1), utc(2026, 2, 1))
