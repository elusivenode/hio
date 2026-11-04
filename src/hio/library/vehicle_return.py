"""Market-price total return of a listed vehicle (RA §3.1, §5), from unadjusted closes and explicit actions.

For consecutive observed days t−1 and t, with a split factor f (new units per old unit, ex on t) and a cash
distribution D per new unit (ex on t):
  PR_t = f P_t / P_{t−1} − 1,   IR_t = f D_t (1 − w) / P_{t−1},   TR_t = PR_t + IR_t
A split alone therefore gives no return (RA-INV-020). The convention is reinvest_ex_close, so chaining TR_t
is the reinvested return. Fund fees are already in the observed prices and are not deducted again. A
vendor's adjusted close is never an input. Pure compute on the numbers it is given: no source, no storage,
nothing filled.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise

from hio.library.numeric import CTX, check_identity

ONE = Decimal(1)


@dataclass(frozen=True)
class VehicleDay:
    day: date
    close: Decimal  # unadjusted, traded close on that day
    distribution: Decimal = Decimal(0)  # cash per unit held after any split, ex on this day
    split_factor: Decimal = ONE  # new units per old unit, ex on this day


@dataclass(frozen=True)
class VehiclePeriod:
    start: date
    end: date
    price_return: Decimal
    income_return: Decimal
    total_return: Decimal


def vehicle_period(
    previous: VehicleDay, current: VehicleDay, withholding: Decimal = Decimal(0)
) -> VehiclePeriod:
    if current.day <= previous.day:
        raise ValueError("observation dates must increase")
    if previous.close <= 0 or current.close <= 0:
        raise ValueError(f"a close is not positive at {previous.day} or {current.day}")
    if current.split_factor <= 0 or current.distribution < 0:
        raise ValueError(f"an impossible corporate action at {current.day}")
    if not 0 <= withholding <= 1:
        raise ValueError("withholding must lie between 0 and 1")
    units = current.split_factor
    price = CTX.subtract(CTX.divide(CTX.multiply(units, current.close), previous.close), ONE)
    net = CTX.multiply(current.distribution, CTX.subtract(ONE, withholding))
    income = CTX.divide(CTX.multiply(units, net), previous.close)
    total = CTX.subtract(
        CTX.divide(CTX.multiply(units, CTX.add(current.close, net)), previous.close),
        ONE,
    )
    check_identity(total, CTX.add(price, income))  # RA-INV-001
    return VehiclePeriod(previous.day, current.day, price, income, total)


def vehicle_series(days: Sequence[VehicleDay], withholding: Decimal = Decimal(0)) -> list[VehiclePeriod]:
    """Every period between consecutive observed days. An action on an unobserved day isn't representable
    here: the caller places it on the first observed day on or after its ex-date, and states that it did."""
    return [vehicle_period(a, b, withholding) for a, b in pairwise(days)]
