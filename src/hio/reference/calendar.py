"""Business calendars (RA §3.2 step 2; RA-INV-018).

Dates here are market-local calendar dates. Nothing in this module converts an instant to a
date (OBS-INV-005).
"""

from __future__ import annotations

import hashlib
from collections.abc import Collection, Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

_MAX_GAP_DAYS = 31  # a calendar with no business day in 31 days is a data error


class CalendarCoverageError(ValueError):
    """A date outside the period a cited calendar covers: refused, never assumed a business day."""


@dataclass(frozen=True)
class BusinessCalendar:
    calendar_id: str
    holidays: frozenset[date] = field(default_factory=frozenset)
    weekend: frozenset[int] = frozenset({5, 6})  # Saturday, Sunday
    # A dated, cited reference calendar (T-0009 §2.7; F-REVIEW-2026-10-25-t0009-5) states what it
    # covers and where it comes from. None for S1a's calendars and for derived ones, as before.
    coverage: tuple[date, date] | None = None
    citation: str | None = None
    as_of: date | None = None
    content_sha256: str | None = None

    @property
    def is_cited(self) -> bool:
        return None not in (self.coverage, self.citation, self.as_of, self.content_sha256)

    @property
    def identity(self) -> str:
        """How a release names the calendar it used: id, as-of date and the hash of the cited file."""
        if not self.is_cited:
            return f"{self.calendar_id} (uncited)"
        return f"{self.calendar_id}@{self.as_of}#sha256:{self.content_sha256}"

    def is_business_day(self, d: date) -> bool:
        if self.coverage is not None and not self.coverage[0] <= d <= self.coverage[1]:
            first, last = self.coverage
            raise CalendarCoverageError(f"{self.calendar_id}: {d} is outside the coverage {first}..{last}")
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


CALENDAR_KINDS = ("reference", "synthetic")


def load_reference_calendar(path: str | Path, *, allow_synthetic: bool = False) -> BusinessCalendar:
    """A dated, cited calendar (T-0009 §2.7, HIO-ADR-0012 gate (c)). The document states its id, kind,
    the date its source was read (`as_of`), the citation, the covered period, the weekend and each
    closed date with a reason. Anything missing, a closure outside the coverage, or a duplicated date
    refuses. `kind: synthetic` (invented test data, never a fact) loads only when allowed; `kind:
    reference` also needs the URL and the rights-register id of its source, because committing real
    calendar data is an operation on that source (rights standard: unknown means deny)."""
    raw = Path(path).read_bytes()
    doc = yaml.safe_load(raw)
    try:
        kind = doc["kind"]
        source = doc["source"]
        start, end = (date.fromisoformat(str(doc["coverage"][k])) for k in ("start", "end"))
        as_of = date.fromisoformat(str(doc["as_of"]))
        citation = str(source["citation"]).strip()
        closed = [(date.fromisoformat(str(c["date"])), str(c["reason"]).strip()) for c in doc["closed"]]
        weekend = frozenset(int(w) for w in doc["weekend"])
        calendar_id = str(doc["calendar_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{path}: not a dated, cited calendar: {exc!r}") from exc
    if kind not in CALENDAR_KINDS:
        raise ValueError(f"{path}: unknown kind {kind!r}")
    if kind == "synthetic" and not allow_synthetic:
        raise ValueError(f"{path}: a synthetic calendar is test data, not reference data")
    if kind == "reference" and not (source.get("url") and source.get("rights_source_id")):
        raise ValueError(f"{path}: reference data needs its source URL and rights_source_id")
    if not citation or end < start or not weekend <= set(range(7)):
        raise ValueError(f"{path}: empty citation, inverted coverage or a bad weekend")
    days = [d for d, _ in closed]
    if len(days) != len(set(days)) or any(not start <= d <= end or not reason for d, reason in closed):
        raise ValueError(f"{path}: a closure is duplicated, unexplained or outside the coverage")
    return BusinessCalendar(
        calendar_id,
        frozenset(days),
        weekend,
        coverage=(start, end),
        citation=citation,
        as_of=as_of,
        content_sha256=hashlib.sha256(raw).hexdigest(),
    )


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
