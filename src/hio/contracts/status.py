"""Append-only lifecycle status events (releases standard §5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from hio.contracts.temporal import require_utc_instant


class Status(StrEnum):
    DRAFT = "draft"
    EXPLORATORY = "exploratory"
    VALIDATED = "validated"
    APPROVED_FOR_CONSUMER = "approved_for_consumer"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


# Level used by consumers to compare against a required minimum. withdrawn is handled separately.
LEVEL = {
    Status.DRAFT: 0,
    Status.EXPLORATORY: 1,
    Status.VALIDATED: 2,
    Status.APPROVED_FOR_CONSUMER: 3,
    Status.SUPERSEDED: 1,
    Status.DEPRECATED: 1,
}


class StatusError(ValueError):
    pass


@dataclass(frozen=True)
class StatusEvent:
    content_sha256: str
    seq: int
    status: Status
    actor: str
    evidence: str
    at: datetime
    consumer_class: str | None = None

    def __post_init__(self) -> None:
        require_utc_instant("at", self.at)
        if self.seq < 1:
            raise StatusError("seq starts at 1")
        if (self.status is Status.APPROVED_FOR_CONSUMER) != (self.consumer_class is not None):
            raise StatusError("consumer_class is required exactly for approved_for_consumer")

    def as_record(self) -> dict:
        return {
            "content_sha256": self.content_sha256,
            "seq": self.seq,
            "status": self.status.value,
            "consumer_class": self.consumer_class,
            "actor": self.actor,
            "evidence": self.evidence,
            "at": self.at,
        }


def validate_sequence(events: list[StatusEvent]) -> None:
    """seq is 1, 2, 3, … with no gap or duplicate; nothing follows withdrawn (§5)."""
    seqs = [e.seq for e in events]
    if seqs != list(range(1, len(events) + 1)):
        raise StatusError(f"status seq must be 1..n with no gap or duplicate: {seqs}")
    if len({e.content_sha256 for e in events}) > 1:
        raise StatusError("events for more than one object")
    for e in events[:-1]:
        if e.status is Status.WITHDRAWN:
            raise StatusError("withdrawn is terminal; no later event may follow it")


def effective_status(events: list[StatusEvent]) -> StatusEvent | None:
    ordered = sorted(events, key=lambda e: e.seq)
    validate_sequence(ordered)
    return ordered[-1] if ordered else None
