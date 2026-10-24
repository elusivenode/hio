"""Property tests for the query modes (S1-A5: OBS-INV-002/003; OD-0020 item 1 determinism)."""

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


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_obs_inv_002_and_003(vs, cutoff):
    captured = select(vs, {}, SERIES, KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff)
    assert all(v.captured_at <= cutoff for v in captured.values.values())  # OBS-INV-002
    known = select(vs, {}, SERIES, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff)
    for v in known.values.values():  # OBS-INV-003
        assert v.knowable_at <= cutoff
        assert v.knowable_basis not in {KnowableBasis.SCHEDULE_ONLY, KnowableBasis.RULE_INFERRED}


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants, st.randoms(use_true_random=False))
def test_results_do_not_depend_on_input_order(vs, cutoff, rnd):
    shuffled = list(vs)
    rnd.shuffle(shuffled)
    for mode in MODES:
        assert select(vs, {}, SERIES, mode, cutoff) == select(shuffled, {}, SERIES, mode, cutoff)
    assert select(vs, {}, SERIES, KnowledgeMode.LATEST, None) == select(
        shuffled, {}, SERIES, KnowledgeMode.LATEST, None
    )


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_only_valid_vintages_are_returned_and_keys_are_never_filled(vs, cutoff):
    for mode in MODES:
        view = select(vs, {}, SERIES, mode, cutoff)
        assert all(v.quality_status is QualityStatus.VALID for v in view.values.values())
        assert list(view.values) == sorted(view.values)
        assert set(view.values) <= {v.valid_time for v in vs}


@settings(max_examples=300, deadline=None)
@given(vintage_sets(), instants)
def test_market_keys_are_a_subset_of_reconstructed_keys(vs, cutoff):
    known = select(vs, {}, SERIES, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff)
    rec = select(vs, {}, SERIES, KnowledgeMode.RECONSTRUCTED, cutoff)
    assert set(known.values) <= set(rec.values)


@settings(max_examples=200, deadline=None)
@given(vintage_sets())
def test_latest_is_the_most_recently_recorded_valid_vintage(vs):
    view = select(vs, {}, SERIES, KnowledgeMode.LATEST, None)
    for key, v in view.values.items():
        valid = [x for x in vs if x.valid_time == key and x.quality_status is QualityStatus.VALID]
        assert v.vintage_seq == max(x.vintage_seq for x in valid)


@settings(max_examples=200, deadline=None)
@given(vintage_sets(), instants)
def test_quality_events_override_the_recorded_status(vs, cutoff):
    released = {(v.series_id, v.valid_time, v.vintage_seq): QualityStatus.VALID for v in vs}
    view = select(vs, released, SERIES, KnowledgeMode.RECONSTRUCTED, cutoff)
    eligible = {v.valid_time for v in vs if v.knowable_at <= cutoff}
    assert set(view.values) == eligible
