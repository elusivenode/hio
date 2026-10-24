"""Receipts and vintages (observations standard §1–§2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from hio.contracts.temporal import KnowableBasis, QualityStatus, require_utc_instant


@dataclass(frozen=True)
class Receipt:
    receipt_id: str  # SHA-256 of the bytes
    source_id: str
    captured_at: datetime
    request: dict[str, Any]
    byte_length: int

    def __post_init__(self) -> None:
        require_utc_instant("captured_at", self.captured_at)

    def as_record(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "source_id": self.source_id,
            "captured_at": self.captured_at,
            "request": self.request,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True)
class Vintage:
    """One distinct value for (series_id, valid_time), with its own knowability evidence.

    valid_time is a market-local calendar date taken from the source, never derived from an
    instant (OBS-INV-005). quality_status is the status at recording; later quality events
    (e.g. an owner's release from quarantine) are applied by the query layer.
    """

    series_id: str
    valid_time: date
    vintage_seq: int
    value: Decimal
    receipt_id: str
    captured_at: datetime
    knowable_at: datetime
    knowable_basis: KnowableBasis
    source_timezone: str
    quality_status: QualityStatus
    quality_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.valid_time, datetime) or not isinstance(self.valid_time, date):
            raise TypeError("valid_time must be a date, not an instant (OBS-INV-005)")
        require_utc_instant("captured_at", self.captured_at)
        require_utc_instant("knowable_at", self.knowable_at)
        if self.vintage_seq < 1:
            raise ValueError("vintage_seq starts at 1")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ValueError("value must be a finite Decimal")

    def as_record(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "valid_time": self.valid_time,
            "vintage_seq": self.vintage_seq,
            "value": self.value,
            "receipt_id": self.receipt_id,
            "captured_at": self.captured_at,
            "knowable_at": self.knowable_at,
            "knowable_basis": self.knowable_basis.value,
            "source_timezone": self.source_timezone,
            "quality_status": self.quality_status.value,
            "quality_reasons": list(self.quality_reasons),
        }

    @classmethod
    def from_record(cls, r: dict[str, Any]) -> Vintage:
        return cls(
            series_id=r["series_id"],
            valid_time=date.fromisoformat(r["valid_time"]),
            vintage_seq=r["vintage_seq"],
            value=Decimal(r["value"]),
            receipt_id=r["receipt_id"],
            captured_at=parse_instant(r["captured_at"]),
            knowable_at=parse_instant(r["knowable_at"]),
            knowable_basis=KnowableBasis(r["knowable_basis"]),
            source_timezone=r["source_timezone"],
            quality_status=QualityStatus(r["quality_status"]),
            quality_reasons=tuple(r["quality_reasons"]),
        )


def parse_instant(text: str) -> datetime:
    """Parse a UTC instant written with a Z suffix. Offsets other than Z are refused."""
    if not text.endswith("Z"):
        raise ValueError(f"instant must be UTC with a Z suffix: {text!r}")
    value = datetime.fromisoformat(text)
    require_utc_instant("instant", value)
    return value
