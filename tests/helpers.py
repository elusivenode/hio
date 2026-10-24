"""Shared S1a test helpers. Everything here is synthetic."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from hio.contracts.rights import Operation
from hio.marketdata.capture import SyntheticSource, capture
from hio.marketdata.series import CaptureMode, ReleaseSchedule, SeriesDef
from hio.marketdata.vintages import VintageStore
from hio.reference.calendar import load_calendars

FIXTURES = Path(__file__).parent / "fixtures" / "synthetic"
CALENDARS = load_calendars(FIXTURES / "calendars.yaml")


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


class AllowAllGate:
    """A test double for step-4 tests only; the real gate (hio.rights) is tested separately."""

    def __init__(self) -> None:
        self.calls: list[tuple[Operation, tuple[str, ...]]] = []

    def authorise(
        self, operation: Operation, source_ids: Iterable[str], consumer_class: str | None = None
    ) -> None:
        self.calls.append((operation, tuple(source_ids)))
        del consumer_class  # every operation is allowed


MONTHLY_X = SeriesDef(
    series_id="synthetic.x",
    source_id="synthetic.monthly_source",
    unit="index",
    source_timezone="UTC",
    calendar=CALENDARS["synthetic.monthly"],
    schedule=ReleaseSchedule(CALENDARS["synthetic.monthly"], time(0, 30), "UTC", 11, timedelta(days=2)),
)

DAILY_RATE = SeriesDef(
    series_id="synthetic.rate",
    source_id="synthetic.daily_source",
    unit="percent per annum",
    source_timezone="Australia/Sydney",
    calendar=CALENDARS["synthetic.xsyd"],
    schedule=ReleaseSchedule(
        CALENDARS["synthetic.xsyd"], time(9, 0), "Australia/Sydney", 0, timedelta(days=1)
    ),
    jump_threshold=Decimal("1.0"),
)

LAGGED = SeriesDef(
    series_id="synthetic.lagged",
    source_id="synthetic.daily_source",
    unit="percent per annum",
    source_timezone="Australia/Sydney",
    calendar=CALENDARS["synthetic.xsyd"],
    schedule=None,
    rule_lag=timedelta(days=1),
)

SERIES = {s.series_id: s for s in (MONTHLY_X, DAILY_RATE, LAGGED)}


def receipt_text(source_hint: str, rows: list[str], header: str = "series_id,valid_time,value") -> str:
    return "\n".join([f"# SYNTHETIC test receipt ({source_hint})", header, *rows]) + "\n"


def ingest_text(
    vs: VintageStore, tmp: Path, source_id: str, text: str, captured_at: datetime, mode: CaptureMode
):
    path = tmp / f"{source_id}.csv"  # one endpoint per source, like a real source's URL
    path.write_text(text)
    receipt, is_new = capture(SyntheticSource(source_id, path), vs.store, AllowAllGate(), captured_at)
    return vs.ingest(receipt, mode) if is_new else None


def ingest_file(vs: VintageStore, source_id: str, path: Path, captured_at: datetime, mode: CaptureMode):
    receipt, is_new = capture(SyntheticSource(source_id, path), vs.store, AllowAllGate(), captured_at)
    return vs.ingest(receipt, mode) if is_new else None
