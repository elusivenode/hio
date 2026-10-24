"""Append-only lifecycle status events (releases standard §5).

Consumer classes (F-REVIEW-2026-10-24-s1a-1-2, OD-0023): an approval names one class, and a
withdrawal may name one class (withdrawing that class only) or none (a global, terminal
withdrawal). For a consumer of class C, the effective status is the latest event that applies to
C: a class-agnostic event, or an event naming C. Approval for one class never authorises
another. The overall effective status (highest seq, §5) is unchanged. How several classes are
represented beyond this is owner question Q-005b.
"""

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
        if self.status is Status.APPROVED_FOR_CONSUMER and self.consumer_class is None:
            raise StatusError("approved_for_consumer needs a consumer_class")
        if self.consumer_class is not None and self.status not in {
            Status.APPROVED_FOR_CONSUMER,
            Status.WITHDRAWN,
        }:
            raise StatusError(
                "only approved_for_consumer and a class-scoped withdrawn may name a consumer_class"
            )

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
        if e.status is Status.WITHDRAWN and e.consumer_class is None:
            raise StatusError("a global withdrawn is terminal; no later event may follow it")


def effective_status(events: list[StatusEvent]) -> StatusEvent | None:
    ordered = sorted(events, key=lambda e: e.seq)
    validate_sequence(ordered)
    return ordered[-1] if ordered else None


def effective_status_for(events: list[StatusEvent], consumer_class: str) -> StatusEvent | None:
    """The latest event that applies to a consumer of this class: class-agnostic, or naming it."""
    ordered = sorted(events, key=lambda e: e.seq)
    validate_sequence(ordered)
    applicable = [e for e in ordered if e.consumer_class in (None, consumer_class)]
    return applicable[-1] if applicable else None
