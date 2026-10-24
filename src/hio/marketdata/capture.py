"""Capture: synthetic source adapters → immutable receipts (observations standard §1, §6).

A receipt's bytes are content-addressed and stored once per capture month. Each capture event
is its own record (receipt_id + captured_at), because the same bytes fetched again after the
source has changed in between (a revert) is an observation HIO made at that time. Only an
identical *consecutive* re-fetch of a source is a no-op (§6 duplicate receipt).

S1a adapters read local fixture files. The fetch and store_raw rights checks run before the
file is read or anything is written (rights standard §3).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.observation import Receipt, parse_instant
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.temporal import require_utc_instant
from hio.storage.objectstore import LocalObjectStore


@dataclass(frozen=True)
class SyntheticSource:
    """A synthetic source whose 'endpoint' is a local fixture file. Its id must start with
    'synthetic.' so that it can never be mistaken for a genuine source."""

    source_id: str
    fixture_path: Path

    def __post_init__(self) -> None:
        if not self.source_id.startswith("synthetic."):
            raise ValueError(f"S1a sources must be synthetic: {self.source_id}")

    def fetch(self) -> bytes:
        return Path(self.fixture_path).read_bytes()


def receipt_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    # A storage partition by capture month (a UTC instant formatted as text), not a valid_time.
    return f"receipts/{source_id}/{captured_at.astimezone(UTC):%Y/%m}/{receipt_id}"


def capture_record_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    stamp = captured_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")  # sorts by capture instant
    return f"catalogue/captures/{source_id}/{stamp}-{receipt_id}.json"


def capture(
    source: SyntheticSource, store: LocalObjectStore, gate: RightsGate, captured_at: datetime
) -> tuple[Receipt, bool]:
    """Fetch and store one receipt. Returns (receipt, is_new). An identical consecutive re-fetch
    returns the previous capture's receipt and writes nothing."""
    require_utc_instant("captured_at", captured_at)
    gate.authorise(Operation.FETCH, [source.source_id])
    gate.authorise(Operation.STORE_RAW, [source.source_id])
    data = source.fetch()
    rid = sha256_hex(data)
    previous = latest_capture(store, source.source_id)
    if previous is not None:
        if captured_at <= previous.captured_at:
            raise ValueError("captures of a source must be recorded in time order")
        if previous.receipt_id == rid:
            return previous, False
    receipt = Receipt(
        rid, source.source_id, captured_at, {"fixture": Path(source.fixture_path).name}, len(data)
    )
    store.put_if_absent(receipt_key(source.source_id, captured_at, rid), data)
    store.put(capture_record_key(source.source_id, captured_at, rid), canonical_json(receipt.as_record()))
    return receipt, True


def latest_capture(store: LocalObjectStore, source_id: str) -> Receipt | None:
    keys = list(store.list(f"catalogue/captures/{source_id}/"))
    return _load(store, keys[-1]) if keys else None  # keys sort by capture instant


def load_receipt(store: LocalObjectStore, source_id: str, captured_at: datetime, receipt_id: str) -> Receipt:
    return _load(store, capture_record_key(source_id, captured_at, receipt_id))


def _load(store: LocalObjectStore, key: str) -> Receipt:
    r = json.loads(store.get(key))
    return Receipt(
        r["receipt_id"], r["source_id"], parse_instant(r["captured_at"]), r["request"], r["byte_length"]
    )


def receipt_bytes(store: LocalObjectStore, receipt: Receipt) -> bytes:
    """Read the raw bytes back, verifying their hash (OBS-INV-004)."""
    return store.get(
        receipt_key(receipt.source_id, receipt.captured_at, receipt.receipt_id), receipt.receipt_id
    )
