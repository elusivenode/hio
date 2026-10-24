"""knowable_at and knowable_basis for one incoming value (observations standard §3; OBS-INV-006).

The basis is decided by the evidence the row carries, then by how HIO captured it:
1. published_at  → publisher_timestamp   (the payload dates this value)
2. vintage_from  → publisher_vintage     (the publisher's vintage archive dates this value)
3. archived_at   → archived_receipt      (an independently dated archive holds this value)
4. a scheduled capture within the schedule's grace after the documented release
                 → captured_on_schedule, knowable_at = the release instant
   but a scheduled capture that sees a *revised* value for a key HIO already holds
                 → captured_on_schedule, knowable_at = the capture instant: the revision was not
                   public at the original release, and HIO's own capture is the only evidence
5. otherwise, with a schedule (a backfill, or a capture later than the grace allows, when the
   value may already be a revision)  → schedule_only, knowable_at = the release instant
6. otherwise, with only a spec-declared lag  → rule_inferred
A value with none of these cannot be placed in time and is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from hio.contracts.temporal import KnowableBasis
from hio.marketdata.parse import RawRow
from hio.marketdata.series import CaptureMode, SeriesDef


class UnplaceableValue(ValueError):
    pass


@dataclass(frozen=True)
class Knowability:
    knowable_at: datetime
    basis: KnowableBasis


def determine(
    row: RawRow, series: SeriesDef, captured_at: datetime, mode: CaptureMode, revision: bool = False
) -> Knowability:
    if row.published_at is not None:
        return Knowability(row.published_at, KnowableBasis.PUBLISHER_TIMESTAMP)
    if row.vintage_from is not None:
        return Knowability(row.vintage_from, KnowableBasis.PUBLISHER_VINTAGE)
    if row.archived_at is not None:
        return Knowability(row.archived_at, KnowableBasis.ARCHIVED_RECEIPT)
    if series.schedule is not None:
        release = series.schedule.release_instant(row.valid_time)
        on_schedule = release <= captured_at <= release + series.schedule.capture_grace
        if mode is CaptureMode.SCHEDULED and revision and captured_at >= release:
            return Knowability(captured_at, KnowableBasis.CAPTURED_ON_SCHEDULE)
        if mode is CaptureMode.SCHEDULED and on_schedule:
            return Knowability(release, KnowableBasis.CAPTURED_ON_SCHEDULE)
        if captured_at < release:
            raise UnplaceableValue(
                f"{series.series_id} {row.valid_time}: captured before its documented release; "
                "the schedule is wrong or the value is not what the schedule describes"
            )
        return Knowability(release, KnowableBasis.SCHEDULE_ONLY)
    if series.rule_lag is not None:
        # The lag is applied to the start of the valid date in the source's own zone.
        local_start = datetime.combine(row.valid_time, time(0), tzinfo=ZoneInfo(series.source_timezone))
        return Knowability(local_start + series.rule_lag, KnowableBasis.RULE_INFERRED)
    raise UnplaceableValue(f"{series.series_id} {row.valid_time}: no evidence, schedule or rule")
