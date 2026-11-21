"""E-0002's issuer check, on invented numbers only."""

import importlib
import sys
from datetime import date
from decimal import Decimal as D
from itertools import pairwise
from pathlib import Path

from hio.library.vehicle_return import VehiclePeriod

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
tool = importlib.import_module("e0002_issuer_check")  # one copy, so its Stop is the one other tools raise

P = VehiclePeriod
DAYS = [date(2020, 1, 31), date(2020, 6, 30), date(2020, 12, 31), date(2021, 6, 30), date(2021, 12, 31)]
PERIODS = [P(a, b, D("0.1"), D(0), D("0.1")) for a, b in pairwise(DAYS)]


def check(start, end, years, percent):
    return tool.Check("X", "annualised", start, end, years, percent)


def test_it_compounds_from_the_last_date_on_or_before_each_end():
    assert tool.compounded(PERIODS, date(2020, 12, 31), date(2021, 12, 31)) == D("0.21")


def test_a_period_outside_the_history_is_none():
    assert tool.compounded(PERIODS, date(2019, 1, 1), date(2021, 1, 1)) is None
    assert tool.compounded(PERIODS, date(2020, 12, 31), date(2022, 1, 1)) is None


def test_annualising_by_hand():
    assert abs(tool.annual_percent(D("0.21"), 2) - 10) < 1e-9


def test_the_pass_mark_is_ten_hundredths_of_a_point_a_year():
    a = tool.evaluate([check(date(2020, 12, 31), date(2021, 12, 31), 1, 21.09)], {"X": PERIODS})[0]
    b = tool.evaluate([check(date(2020, 12, 31), date(2021, 12, 31), 1, 21.11)], {"X": PERIODS})[0]
    assert a["passes"] is True and b["passes"] is False


def test_out_of_range_fails_and_is_never_a_pass():
    row = tool.evaluate([check(date(2019, 1, 1), date(2021, 1, 1), 1, 5.0)], {"X": PERIODS})[0]
    assert row["passes"] is False and row["hio"] is None


def test_the_tally_counts_passes_and_holds_no_value():
    rows = tool.evaluate([check(date(2020, 12, 31), date(2021, 12, 31), 1, 21.0)], {"X": PERIODS})
    assert tool.tally(rows) == {"X": {"checks": 1, "pass": 1}}


def test_the_report_is_marked_for_the_owner():
    rows = tool.evaluate([check(date(2020, 12, 31), date(2021, 12, 31), 1, 21.0)], {"X": PERIODS})
    assert tool.render(rows).startswith("# E-0002 issuer check: for the owner and HIO's agents")
