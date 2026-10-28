"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-5 (OD-0067): RITS and NSW calendars are
dated, cited documents with a stated coverage; a date outside it refuses; and dates on which RITS and
NSW differ change rate selection and period ends as RA §3.2 requires.

The fixtures are SYNTHETIC (invented closures). Retaining real RITS and NSW reference data is a
separate step that needs the owner's D7 rights decision; these tests fix the format and behaviour."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from hio.contracts.temporal import KnowableBasis
from hio.jobs.s1b1 import Calendars
from hio.library.cash import ACT_360, ACT_365F, RateFixing, overnight_series
from hio.reference.calendar import BusinessCalendar, CalendarCoverageError, load_reference_calendar
from tests.test_s1b1_releases import (  # noqa: F401  (world is a fixture)
    CAL_FX,
    NSW,
    RITS,
    world,
)

D = date
RITS_ONLY_CLOSED = D(2026, 11, 3)  # a synthetic RITS closure on an NSW business day
NSW_ONLY_CLOSED = D(2026, 10, 5)  # a synthetic NSW closure on a RITS business day


def fix(*days_rates):
    at = datetime(2026, 11, 30, tzinfo=UTC)
    return {d: RateFixing(d, Decimal(r), at, KnowableBasis.SCHEDULE_ONLY) for d, r in days_rates}


def test_f5_the_fixtures_differ_in_both_directions():
    assert not RITS.is_business_day(RITS_ONLY_CLOSED) and NSW.is_business_day(RITS_ONLY_CLOSED)
    assert RITS.is_business_day(NSW_ONLY_CLOSED) and not NSW.is_business_day(NSW_ONLY_CLOSED)


def test_f5_a_rits_closure_carries_the_prior_rits_rate_and_ends_no_aud_period():
    fixings = fix((D(2026, 11, 2), "3.65"), (D(2026, 11, 4), "3.70"))
    ends = RITS.business_days(D(2026, 11, 2), D(2026, 11, 5))
    assert RITS_ONLY_CLOSED not in ends
    series = overnight_series(ends, fixings, RITS, ACT_365F)
    first = series.periods[0]
    assert (first.start, first.end) == (D(2026, 11, 2), D(2026, 11, 4))
    assert first.legs == ((D(2026, 11, 2), Decimal("3.65"), 2),)  # Mon's rate for Mon and Tue
    assert first.r == Decimal("3.65") / 100 * 2 / 365


def test_f5_the_same_dates_on_nsw_period_ends_split_the_period_but_select_the_same_rate():
    """USD-style: period ends on NSW (Nov 3 is an NSW day); rates selected on the rate calendar."""
    fixings = fix((D(2026, 11, 2), "3.65"), (D(2026, 11, 4), "3.70"))
    ends = NSW.business_days(D(2026, 11, 2), D(2026, 11, 5))
    assert RITS_ONLY_CLOSED in ends
    series = overnight_series(ends, fixings, RITS, ACT_360)
    by_start = {p.start: p for p in series.periods}
    assert by_start[D(2026, 11, 2)].end == RITS_ONLY_CLOSED
    assert by_start[RITS_ONLY_CLOSED].legs == ((D(2026, 11, 2), Decimal("3.65"), 1),)  # no Nov 3 rate exists


def test_f5_an_nsw_closure_ends_no_usd_period_in_the_built_release(world):
    usd = world[6]["cash.usd.overnight"]
    ends = {line.split(",")[1] for line in usd.files["data.csv"].decode().splitlines()[1:]}
    assert NSW_ONLY_CLOSED.isoformat() not in ends


def test_f5_a_date_outside_the_cited_coverage_refuses():
    with pytest.raises(CalendarCoverageError):
        RITS.is_business_day(D(2027, 1, 4))
    with pytest.raises(CalendarCoverageError):
        RITS.latest_on_or_before(D(2026, 8, 31))
    with pytest.raises(CalendarCoverageError):  # a period that runs past the coverage is not guessed
        overnight_series([D(2026, 12, 30), D(2027, 1, 4)], fix((D(2026, 12, 30), "3.6")), RITS, ACT_365F)


def test_f5_releases_name_the_dated_calendar_files_they_used(world):
    qs = world[6]["cash.aud.overnight"].core["quality_summary"]["calendars"]
    digest = hashlib.sha256((CAL_FX / "calendar_rits.yaml").read_bytes()).hexdigest()
    assert qs == {"rate_selection": f"rits@2026-10-28#sha256:{digest}", "period_ends": qs["rate_selection"]}
    usd = world[6]["cash.usd.overnight"].core["quality_summary"]["calendars"]
    assert usd["period_ends"].startswith("nsw@2026-10-28#sha256:")
    assert usd["rate_selection"] == "nyfed.observed (derived from captured publication dates)"


def test_f5_an_uncited_rits_or_nsw_calendar_refuses():
    ny = BusinessCalendar("nyfed.observed")
    with pytest.raises(ValueError, match="rits calendar must be dated"):
        Calendars(BusinessCalendar("rits"), NSW, ny)
    with pytest.raises(ValueError, match="nsw calendar must be dated"):
        Calendars(RITS, BusinessCalendar("nsw", frozenset({NSW_ONLY_CLOSED})), ny)


GOOD = """# SYNTHETIC
calendar_id: rits
kind: {kind}
as_of: 2026-10-28
source: {source}
coverage: {{start: 2026-09-01, end: 2026-12-31}}
weekend: [5, 6]
closed:
{closed}
"""
SYNTH_SOURCE = '{citation: "SYNTHETIC test"}'
ONE = "  - {date: 2026-11-03, reason: x}"


def _load(tmp_path: Path, allow=True, **kw):
    fields = {"kind": "synthetic", "source": SYNTH_SOURCE, "closed": ONE, **kw}
    path = tmp_path / "c.yaml"
    path.write_text(GOOD.format(**fields))
    return load_reference_calendar(path, allow_synthetic=allow)


def test_f5_the_loader_accepts_only_complete_dated_cited_documents(tmp_path):
    assert _load(tmp_path).holidays == frozenset({RITS_ONLY_CLOSED})
    with pytest.raises(ValueError, match="test data"):
        _load(tmp_path, allow=False)
    with pytest.raises(ValueError, match="URL and rights_source_id"):
        _load(tmp_path, kind="reference", source='{citation: "RBA"}')
    with pytest.raises(ValueError, match="outside the coverage"):
        _load(tmp_path, closed="  - {date: 2027-01-01, reason: x}")
    with pytest.raises(ValueError, match="duplicated"):
        _load(tmp_path, closed=ONE + "\n" + ONE)
    with pytest.raises(ValueError, match="unexplained"):
        _load(tmp_path, closed="  - {date: 2026-11-03, reason: ''}")
    with pytest.raises(ValueError, match="empty citation"):
        _load(tmp_path, source='{citation: ""}')
    with pytest.raises(ValueError, match="not a dated, cited calendar"):
        _load(tmp_path, source="{url: x}")
    (tmp_path / "c.yaml").write_text(
        GOOD.format(kind="synthetic", source=SYNTH_SOURCE, closed=ONE).replace("as_of: 2026-10-28\n", "")
    )
    with pytest.raises(ValueError, match="not a dated, cited calendar"):
        load_reference_calendar(tmp_path / "c.yaml", allow_synthetic=True)
