"""The SPY diagnostic, on invented numbers."""

import sys
from datetime import date
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import t0023_spy_diagnostic as tool
from hio.library.vehicle_return import VehiclePeriod


def test_the_boundary_premium_is_close_over_nav_by_hand():
    assert tool.boundary_premium(D(99), D(100)) == D("-0.01")


def test_a_year_separates_the_close_gap_from_the_nav_gap_by_hand():
    a, b = date(2008, 9, 30), date(2009, 9, 30)
    fact = SimpleNamespace(start=date(2008, 10, 1), end=b, total_return_pct=D(10))
    close = [VehiclePeriod(a, b, D("0.12"), D(0), D("0.12"))]
    nav = [VehiclePeriod(a, b, D("0.10"), D(0), D("0.10"))]
    row = tool.year_row(fact, close, nav, {a: D(99), b: D(110)}, {a: D(100), b: D(110)})
    assert float(row["close_gap_points"]) == pytest.approx(2)
    assert float(row["nav_gap_points"]) == pytest.approx(0)
    assert float(row["premium_at_start_pct"]) == pytest.approx(-1)
    assert float(row["premium_at_end_pct"]) == pytest.approx(0)
