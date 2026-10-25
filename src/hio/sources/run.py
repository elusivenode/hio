"""One capture run of one dataset (T-0009 §2 and §4).

Order: rights gate (before any request) -> request -> validate the payload -> write. A receipt is
written only for a payload that passed its schema, through the S1a receipt and capture-record keys,
and in one transaction with the run record. A re-fetch with identical bytes writes **no** receipt
and exactly one run record; a failed run writes one failed record and nothing else. `capture()` is
not called or changed (HIO-ADR-0012 §3.4); this module repeats its small write tail.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.layout import capture_record_key, receipt_key
from hio.contracts.observation import Receipt
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.capture import latest_capture
from hio.marketdata.runrecord import Execution, RunRecord, envelope_headers
from hio.sources.datasets import DatasetSpec, MalformedPayload
from hio.sources.transport import HttpResponse, Transport, TransportError
from hio.storage.objectstore import LocalObjectStore, StagedWrites


@dataclass(frozen=True)
class RunResult:
    record: RunRecord
    receipt: Receipt | None  # the receipt this run is bound to (new, or the held one)
    is_new: bool


def run_capture(
    spec: DatasetSpec,
    *,
    transport: Transport,
    store: LocalObjectStore,
    gate: RightsGate,
    clock: Callable[[], datetime],
    execution: Execution,
    user_agent: str,
    url: str | None = None,
    slot: str | None = None,
    slot_due_at: datetime | None = None,
) -> RunResult:
    target = url or spec.url
    if not target:
        raise ValueError(
            f"{spec.source_id}: no URL configured; a URL is part of the approved request identity"
        )
    gate.authorise(Operation.FETCH, [spec.source_id])
    gate.authorise(Operation.STORE_RAW, [spec.source_id])

    attempted_at = clock()
    require_utc_instant("attempted_at", attempted_at)
    request = {"method": "GET", "url": target, "final_url": None, "user_agent": user_agent}

    def failed(error_class: str, response: HttpResponse | None, completed_at: datetime) -> RunResult:
        record = RunRecord(
            source_id=spec.source_id,
            execution=execution,
            request={**request, "final_url": response.final_url if response else None},
            status=response.status if response else None,
            headers=envelope_headers(response.headers) if response else [],
            response_sha256=None,
            response_bytes=None,
            attempted_at=attempted_at,
            completed_at=completed_at,
            outcome="failed",
            error_class=error_class,
            slot=slot,
            slot_due_at=slot_due_at,
        )
        store.put(record.key, record.canonical())
        return RunResult(record, None, False)

    try:
        response = transport.get(target, {"User-Agent": user_agent})
    except TransportError:
        return failed("network", None, max(clock(), attempted_at))
    completed_at = max(clock(), attempted_at)
    require_utc_instant("completed_at", completed_at)
    request["final_url"] = response.final_url
    if response.status != 200:
        return failed("http_status", response, completed_at)
    try:
        spec.parse(response.body)
    except MalformedPayload as exc:
        return failed(exc.error_class, response, completed_at)

    data = response.body
    rid = sha256_hex(data)
    previous = latest_capture(store, spec.source_id)
    if previous is not None and completed_at <= previous.captured_at:
        return failed("clock_order", response, completed_at)

    def record_for(outcome: str) -> RunRecord:
        return RunRecord(
            source_id=spec.source_id,
            execution=execution,
            request=request,
            status=response.status,
            headers=envelope_headers(response.headers),
            response_sha256=rid,
            response_bytes=len(data),
            attempted_at=attempted_at,
            completed_at=completed_at,
            outcome=outcome,
            receipt_id=rid,
            slot=slot,
            slot_due_at=slot_due_at,
        )

    if previous is not None and previous.receipt_id == rid:
        record = record_for("verified_unchanged")
        store.put(record.key, record.canonical())
        return RunResult(record, previous, False)

    receipt = Receipt(rid, spec.source_id, completed_at, dict(request), len(data))
    record = record_for("verified_changed")
    staged = StagedWrites(store)
    bytes_key = receipt_key(spec.source_id, completed_at, rid)
    if not store.put_if_absent_check(bytes_key, data):
        staged.add(bytes_key, data)
    staged.add(capture_record_key(spec.source_id, completed_at, rid), canonical_json(receipt.as_record()))
    staged.add(record.key, record.canonical())
    staged.commit()
    return RunResult(record, receipt, True)
