"""External finality evaluation record (T-0014 P-2; base-camp criterion 4; HIO-ADR-0012 §4.3.3-§4.3.4).

`hio.marketdata.finality` computes C1-C7 and finality as pure answers. This module keeps one such answer,
for the exact inputs of one built release, as a canonical content-addressed record:

    catalogue/finality/<release_id>/<evaluation_sha256>.json

The record is *evidence about* a release, never part of it. It is not in the manifest (the manifest's
content hash would then depend on a judgement made after the release), it is not signed (ADR-0012), and
writing or reading one never touches a manifest or a lifecycle status: a passing record changes no
status, and a missing, unreadable or failing one means there is no final claim (`require_final_claim`).
The record claims only what `finality` computed: it does not make ADR-0012's other finality obligations
met.

The body holds the release hash and cutoff, the evaluator revision, the policy and spec references, every
contributing vintage with its verdict, the C1-C7 outcomes and reasons of each attempt record considered,
the attempt-record ids, references to the retained witnesses (attempt records, receipts and the
provider-assigned write times), and the aggregate verdict. The file's name is the SHA-256 of its own
canonical bytes, so a read recomputes and compares it (a changed record is a different address, never a
silent edit).
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from hio.contracts.canonical import canonical_json, decimal_str, sha256_hex
from hio.contracts.observation import Vintage
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.finality import CHECK_NAMES, FinalityPolicy, RecordEvaluation, ReleaseVerdict, Verdict
from hio.marketdata.runrecord import value_digest
from hio.storage.objectstore import IntegrityError

FORMAT = "hio-finality-evaluation/1"
FINALITY_PREFIX = "catalogue/finality/"
POLICY_REFERENCE = "HIO-ADR-0012 §4.3.3 (C1-C7) and §4.3.4 (finality)"
STATUS_EFFECT = "none: an evaluation labels nothing final and changes no lifecycle status"

_SHA = re.compile(r"^[0-9a-f]{64}$")


class FinalityRecordError(IntegrityError):
    """A finality record that cannot be trusted: wrong address, not canonical, or not about its release."""


class NoFinalClaim(Exception):
    """No verified, passing external finality evaluation exists for the release."""


@dataclass(frozen=True)
class ReleaseRef:
    """The release an evaluation is about: its hash, dataset, cutoff and cited spec."""

    release_id: str
    content_sha256: str
    dataset_id: str
    knowledge_cutoff: datetime
    spec_ref: str

    def __post_init__(self) -> None:
        if not _SHA.match(self.content_sha256) or self.release_id != f"rel-{self.content_sha256}":
            raise ValueError("release_id must be rel-<content_sha256>")
        require_utc_instant("knowledge_cutoff", self.knowledge_cutoff)

    def as_record(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "content_sha256": self.content_sha256,
            "dataset_id": self.dataset_id,
            "knowledge_cutoff": self.knowledge_cutoff,
            "spec_ref": self.spec_ref,
        }


@dataclass(frozen=True)
class VintageEvaluation:
    """One contributing vintage: its verdict at the cutoff and the attempt records evaluated for it."""

    vintage: Vintage
    source_id: str
    w_doc: datetime | None
    verdict: Verdict
    attempts: tuple[RecordEvaluation, ...] = ()


# --- addressing -------------------------------------------------------------------------------------------


def evaluation_sha256(body: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json(body))


def finality_key(release_id: str, evaluation_sha: str) -> str:
    return f"{FINALITY_PREFIX}{release_id}/{evaluation_sha}.json"


# --- building ---------------------------------------------------------------------------------------------


def _reasons(reasons) -> list[dict[str, str]]:
    return [{"code": r.code, "category": r.category, "detail": r.detail} for r in reasons]


def _attempt(ev: RecordEvaluation) -> dict[str, Any]:
    rec = ev.record
    out: dict[str, Any] = {
        "attempt_record": ev.key,
        "record_sha256": ev.key.rsplit("-", 1)[-1].removesuffix(".json"),
        "readable": rec is not None,
        "outcome": rec.outcome if rec else None,
        "receipt_id": rec.receipt_id if rec else None,
        "attempted_at": rec.attempted_at if rec else None,
        "completed_at": rec.completed_at if rec else None,
        "provider_write_time": ev.write_time,
        "passed": ev.passed,
        "failed_checks": list(ev.failed),
        "category": ev.category,
        "checks": [
            {"name": c.name, "passed": c.passed, "category": c.category, "reasons": _reasons(c.reasons)}
            for c in ev.checks
        ],
    }
    return out


def _vintage(e: VintageEvaluation) -> dict[str, Any]:
    v, verdict = e.vintage, e.verdict
    return {
        "series_id": v.series_id,
        "valid_time": v.valid_time,
        "vintage_seq": v.vintage_seq,
        "receipt_id": v.receipt_id,
        "captured_at": v.captured_at,
        "value_digest": value_digest(decimal_str(v.value)),
        "source_id": e.source_id,
        "w_doc": e.w_doc,
        "verdict": {
            "final": verdict.final,
            "category": verdict.category,
            "reasons": list(verdict.reasons),
            "evidence": list(verdict.evidence),
            "quarantine": verdict.quarantine,
        },
        "attempts": [_attempt(a) for a in sorted(e.attempts, key=lambda a: a.key)],
    }


def _check_summary(evaluations: Sequence[VintageEvaluation]) -> dict[str, dict[str, Any]]:
    """Per check, over every distinct attempt record considered: how many were evaluated, how many failed,
    and the failure categories seen. A tally, not a verdict: the aggregate comes from `release_finality`."""
    distinct = {a.key: a for e in evaluations for a in e.attempts}
    out: dict[str, dict[str, Any]] = {}
    for name in CHECK_NAMES:
        checks = [a.check(name) for a in distinct.values()]
        out[name] = {
            "records_evaluated": len(checks),
            "records_failed": sum(1 for c in checks if not c.passed),
            "categories": sorted({c.category for c in checks if c.category}),
        }
    return out


def _policy(policies: Mapping[str, FinalityPolicy]) -> dict[str, Any]:
    return {
        "reference": POLICY_REFERENCE,
        "sources": {
            source: {
                "ci_platform": p.ci_platform,
                "pinned_commit": p.pinned_commit,
                "delta_seconds": p.delta.total_seconds(),
                "epsilon_seconds": p.epsilon.total_seconds(),
            }
            for source, p in sorted(policies.items())
        },
    }


def build_record(
    release: ReleaseRef,
    *,
    evaluator: Mapping[str, str],
    policies: Mapping[str, FinalityPolicy],
    spec_refs: Sequence[str],
    upstream: Sequence[Mapping[str, str]],
    evaluations: Sequence[VintageEvaluation],
    verdict: ReleaseVerdict,
) -> dict[str, Any]:
    """The record body (no hash inside it). `evaluator` is the revision of the code that evaluated (a
    `current_code_ref` mapping). `upstream` lists the releases whose inputs were evaluated with this one's."""
    ordered = sorted(
        evaluations, key=lambda e: (e.vintage.series_id, e.vintage.valid_time, e.vintage.vintage_seq)
    )
    attempts = {a.key: a for e in ordered for a in e.attempts}
    witnesses = [
        {
            "attempt_record": key,
            "receipt_id": a.record.receipt_id if a.record else None,
            "provider_write_time": a.write_time,
        }
        for key, a in sorted(attempts.items())
    ]
    return {
        "format": FORMAT,
        "release": release.as_record(),
        "evaluator": dict(evaluator),
        "policy": _policy(policies),
        "spec_refs": sorted(set(spec_refs)),
        "upstream_releases": sorted((dict(u) for u in upstream), key=canonical_json),
        "vintages": [_vintage(e) for e in ordered],
        "checks": _check_summary(ordered),
        "attempt_record_ids": sorted(attempts),
        "witnesses": witnesses,
        "aggregate": {
            "final": verdict.final,
            "category": verdict.category,
            "cutoff": verdict.cutoff,
            "reasons": list(verdict.reasons),
            "refused": [
                {
                    "series_id": v.series_id,
                    "valid_time": v.valid_time,
                    "vintage_seq": v.vintage_seq,
                    "category": v.category,
                }
                for v in verdict.refused
            ],
            "evidence": list(verdict.evidence),
        },
        "status_effect": STATUS_EFFECT,
    }


# --- storing and reading ----------------------------------------------------------------------------------


def write_record(store, body: Mapping[str, Any]) -> str:
    """Store the record at its content address and return the key. Idempotent: the same evaluation of the
    same inputs is the same bytes at the same key. Writes nothing else; never a manifest."""
    release_id = body["release"]["release_id"]
    key = finality_key(release_id, evaluation_sha256(body))
    store.put_if_absent(key, canonical_json(body))
    return key


@dataclass(frozen=True)
class LoadedRecord:
    key: str
    evaluation_sha256: str
    body: dict[str, Any]

    @property
    def final(self) -> bool:
        return self.body["aggregate"]["final"] is True


def load_record(store, release_id: str, evaluation_sha: str) -> LoadedRecord:
    """Read a record and verify its address: the bytes hash to the name, are canonical, name this release,
    and the release id agrees with the release hash. Anything else raises `FinalityRecordError`."""
    key = finality_key(release_id, evaluation_sha)
    data = store.get(key)
    if sha256_hex(data) != evaluation_sha:
        raise FinalityRecordError(f"finality record does not match its content address: {key}")
    try:
        body = json.loads(data)
        release = body["release"]
    except (ValueError, KeyError, TypeError) as exc:
        raise FinalityRecordError(f"finality record is not readable: {key}") from exc
    if canonical_json(body) != data:
        raise FinalityRecordError(f"finality record is not in canonical form: {key}")
    if body.get("format") != FORMAT:
        raise FinalityRecordError(f"unknown finality record format: {key}")
    if release.get("release_id") != release_id or release_id != f"rel-{release.get('content_sha256')}":
        raise FinalityRecordError(f"finality record is not about {release_id}: {key}")
    return LoadedRecord(key, evaluation_sha, body)


def record_shas(store, release_id: str) -> list[str]:
    prefix = f"{FINALITY_PREFIX}{release_id}/"
    return sorted(k[len(prefix) :].removesuffix(".json") for k in store.list(prefix) if k.endswith(".json"))


def verified_records(store, release_id: str) -> list[LoadedRecord]:
    """Every record of the release that reads back under its address; an unreadable one is skipped
    (it is not evidence)."""
    out = []
    for sha in record_shas(store, release_id):
        try:
            out.append(load_record(store, release_id, sha))
        except Exception:
            continue
    return out


def require_final_claim(store, release_id: str) -> LoadedRecord:
    """The evaluation that supports a final claim about `release_id`, or `NoFinalClaim`. Fail closed: no
    record, only unreadable or tampered records, or only failing evaluations, is no claim. A returned
    record changes no status; it is the evidence a caller may cite."""
    records = verified_records(store, release_id)
    passing = [r for r in records if r.final]
    if not passing:
        raise NoFinalClaim(
            f"{release_id}: no passing external finality evaluation "
            f"({len(records)} verified, {len(record_shas(store, release_id))} stored)"
        )
    return passing[0]
