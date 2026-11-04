"""A constant-maturity synthetic bond total return (RA §6; proposed spec rates.us.cmt_10y.total_return).

For consecutive observation dates t−1 and t:
  strike at t−1:  a 10-year bond, coupon = y(t−1, 10y), semi-annual, dirty price 100
  value at t:     P_dirty(t) = Σ CF_j / (1 + y/2)^(w + j), at y = y(t, 10y − τ), between the 7y and 10y points
  return:         R_t = (P_dirty(t) + C) / P_dirty(t−1) − 1   (RA-INV-013; C is coupon cash in the period)
The decomposition is reported, and is not the definition. Pure compute on the numbers it is given: no source,
no storage. Nothing is forward-filled, and a missing tenor refuses.
"""

from __future__ import annotations

import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise

from hio.library.numeric import CTX

MATURITY_YEARS = Decimal(10)
SHORT_TENOR_YEARS = Decimal(7)
PAYMENTS = 20  # semi-annual, ten years
DAYS_PER_YEAR = Decimal("365.25")
HUNDRED = Decimal(100)
TWO = Decimal(2)
LONG_GAP_DAYS = 5


class MissingTenor(LookupError):
    """A tenor the period needs is absent. The period refuses and is never filled."""


class PeriodTooLong(ValueError):
    """A gap longer than one coupon period: the construction doesn't re-strike across it."""


@dataclass(frozen=True)
class CurveObservation:
    day: date
    y7_pct: Decimal | None  # par yield, percent per annum, bond-equivalent
    y10_pct: Decimal | None


@dataclass(frozen=True)
class CmtPeriod:
    start: date  # t−1
    end: date  # t
    coupon_pct: Decimal  # the coupon struck at t−1
    yield_pct: Decimal  # the interpolated yield at t for the aged bond
    dirty: Decimal  # P_dirty(t), per 100
    coupon_cash: Decimal  # C in (t−1, t], per 100
    r: Decimal
    carry: Decimal
    roll_down: Decimal
    curve_change: Decimal
    convexity: Decimal
    residual: Decimal
    long_gap: bool


def _add_months(day: date, months: int) -> date:
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def total_return(dirty_start: Decimal, dirty_end: Decimal, coupon: Decimal) -> Decimal:
    """RA-INV-013: (P_dirty(t) + C) / P_dirty(t−1) − 1. Omitting C is the error this form prevents."""
    return CTX.subtract(CTX.divide(CTX.add(dirty_end, coupon), dirty_start), Decimal(1))


def dirty_and_coupon(
    strike: date, settle: date, coupon_pct: Decimal, yield_pct: Decimal
) -> tuple[Decimal, Decimal]:
    """The dirty price at `settle` of the par bond struck at `strike`, and the coupon cash paid in
    (strike, settle]. Street convention: w = days to the next coupon / days in the coupon period."""
    if settle < strike:
        raise ValueError("settlement before the strike")
    if settle > _add_months(strike, 6):
        raise PeriodTooLong(f"{strike} to {settle} is longer than one coupon period")
    each = CTX.divide(coupon_pct, TWO)
    dates = [_add_months(strike, 6 * k) for k in range(PAYMENTS + 1)]
    paid = sum(1 for d in dates[1:] if d <= settle)
    following = paid + 1
    w = CTX.divide(
        Decimal((dates[following] - settle).days), Decimal((dates[following] - dates[following - 1]).days)
    )
    growth = CTX.add(Decimal(1), CTX.divide(yield_pct, Decimal(200)))
    price = Decimal(0)
    for j, k in enumerate(range(following, PAYMENTS + 1)):
        flow = CTX.add(each, HUNDRED) if k == PAYMENTS else each
        price = CTX.add(price, CTX.divide(flow, CTX.power(growth, CTX.add(w, Decimal(j)))))
    return price, CTX.multiply(each, Decimal(paid))


def aged_yield(y7_pct: Decimal, y10_pct: Decimal, tau_years: Decimal) -> Decimal:
    """Linear in maturity between 7y and 10y, at 10y − τ. Never extrapolates."""
    remaining = CTX.subtract(MATURITY_YEARS, tau_years)
    if remaining < SHORT_TENOR_YEARS or remaining > MATURITY_YEARS:
        raise ValueError(f"maturity {remaining} is outside 7y to 10y")
    slope = CTX.divide(CTX.subtract(y10_pct, y7_pct), MATURITY_YEARS - SHORT_TENOR_YEARS)
    return CTX.add(y7_pct, CTX.multiply(slope, CTX.subtract(remaining, SHORT_TENOR_YEARS)))


def _duration_and_convexity(yield_pct: Decimal) -> tuple[Decimal, Decimal]:
    """Modified duration and convexity, in years, of a par bond at the strike."""
    half = CTX.divide(yield_pct, Decimal(200))
    growth = CTX.add(Decimal(1), half)
    coupon = CTX.divide(yield_pct, TWO)
    duration, convexity = Decimal(0), Decimal(0)
    for k in range(1, PAYMENTS + 1):
        flow = CTX.add(coupon, HUNDRED) if k == PAYMENTS else coupon
        pv = CTX.divide(flow, CTX.power(growth, Decimal(k)))
        duration = CTX.add(duration, CTX.multiply(pv, Decimal(k)))
        convexity = CTX.add(convexity, CTX.multiply(pv, Decimal(k * (k + 1))))
    modified = CTX.divide(duration, CTX.multiply(Decimal(200), growth))
    curved = CTX.divide(convexity, CTX.multiply(Decimal(400), CTX.multiply(growth, growth)))
    return modified, curved


def _complete(observation: CurveObservation) -> tuple[Decimal, Decimal]:
    if observation.y7_pct is None or observation.y10_pct is None:
        raise MissingTenor(f"{observation.day}: a tenor is absent")
    return observation.y7_pct, observation.y10_pct


def cmt_period(previous: CurveObservation, current: CurveObservation) -> CmtPeriod:
    y7_then, coupon = _complete(previous)
    y7_now, y10_now = _complete(current)
    days = (current.day - previous.day).days
    if days <= 0:
        raise ValueError("observation dates must increase")
    tau = CTX.divide(Decimal(days), DAYS_PER_YEAR)
    y_now = aged_yield(y7_now, y10_now, tau)
    dirty, cash = dirty_and_coupon(previous.day, current.day, coupon, y_now)
    r = total_return(HUNDRED, dirty, cash)

    y_then = aged_yield(y7_then, coupon, tau)
    duration, curve_term = _duration_and_convexity(coupon)
    carry = CTX.multiply(CTX.divide(coupon, HUNDRED), tau)
    roll_down = CTX.minus(CTX.multiply(duration, CTX.divide(CTX.subtract(y_then, coupon), HUNDRED)))
    curve_change = CTX.minus(CTX.multiply(duration, CTX.divide(CTX.subtract(y_now, y_then), HUNDRED)))
    move = CTX.divide(CTX.subtract(y_now, coupon), HUNDRED)
    convexity = CTX.divide(CTX.multiply(curve_term, CTX.multiply(move, move)), TWO)
    explained = sum((carry, roll_down, curve_change, convexity), Decimal(0))
    return CmtPeriod(
        previous.day,
        current.day,
        coupon,
        y_now,
        dirty,
        cash,
        r,
        carry,
        roll_down,
        curve_change,
        convexity,
        CTX.subtract(r, explained),
        days > LONG_GAP_DAYS,
    )


def cmt_series(observations: Sequence[CurveObservation]) -> list[CmtPeriod]:
    """Every period between consecutive observations. Any absent tenor refuses the whole series: which dates
    enter is the caller's stated choice, and this function never fills one."""
    return [cmt_period(a, b) for a, b in pairwise(observations)]


def chain(periods: Sequence[CmtPeriod], base: Decimal = Decimal(1)) -> Decimal:
    level = base
    for period in periods:
        level = CTX.multiply(level, CTX.add(Decimal(1), period.r))
    return level
