"""Business calendars (RA §3.2 step 2; RA-INV-018).

Dates here are market-local calendar dates. Nothing in this module converts an instant to a
date (OBS-INV-005).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

_MAX_GAP_DAYS = 31  # a calendar with no business day in 31 days is a data error


@dataclass(frozen=True)
class BusinessCalendar:
    calendar_id: str
    holidays: frozenset[date] = field(default_factory=frozenset)
    weekend: frozenset[int] = frozenset({5, 6})  # Saturday, Sunday

    def is_business_day(self, d: date) -> bool:
        return d.weekday() not in self.weekend and d not in self.holidays

    def latest_on_or_before(self, d: date) -> date:
        """The latest business day b <= d: the rate fixed for d's overnight (RA §3.2)."""
        for back in range(_MAX_GAP_DAYS):
            candidate = d - timedelta(days=back)
            if self.is_business_day(candidate):
                return candidate
        raise ValueError(f"{self.calendar_id}: no business day within {_MAX_GAP_DAYS} days before {d}")

    def add_business_days(self, d: date, n: int) -> date:
        """d plus n business days (n >= 0; n = 0 returns d itself if it is a business day)."""
        if n < 0:
            raise ValueError("n must be >= 0")
        current = d
        if n == 0:
            if not self.is_business_day(current):
                raise ValueError(f"{d} is not a {self.calendar_id} business day")
            return current
        while n:
            current += timedelta(days=1)
            if self.is_business_day(current):
                n -= 1
        return current

    def business_days(self, start: date, end: date) -> list[date]:
        """Business days in [start, end]."""
        days, d = [], start
        while d <= end:
            if self.is_business_day(d):
                days.append(d)
            d += timedelta(days=1)
        return days


def load_calendars(path: str | Path) -> dict[str, BusinessCalendar]:
    data = yaml.safe_load(Path(path).read_text())
    out = {}
    for cal_id, spec in data["calendars"].items():
        out[cal_id] = BusinessCalendar(
            calendar_id=cal_id,
            holidays=frozenset(date.fromisoformat(str(h)) for h in spec.get("holidays", [])),
        )
    return out


def calendar_from_observations(
    calendar_id: str, observations: Iterable[Collection[date]], weekend: frozenset[int] = frozenset({5, 6})
) -> BusinessCalendar:
    """A calendar derived from the dates a publisher actually published (T-0009 §2.7, owner
    direction 2026-10-25). Each observation is the set of value dates one captured payload lists.
    A weekday is a holiday only when it lies inside some payload's span (first to last listed date)
    and that payload does not list it. A weekday outside every span stays a business day, so a rate
    the period needs but nobody published is reported missing (an absent period), never guessed.
    Evidence that disagrees (a date listed by one payload and absent from another's span) refuses."""
    listed: set[date] = set()
    absent: set[date] = set()
    for dates in observations:
        ds = sorted(dates)
        if not ds:
            continue
        listed |= set(ds)
        d = ds[0]
        while d < ds[-1]:
            if d.weekday() not in weekend and d not in dates:
                absent.add(d)
            d += timedelta(days=1)
    conflict = listed & absent
    if conflict:
        raise ValueError(f"{calendar_id}: observations disagree about {sorted(conflict)}")
    return BusinessCalendar(calendar_id, frozenset(absent), weekend)
