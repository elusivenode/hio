"""T-0020 X-2: the zero-curve sensitivity (spec 0.1.3, ZC-INV-1 to 3). Every yield is invented."""

from datetime import date, timedelta
from decimal import Decimal as D

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hio.library.cmt import CurveObservation, PeriodTooLong, cmt_period, dirty_and_coupon
from hio.library.numeric import CTX
from hio.library.zero_curve import (
    KNOTS,
    MissingKnot,
    NonPositiveDiscount,
    bootstrap,
    par_grid,
    value_on_curve,
    zero_curve_return,
)

STRIKE = date(2026, 3, 16)
STEEP = dict(zip(KNOTS, [D("3.0"), D("3.2"), D("3.5"), D("3.7"), D("4.0"), D("4.3"), D("4.5")], strict=True))
INVERTED = dict(
    zip(KNOTS, [D("5.5"), D("5.2"), D("4.8"), D("4.6"), D("4.4"), D("4.3"), D("4.2")], strict=True)
)


def flat(level: str) -> dict[D, D]:
    return dict.fromkeys(KNOTS, D(level))


def relative(a: D, b: D) -> D:
    return abs(CTX.divide(CTX.subtract(a, b), b))


# --- the method, by hand


def test_the_grid_is_linear_between_knots():
    grid = par_grid(STEEP)
    assert len(grid) == 20
    assert grid[0] == D("3.0")  # 6m is a knot
    assert grid[1] == D("3.2")  # 1y is a knot
    assert grid[2] == D("3.35")  # 1.5y, halfway from 1y to 2y
    assert grid[7] == D("3.85")  # 4y, halfway from 3y to 5y
    assert grid[19] == D("4.5")  # 10y is a knot


def test_the_first_two_discount_factors_by_hand():
    curve = bootstrap(flat("4"))
    assert curve.discount(D("0.5")) == pytest.approx(D(1) / D("1.02"), abs=D("1e-25"))
    assert curve.discount(D(1)) == pytest.approx(D(1) / D("1.02") ** 2, abs=D("1e-25"))


def test_the_second_factor_on_a_sloped_curve_by_hand():
    knots = {**flat("5"), D("0.5"): D("4")}
    curve = bootstrap(knots)
    d1 = D(1) / D("1.02")
    d2 = (D(1) - D("0.025") * d1) / D("1.025")
    assert curve.discount(D(1)) == pytest.approx(d2, abs=D("1e-25"))


def test_discounting_is_log_linear_with_d_of_zero_at_one():
    curve = bootstrap(STEEP)
    d1, d2 = curve.discount(D("0.5")), curve.discount(D(1))
    assert curve.discount(D(0)) == 1
    assert curve.discount(D("0.25")) == pytest.approx(d1.sqrt(), abs=D("1e-25"))
    assert curve.discount(D("0.75")) == pytest.approx((d1 * d2).sqrt(), abs=D("1e-25"))


@pytest.mark.parametrize("years", [D("-0.1"), D("10.1")])
def test_nothing_outside_the_curve_is_used(years):
    with pytest.raises(ValueError, match="outside"):
        bootstrap(STEEP).discount(years)


# --- ZC-INV-1


@pytest.mark.parametrize("knots", [STEEP, INVERTED, flat("0"), flat("8")])
@pytest.mark.parametrize("strike", [STRIKE, date(2024, 2, 29), date(2026, 8, 31)])
def test_zc_inv_1_the_bond_struck_today_values_to_100(knots, strike):
    curve = bootstrap(knots)
    value, cash = value_on_curve(strike, strike, knots[D(10)], curve)
    assert abs(CTX.divide(value, D(100)) - 1) <= D("1e-10")
    assert cash == 0


# --- ZC-INV-2


@pytest.mark.parametrize("days", [0, 1, 3, 30, 120, 183])
@pytest.mark.parametrize("level", ["0.5", "4", "12"])
def test_zc_inv_2_a_flat_curve_prices_as_the_flat_yield_does(days, level):
    settle = STRIKE + timedelta(days=days)
    curve = bootstrap(flat(level))
    on_curve, cash = value_on_curve(STRIKE, settle, D(level), curve)
    flat_price, flat_cash = dirty_and_coupon(STRIKE, settle, D(level), D(level))
    assert relative(on_curve, flat_price) <= D("1e-10")
    assert cash == flat_cash


def test_zc_inv_2_on_a_flat_unchanged_curve_d_t_is_zero():
    then, now = STRIKE, STRIKE + timedelta(days=1)
    observed = cmt_period(CurveObservation(then, D(4), D(4)), CurveObservation(now, D(4), D(4)))
    rz = zero_curve_return(then, now, D(4), bootstrap(flat("4")), bootstrap(flat("4")))
    assert abs(rz - observed.r) <= D("1e-10")


def test_a_sloped_curve_gives_a_small_nonzero_difference():
    # The quantity the experiment measures: it must be able to differ from zero.
    then, now = STRIKE, STRIKE + timedelta(days=1)
    moved = {k: v + D("0.10") for k, v in STEEP.items()}
    previous = CurveObservation(then, STEEP[D(7)], STEEP[D(10)])
    current = CurveObservation(now, moved[D(7)], moved[D(10)])
    observed = cmt_period(previous, current)
    rz = zero_curve_return(then, now, STEEP[D(10)], bootstrap(STEEP), bootstrap(moved))
    assert rz < 0
    assert observed.r < 0
    assert abs(rz - observed.r) > 0


# --- ZC-INV-3


@pytest.mark.parametrize("gone", KNOTS)
def test_zc_inv_3_a_missing_knot_gives_no_curve(gone):
    with pytest.raises(MissingKnot):
        bootstrap({k: v for k, v in STEEP.items() if k != gone})
    with pytest.raises(MissingKnot):
        bootstrap({**STEEP, gone: None})


def test_zc_inv_3_a_non_positive_factor_refuses():
    knots = {**flat("0"), D(10): D(60)}
    with pytest.raises(NonPositiveDiscount):
        bootstrap(knots)


# --- the schedule


def test_a_coupon_in_the_period_is_cash_at_the_end():
    settle = date(2026, 9, 16)  # exactly six months: the first coupon
    curve = bootstrap(flat("4"))
    value, cash = value_on_curve(STRIKE, settle, D(4), curve)
    assert cash == 2
    assert value > 0


def test_a_period_longer_than_a_coupon_refuses():
    with pytest.raises(PeriodTooLong):
        value_on_curve(STRIKE, date(2026, 9, 17), D(4), bootstrap(flat("4")))


def test_settlement_before_the_strike_refuses():
    with pytest.raises(ValueError, match="before the strike"):
        value_on_curve(STRIKE, date(2026, 3, 15), D(4), bootstrap(flat("4")))


yields = st.decimals(min_value=D("0.1"), max_value=D(15), places=2)


@settings(max_examples=30, deadline=None)
@given(st.lists(yields, min_size=7, max_size=7), st.integers(min_value=0, max_value=4000))
def test_any_ordinary_curve_prices_its_new_bond_at_par(levels, offset):
    knots = dict(zip(KNOTS, levels, strict=True))
    strike = date(2015, 1, 1) + timedelta(days=offset)
    value, _ = value_on_curve(strike, strike, knots[D(10)], bootstrap(knots))
    assert abs(CTX.divide(value, D(100)) - 1) <= D("1e-10")
