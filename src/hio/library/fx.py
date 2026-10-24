"""AUD-numeraire investor holding USD overnight cash, in excess of AUD overnight cash
(spec fx.usd_cash_vs_aud.excess@0.2.0; RA §4.1–§4.2).

For each period (t−1, t] on the joint calendar J (Sydney business days with an RBA fixing):
  s_t     = q_{t−1}/q_t − 1                 q quoted USD per AUD (RA-INV-007)
  R_t     = (1 + r_usd_t)(1 + s_t) − 1      AUD return of holding USD cash (RA-INV-006)
  X_t     = R_t − r_aud_t                   arithmetic excess (RA §1)
  carry_t = r_usd_t − r_aud_t;  cross_t = r_usd_t × s_t
Identities checked every period: X = s + carry + cross (FXC-INV-1); R = r_aud + X (FXC-INV-2).
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from hio.contracts.temporal import KnowableBasis, weakest
from hio.library.cash import ACT_360, ACT_365F, MissingRate, RateFixing, overnight_period
from hio.library.numeric import CTX, check_identity
from hio.reference.calendar import BusinessCalendar


@dataclass(frozen=True)
class FxQuote:
    valid_time: date
    q: Decimal  # USD per AUD
    knowable_at: datetime
    basis: KnowableBasis


@dataclass(frozen=True)
class FxPeriod:
    start: date
    end: date
    s: Decimal
    r_usd: Decimal
    r_aud: Decimal
    R: Decimal
    X: Decimal
    carry: Decimal
    cross: Decimal
    knowable_at: datetime
    weakest_basis: KnowableBasis


def joint_calendar(quotes: Mapping[date, FxQuote], sydney: BusinessCalendar) -> list[date]:
    """J: Sydney business days on which an RBA fixing exists in the view."""
    return sorted(d for d in quotes if sydney.is_business_day(d))


def spot_return(q_prev: Decimal, q_now: Decimal) -> Decimal:
    """RA-INV-007: q is foreign per home (USD per AUD), so s = q_{t−1}/q_t − 1."""
    return CTX.subtract(CTX.divide(q_prev, q_now), Decimal(1))


def fx_period(
    start: date,
    end: date,
    quotes: Mapping[date, FxQuote],
    usd_fixings: Mapping[date, RateFixing],
    usd_calendar: BusinessCalendar,
    aud_fixings: Mapping[date, RateFixing],
    aud_calendar: BusinessCalendar,
) -> FxPeriod:
    q0, q1 = quotes[start], quotes[end]
    usd = overnight_period(start, end, usd_fixings, usd_calendar, ACT_360)
    aud = overnight_period(start, end, aud_fixings, aud_calendar, ACT_365F)
    s = spot_return(q0.q, q1.q)
    big_r = CTX.subtract(CTX.multiply(CTX.add(Decimal(1), usd.r), CTX.add(Decimal(1), s)), Decimal(1))
    x = CTX.subtract(big_r, aud.r)
    carry = CTX.subtract(usd.r, aud.r)
    cross = CTX.multiply(usd.r, s)
    check_identity(x, CTX.add(CTX.add(s, carry), cross))  # FXC-INV-1
    check_identity(big_r, CTX.add(aud.r, x))  # FXC-INV-2 (RA-INV-005)
    return FxPeriod(
        start=start,
        end=end,
        s=s,
        r_usd=usd.r,
        r_aud=aud.r,
        R=big_r,
        X=x,
        carry=carry,
        cross=cross,
        knowable_at=max(q0.knowable_at, q1.knowable_at, usd.knowable_at, aud.knowable_at),
        weakest_basis=weakest([q0.basis, q1.basis, usd.weakest_basis, aud.weakest_basis]),
    )


@dataclass(frozen=True)
class FxSeries:
    periods: tuple[FxPeriod, ...]
    gaps: tuple[tuple[date, date, str], ...]


def fx_series(
    joint: Sequence[date],
    quotes: Mapping[date, FxQuote],
    usd_fixings: Mapping[date, RateFixing],
    usd_calendar: BusinessCalendar,
    aud_fixings: Mapping[date, RateFixing],
    aud_calendar: BusinessCalendar,
) -> FxSeries:
    periods, gaps = [], []
    for start, end in itertools.pairwise(joint):
        try:
            periods.append(
                fx_period(start, end, quotes, usd_fixings, usd_calendar, aud_fixings, aud_calendar)
            )
        except MissingRate as exc:
            gaps.append((start, end, str(exc)))
    return FxSeries(tuple(periods), tuple(gaps))


def compound(returns: Sequence[Decimal]) -> Decimal:
    """Π(1 + r) − 1. Cumulative comparisons compound the per-period identity (RA-INV-016)."""
    growth = Decimal(1)
    for r in returns:
        growth = CTX.multiply(growth, CTX.add(Decimal(1), r))
    return CTX.subtract(growth, Decimal(1))
