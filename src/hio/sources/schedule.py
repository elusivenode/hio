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

Nothing here makes a request. The schedule is defined, not enabled: the workflow definition is
kept outside `.github/workflows/` and live operation needs Authorisation B (T-0009 §8).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from hio.contracts.layout import ATTEMPTS_PREFIX
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.runrecord import load_run_record
from hio.reference.calendar import BusinessCalendar
from hio.storage.objectstore import LocalObjectStore

SYD, NY = "Australia/Sydney", "America/New_York"
LATENESS = timedelta(hours=3)  # a due slot may run up to this long after its due instant


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


def due_slots(now: datetime, calendars: Mapping[str, BusinessCalendar]) -> list[tuple[Slot, datetime]]:
    """Every slot due at `now`: its local date is a business day of its calendar and
    due_at <= now < due_at + LATENESS. Sorted by due instant, then publication."""
    require_utc_instant("now", now)
    out = []
    for slot in SLOTS:
        # The local wall-clock date of the check, never a valid_time (the one exemption in
        # tools/check_repo.py VALID_TIME_EXEMPT).
        local_day = now.astimezone(ZoneInfo(slot.tz)).date()
        if not calendars[slot.calendar].is_business_day(local_day):
            continue
        due = slot.due_at(local_day)
        if due <= now < due + LATENESS:
            out.append((slot, due))
    return sorted(out, key=lambda x: (x[1], x[0].publication_id, x[0].name))


def already_verified(store: LocalObjectStore, slot: Slot, due: datetime) -> bool:
    """A verified record exists for this publication, slot and due instant (records are verified on
    read: a corrupt one refuses rather than counting)."""
    for key in store.list(f"{ATTEMPTS_PREFIX}{slot.publication_id}/"):
        rec = load_run_record(store, key)
        if rec.slot == slot.name and rec.slot_due_at == due and rec.outcome != "failed":
            return True
    return False
