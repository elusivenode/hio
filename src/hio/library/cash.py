"""Overnight cash legs (RA §3.2; specs cash.aud.overnight@0.2.0 and cash.usd.overnight@0.2.0).

For a period (t−1, t]:
  window W   = calendar days d with t−1 <= d < t
  b(d)       = the latest rate-business day <= d (the rate fixed for d's overnight)
  n_b        = the number of window days that use rate_b
  r_t        = Π_b (1 + rate_b/100 × n_b / B) − 1        (exact; B = 365 AUD, 360 USD)
  knowable_at(t) = max_b knowable_at(rate_b)              (selection never depends on knowability)
No rate whose overnight starts on or after t is ever used (CASH-USD-INV-3).
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from hio.contracts.temporal import KnowableBasis, weakest
from hio.library.numeric import CTX, check_identity
from hio.reference.calendar import BusinessCalendar

ACT_365F = Decimal(365)
ACT_360 = Decimal(360)
HUNDRED = Decimal(100)


@dataclass(frozen=True)
class RateFixing:
    business_day: date
    rate_pct: Decimal  # percent per annum
    knowable_at: datetime
    basis: KnowableBasis


@dataclass(frozen=True)
class CashPeriod:
    start: date  # t−1
    end: date  # t
    r: Decimal
    legs: tuple[tuple[date, Decimal, int], ...]  # (b, rate_b, n_b)
    knowable_at: datetime
    weakest_basis: KnowableBasis


class MissingRate(LookupError):
    """A rate the period needs is absent from the view: the period is absent, never filled."""

    def __init__(self, start: date, end: date, business_day: date) -> None:
        self.business_day = business_day
        super().__init__(f"period ({start}, {end}] needs the rate fixed on {business_day}")


def overnight_period(
    start: date,
    end: date,
    fixings: Mapping[date, RateFixing],
    rate_calendar: BusinessCalendar,
    day_count_base: Decimal,
) -> CashPeriod:
    if end <= start:
        raise ValueError(f"empty period ({start}, {end}]")
    counts: dict[date, int] = {}
    for k in range((end - start).days):
        d = start + timedelta(days=k)
        b = rate_calendar.latest_on_or_before(d)
        assert b <= d < end  # the overnight starting on b covers d, inside the window
        counts[b] = counts.get(b, 0) + 1
    growth = Decimal(1)
    legs = []
    for b in sorted(counts):
        fixing = fixings.get(b)
        if fixing is None:
            raise MissingRate(start, end, b)
        accrual = CTX.divide(
            CTX.multiply(CTX.divide(fixing.rate_pct, HUNDRED), Decimal(counts[b])), day_count_base
        )
        growth = CTX.multiply(growth, CTX.add(Decimal(1), accrual))
        legs.append((b, fixing.rate_pct, counts[b]))
    used = [fixings[b] for b in counts]
    return CashPeriod(
        start=start,
        end=end,
        r=CTX.subtract(growth, Decimal(1)),
        legs=tuple(legs),
        knowable_at=max(f.knowable_at for f in used),
        weakest_basis=weakest(f.basis for f in used),
    )


@dataclass(frozen=True)
class CashSeries:
    periods: tuple[CashPeriod, ...]
    gaps: tuple[tuple[date, date, str], ...]  # (start, end, reason): absent periods, recorded


def overnight_series(
    period_ends: Sequence[date],
    fixings: Mapping[date, RateFixing],
    rate_calendar: BusinessCalendar,
    day_count_base: Decimal,
) -> CashSeries:
    periods, gaps = [], []
    for start, end in itertools.pairwise(period_ends):
        try:
            periods.append(overnight_period(start, end, fixings, rate_calendar, day_count_base))
        except MissingRate as exc:
            gaps.append((start, end, str(exc)))
    return CashSeries(tuple(periods), tuple(gaps))


def chain_index(
    returns: Sequence[tuple[date, Decimal]], base: Decimal = HUNDRED
) -> list[tuple[date, Decimal]]:
    """I_t = I_{t−1}(1 + r_t), I_base = base. Checks I_t/I_{t−1} − 1 = r_t (CASH-*-INV-1)."""
    out, level = [], base
    for end, r in returns:
        new = CTX.multiply(level, CTX.add(Decimal(1), r))
        check_identity(CTX.subtract(CTX.divide(new, level), Decimal(1)), r)
        out.append((end, new))
        level = new
    return out
