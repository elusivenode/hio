"""Temporal vocabulary (observations standard §2–§4; HIO-ADR-0004)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum


class KnowableBasis(StrEnum):
    """Evidence that *this vintage's value* was public at knowable_at, strongest first (§3)."""

    PUBLISHER_TIMESTAMP = "publisher_timestamp"
    PUBLISHER_VINTAGE = "publisher_vintage"
    ARCHIVED_RECEIPT = "archived_receipt"
    CAPTURED_ON_SCHEDULE = "captured_on_schedule"
    SCHEDULE_ONLY = "schedule_only"
    RULE_INFERRED = "rule_inferred"

    @property
    def strength(self) -> int:
        """Higher is stronger. Used for weakest-basis reporting and deterministic tie-breaks."""
        return len(_ORDER) - _ORDER.index(self)

    @property
    def supports_market_knowledge(self) -> bool:
        """May this basis support as_known_by_market (§3, "yes" rows)?"""
        return self not in {KnowableBasis.SCHEDULE_ONLY, KnowableBasis.RULE_INFERRED}


_ORDER = list(KnowableBasis)


def weakest(bases) -> KnowableBasis:
    items = list(bases)
    if not items:
        raise ValueError("no bases")
    return min(items, key=lambda b: b.strength)


class QualityStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"


class KnowledgeMode(StrEnum):
    AS_CAPTURED_BY_HIO = "as_captured_by_hio"
    AS_KNOWN_BY_MARKET = "as_known_by_market"
    RECONSTRUCTED = "reconstructed"
    LATEST = "latest"

    @property
    def point_in_time(self) -> bool:
        """Only these two modes may support work labelled point-in-time (§4)."""
        return self in {KnowledgeMode.AS_CAPTURED_BY_HIO, KnowledgeMode.AS_KNOWN_BY_MARKET}


def require_utc_instant(name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware instant")
