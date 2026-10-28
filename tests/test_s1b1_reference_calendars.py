"""F-REVIEW-2026-10-25-t0009-5, completed under D7 (OD-0076): the real RITS and NSW calendars for 2026
are dated, cited reference documents from an owner-verified source, and the dates on which they differ
change period ends but never the rate selected (RA §3.2 step 2; T-0009 §2.7, A-8).

Source: Reserve Bank of Australia 2026 (the RITS Business Hours and Public & Bank Holidays pages, read
once by hand on 2026-10-28). The calendar files are real data; the rates below are invented."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from hio.contracts.temporal import KnowableBasis
from hio.jobs.s1b1 import Calendars
from hio.library.cash import ACT_365F, RateFixing, overnight_series
from hio.reference.calendar import BusinessCalendar, CalendarCoverageError, load_reference_calendar

REPO = Path(__file__).resolve().parents[1]
CAL_DIR = REPO / "src/hio/reference/calendars"
RITS = load_reference_calendar(CAL_DIR / "rits-2026.yaml")  # no allow_synthetic: reference data only
NSW = load_reference_calendar(CAL_DIR / "nsw-2026.yaml")

D = date
NSW_BANK_HOLIDAY = D(2026, 8, 3)  # Monday: NSW Bank Holiday; RITS open (not a named RITS holiday)
NSW_ONLY = {D(2026, 4, 27), NSW_BANK_HOLIDAY, D(2026, 10, 5)}  # Additional Day, Bank Holiday, Labour Day


def fix(*days_rates):
    at = datetime(2026, 8, 31, tzinfo=UTC)
    return {d: RateFixing(d, Decimal(r), at, KnowableBasis.SCHEDULE_ONLY) for d, r in days_rates}


@pytest.mark.parametrize("cal", [RITS, NSW], ids=["rits", "nsw"])
def test_f5_the_real_calendars_are_dated_cited_reference_data(cal):
    raw = (CAL_DIR / f"{cal.calendar_id}-2026.yaml").read_text()
    doc = yaml.safe_load(raw)
    assert doc["kind"] == "reference" and "SYNTHETIC" not in raw
    assert cal.is_cited and cal.coverage == (D(2026, 1, 1), D(2026, 12, 31))
    assert cal.citation.startswith("Source: Reserve Bank of Australia 2026.")
    assert doc["source"]["url"].startswith("https://www.rba.gov.au/")
    assert all(d.weekday() < 5 for d in cal.holidays)  # weekend holidays are covered by the weekend


def test_f5_their_source_is_owner_verified_for_the_operations_used():
    sources = yaml.safe_load((REPO / "registers/sources.yaml").read_text())["sources"]
    (src,) = [s for s in sources if s["id"] == "rba_calendar_pages"]
    assert src["verification"] == "owner_verified" and src["verified_by"] == "OD-0076"
    rights = src["rights"]
    assert rights["automated_retrieval"] == "deny"  # a manual, cited read only
    for op in ("raw_retention", "internal_compute", "derivation", "derived_storage", "agent_context"):
        assert rights[op].startswith("conditional(attribution 'Source: Reserve Bank of Australia")
    for f in ("rits", "nsw"):
        doc = yaml.safe_load((CAL_DIR / f"{f}-2026.yaml").read_text())
        assert doc["source"]["rights_source_id"] == "rba_calendar_pages"


def test_f5_rits_closes_only_where_nsw_also_closes_and_they_differ_on_three_nsw_only_days():
    assert RITS.holidays < NSW.holidays
    assert NSW.holidays - RITS.holidays == NSW_ONLY
    for d in NSW_ONLY:
        assert RITS.is_business_day(d) and not NSW.is_business_day(d)


def test_f5_on_the_nsw_bank_holiday_aud_has_a_rate_and_a_period_end():
    """AUD: rates and period ends both on RITS. 3 August is a RITS day, so its own rate is used."""
    fixings = fix((D(2026, 7, 31), "3.60"), (NSW_BANK_HOLIDAY, "3.65"), (D(2026, 8, 4), "3.70"))
    ends = RITS.business_days(D(2026, 7, 31), D(2026, 8, 4))
    assert ends == [D(2026, 7, 31), NSW_BANK_HOLIDAY, D(2026, 8, 4)]
    by_start = {p.start: p for p in overnight_series(ends, fixings, RITS, ACT_365F).periods}
    assert by_start[D(2026, 7, 31)].legs == ((D(2026, 7, 31), Decimal("3.60"), 3),)  # Fri over the weekend
    assert by_start[NSW_BANK_HOLIDAY].legs == ((NSW_BANK_HOLIDAY, Decimal("3.65"), 1),)


def test_f5_on_nsw_period_ends_the_bank_holiday_ends_no_period_but_its_rits_rate_is_still_selected():
    """Period ends on NSW skip 3 August; rate selection stays on RITS, so the 3 August rate covers one day."""
    fixings = fix((D(2026, 7, 31), "3.60"), (NSW_BANK_HOLIDAY, "3.65"), (D(2026, 8, 4), "3.70"))
    ends = NSW.business_days(D(2026, 7, 31), D(2026, 8, 4))
    assert ends == [D(2026, 7, 31), D(2026, 8, 4)]
    (period,) = overnight_series(ends, fixings, RITS, ACT_365F).periods
    assert (period.start, period.end) == (D(2026, 7, 31), D(2026, 8, 4))
    assert period.legs == ((D(2026, 7, 31), Decimal("3.60"), 3), (NSW_BANK_HOLIDAY, Decimal("3.65"), 1))


def test_f5_the_real_calendars_are_accepted_where_rits_and_nsw_must_be_cited():
    cals = Calendars(RITS, NSW, BusinessCalendar("nyfed.observed"))
    assert cals.rits.identity.startswith("rits@2026-10-28#sha256:")
    assert cals.nsw.identity.startswith("nsw@2026-10-28#sha256:")


def test_f5_a_date_outside_2026_refuses_rather_than_guessing():
    for cal in (RITS, NSW):
        with pytest.raises(CalendarCoverageError):
            cal.is_business_day(D(2027, 1, 4))
        with pytest.raises(CalendarCoverageError):
            cal.is_business_day(D(2025, 12, 31))
