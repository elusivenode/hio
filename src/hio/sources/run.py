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

from hio.contracts.canonical import canonical_json, decimal_str, sha256_hex
from hio.contracts.layout import capture_record_key, link_record_key, receipt_key
from hio.contracts.observation import Receipt
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.capture import latest_capture, receipt_bytes
from hio.marketdata.runrecord import SLOT_NAMES, Execution, RunRecord, envelope_headers, value_digest
from hio.sources.datasets import MalformedPayload, Parsed, Publication
from hio.sources.transport import HttpResponse, Transport, TransportError
from hio.storage.objectstore import LocalObjectStore
from hio.storage.staging import staged_writes


@dataclass(frozen=True)
class RunResult:
    record: RunRecord
    receipt: Receipt | None  # the receipt this run is bound to (new, or the held one)
    is_new: bool


def run_capture(
    spec: Publication,
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
            f"{spec.publication_id}: no URL configured; a URL is part of the approved request identity"
        )
    # Every dataset the file serves must allow the operation: fetching or retaining the file is an
    # operation on all of its datasets, and each is evaluated on its own record (OD-0065).
    subjects = [d.source_id for d in spec.datasets]
    gate.authorise(Operation.FETCH, subjects)
    gate.authorise(Operation.STORE_RAW, subjects)

    attempted_at = clock()
    require_utc_instant("attempted_at", attempted_at)
    # The slot facts the record will carry are checked before any request (F-REVIEW-2026-10-25-t0009-7).
    if (slot is None) != (slot_due_at is None) or (slot is not None and slot not in SLOT_NAMES):
        raise ValueError("a scheduled run names a known slot and its due instant together")
    if slot_due_at is not None and attempted_at < slot_due_at:
        raise ValueError("a scheduled run cannot start before its slot is due")
    request = {"method": "GET", "url": target, "final_url": None, "user_agent": user_agent}

    def failed(error_class: str, response: HttpResponse | None, completed_at: datetime) -> RunResult:
        record = RunRecord(
            source_id=spec.publication_id,
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
            datasets=subjects,
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
        keys = checked_keys(spec.parse(response.body))
    except MalformedPayload as exc:
        return failed(exc.error_class, response, completed_at)

    data = response.body
    rid = sha256_hex(data)
    previous = latest_capture(store, spec.publication_id)
    if previous is not None and completed_at <= previous.captured_at:
        return failed("clock_order", response, completed_at)
    held = checked_keys(spec.parse(receipt_bytes(store, previous))) if previous is not None else []
    if missing_keys(spec, keys, held):
        return failed("key_missing", response, completed_at)

    def record_for(outcome: str) -> RunRecord:
        return RunRecord(
            source_id=spec.publication_id,
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
            datasets=subjects,
            keys_checked=keys,
        )

    if previous is not None and previous.receipt_id == rid:
        record = record_for("verified_unchanged")
        store.put(record.key, record.canonical())
        return RunResult(record, previous, False)

    receipt = Receipt(rid, spec.publication_id, completed_at, dict(request), len(data))
    record = record_for("verified_changed")
    staged = staged_writes(store)
    bytes_key = receipt_key(spec.publication_id, completed_at, rid)
    if not store.put_if_absent_check(bytes_key, data):
        staged.add(bytes_key, data)
    staged.add(
        capture_record_key(spec.publication_id, completed_at, rid), canonical_json(receipt.as_record())
    )
    if spec.shared:
        link = {
            "publication_id": spec.publication_id,
            "receipt_id": rid,
            "captured_at": completed_at,
            "datasets": spec.link(),
        }
        staged.add(link_record_key(spec.publication_id, completed_at, rid), canonical_json(link))
    staged.add(record.key, record.canonical())
    staged.commit()
    return RunResult(record, receipt, True)


def checked_keys(parsed: Parsed) -> list[tuple[str, str, str]]:
    """Every key the run parsed, with the digest of its value (HIO-ADR-0012 §4.3.3;
    F-REVIEW-2026-10-25-t0009-6). A rate or index is digested as its canonical decimal text, an
    expert-judgement flag as its fallback type under the key `rba.expert_judgement.fallback_type`."""
    keys = {(r.series_id, r.valid_time.isoformat(), value_digest(decimal_str(r.value))) for r in parsed.rows}
    keys |= {
        ("rba.expert_judgement.fallback_type", f.valid_time.isoformat(), value_digest(f.kind))
        for f in parsed.flags
    }
    return sorted(keys)


def missing_keys(
    spec: Publication, keys: list[tuple[str, str, str]], held: list[tuple[str, str, str]]
) -> list[tuple[str, str]]:
    """Keys a response should hold but does not: a series the publication serves with no key at all,
    or a key of the held capture that lies inside the new response's span for its series (on or after
    its first date) and is absent. A key that rolled off the start of a publisher's window is not
    missing; a changed value is a revision, recorded by the vintages, not a missing key."""
    present: dict[str, set[str]] = {}
    for sid, day, _ in keys:
        present.setdefault(sid, set()).add(day)
    missing = [(sid, "*") for d in spec.datasets for sid in d.series if sid not in present]
    for sid, day, _ in held:
        if sid in present and day >= min(present[sid]) and day not in present[sid]:
            missing.append((sid, day))
    return missing
