"""Capture-run records (HIO-ADR-0012 §4.3.3, staged by OD-0063 and T-0009 §4).

One write-once record per capture run of a dataset, including a re-fetch that found no change
(which `capture()` deliberately writes nothing for) and a run that failed. It keeps what cannot be
reconstructed later: that the check happened and when, the publisher's own response headers as
received, the exact request, the hash and length of the body, and the identity of the run.

Staged scope (OD-0063): the records are written in full. The C1-C7 completion checks and finality
(§4.3.4) are **not** implemented here and remain owed. `outcome` is the adapter's own assertion
(it parsed the body and compared it with the held capture); a `verified_*` outcome is NOT completion
evidence and does not make any release final. The record assigns no publication time.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.layout import attempt_record_key
from hio.contracts.observation import parse_instant
from hio.contracts.temporal import require_utc_instant
from hio.storage.objectstore import IntegrityError, LocalObjectStore

OUTCOMES = ("verified_changed", "verified_unchanged", "failed")
ERROR_CLASSES = ("network", "http_status", "parse", "schema", "clock_order", "store")
WITHHELD = "[withheld]"
_WITHHELD_HEADERS = {"set-cookie", "authorization", "proxy-authenticate", "www-authenticate"}


@dataclass(frozen=True)
class Execution:
    """Who ran the capture. Copied unaltered from the CI environment; any other run is 'other'."""

    platform: str
    run_id: str | None = None
    run_attempt: str | None = None
    job: str | None = None
    sha: str | None = None

    @classmethod
    def from_environ(cls, env: Mapping[str, str]) -> Execution:
        if env.get("GITHUB_ACTIONS") != "true":
            return cls("other")
        return cls(
            "github_actions",
            env.get("GITHUB_RUN_ID"),
            env.get("GITHUB_RUN_ATTEMPT"),
            env.get("GITHUB_JOB"),
            env.get("GITHUB_SHA"),
        )

    def as_record(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "run_id": self.run_id,
            "run_attempt": self.run_attempt,
            "job": self.job,
            "sha": self.sha,
        }


def envelope_headers(headers: Sequence[tuple[str, str]]) -> list[list[str]]:
    """Every response header, in order, as received. Only credential-bearing values are withheld."""
    return [[n, WITHHELD if n.lower() in _WITHHELD_HEADERS else v] for n, v in headers]


@dataclass(frozen=True)
class RunRecord:
    source_id: str  # the publication: the file that was fetched
    execution: Execution
    request: Mapping[str, Any]  # method, url, final_url, user_agent
    status: int | None
    headers: Sequence[Sequence[str]]  # [[name, value], ...] as received
    response_sha256: str | None
    response_bytes: int | None
    attempted_at: datetime
    completed_at: datetime
    outcome: str
    receipt_id: str | None = None
    error_class: str | None = None
    slot: str | None = None  # the intended slot, e.g. "first" or "final"
    slot_due_at: datetime | None = None
    datasets: Sequence[str] = ()  # the datasets this publication serves (rights subjects), if shared

    def __post_init__(self) -> None:
        object.__setattr__(self, "datasets", tuple(self.datasets))
        require_utc_instant("attempted_at", self.attempted_at)
        require_utc_instant("completed_at", self.completed_at)
        if self.completed_at < self.attempted_at:
            raise ValueError("completed_at precedes attempted_at")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {self.outcome!r}")
        if self.outcome == "failed":
            if self.error_class not in ERROR_CLASSES:
                raise ValueError("a failed run needs an error class")
            if self.receipt_id is not None:
                raise ValueError("a failed run has no receipt")
        elif self.receipt_id is None or self.response_sha256 is None:
            raise ValueError("a successful run names its receipt and body hash")
        elif self.receipt_id != self.response_sha256:
            raise ValueError("receipt id must equal the response body hash")

    def as_record(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "execution": self.execution.as_record(),
            "request": dict(self.request),
            "response_envelope": {"status": self.status, "headers": [list(h) for h in self.headers]},
            "response_sha256": self.response_sha256,
            "response_bytes": self.response_bytes,
            "attempted_at": self.attempted_at,
            "completed_at": self.completed_at,
            "outcome": self.outcome,
            "receipt_id": self.receipt_id,
            "error_class": self.error_class,
            "slot": self.slot,
            "slot_due_at": self.slot_due_at,
            "datasets": list(self.datasets),
        }

    def canonical(self) -> bytes:
        return canonical_json(self.as_record())

    @property
    def record_sha256(self) -> str:
        return sha256_hex(self.canonical())

    @property
    def key(self) -> str:
        return attempt_record_key(self.source_id, self.attempted_at, self.record_sha256)


def load_run_record(store: LocalObjectStore, key: str) -> RunRecord:
    """Read a record back, recomputing its content hash and comparing it with the key."""
    data = store.get(key)
    rec = _decode(data)
    if rec.key != key or sha256_hex(rec.canonical()) != key.rsplit("-", 1)[-1].removesuffix(".json"):
        raise IntegrityError(f"capture-run record does not match its key: {key}")
    if rec.canonical() != data:
        raise IntegrityError(f"capture-run record is not in canonical form: {key}")
    return rec


def _decode(data: bytes) -> RunRecord:
    r = json.loads(data)
    env = r["response_envelope"]
    return RunRecord(
        source_id=r["source_id"],
        execution=Execution(**r["execution"]),
        request=r["request"],
        status=env["status"],
        headers=env["headers"],
        response_sha256=r["response_sha256"],
        response_bytes=r["response_bytes"],
        attempted_at=parse_instant(r["attempted_at"]),
        completed_at=parse_instant(r["completed_at"]),
        outcome=r["outcome"],
        receipt_id=r["receipt_id"],
        error_class=r["error_class"],
        slot=r["slot"],
        slot_due_at=parse_instant(r["slot_due_at"]) if r["slot_due_at"] else None,
        datasets=tuple(r["datasets"]),
    )
