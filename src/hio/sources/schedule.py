"""The capture schedule and its local-time due gate (T-0009 §2.5; HIO-ADR-0012 §4.3 "Capture
schedule"; F-REVIEW-2026-10-25-t0009-7).

Each publication has a **first** check shortly after its documented publication and a **final**
check after its documented window close, at a local time on the publisher's business days:
- the RBA files at 09:45 and 16:30 Sydney, on RITS days;
- the NY Fed files at 08:30 and 15:00 New York, on weekdays (no SIFMA calendar: a check on a US
  holiday finds no change and records `verified_unchanged`, which is harmless).

A workflow fires on several fixed UTC cron slots (`CRON_UTC`), because the Sydney and New York
daylight-saving switches move independently. The gate decides which slot is due: a slot is due from
its local due instant until `LATENESS` after it, so a late or repeated firing still runs, and a slot
that already has a verified record is not run again (idempotence); a failed one is retried. The
due instant written to the run record comes from this gate, never from the caller.

`expected_slots` and `missed_slots` (T-0013 A-1) are the completeness side of the same calendar: which
slots should have been attempted in a period, and which of those closed their window without any attempt
record. The capture job runs `missed_slots` after every live run and fails on a missed slot.

Nothing here makes a request. The schedule is defined, not enabled: the workflow definition is
kept outside `.github/workflows/` and live operation needs Authorisation B (T-0009 §8).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from hio.contracts.layout import ATTEMPTS_PREFIX
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.runrecord import RunRecord, load_run_record
from hio.reference.calendar import BusinessCalendar
from hio.storage.objectstore import LocalObjectStore

SYD, NY = "Australia/Sydney", "America/New_York"
LATENESS = timedelta(hours=3)  # a due slot may run up to this long after its due instant
MISSED_HORIZON = timedelta(hours=24)  # how far back the capture job looks for a slot that was never attempted


@dataclass(frozen=True)
class Slot:
    publication_id: str
    name: str  # "first" or "final"
    local_time: time
    tz: str
    calendar: str  # the key of the publisher's business-day calendar: "rits" or "weekdays"

    def due_at(self, day: date) -> datetime:
        """The UTC instant of this slot on a local date (built from local date and time, OBS-INV-005)."""
        return datetime.combine(day, self.local_time, tzinfo=ZoneInfo(self.tz)).astimezone(UTC)


def _slots(publication_id: str, tz: str, calendar: str, first: time, final: time) -> tuple[Slot, ...]:
    return tuple(Slot(publication_id, n, t, tz, calendar) for n, t in (("first", first), ("final", final)))


SLOTS: tuple[Slot, ...] = (
    *_slots("rba.f1", SYD, "rits", time(9, 45), time(16, 30)),
    *_slots("rba.expert_judgement", SYD, "rits", time(9, 45), time(16, 30)),
    *_slots("nyfed.sofr", NY, "weekdays", time(8, 30), time(15, 0)),
    *_slots("nyfed.sofr_index", NY, "weekdays", time(8, 30), time(15, 0)),
)

# The UTC firing times, "minute hour": each local slot in both daylight-saving regimes (Sydney UTC+10
# and +11, New York UTC-5 and -4), and once more an hour later as a same-day retry. Verified against
# every day of two years by tests/test_s1b1_remediation_schedule.py.
CRON_UTC: tuple[str, ...] = (
    "45 22",  # Sydney 09:45 AEDT (and 08:45 AEST: not yet due)
    "45 23",  # Sydney 09:45 AEST; 10:45 AEDT retry
    "45 0",  # Sydney 10:45 AEST retry
    "30 5",  # Sydney 16:30 AEDT
    "30 6",  # Sydney 16:30 AEST; 17:30 AEDT retry
    "30 7",  # Sydney 17:30 AEST retry
    "30 12",  # New York 08:30 EDT
    "30 13",  # New York 08:30 EST; 09:30 EDT retry
    "30 14",  # New York 09:30 EST retry
    "0 19",  # New York 15:00 EDT
    "0 20",  # New York 15:00 EST; 16:00 EDT retry
    "0 21",  # New York 16:00 EST retry
)


def _local_day(instant: datetime, tz: str) -> date:
    """The local wall-clock date of an instant in a publisher's zone, never a valid_time (the one exemption
    in tools/check_repo.py VALID_TIME_EXEMPT)."""
    return instant.astimezone(ZoneInfo(tz)).date()


def due_slots(now: datetime, calendars: Mapping[str, BusinessCalendar]) -> list[tuple[Slot, datetime]]:
    """Every slot due at `now`: its local date is a business day of its calendar and
    due_at <= now < due_at + LATENESS. Sorted by due instant, then publication."""
    require_utc_instant("now", now)
    out = []
    for slot in SLOTS:
        local_day = _local_day(now, slot.tz)
        if not calendars[slot.calendar].is_business_day(local_day):
            continue
        due = slot.due_at(local_day)
        if due <= now < due + LATENESS:
            out.append((slot, due))
    return sorted(out, key=lambda x: (x[1], x[0].publication_id, x[0].name))


def expected_slots(
    start: datetime, end: datetime, calendars: Mapping[str, BusinessCalendar]
) -> list[tuple[Slot, datetime]]:
    """Every slot instance whose local date is a business day of its calendar and whose due instant
    lies in [start, end). Sorted like `due_slots`. A date the calendar does not cover raises
    `CalendarCoverageError`: an expected slot is never guessed."""
    require_utc_instant("start", start)
    require_utc_instant("end", end)
    out = []
    for slot in SLOTS:
        # One local day either side, because the local date of an instant differs from its UTC date.
        day = _local_day(start, slot.tz) - timedelta(days=1)
        last = _local_day(end, slot.tz) + timedelta(days=1)
        while day <= last:
            due = slot.due_at(day)
            # The calendar is asked only about a day that has a slot in the range, so coverage is
            # required exactly where the range needs it.
            if start <= due < end and calendars[slot.calendar].is_business_day(day):
                out.append((slot, due))
            day += timedelta(days=1)
    return sorted(out, key=lambda x: (x[1], x[0].publication_id, x[0].name))


def missed_slots(
    now: datetime,
    calendars: Mapping[str, BusinessCalendar],
    records: Iterable[RunRecord],
    horizon: timedelta = MISSED_HORIZON,
) -> list[tuple[Slot, datetime]]:
    """Expected slots whose window (`due_at + LATENESS`) closed in (now - horizon, now] and that have no
    attempt record for the same publication, slot and due instant. A `failed` record counts as an
    attempt (the failure is its own alert); it is never taken for a capture."""
    require_utc_instant("now", now)
    # window close = due + LATENESS in (now - horizon, now]  <=>  due in [lo, hi), at microsecond resolution
    lo = now - horizon - LATENESS + timedelta.resolution
    hi = now - LATENESS + timedelta.resolution
    attempted = {(r.source_id, r.slot, r.slot_due_at) for r in records}
    return [
        (slot, due)
        for slot, due in expected_slots(lo, hi, calendars)
        if (slot.publication_id, slot.name, due) not in attempted
    ]


_ATTEMPT_NAME = re.compile(r"^(\d{8}-\d{12})-[0-9a-f]{64}\.json$")


def load_attempt_records(
    store: LocalObjectStore, since: datetime, unreadable: list[str] | None = None
) -> list[RunRecord]:
    """Every attempt record of every publication that started at or after `since`, listing the attempts
    prefix once. A record cannot start before the slot it names is due, so one that started before
    `since` cannot answer for a slot due at or after `since`; its key carries the start instant, so it
    is skipped unread. A key that does not parse, or a record that fails verification, raises; with
    `unreadable` given its key is collected instead and the rest are still returned."""
    require_utc_instant("since", since)
    floor = since.strftime("%Y%m%d-%H%M%S%f")
    out = []
    for key in store.list(ATTEMPTS_PREFIX):
        try:
            named = _ATTEMPT_NAME.match(key.rsplit("/", 1)[-1])
            if named is None:
                raise ValueError(f"not an attempt-record key: {key}")
            if named.group(1) < floor:
                continue
            out.append(load_run_record(store, key))
        except Exception:
            if unreadable is None:
                raise
            unreadable.append(key)
    return out


def already_verified(store: LocalObjectStore, slot: Slot, due: datetime) -> bool:
    """A verified record exists for this publication, slot and due instant (records are verified on
    read: a corrupt one refuses rather than counting)."""
    for key in store.list(f"{ATTEMPTS_PREFIX}{slot.publication_id}/"):
        rec = load_run_record(store, key)
        if rec.slot == slot.name and rec.slot_due_at == due and rec.outcome != "failed":
            return True
    return False
