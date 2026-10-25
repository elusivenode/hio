"""Object-store key layout for receipts and capture records (releases standard §1).

Shared by marketdata (which writes them) and publish (which follows lineage through them), so
neither needs to import the other.
"""

from __future__ import annotations

from datetime import UTC, datetime


def receipt_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    # A storage partition by capture month (a UTC instant formatted as text), not a valid_time.
    return f"receipts/{source_id}/{captured_at.astimezone(UTC):%Y/%m}/{receipt_id}"


def capture_record_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    stamp = captured_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")  # sorts by capture instant
    return f"catalogue/captures/{source_id}/{stamp}-{receipt_id}.json"


CAPTURES_PREFIX = "catalogue/captures/"


def attempt_record_key(source_id: str, attempted_at: datetime, record_sha256: str) -> str:
    """A capture-run record (HIO-ADR-0012 §4.3.3): keyed by the attempt instant and the hash of its
    own canonical content, so a read can recompute the hash and compare."""
    stamp = attempted_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")  # sorts by attempt instant
    return f"catalogue/attempts/{source_id}/{stamp}-{record_sha256}.json"


ATTEMPTS_PREFIX = "catalogue/attempts/"
