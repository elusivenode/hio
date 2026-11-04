"""The pricing-basis sensitivity of rates.us.cmt_10y.total_return 0.1.3: a zero curve from the par curve.

It reprices the bond the CMT construction strikes, on discount factors bootstrapped from the same source, so
it measures the flat-yield approximation only. It isn't independent, and agreement validates neither. Spec
steps:
  a. knots at 6m, 1y, 2y, 3y, 5y, 7y and 10y; a date missing any has no curve, and nothing is filled;
  b. a half-year par grid, linear in maturity between knots, at n/2 years, n = 1..20;
  c. D_1 = 1 / (1 + g_1/200); D_n = (1 - (g_n/200) * sum_{k<n} D_k) / (1 + g_n/200), and D_n <= 0 refuses;
  d. log-linear in D across the grid, with D(0) = 1, at s = (w + j) / 2 years;
  e. the same cash flows at both ends: Rz_t = (V(t) + C) / V(t-1) - 1, with V(t-1) computed, not assumed.
Pure compute on the numbers it is given: no source, no storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from hio.library.cmt import PAYMENTS, PeriodTooLong, _add_months
from hio.library.numeric import CTX

KNOTS = (Decimal("0.5"), Decimal(1), Decimal(2), Decimal(3), Decimal(5), Decimal(7), Decimal(10))
HALF = Decimal("0.5")
TWO = Decimal(2)
HUNDRED = Decimal(100)
ONE = Decimal(1)


class MissingKnot(LookupError):
    """A knot the bootstrap needs is absent. The date has no curve, and nothing is filled."""


class NonPositiveDiscount(ArithmeticError):
    """The bootstrap gave D_n <= 0 for this curve. It refuses rather than continuing."""


@dataclass(frozen=True)
class ZeroCurve:
    log_discount: tuple[Decimal, ...]  # ln D_n, n = 1..20; index 0 is the half-year point

    def discount(self, years: Decimal) -> Decimal:
        """D(s), log-linear across the grid, so forwards are constant between grid points."""
        if years < 0 or years > Decimal(PAYMENTS) / TWO:
            raise ValueError(f"{years} years is outside the curve")
        position = CTX.multiply(years, TWO)
        below = int(position)
        if below == PAYMENTS:
            return CTX.exp(self.log_discount[-1])
        lower = Decimal(0) if below == 0 else self.log_discount[below - 1]
        upper = self.log_discount[below]
        weight = CTX.subtract(position, Decimal(below))
        return CTX.exp(CTX.add(lower, CTX.multiply(weight, CTX.subtract(upper, lower))))


def par_grid(knots: Mapping[Decimal, Decimal | None]) -> tuple[Decimal, ...]:
    """Grid par yields g_n, percent, at n/2 years, linear in maturity between knots."""
    missing = [k for k in KNOTS if knots.get(k) is None]
    if missing:
        raise MissingKnot(f"no par yield at {[str(k) for k in missing]} years")
    grid = []
    for n in range(1, PAYMENTS + 1):
        maturity = CTX.divide(Decimal(n), TWO)
        upper = next(k for k in KNOTS if k >= maturity)
        if upper == maturity:
            grid.append(knots[upper])
            continue
        lower = KNOTS[KNOTS.index(upper) - 1]
        slope = CTX.divide(CTX.subtract(knots[upper], knots[lower]), CTX.subtract(upper, lower))
        grid.append(CTX.add(knots[lower], CTX.multiply(slope, CTX.subtract(maturity, lower))))
    return tuple(grid)


def bootstrap(knots: Mapping[Decimal, Decimal | None]) -> ZeroCurve:
    logs, total = [], Decimal(0)
    for n, g in enumerate(par_grid(knots), start=1):
        half = CTX.divide(g, Decimal(200))
        factor = CTX.divide(CTX.subtract(ONE, CTX.multiply(half, total)), CTX.add(ONE, half))
        if factor <= 0:
            raise NonPositiveDiscount(f"D_{n} = {factor}")
        total = CTX.add(total, factor)
        logs.append(CTX.ln(factor))
    return ZeroCurve(tuple(logs))


def value_on_curve(
    strike: date, settle: date, coupon_pct: Decimal, curve: ZeroCurve
) -> tuple[Decimal, Decimal]:
    """The value per 100 at `settle` of the bond struck at `strike`, on `curve`, and the coupon cash paid in
    (strike, settle]. The schedule and w are those of `hio.library.cmt.dirty_and_coupon`."""
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
    value = Decimal(0)
    for j, k in enumerate(range(following, PAYMENTS + 1)):
        flow = CTX.add(each, HUNDRED) if k == PAYMENTS else each
        years = CTX.divide(CTX.add(w, Decimal(j)), TWO)
        value = CTX.add(value, CTX.multiply(flow, curve.discount(years)))
    return value, CTX.multiply(each, Decimal(paid))


def zero_curve_return(
    strike: date, settle: date, coupon_pct: Decimal, curve_then: ZeroCurve, curve_now: ZeroCurve
) -> Decimal:
    """Rz_t: the same cash flows valued at both ends, each on its own date's curve."""
    start, _ = value_on_curve(strike, strike, coupon_pct, curve_then)
    end, cash = value_on_curve(strike, settle, coupon_pct, curve_now)
    return CTX.subtract(CTX.divide(CTX.add(end, cash), start), ONE)
