"""Business calendars (RA §3.2 step 2; RA-INV-018).

Dates here are market-local calendar dates. Nothing in this module converts an instant to a
date (OBS-INV-005).
"""

from __future__ import annotations

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
