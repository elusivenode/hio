"""T-0021: market-price total return of a vehicle, on invented numbers only (RA §3.1, §5)."""

from datetime import date
from decimal import Decimal as D

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hio.library.numeric import CTX
from hio.library.vehicle_return import VehicleDay, vehicle_period, vehicle_series

MON, TUE, WED = date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)


def test_a_plain_day_is_the_price_return():
    p = vehicle_period(VehicleDay(MON, D(100)), VehicleDay(TUE, D(101)))
    assert (p.price_return, p.income_return, p.total_return) == (D("0.01"), D(0), D("0.01"))


def test_a_distribution_counts_as_income_on_its_ex_date():
    p = vehicle_period(VehicleDay(MON, D(100)), VehicleDay(TUE, D(99), distribution=D(2)))
    assert p.price_return == D("-0.01")
    assert p.income_return == D("0.02")
    assert p.total_return == D("0.01")


def test_withholding_reduces_income_only():
    p = vehicle_period(VehicleDay(MON, D(100)), VehicleDay(TUE, D(100), distribution=D(2)), D("0.15"))
    assert p.price_return == 0
    assert p.income_return == D("0.017")


def test_a_split_alone_gives_no_return_ra_inv_020():
    p = vehicle_period(VehicleDay(MON, D(100)), VehicleDay(TUE, D(50), split_factor=D(2)))
    assert p.total_return == 0


def test_a_reverse_split_alone_gives_no_return_ra_inv_020():
    p = vehicle_period(VehicleDay(MON, D(10)), VehicleDay(TUE, D(100), split_factor=D("0.1")))
    assert abs(p.total_return) < D("1e-40")


def test_a_split_and_a_distribution_on_one_day():
    # Two units for one at 51, each paying 1: 2 * (51 + 1) / 100 - 1
    p = vehicle_period(VehicleDay(MON, D(100)), VehicleDay(TUE, D(51), D(1), D(2)))
    assert p.total_return == D("0.04")
    assert p.price_return == D("0.02")
    assert p.income_return == D("0.02")


def test_a_series_chains_across_an_unobserved_day_without_filling():
    periods = vehicle_series([VehicleDay(MON, D(100)), VehicleDay(WED, D(102))])
    assert [(p.start, p.end) for p in periods] == [(MON, WED)]


@pytest.mark.parametrize(
    "previous, current",
    [
        (VehicleDay(TUE, D(100)), VehicleDay(MON, D(100))),
        (VehicleDay(MON, D(0)), VehicleDay(TUE, D(100))),
        (VehicleDay(MON, D(100)), VehicleDay(TUE, D(-1))),
        (VehicleDay(MON, D(100)), VehicleDay(TUE, D(100), split_factor=D(0))),
        (VehicleDay(MON, D(100)), VehicleDay(TUE, D(100), distribution=D(-1))),
    ],
)
def test_impossible_inputs_refuse(previous, current):
    with pytest.raises(ValueError):
        vehicle_period(previous, current)


prices = st.decimals(min_value=D("0.01"), max_value=D(10000), places=4)
payments = st.decimals(min_value=D(0), max_value=D(100), places=4)
factors = st.sampled_from([D(1), D(2), D(3), D("1.5"), D("0.1")])


@given(prices, prices, payments, factors)
def test_total_is_price_plus_income_ra_inv_001(before, after, paid, factor):
    p = vehicle_period(VehicleDay(MON, before), VehicleDay(TUE, after, paid, factor))
    assert abs(CTX.subtract(p.total_return, CTX.add(p.price_return, p.income_return))) <= D("1e-30")
