"""The 2027 RITS and NSW reference calendars (OD-0184 A7), and the year boundary the live capture job crosses.

Source: Reserve Bank of Australia 2026 (the RITS Business Hours and "RBA Office Closures – Public and
Bank Holidays 2027" pages, read once by hand on 2026-11-21). The calendar files are real data; nothing
here is a rate. The capture workflow passes every `rits-*.yaml` to `merge_calendars`, so these tests
load the files that way."""

from __future__ import annotations

from datetime import date as D
from pathlib import Path

import pytest
import yaml

from hio.jobs.s1b1_capture import merge_calendars
from hio.reference.calendar import CalendarCoverageError, load_reference_calendar

CAL_DIR = Path(__file__).resolve().parents[1] / "src/hio/reference/calendars"
RITS27 = load_reference_calendar(CAL_DIR / "rits-2027.yaml")
NSW27 = load_reference_calendar(CAL_DIR / "nsw-2027.yaml")
# Anzac Additional Day, Bank Holiday, Labour Day
NSW_ONLY_2027 = {D(2027, 4, 26), D(2027, 8, 2), D(2027, 10, 4)}


def merged(prefix):
    return merge_calendars([load_reference_calendar(p) for p in sorted(CAL_DIR.glob(f"{prefix}-*.yaml"))])


@pytest.mark.parametrize("cal", [RITS27, NSW27], ids=["rits", "nsw"])
def test_2027_files_are_dated_cited_reference_data_from_the_cleared_source(cal):
    raw = (CAL_DIR / f"{cal.calendar_id}-2027.yaml").read_text()
    doc = yaml.safe_load(raw)
    assert doc["kind"] == "reference" and "SYNTHETIC" not in raw
    assert cal.is_cited and cal.coverage == (D(2027, 1, 1), D(2027, 12, 31))
    assert cal.citation.startswith("Source: Reserve Bank of Australia 2026.")
    assert doc["source"]["url"].startswith("https://www.rba.gov.au/")
    assert doc["source"]["rights_source_id"] == "rba_calendar_pages"
    assert all(d.weekday() < 5 for d in cal.holidays)


def test_2027_rits_closures_are_the_named_holidays_observed_in_nsw_and_victoria():
    assert RITS27.holidays == {
        D(2027, 1, 1),
        D(2027, 1, 26),
        D(2027, 3, 26),
        D(2027, 3, 29),
        D(2027, 6, 14),
        D(2027, 12, 27),
        D(2027, 12, 28),
    }


def test_2027_rits_closes_only_where_nsw_also_closes_and_differs_on_three_nsw_only_days():
    assert RITS27.holidays < NSW27.holidays
    assert NSW27.holidays - RITS27.holidays == NSW_ONLY_2027


@pytest.mark.parametrize("prefix", ["rits", "nsw"])
def test_the_committed_files_merge_across_the_year_boundary(prefix):
    cal = merged(prefix)
    assert cal.coverage == (D(2026, 1, 1), D(2027, 12, 31))
    assert cal.is_business_day(D(2026, 12, 31))  # Thursday
    assert not cal.is_business_day(D(2027, 1, 1))  # New Year's Day
    assert cal.is_business_day(D(2027, 1, 4))  # the first 2027 business day; refused before this file existed
    assert cal.business_days(D(2026, 12, 24), D(2027, 1, 5)) == [
        D(2026, 12, 24),
        D(2026, 12, 29),
        D(2026, 12, 30),
        D(2026, 12, 31),
        D(2027, 1, 4),
        D(2027, 1, 5),
    ]


def test_the_merged_rits_calendar_still_refuses_outside_its_coverage():
    cal = merged("rits")
    with pytest.raises(CalendarCoverageError):
        cal.is_business_day(D(2028, 1, 3))
