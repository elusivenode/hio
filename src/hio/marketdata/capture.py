"""Capture: synthetic source adapters → immutable receipts (observations standard §1, §6).

A receipt's bytes are content-addressed and stored once per capture month. Each capture event
is its own record (receipt_id + captured_at), because the same bytes fetched again after the
source has changed in between (a revert) is an observation HIO made at that time. Only an
identical *consecutive* re-fetch of a source is a no-op (§6 duplicate receipt).

S1a adapters read local fixture files. The fetch and store_raw rights checks run before the
file is read or anything is written (rights standard §3).
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.observation import Receipt, parse_instant
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.series import SeriesDef
from hio.storage.objectstore import LocalObjectStore, StagedWrites


@dataclass(frozen=True)
class SyntheticSource:
    """A synthetic source whose 'endpoint' is a local fixture file. Its id must start with
    'synthetic.' so that it can never be mistaken for a genuine source."""

    source_id: str
    fixture_path: Path

    def __post_init__(self) -> None:
        if not self.source_id.startswith("synthetic."):
            raise ValueError(f"S1a sources must be synthetic: {self.source_id}")

    def fetch(self, as_of: datetime) -> bytes:
        del as_of  # a static fixture: the same bytes whenever it is fetched
        return Path(self.fixture_path).read_bytes()


@dataclass(frozen=True)
class SyntheticWorldSource:
    """A synthetic source backed by a 'world' file of true values. Fetched at an instant, it
    returns what a real source's current file would hold then: the rows whose documented release
    has happened. No network; the world file is a local synthetic fixture."""

    source_id: str
    world_path: Path
    series: Mapping[str, SeriesDef]

    def __post_init__(self) -> None:
        if not self.source_id.startswith("synthetic."):
            raise ValueError(f"S1a sources must be synthetic: {self.source_id}")

    def fetch(self, as_of: datetime) -> bytes:
        lines = Path(self.world_path).read_text().splitlines()
        reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
        released = []
        for row in reader:
            series = self.series[row["series_id"]]
            schedule = series.schedule
            if schedule is None:
                raise ValueError(f"world series {series.series_id} needs a release schedule")
            if schedule.release_instant(date.fromisoformat(row["valid_time"])) <= as_of:
                released.append(f"{row['series_id']},{row['valid_time']},{row['value']}")
        body = [
            f"# SYNTHETIC receipt from {self.source_id} (released rows only)",
            "series_id,valid_time,value",
            *released,
        ]
        return ("\n".join(body) + "\n").encode("utf-8")


def receipt_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    # A storage partition by capture month (a UTC instant formatted as text), not a valid_time.
    return f"receipts/{source_id}/{captured_at.astimezone(UTC):%Y/%m}/{receipt_id}"


def capture_record_key(source_id: str, captured_at: datetime, receipt_id: str) -> str:
    stamp = captured_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")  # sorts by capture instant
    return f"catalogue/captures/{source_id}/{stamp}-{receipt_id}.json"


def capture(
    source: SyntheticSource | SyntheticWorldSource,
    store: LocalObjectStore,
    gate: RightsGate,
    captured_at: datetime,
) -> tuple[Receipt, bool]:
    """Fetch and store one receipt. Returns (receipt, is_new). An identical consecutive re-fetch
    returns the previous capture's receipt and writes nothing."""
    require_utc_instant("captured_at", captured_at)
    gate.authorise(Operation.FETCH, [source.source_id])
    gate.authorise(Operation.STORE_RAW, [source.source_id])
    data = source.fetch(captured_at)
    rid = sha256_hex(data)
    previous = latest_capture(store, source.source_id)
    if previous is not None:
        if captured_at <= previous.captured_at:
            raise ValueError("captures of a source must be recorded in time order")
        if previous.receipt_id == rid:
            return previous, False
    origin = source.fixture_path if isinstance(source, SyntheticSource) else source.world_path
    receipt = Receipt(rid, source.source_id, captured_at, {"fixture": Path(origin).name}, len(data))
    # The bytes and the capture record are one transaction (F-REVIEW-2026-10-24-s1a-1-6).
    staged = StagedWrites(store)
    bytes_key = receipt_key(source.source_id, captured_at, rid)
    if not store.put_if_absent_check(bytes_key, data):
        staged.add(bytes_key, data)
    staged.add(capture_record_key(source.source_id, captured_at, rid), canonical_json(receipt.as_record()))
    staged.commit()
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
