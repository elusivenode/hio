"""Series definitions and release schedules (observations standard §1, §3, §5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from hio.reference.calendar import BusinessCalendar


class CaptureMode(StrEnum):
    SCHEDULED = "scheduled"  # HIO's own capture after a documented release
    BACKFILL = "backfill"  # history fetched later: the current value of each key, which may be a revision
    # HIO's own live capture placed by HIO-ADR-0012 P3 (T-0009, OD-0063): knowable_at is the
    # documented release instant and the basis is always schedule_only, never market evidence.
    # Opt-in; S1a does not use it.
    SCHEDULED_P3 = "scheduled_p3"


@dataclass(frozen=True)
class ReleaseSchedule:
    """A documented release rule: value for valid_time v is released at release_time (local, in
    tz) on the lag_business_days-th business day after v. capture_grace bounds how late a
    capture may be and still count as captured_on_schedule."""

    calendar: BusinessCalendar
    release_time: time
    tz: str
    lag_business_days: int
    capture_grace: timedelta

    def release_instant(self, valid_time: date) -> datetime:
        """A UTC instant built from a local date and time (never the reverse; OBS-INV-005)."""
        release_day = self.calendar.add_business_days(valid_time, self.lag_business_days)
        local = datetime.combine(release_day, self.release_time, tzinfo=ZoneInfo(self.tz))
        return local.astimezone(UTC)


@dataclass(frozen=True)
class SeriesDef:
    series_id: str
    source_id: str
    unit: str
    source_timezone: str
    calendar: BusinessCalendar
    schedule: ReleaseSchedule | None
    jump_threshold: Decimal | None = None  # absolute change between consecutive keys that quarantines
    rule_lag: timedelta | None = None  # a spec-declared lag: basis rule_inferred, never market evidence
