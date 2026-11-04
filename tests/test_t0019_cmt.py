"""T-0019 (OD-0150): the CMT synthetic bond return on invented inputs only. No real yield appears here."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from hio.library.cmt import (
    CurveObservation as Obs,
)
from hio.library.cmt import (
    MissingTenor,
    PeriodTooLong,
    _duration_and_convexity,
    aged_yield,
    chain,
    cmt_period,
    cmt_series,
    dirty_and_coupon,
    total_return,
)

DAY = date(2026, 1, 2)


def rel(a: D, b: D) -> D:
    return abs(a - b) / abs(b)


# --- CMT-INV-1, RA-INV-013 -----------------------------------------------------------------------------


def test_the_coupon_date_fixture_gives_zero_and_omitting_the_coupon_would_not():
    assert total_return(D(102), D(100), D(2)) == 0
    assert total_return(D(102), D(100), D(0)) < D("-0.019")


def test_the_non_coupon_date_fixture():
    assert round(total_return(D("101.00"), D("101.05"), D(0)), 12) == D("0.000495049505")


# --- CMT-INV-2, CMT-INV-3 ------------------------------------------------------------------------------


@pytest.mark.parametrize("coupon", [D("0.5"), D("4.00"), D("12.25")])
def test_a_par_bond_prices_at_par_on_its_strike_date(coupon):
    dirty, cash = dirty_and_coupon(DAY, DAY, coupon, coupon)
    assert abs(dirty - 100) / 100 < D("1e-12") and cash == 0


def test_a_flat_unchanged_curve_earns_its_accrual():
    p = cmt_period(Obs(DAY, D(4), D(4)), Obs(DAY + timedelta(days=3), D(4), D(4)))
    assert p.r > 0
    assert abs(p.r - p.carry) < D("1e-6")
    assert abs(p.roll_down) == 0 and abs(p.curve_change) == 0


# --- RA §14.6, the worked one-day case -------------------------------------------------------------------


def test_the_worked_example_reproduces():
    p = cmt_period(Obs(DAY, D(4), D(4)), Obs(DAY + timedelta(days=1), D("4.05"), D("4.05")))
    assert abs(p.r - D("-0.00397")) < D("0.00001")
    assert abs(p.carry - D("0.00011")) < D("0.00001")
    assert abs(p.curve_change - D("-0.00409")) < D("0.00005")
    assert abs(p.convexity - D("0.0000099")) < D("0.0000002")  # 1/2 x 79 x 0.0005^2, not merely "small"


def test_duration_and_convexity_match_the_worked_example():
    duration, convexity = _duration_and_convexity(D(4))
    assert abs(duration - D("8.18")) < D("0.01")
    assert abs(convexity - D(79)) < D(1)


# --- coupon cash inside a period --------------------------------------------------------------------------


def test_a_period_ending_on_a_coupon_date_pays_it_and_wealth_is_kept():
    end = date(2026, 7, 2)
    p = cmt_period(Obs(DAY, D(4), D(4)), Obs(end, D(4), D(4)))
    assert p.coupon_cash == D(2) and p.long_gap
    assert rel(p.dirty, D(100)) < D("1e-12")  # still flat at the coupon: ex-coupon back at par
    assert abs(p.r - D("0.02")) < D("1e-12")


def test_a_gap_longer_than_a_coupon_period_refuses():
    with pytest.raises(PeriodTooLong):
        cmt_period(Obs(DAY, D(4), D(4)), Obs(date(2026, 7, 3), D(4), D(4)))


# --- CMT-INV-4 --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", [Obs(DAY, None, D(4)), Obs(DAY, D(4), None)], ids=["no-short-tenor", "no-long-tenor"]
)
def test_a_missing_tenor_refuses_at_either_end(bad):
    good = Obs(DAY + timedelta(days=1), D(4), D(4))
    with pytest.raises(MissingTenor):
        cmt_period(bad, good)
    with pytest.raises(MissingTenor):
        cmt_period(replace_day(good, DAY - timedelta(days=1)), bad)


def replace_day(obs: Obs, day: date) -> Obs:
    return Obs(day, obs.y7_pct, obs.y10_pct)


def test_dates_must_increase():
    with pytest.raises(ValueError):
        cmt_period(Obs(DAY, D(4), D(4)), Obs(DAY, D(4), D(4)))


def test_interpolation_stays_between_the_tenors_and_never_extrapolates():
    assert aged_yield(D(3), D(4), D(0)) == D(4)
    assert aged_yield(D(3), D(4), D(3)) == D(3)
    assert aged_yield(D(3), D(4), D("1.5")) == D("3.5")
    for tau in (D("-0.01"), D("3.01")):
        with pytest.raises(ValueError):
            aged_yield(D(3), D(4), tau)


# --- CMT-INV-5, and the sign of the risk ------------------------------------------------------------------


def invented_curve(seed: int, days: int) -> list[Obs]:
    rng = random.Random(seed)
    y10, spread, out, day = D("4.00"), D("0.30"), [], DAY
    while len(out) < days:
        if day.weekday() < 5:
            out.append(Obs(day, y10 - spread, y10))
            y10 += D(rng.randint(-24, 24)) / 100
            y10 = max(y10, D("0.25"))
            spread = max(min(spread + D(rng.randint(-2, 2)) / 100, D("0.8")), D("-0.3"))
        day += timedelta(days=1)
    return out


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_decomposition_residual_is_below_a_basis_point_for_ordinary_moves(seed):
    worst = D(0)
    for p in cmt_series(invented_curve(seed, 750)):
        worst = max(worst, abs(p.residual))
    assert worst < D("0.0001"), worst


def test_a_rise_in_yields_loses_money_and_a_fall_makes_it():
    start = Obs(DAY, D(4), D(4))
    up = cmt_period(start, Obs(DAY + timedelta(days=1), D("4.5"), D("4.5")))
    down = cmt_period(start, Obs(DAY + timedelta(days=1), D("3.5"), D("3.5")))
    assert up.r < 0 < down.r
    assert abs(down.r) > abs(up.r)  # convexity


def test_chaining_and_the_series_length():
    curve = invented_curve(7, 20)
    periods = cmt_series(curve)
    assert len(periods) == 19 and [p.start for p in periods] == [o.day for o in curve[:-1]]
    level = chain(periods)
    expected = D(1)
    for p in periods:
        expected *= 1 + p.r
    assert rel(level, expected) < D("1e-20")


def test_the_same_inputs_give_the_same_decimal_result():
    a, b = cmt_series(invented_curve(9, 30)), cmt_series(invented_curve(9, 30))
    assert a == b
