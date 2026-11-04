"""E-0001's variant V1, on invented yields only."""

import importlib.util
import sys
from datetime import date, timedelta
from decimal import Decimal as D
from itertools import pairwise
from pathlib import Path

import pytest

from hio.library.zero_curve import KNOTS, MissingKnot, par_grid, pchip_grid

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
_spec = importlib.util.spec_from_file_location("e0001_variant", REPO / "tools" / "e0001_variant.py")
tool = importlib.util.module_from_spec(_spec)
sys.modules["e0001_variant"] = tool
_spec.loader.exec_module(tool)

STEEP = [D("3.0"), D("3.2"), D("3.5"), D("3.7"), D("4.0"), D("4.3"), D("4.5")]


def knots(levels):
    return dict(zip(KNOTS, levels, strict=True))


def test_the_cubic_passes_through_every_knot():
    grid = pchip_grid(knots(STEEP))
    for n, value in zip((1, 2, 4, 6, 10, 14, 20), STEEP, strict=True):
        assert grid[n - 1] == value


def test_a_flat_curve_stays_flat():
    assert set(pchip_grid(knots([D(4)] * 7))) == {D(4)}


def test_a_rising_curve_stays_monotone_with_no_overshoot():
    grid = pchip_grid(knots(STEEP))
    assert all(a <= b for a, b in pairwise(grid))


def test_a_kink_does_not_overshoot_its_neighbours():
    grid = pchip_grid(knots([D(3), D(3), D(3), D(5), D(5), D(5), D(5)]))
    assert min(grid) == D(3) and max(grid) == D(5)


def test_it_differs_from_linear_between_knots_on_a_sloped_curve():
    linear, cubic = par_grid(knots(STEEP)), pchip_grid(knots(STEEP))
    assert linear != cubic and linear[0] == cubic[0] and linear[19] == cubic[19]


def test_a_missing_knot_refuses():
    with pytest.raises(MissingKnot):
        pchip_grid({**knots(STEEP), D(2): None})


def rows(levels, count=12):
    start = date(2026, 1, 5)
    return [tool.base.Row(start + timedelta(days=i), knots(levels)) for i in range(count)]


def test_on_a_flat_curve_all_three_returns_agree():
    table, report = tool.build(rows([D(4)] * 7))
    assert report["periods"] == 11
    assert report["zero_against_flat"]["within_1bp_on_99pct"] is True
    assert D(report["zero_against_flat"]["max_bp"]) < D("1e-5")
    assert D(report["cubic_against_linear"]["max_bp"]) < D("1e-5")
    assert table[0][0] < table[0][1]


def test_a_missing_ten_year_is_spanned_and_counted():
    data = rows([D(4)] * 7, 5)
    data[2] = tool.base.Row(data[2].day, {**data[2].knots, D(10): None})
    table, report = tool.build(data)
    assert report["missing_tenor"] == 1 and report["periods"] == 3
    assert (table[1][0], table[1][1]) == (data[1].day.isoformat(), data[3].day.isoformat())


def test_a_date_with_no_curve_is_uncovered_and_never_filled():
    data = rows([D(4)] * 7, 5)
    data[2] = tool.base.Row(data[2].day, {**data[2].knots, D(2): None})
    _, report = tool.build(data)
    assert report["missing_knot"] == 1 and report["uncovered"] == 2 and report["periods"] == 2
