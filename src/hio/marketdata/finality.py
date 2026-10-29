"""Completion checks C1-C7 and finality (HIO-ADR-0012 §4.3.3 and §4.3.4, fail closed; T-0010 W-4).

Pure, deterministic functions over what HIO retains: the capture-run records
(`catalogue/attempts/<source_id>/…`, `hio.marketdata.runrecord`), the capture records and receipt
bytes, the vintages, and the object store's own provider-assigned write time. Nothing here writes, labels
or approves anything: a `Verdict` is a computed answer for one vintage at one cutoff, not a status. No
release is labelled final by this module (T-0010 A-9); a caller that wants a release verdict passes the
input vintages' verdicts to `release_finality`.

Fail closed. Any missing field, unreadable record, unparseable header or absent witness is *not
evidence*: the corresponding check fails and says why. A record is completion evidence only if every
check passes. The checks that need `W_doc(k)` (C4, C5) take it from the caller for the key of interest;
a missing `W_doc` fails them.

The series schema (how a stored body is turned into `(series_id, valid_time, digest)` keys, C3) is
injected as `FinalityPolicy.parse_keys`, because `hio.marketdata` may not import the source adapters.

Refusal categories (§4.3.4): missing, failed, delayed, inconsistent, unverified. Each failed check
carries the category of its failure; a record or verdict reports the most severe one, in the order
unverified > inconsistent > failed > delayed > missing.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

from hio.contracts.canonical import decimal_str
from hio.contracts.layout import ATTEMPTS_PREFIX, CAPTURES_PREFIX
from hio.contracts.observation import Receipt, Vintage
from hio.contracts.temporal import require_utc_instant
from hio.marketdata.capture import load_receipt_record, receipt_bytes
from hio.marketdata.runrecord import (
    CAPTURE_EVENTS,
    CAPTURE_REF,
    CAPTURE_WORKFLOW_SUFFIX,
    Execution,
    RunRecord,
    load_run_record,
    value_digest,
)
from hio.storage.objectstore import IntegrityError

CHECK_NAMES = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")
MISSING, FAILED, DELAYED, INCONSISTENT, UNVERIFIED = (
    "missing",
    "failed",
    "delayed",
    "inconsistent",
    "unverified",
)
CATEGORIES = (MISSING, FAILED, DELAYED, INCONSISTENT, UNVERIFIED)
_SEVERITY = (UNVERIFIED, INCONSISTENT, FAILED, DELAYED, MISSING)  # most severe first

DEFAULT_DELTA = timedelta(minutes=10)  # ADR-0012 §4.3.3, proposed
DEFAULT_EPSILON = timedelta(minutes=2)

_RUN_NUMBER = re.compile(r"^[1-9][0-9]{0,19}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")

KeyDigest = tuple[str, str, str]  # (series_id, valid_time as ISO text, digest)


@dataclass(frozen=True)
class Reason:
    code: str
    category: str
    detail: str = ""


@dataclass(frozen=True)
class Check:
    name: str
    reasons: tuple[Reason, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.reasons

    @property
    def category(self) -> str | None:
        return _worst(r.category for r in self.reasons)


@dataclass(frozen=True)
class FinalityPolicy:
    """What the checks are measured against. `code_ref` is the pinned adapter code reference: the
    mapping `hio.jobs.s1a.current_code_ref` returns (its `commit`), or the commit text itself."""

    ci_platform: str
    code_ref: Mapping[str, str] | str
    parse_keys: Callable[[bytes], Iterable[Sequence[str]]]
    delta: timedelta = DEFAULT_DELTA
    epsilon: timedelta = DEFAULT_EPSILON

    @property
    def pinned_commit(self) -> str | None:
        commit = self.code_ref if isinstance(self.code_ref, str) else self.code_ref.get("commit")
        return commit if isinstance(commit, str) and _COMMIT.match(commit) else None


@dataclass(frozen=True)
class RecordEvaluation:
    """C1-C7 for one attempt record, in order. `record` is None when C1 could not read it."""

    key: str
    record: RunRecord | None
    checks: tuple[Check, ...]
    write_time: datetime | None = None  # the provider-assigned write time s, if the store supplied one

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.checks if not c.passed)

    @property
    def category(self) -> str | None:
        return _worst(c.category for c in self.checks)

    def check(self, name: str) -> Check:
        return next(c for c in self.checks if c.name == name)

    def digests(self) -> dict[tuple[str, str], str]:
        """key -> digest, from the record's keys_checked (empty for an unreadable or failed record)."""
        if self.record is None or self.record.keys_checked is None:
            return {}
        return {(k[0], k[1]): k[2] for k in self.record.keys_checked}


@dataclass(frozen=True)
class Verdict:
    """Finality of one vintage at one cutoff (§4.3.4). `final` is a computed answer, not a label.
    `evidence` holds the keys of the attempt records that make it final; `quarantine` is set when
    two records disagree about the key's value (owner review, §4.3.4)."""

    series_id: str
    valid_time: str
    vintage_seq: int
    cutoff: datetime
    final: bool
    category: str | None
    reasons: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    quarantine: bool = False


@dataclass(frozen=True)
class ReleaseVerdict:
    """A release is final only if every input vintage is final at its knowledge_cutoff (§4.3.4)."""

    cutoff: datetime
    final: bool
    category: str | None
    refused: tuple[Verdict, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()  # attempt-record keys, to be recorded among the release's inputs


def _worst(categories: Iterable[str]) -> str | None:
    found = set(categories)
    return next((c for c in _SEVERITY if c in found), None)


# --- record evaluation ----------------------------------------------------------------------------------


def evaluate_records(
    store,
    source_id: str,
    policy: FinalityPolicy,
    *,
    w_doc: datetime | None,
    vintages: Iterable[Vintage] = (),
) -> list[RecordEvaluation]:
    """Evaluate C1-C7 for every attempt record of `source_id`, in key order. `w_doc` is the documented
    window close of the key of interest (None fails C4 and C5). `vintages` are the held vintages C3
    compares with. `store` is a `LocalObjectStore` or `BlobObjectStore`; a store with no
    `write_time` cannot pass C5."""
    if w_doc is not None:
        require_utc_instant("w_doc", w_doc)
    loaded = {
        key: _load(store, key, source_id) for key in sorted(store.list(f"{ATTEMPTS_PREFIX}{source_id}/"))
    }
    claims = Counter(
        _execution_claim(rec) for rec, _ in loaded.values() if rec is not None and _execution_claim(rec)
    )
    captures = _captures(store, source_id)
    held = _held_index(vintages)
    out = []
    for key, (rec, c1) in loaded.items():
        if rec is None:
            unread = Reason(
                "record_unavailable", c1[0].category, "not evaluated: the record could not be read"
            )
            out.append(
                RecordEvaluation(
                    key, None, (Check("C1", c1), *(Check(n, (unread,)) for n in CHECK_NAMES[1:]))
                )
            )
            continue
        c2, body = _c2(store, rec, captures)
        s, c5 = _c5(store, key, rec, w_doc, policy)
        checks = (
            Check("C1", c1),
            Check("C2", c2),
            Check("C3", _c3(rec, body, held, policy)),
            Check("C4", _c4(rec, w_doc, policy)),
            Check("C5", c5),
            Check("C6", _c6(rec, policy)),
            Check("C7", _c7(rec, claims)),
        )
        out.append(RecordEvaluation(key, rec, checks, s))
    return out


def _load(store, key: str, source_id: str) -> tuple[RunRecord | None, tuple[Reason, ...]]:
    """C1: the record reads back under its own key with the content hash recomputed, from the stored
    version (a store that finds more than one version refuses), and belongs to this source."""
    try:
        rec = load_run_record(store, key)
    except Exception as exc:
        category = INCONSISTENT if isinstance(exc, IntegrityError) else MISSING
        return None, (Reason("record_unreadable", category, f"{type(exc).__name__}: {exc}"),)
    if rec.source_id != source_id:
        return None, (Reason("wrong_source", INCONSISTENT, f"{rec.source_id} under {source_id}"),)
    return rec, ()


def _execution_claim(rec: RunRecord) -> tuple[str, str, str, str] | None:
    e = rec.execution
    if e.run_id is None or e.run_attempt is None:
        return None
    return (e.platform, e.run_id, e.run_attempt, rec.source_id)


def _captures(store, source_id: str) -> list[Receipt]:
    out = []
    for key in sorted(store.list(f"{CAPTURES_PREFIX}{source_id}/")):
        try:
            out.append(load_receipt_record(store, key))
        except Exception:
            continue
    return out


def _c2(store, rec: RunRecord, captures: list[Receipt]) -> tuple[tuple[Reason, ...], bytes | None]:
    """Response binding: the response hash is the referenced receipt's id, and the receipt's stored
    bytes re-hash to it. A changed run names the capture made at its completion; an unchanged run
    names a capture held before it."""
    if rec.outcome == "failed":
        return (Reason("failed_record", FAILED, rec.error_class or ""),), None
    if rec.response_sha256 is None or rec.receipt_id != rec.response_sha256:
        return (Reason("receipt_not_bound", MISSING, "response_sha256 is not the receipt id"),), None
    if rec.outcome == "verified_changed":
        named = [c for c in captures if c.receipt_id == rec.receipt_id and c.captured_at == rec.completed_at]
    else:
        named = [c for c in captures if c.receipt_id == rec.receipt_id and c.captured_at <= rec.attempted_at]
    if not named:
        return (Reason("no_capture_record", MISSING, f"no held capture of {rec.receipt_id}"),), None
    try:
        body = receipt_bytes(store, max(named, key=lambda c: c.captured_at))
    except Exception as exc:
        return (Reason("receipt_bytes", INCONSISTENT, f"{type(exc).__name__}: {exc}"),), None
    if rec.response_bytes != len(body):
        return (Reason("length_mismatch", INCONSISTENT, f"{rec.response_bytes} != {len(body)}"),), None
    return (), body


def _held_index(vintages: Iterable[Vintage]) -> dict[tuple[str, str], list[tuple[datetime, int, str]]]:
    idx: dict[tuple[str, str], list[tuple[datetime, int, str]]] = {}
    for v in vintages:
        idx.setdefault((v.series_id, v.valid_time.isoformat()), []).append(
            (v.captured_at, v.vintage_seq, value_digest(decimal_str(v.value)))
        )
    return idx


def _c3(
    rec: RunRecord,
    body: bytes | None,
    held: dict[tuple[str, str], list[tuple[datetime, int, str]]],
    policy: FinalityPolicy,
) -> tuple[Reason, ...]:
    """Content: parsing the stored bytes reproduces each keys_checked digest, and each equals the
    digest of the vintage HIO held for that key when the run completed (the new vintage, for a
    changed run)."""
    if rec.outcome == "failed":
        return (Reason("failed_record", FAILED, rec.error_class or ""),)
    if body is None:
        return (Reason("no_verified_bytes", MISSING, "C2 did not produce the stored bytes"),)
    try:
        parsed = {(k[0], k[1]): k[2] for k in policy.parse_keys(body)}
    except Exception as exc:
        return (Reason("parse_failed", FAILED, f"{type(exc).__name__}: {exc}"),)
    reasons = []
    for sid, vt, digest in rec.keys_checked or ():
        if (sid, vt) not in parsed:
            reasons.append(Reason("key_not_in_body", FAILED, f"{sid} {vt}"))
        elif parsed[(sid, vt)] != digest:
            reasons.append(Reason("digest_not_reproduced", INCONSISTENT, f"{sid} {vt}"))
        at_completion = sorted(h for h in held.get((sid, vt), []) if h[0] <= rec.completed_at)
        if not at_completion:
            reasons.append(Reason("no_held_vintage", MISSING, f"{sid} {vt}"))
        elif at_completion[-1][2] != digest:
            reasons.append(Reason("held_value_differs", INCONSISTENT, f"{sid} {vt}"))
    if not rec.keys_checked:
        reasons.append(Reason("no_keys_checked", MISSING))
    return tuple(reasons)


def _date_header(rec: RunRecord) -> tuple[datetime | None, tuple[Reason, ...]]:
    dates = [h[1] for h in rec.headers if len(h) == 2 and h[0].strip().lower() == "date"]
    if not dates:
        return None, (Reason("date_missing", MISSING),)
    if len(dates) > 1:
        return None, (Reason("date_repeated", INCONSISTENT, f"{len(dates)} Date headers"),)
    try:
        parsed = parsedate_to_datetime(dates[0])
    except (TypeError, ValueError, IndexError):
        return None, (Reason("date_unparseable", MISSING, dates[0]),)
    if parsed.tzinfo is None:
        return None, (Reason("date_without_zone", MISSING, dates[0]),)
    return parsed.astimezone(UTC), ()


def _c4(rec: RunRecord, w_doc: datetime | None, policy: FinalityPolicy) -> tuple[Reason, ...]:
    """Freshness: `Date` (the origin server's clock at generation) is present, parses, is not before
    W_doc, and −ε ≤ completed_at − Date ≤ δ."""
    if rec.outcome == "failed":
        return (Reason("failed_record", FAILED, rec.error_class or ""),)
    date, reasons = _date_header(rec)
    if date is None:
        return reasons
    out = []
    if w_doc is None:
        out.append(Reason("w_doc_missing", MISSING))
    elif date < w_doc:
        out.append(Reason("date_precedes_window", DELAYED, f"Date {date:%H:%M:%S} < W_doc {w_doc:%H:%M:%S}"))
    lag = rec.completed_at - date
    if lag < -policy.epsilon:
        out.append(Reason("date_after_completion", INCONSISTENT, f"completed_at - Date = {lag}"))
    elif lag > policy.delta:
        out.append(Reason("date_too_old", DELAYED, f"completed_at - Date = {lag}"))  # stale, no conflict
    return tuple(out)


def _c5(
    store, key: str, rec: RunRecord, w_doc: datetime | None, policy: FinalityPolicy
) -> tuple[datetime | None, tuple[Reason, ...]]:
    """Timing: W_doc ≤ attempted_at ≤ completed_at, and the provider-assigned write time s satisfies
    completed_at ≤ s ≤ completed_at + δ. A store that cannot supply s fails this check."""
    out = []
    if w_doc is None:
        out.append(Reason("w_doc_missing", MISSING))
    elif rec.attempted_at < w_doc:
        out.append(Reason("attempted_before_window", DELAYED, f"{rec.attempted_at} < W_doc {w_doc}"))
    if rec.completed_at < rec.attempted_at:
        out.append(Reason("completed_before_attempted", INCONSISTENT))
    write_time = getattr(store, "write_time", None)
    s: datetime | None = None
    if write_time is None:
        out.append(Reason("no_provider_write_time", UNVERIFIED, "the store cannot supply a write time"))
    else:
        try:
            s = write_time(key)
            require_utc_instant("write_time", s)
        except Exception as exc:
            s = None
            out.append(Reason("write_time_unavailable", UNVERIFIED, f"{type(exc).__name__}: {exc}"))
    if s is not None:
        if s < rec.completed_at:
            out.append(Reason("written_before_completion", INCONSISTENT, f"s {s} < completed_at"))
        elif s > rec.completed_at + policy.delta:
            out.append(Reason("written_too_late", INCONSISTENT, f"s - completed_at = {s - rec.completed_at}"))
    return s, tuple(out)


def _c6(rec: RunRecord, policy: FinalityPolicy) -> tuple[Reason, ...]:
    """Execution binding: the platform is the CI platform (`other` is a manual or local run), the sha
    is the pinned code_ref, the run identifiers are well formed, and the run is of the capture workflow
    on main, scheduled or dispatched."""
    e = rec.execution
    out = []
    if e.platform == "other" or policy.ci_platform in ("", "other"):
        out.append(Reason("platform_other", UNVERIFIED, "a manual or local run is not CI-witnessed"))
    elif e.platform != policy.ci_platform:
        out.append(Reason("platform_mismatch", INCONSISTENT, f"{e.platform} != {policy.ci_platform}"))
    pinned = policy.pinned_commit
    if pinned is None:
        out.append(Reason("code_ref_not_pinned", UNVERIFIED, "the pinned code_ref is not a 40-hex commit"))
    elif e.sha is None:
        out.append(Reason("sha_missing", MISSING))
    elif e.sha != pinned:
        out.append(Reason("sha_not_code_ref", INCONSISTENT, f"{e.sha} != {pinned}"))
    for name, value in (("run_id", e.run_id), ("run_attempt", e.run_attempt)):
        if value is None:
            out.append(Reason(f"{name}_missing", MISSING))
        elif not _RUN_NUMBER.match(value):
            out.append(Reason(f"{name}_malformed", INCONSISTENT, repr(value)))
    if not e.job:
        out.append(Reason("job_missing", MISSING))
    out.extend(_capture_workflow_reasons(e))
    return tuple(out)


def _capture_workflow_reasons(e: Execution) -> list[Reason]:
    """The run is of the capture workflow on main, started by a schedule or a dispatch (§4.3.3). A
    run of another workflow in the same repository is not completion evidence
    (F-REVIEW-2026-10-29-t0010-1-2). An absent field, as in a record written before the fields
    existed, fails closed."""
    out = []
    if not e.workflow_ref:
        out.append(Reason("workflow_ref_missing", MISSING))
    elif not e.workflow_ref.endswith(CAPTURE_WORKFLOW_SUFFIX):
        out.append(Reason("workflow_not_capture", UNVERIFIED, f"workflow_ref {e.workflow_ref!r}"))
    if not e.ref:
        out.append(Reason("ref_missing", MISSING))
    elif e.ref != CAPTURE_REF:
        out.append(Reason("ref_not_main", UNVERIFIED, f"ref {e.ref!r}"))
    if not e.event:
        out.append(Reason("event_missing", MISSING))
    elif e.event not in CAPTURE_EVENTS:
        out.append(Reason("event_not_scheduled_or_dispatched", UNVERIFIED, f"event {e.event!r}"))
    return out


def _c7(rec: RunRecord, claims: Counter) -> tuple[Reason, ...]:
    """Uniqueness over (platform, run_id, run_attempt, source_id)."""
    claim = _execution_claim(rec)
    if claim is None:
        return (Reason("no_execution_identity", MISSING, "run_id or run_attempt absent"),)
    if claims[claim] > 1:
        return (Reason("execution_claimed_twice", INCONSISTENT, f"{claims[claim]} records claim {claim}"),)
    return ()


# --- finality -------------------------------------------------------------------------------------------


def vintage_finality(
    store,
    source_id: str,
    vintage: Vintage,
    vintages: Iterable[Vintage],
    cutoff: datetime,
    *,
    w_doc: datetime | None,
    policy: FinalityPolicy,
) -> Verdict:
    """Is `vintage` final at `cutoff` (§4.3.4)? `vintages` are the held vintages of the dataset (they
    include `vintage`); `w_doc` is W_doc for the vintage's key. All of: (1) an attempt record with
    outcome verified_changed or verified_unchanged covering the key passes C1-C7, with
    W_doc ≤ attempted_at and s ≤ cutoff; (2) its value for the key equals the vintage's; (3) no later
    vintage of the key has captured_at ≤ cutoff. Otherwise the verdict names the refusal category."""
    require_utc_instant("cutoff", cutoff)
    held = list(vintages)
    k = (vintage.series_id, vintage.valid_time.isoformat())

    def refuse(category: str, *reasons: str, quarantine: bool = False) -> Verdict:
        return Verdict(*k, vintage.vintage_seq, cutoff, False, category, reasons, quarantine=quarantine)

    if vintage.captured_at > cutoff:
        return refuse(MISSING, "vintage_not_captured_by_cutoff")
    if any(
        (v.series_id, v.valid_time.isoformat()) == k
        and v.vintage_seq > vintage.vintage_seq
        and v.captured_at <= cutoff
        for v in held
    ):
        return refuse(INCONSISTENT, "superseded: a later vintage of the key has captured_at <= cutoff")
    if w_doc is None:
        return refuse(MISSING, "w_doc_missing: the dataset declares no window close for the key")

    evals = evaluate_records(store, source_id, policy, w_doc=w_doc, vintages=held)
    covering = [
        e for e in evals if e.record is not None and e.record.outcome != "failed" and k in e.digests()
    ]
    if not covering:
        failed_after = [
            e
            for e in evals
            if e.record is not None and e.record.outcome == "failed" and e.record.attempted_at >= w_doc
        ]
        unreadable = [e for e in evals if e.record is None]
        notes = [f"unreadable attempt record: {e.key}" for e in unreadable]
        if failed_after:
            return refuse(
                FAILED, "only failed attempts since W_doc: " + ", ".join(e.key for e in failed_after), *notes
            )
        return refuse(MISSING, "no attempt record covers the key", *notes)

    in_window = [
        e
        for e in covering
        if e.record is not None
        and e.record.attempted_at >= w_doc
        and (e.write_time is None or e.write_time <= cutoff)
    ]
    if len({e.digests()[k] for e in in_window}) > 1:
        return refuse(
            INCONSISTENT,
            "records for the key since W_doc disagree about its value (quarantine pending owner review): "
            + ", ".join(e.key for e in in_window),
            quarantine=True,
        )

    want = value_digest(decimal_str(vintage.value))
    issues = {e.key: _issues(e, k, want, cutoff) for e in covering}
    good = [e for e in covering if not issues[e.key]]
    if good:
        return Verdict(*k, vintage.vintage_seq, cutoff, True, None, (), tuple(sorted(e.key for e in good)))
    best = min(covering, key=lambda e: (len(issues[e.key]), e.key))
    chosen = issues[best.key]
    return refuse(
        _worst(r.category for r in chosen) or MISSING,
        *(f"{best.key}: {r.code} {r.detail}".rstrip() for r in chosen),
    )


def _issues(e: RecordEvaluation, k: tuple[str, str], want: str, cutoff: datetime) -> list[Reason]:
    """Everything that stops record `e` supporting the vintage at `cutoff`. A record stored after the
    cutoff did not exist then: its only issue is that it may support a later cutoff."""
    if e.write_time is not None and e.write_time > cutoff:
        return [Reason("stored_after_cutoff", DELAYED, f"s {e.write_time} > cutoff")]
    out = [r for c in e.checks for r in c.reasons]
    if e.digests()[k] != want:
        out.append(Reason("value_differs_from_vintage", INCONSISTENT, "condition 2"))
    return out


def release_finality(verdicts: Sequence[Verdict], cutoff: datetime) -> ReleaseVerdict:
    """A release is final only if every input vintage it uses is final at the release's
    knowledge_cutoff. No inputs, or a verdict computed for another cutoff, is not final."""
    require_utc_instant("cutoff", cutoff)
    if not verdicts:
        return ReleaseVerdict(cutoff, False, MISSING, reasons=("no input vintages: nothing is established",))
    wrong = [v for v in verdicts if v.cutoff != cutoff]
    if wrong:
        return ReleaseVerdict(
            cutoff,
            False,
            INCONSISTENT,
            tuple(wrong),
            tuple(
                f"verdict for {v.series_id} {v.valid_time} #{v.vintage_seq} is for cutoff {v.cutoff}"
                for v in wrong
            ),
        )
    refused = tuple(v for v in verdicts if not v.final)
    if refused:
        return ReleaseVerdict(
            cutoff,
            False,
            _worst(v.category for v in refused if v.category),
            refused,
            tuple(f"{v.series_id} {v.valid_time} #{v.vintage_seq}: {v.category}" for v in refused),
        )
    return ReleaseVerdict(
        cutoff, True, None, evidence=tuple(sorted({e for v in verdicts for e in v.evidence}))
    )
