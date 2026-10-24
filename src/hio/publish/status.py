"""Writing and resolving status events (releases standard §5, §7).

Transition authority (§5): the producing job may set exploratory once invariants pass;
validated, approved_for_consumer(C) and withdrawn are the owner's actions. Approval for a
class also runs the publish rights gate for that class first.
"""

from __future__ import annotations

import json
from datetime import datetime

from hio.contracts.canonical import canonical_json
from hio.contracts.observation import parse_instant
from hio.contracts.rights import Operation, RightsGate
from hio.contracts.status import LEVEL, Status, StatusError, StatusEvent, effective_status
from hio.publish.release import verify_release
from hio.storage.objectstore import LocalObjectStore

OWNER_ONLY = {
    Status.VALIDATED,
    Status.APPROVED_FOR_CONSUMER,
    Status.WITHDRAWN,
    Status.SUPERSEDED,
    Status.DEPRECATED,
}


def events(store: LocalObjectStore, sha: str) -> list[StatusEvent]:
    out = []
    for key in store.list(f"catalogue/status/{sha}/"):
        r = json.loads(store.get(key))
        out.append(
            StatusEvent(
                r["content_sha256"],
                r["seq"],
                Status(r["status"]),
                r["actor"],
                r["evidence"],
                parse_instant(r["at"]),
                r["consumer_class"],
            )
        )
    return out


def append_status(
    store: LocalObjectStore,
    sha: str,
    status: Status,
    actor: str,
    evidence: str,
    at: datetime,
    *,
    gate: RightsGate | None = None,
    source_ids: tuple[str, ...] = (),
    consumer_class: str | None = None,
) -> StatusEvent:
    if status in OWNER_ONLY and actor != "owner":
        raise PermissionError(f"{status.value} is an owner action, not {actor!r}")
    if status is Status.APPROVED_FOR_CONSUMER:
        if gate is None:
            raise StatusError("approval for a consumer class needs the publish rights gate")
        gate.authorise(Operation.PUBLISH, source_ids, consumer_class)
    existing = events(store, sha)
    event = StatusEvent(sha, len(existing) + 1, status, actor, evidence, at, consumer_class)
    effective_status([*existing, event])  # validates seq and withdrawal precedence before writing
    store.put(f"catalogue/status/{sha}/{event.seq:06d}.json", canonical_json(event.as_record()))
    return event


class RefusedUse(Exception):
    pass


def resolve_for_use(
    store: LocalObjectStore,
    dataset_id: str,
    sha: str,
    *,
    required: Status,
    consumer_class: str,
    gate: RightsGate,
    source_ids: tuple[str, ...],
) -> dict:
    """A pinned consumer's check at each use (§7): bytes verify; the effective status is not
    withdrawn and is at least `required`; the CURRENT rights allow the class."""
    core = verify_release(store, dataset_id, sha)
    current = effective_status(events(store, sha))
    if current is None:
        raise RefusedUse("no status")
    if current.status is Status.WITHDRAWN:
        raise RefusedUse("withdrawn")
    if LEVEL[current.status] < LEVEL[required]:
        raise RefusedUse(f"status {current.status.value} is below {required.value}")
    gate.authorise(Operation.PUBLISH, source_ids, consumer_class)
    return core
