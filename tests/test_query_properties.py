"""Property tests for the query modes (S1-A5: OBS-INV-002/003; OD-0020 item 1 determinism), on the
two-clock model and derived conflicts (OBS-AMEND-Q001/Q002; OD-0029, OD-0030). Q_ALL is an HIO
decision cutoff after every generated capture, so the non-captured modes see all evidence."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from hio.contracts.observation import Vintage
from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus
from hio.marketdata.queries import select

SERIES = "synthetic.p"
T0 = datetime(2026, 1, 1, tzinfo=UTC)
instants = st.integers(min_value=0, max_value=200).map(lambda h: T0 + timedelta(hours=h))
keys = st.integers(min_value=0, max_value=4).map(lambda d: date(2026, 1, 5) + timedelta(days=d))


@st.composite
def vintage_sets(draw):
    raw = draw(
        st.lists(
            st.tuples(
                keys,
                st.integers(min_value=0, max_value=20).map(Decimal),
                instants,
                instants,
                st.sampled_from(list(KnowableBasis)),
                st.sampled_from([QualityStatus.VALID, QualityStatus.VALID, QualityStatus.QUARANTINED]),
            ),
            max_size=25,
        )
    )
    seq: dict[date, int] = {}
    out = []
    for key, value, captured, knowable, basis, quality in raw:
        seq[key] = seq.get(key, 0) + 1
        out.append(Vintage(SERIES, key, seq[key], value, "r" * 64, captured, knowable, basis, "UTC", quality))
    return out


MODES = [KnowledgeMode.AS_CAPTURED_BY_HIO, KnowledgeMode.AS_KNOWN_BY_MARKET, KnowledgeMode.RECONSTRUCTED]
Q_ALL = T0 + timedelta(hours=1000)


def q_for(mode):
    return None if mode is KnowledgeMode.AS_CAPTURED_BY_HIO else Q_ALL


def suppressed(view):
    return {r.conflict.key for r in view.conflicts if r.effect == "suppresses_key"}


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_obs_inv_002_and_003(vs, cutoff):
    captured = select(vs, {}, SERIES, KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff)
    assert all(v.captured_at <= cutoff for v in captured.values.values())  # OBS-INV-002
    known = select(vs, {}, SERIES, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff, Q_ALL)
    for v in known.values.values():  # OBS-INV-003
        assert v.knowable_at <= cutoff
        assert v.knowable_basis not in {KnowableBasis.SCHEDULE_ONLY, KnowableBasis.RULE_INFERRED}


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants, st.randoms(use_true_random=False))
def test_results_do_not_depend_on_input_order(vs, cutoff, rnd):
    shuffled = list(vs)
    rnd.shuffle(shuffled)
    for mode in MODES:
        assert select(vs, {}, SERIES, mode, cutoff, q_for(mode)) == select(
            shuffled, {}, SERIES, mode, cutoff, q_for(mode)
        )
    assert select(vs, {}, SERIES, KnowledgeMode.LATEST, None, Q_ALL) == select(
        shuffled, {}, SERIES, KnowledgeMode.LATEST, None, Q_ALL
    )


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_only_valid_vintages_are_returned_and_keys_are_never_filled(vs, cutoff):
    for mode in MODES:
        view = select(vs, {}, SERIES, mode, cutoff, q_for(mode))
        assert all(v.quality_status is QualityStatus.VALID for v in view.values.values())
        assert list(view.values) == sorted(view.values)
        assert set(view.values) <= {v.valid_time for v in vs}


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_market_keys_are_a_subset_of_reconstructed_keys(vs, cutoff):
    known = select(vs, {}, SERIES, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff, Q_ALL)
    rec = select(vs, {}, SERIES, KnowledgeMode.RECONSTRUCTED, cutoff, Q_ALL)
    # Changed by OBS-AMEND-Q002: reconstructed can lose a key that market keeps, when its own
    # top slot (for example a later schedule-only pair) is an unresolved conflict; that is then
    # reported, never silent.
    assert set(known.values) <= set(rec.values) | suppressed(rec)


@settings(max_examples=200, deadline=None)
@given(vintage_sets())
def test_latest_ranks_by_knowable_at_then_strength_never_by_recording_order(vs):
    """Changed by OBS-AMEND-Q002: latest() previously took the greatest vintage_seq (recording
    order). It now ranks by (knowable_at, basis strength); a contradictory top is suppressed."""
    view = select(vs, {}, SERIES, KnowledgeMode.LATEST, None, Q_ALL)
    for key in {x.valid_time for x in vs if x.quality_status is QualityStatus.VALID}:
        valid = [x for x in vs if x.valid_time == key and x.quality_status is QualityStatus.VALID]
        top = max((x.knowable_at, x.knowable_basis.strength) for x in valid)
        top_values = {x.value for x in valid if (x.knowable_at, x.knowable_basis.strength) == top}
        if key in view.values:
            assert (view.values[key].knowable_at, view.values[key].knowable_basis.strength) == top
            assert view.values[key].value in top_values
        else:
            assert key in suppressed(view)


@settings(max_examples=200, deadline=None)
@given(vintage_sets(), instants)
def test_quality_decisions_in_force_at_q_override_the_recorded_status(vs, cutoff):
    released = {
        (v.series_id, v.valid_time, v.vintage_seq): [
            (v.captured_at + timedelta(seconds=1), QualityStatus.VALID)
        ]
        for v in vs
    }
    view = select(vs, released, SERIES, KnowledgeMode.RECONSTRUCTED, cutoff, Q_ALL)
    eligible = {v.valid_time for v in vs if v.knowable_at <= cutoff}
    assert set(view.values) | suppressed(view) == eligible
    # A decision cutoff before every release decision leaves the recorded statuses in force.
    before = select(vs, released, SERIES, KnowledgeMode.RECONSTRUCTED, cutoff, T0 - timedelta(hours=1))
    assert before.values == {}  # nothing captured by then
