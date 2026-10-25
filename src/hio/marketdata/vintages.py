"""The vintage store: append-on-change recording, quality gates, quality decisions and owner
conflict resolutions (observations standard §1, §6, §7; OBS-AMEND-Q001 revision 4 and
OBS-AMEND-Q002 revision 5, approved by OD-0029 and OD-0030).

Records are append-only JSON objects in the object store:
    catalogue/vintages/<series_id>/<valid_time>/<vintage_seq>.json
    catalogue/quality/<series_id>/<valid_time>/<vintage_seq>/<event_seq>.json
    catalogue/resolutions/<series_id>/<conflict_id>/<decided_at>-<sha256>.json
    catalogue/quarantine/receipts/<receipt_id>.json
Conflicts are derived from the evidence on every query and never stored. The in-memory state is
rebuilt from the records, so a reload gives identical query results.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from hio.contracts.canonical import canonical_json, instant_str, sha256_hex
from hio.contracts.layout import CAPTURES_PREFIX
from hio.contracts.observation import Receipt, Vintage, parse_instant
from hio.contracts.temporal import KnowledgeMode, QualityStatus, require_utc_instant
from hio.marketdata.capture import capture_record_key, load_receipt, load_receipt_record, receipt_bytes
from hio.marketdata.knowability import determine
from hio.marketdata.parse import MalformedReceipt, RawRow, parse_receipt
from hio.marketdata.queries import (
    Conflict,
    Resolution,
    View,
    canonical_value,
    conflict_chain,
    derive_conflicts,
    effective_quality_cutoff,
    resolutions_in_force,
    select,
    status_at,
)
from hio.marketdata.series import CaptureMode, SeriesDef
from hio.storage.objectstore import IntegrityError, LocalObjectStore, StagedWrites


class ReceiptIntegrityError(Exception):
    """A selected vintage's receipt is missing, or its bytes do not match their hash (OBS-INV-004).
    The view fails closed: nothing built on it can be produced (F-REVIEW-2026-10-24-s1a-1-3)."""


class IncompleteProcessing(Exception):
    """Some captured evidence dated <= Q is not reflected in the processed vintages, so no result
    or resolution at Q can be established (OBS-INV-019). Nothing partial is returned."""


class PinMismatch(Exception):
    """A recorded reproducibility pin, or a recorded input reference, differs from the inputs
    reconstructed independently from the store (OBS-INV-018, OBS-AMEND-Q002-R1). Refused; the
    recorded result is never silently replaced."""


class DecisionRefused(ValueError):
    """A quality decision or resolution that the decision-clock rules forbid (OBS-INV-012 and the
    Q-002 refusals). The store is unchanged."""


# Only the gate's own rules or the owner may release a quarantined vintage (§6). An agent may
# propose; it may not decide.
RELEASE_ACTORS = frozenset({"owner", "gate"})
# Only the owner may resolve a conflict in S1a (OBS-AMEND-Q002 §3).
RESOLUTION_ACTORS = frozenset({"owner"})
RESOLUTIONS_PREFIX = "catalogue/resolutions/"
PROCESSED_PREFIX = "catalogue/processed/"
QUALITY_DIGEST_SCHEMA = "hio-quality-digest/1"


@dataclass
class IngestResult:
    new_vintages: list[Vintage] = field(default_factory=list)
    redundant: int = 0
    revisions: list[tuple[str, date, Decimal, Decimal]] = field(
        default_factory=list
    )  # logged, not quarantined
    quarantined: list[Vintage] = field(default_factory=list)
    receipt_quarantined: str | None = None


class VintageStore:
    def __init__(
        self,
        store: LocalObjectStore,
        series: Mapping[str, SeriesDef],
        clock: Callable[[], datetime] | None = None,
        parsers: Mapping[str, Callable[[bytes], list[RawRow]]] | None = None,
    ) -> None:
        """clock is the recording clock for decisions (OBS-INV-012: no decision is dated before
        the moment it is recorded). Tests inject one; the default is the system clock."""
        self.store = store
        self.series = dict(series)
        self._clock = clock or (lambda: datetime.now(UTC))
        # An opt-in payload parser per source id (S1b adapters). A source without one uses the
        # synthetic receipt format, exactly as in S1a.
        self._parsers = dict(parsers or {})
        self._vintages: dict[tuple[str, date], list[Vintage]] = {}
        # (series_id, valid_time, vintage_seq) -> [(decided_at, status)], strictly increasing
        self._decisions: dict[tuple[str, date, int], list[tuple[datetime, QualityStatus]]] = {}
        self._resolutions: dict[str, list[Resolution]] = {}
        # every quality event as stored, with its key: the input to quality_digest (OBS-AMEND-Q002-R1)
        self._quality_events: list[dict] = []
        self._load()

    # --- persistence ---------------------------------------------------------------------------

    def _load(self) -> None:
        for key in self.store.list("catalogue/vintages/"):
            v = Vintage.from_record(json.loads(self.store.get(key)))
            self._vintages.setdefault((v.series_id, v.valid_time), []).append(v)
        for vs in self._vintages.values():
            vs.sort(key=lambda v: v.vintage_seq)
            if [v.vintage_seq for v in vs] != list(range(1, len(vs) + 1)):
                raise ValueError(f"vintage seq gap for {vs[0].series_id} {vs[0].valid_time}")
        seqs: dict[tuple[str, date, int], int] = {}
        for key in self.store.list("catalogue/quality/"):
            e = json.loads(self.store.get(key))
            k = (e["series_id"], date.fromisoformat(e["valid_time"]), e["vintage_seq"])
            if e["event_seq"] != seqs.get(k, 0) + 1:
                raise ValueError(f"quality event seq gap for {k}")
            if "decided_at" not in e:
                raise ValueError(f"quality event {key} has no decided_at; it predates the decision clock")
            seqs[k] = e["event_seq"]
            decided = parse_instant(e["decided_at"])
            previous = self._decisions.get(k, [])
            # The same decision-clock rule as set_quality (Q-001 OBS-INV-012), applied to every
            # stored event before it can reach a view, digest, pin check or release: quality_digest
            # excludes recorded_at only because this rule holds (VERIFY-2026-10-24-s1a-1-10).
            if "recorded_at" not in e:
                raise DecisionRefused(f"quality event {key} has no recorded_at")
            vintage = next((v for v in self._vintages.get(k[:2], []) if v.vintage_seq == k[2]), None)
            try:
                _check_decision_clock(
                    decided,
                    parse_instant(e["recorded_at"]),
                    vintage.captured_at if vintage is not None else None,
                    previous[-1][0] if previous else None,
                )
            except DecisionRefused as exc:
                raise DecisionRefused(f"stored quality event {key}: {exc}") from None
            self._decisions.setdefault(k, []).append((decided, QualityStatus(e["status"])))
            self._quality_events.append(_quality_event(key, e))
        for key in self.store.list(RESOLUTIONS_PREFIX):
            r = json.loads(self.store.get(key))
            res = Resolution(
                series_id=r["series_id"],
                conflict_id=r["conflict_id"],
                outcome=r["outcome"],
                member=tuple(r["member"]) if r["member"] else None,
                reason=r["reason"],
                actor=r["actor"],
                evidence=r["evidence"],
                decided_at=parse_instant(r["decided_at"]),
                recorded_at=parse_instant(r["recorded_at"]),
            )
            if key != _resolution_key(res):
                raise ValueError(f"resolution {key} is not stored under its content key")
            self._resolutions.setdefault(res.series_id, []).append(res)

    def all_vintages(self) -> list[Vintage]:
        return [v for key in sorted(self._vintages) for v in self._vintages[key]]

    # --- ingest ------------------------------------------------------------------------------------

    def ingest(self, receipt: Receipt, mode: CaptureMode) -> IngestResult:
        self._require_processed_before(receipt)
        result = IngestResult()
        rows, reason = self._validate(receipt, receipt_bytes(self.store, receipt))
        if reason is not None:
            # The whole receipt is quarantined; no observation is created from it (S1-A14).
            key = _quarantine_key(receipt)
            if not self.store.exists(key):
                self.store.put(key, canonical_json(_quarantine_record(receipt, reason)))
            result.receipt_quarantined = reason
            return result

        # One catalogue transaction per receipt: every vintage is decided first, then all are
        # committed together with the receipt's processing outcome, so a refused row leaves
        # nothing behind (F-REVIEW-2026-10-24-s1a-1-6) and every processed receipt is accounted
        # for (OBS-INV-019; VERIFY-2026-10-24-s1a-1-6).
        outcome_key = _processed_key(receipt)
        if self.store.exists(outcome_key):
            raise IncompleteProcessing(f"receipt {receipt.receipt_id} is already processed")
        outcome_rows, derived = self._derive(receipt, rows, mode)
        result.new_vintages, result.quarantined = derived.new_vintages, derived.quarantined
        result.redundant, result.revisions = derived.redundant, derived.revisions
        staged = StagedWrites(self.store)
        for v in result.new_vintages:
            staged.add(_vintage_key(v), canonical_json(v.as_record()))
        # The processing outcome is distinct from the capture evidence (the receipt and its
        # capture record) and records the capture mode, which the receipt bytes do not determine.
        staged.add(
            outcome_key,
            canonical_json(
                {
                    "receipt_id": receipt.receipt_id,
                    "source_id": receipt.source_id,
                    "captured_at": receipt.captured_at,
                    "capture_mode": mode.value,
                    "rows": outcome_rows,
                }
            ),
        )
        staged.commit()
        for v in result.new_vintages:
            self._vintages.setdefault((v.series_id, v.valid_time), []).append(v)
        return result

    def _validate(self, receipt: Receipt, raw: bytes) -> tuple[list, str | None]:
        """The ingest validation, shared by ingest (to quarantine) and completeness (to verify a
        quarantine): (rows, None) for a valid receipt, or ([], reason) for one quarantined whole."""
        try:
            rows = self._parsers.get(receipt.source_id, parse_receipt)(raw)
            unknown = sorted({r.series_id for r in rows} - set(self.series))
            if unknown:
                raise MalformedReceipt(f"unknown series {unknown}")
            if any(self.series[r.series_id].source_id != receipt.source_id for r in rows):
                raise MalformedReceipt("a row's series belongs to another source")
        except MalformedReceipt as exc:
            return [], str(exc)
        return rows, None

    def _derive(self, receipt: Receipt, rows, mode: CaptureMode) -> tuple[list[dict], IngestResult]:
        """The capture-order processing of one receipt: the single rule set used both by ingest
        (to decide) and by completeness (to verify; VERIFY-2026-10-24-s1a-1-7). It sees only the
        vintages captured before this receipt, plus those it decides itself, so the outcome is a
        function of the earlier evidence, the receipt and its capture mode."""
        base = {k: [v for v in vs if v.captured_at < receipt.captured_at] for k, vs in self._vintages.items()}
        pending: dict[tuple[str, date], list[Vintage]] = {}
        outcome_rows: list[dict] = []
        result = IngestResult()
        for row in sorted(rows, key=_row_order):
            series = self.series[row.series_id]
            key = (row.series_id, row.valid_time)
            existing = base.get(key, []) + pending.get(key, [])
            k = determine(
                row,
                series,
                receipt.captured_at,
                mode,
                revision=bool(existing) and existing[-1].value != row.value,
            )
            if existing and _redundant(existing, row.value, k.knowable_at, k.basis.strength):
                result.redundant += 1
                outcome_rows.append(_outcome_row(row, k.knowable_at, k.basis, "redundant", None))
                continue
            if existing and existing[-1].value != row.value:
                result.revisions.append((row.series_id, row.valid_time, existing[-1].value, row.value))
            reasons = self._jump_reasons(
                series, row.valid_time, row.value, base, pending, receipt.captured_at
            )
            v = Vintage(
                series_id=row.series_id,
                valid_time=row.valid_time,
                vintage_seq=len(existing) + 1,
                value=row.value,
                receipt_id=receipt.receipt_id,
                captured_at=receipt.captured_at,
                knowable_at=k.knowable_at,
                knowable_basis=k.basis,
                source_timezone=series.source_timezone,
                quality_status=QualityStatus.QUARANTINED if reasons else QualityStatus.VALID,
                quality_reasons=tuple(reasons),
            )
            pending.setdefault(key, []).append(v)
            outcome_rows.append(_outcome_row(row, k.knowable_at, k.basis, "vintage", v.vintage_seq))
            result.new_vintages.append(v)
            if reasons:
                result.quarantined.append(v)
        return outcome_rows, result

    def _jump_reasons(
        self,
        series: SeriesDef,
        valid_time: date,
        value: Decimal,
        base: dict[tuple[str, date], list[Vintage]],
        pending: dict[tuple[str, date], list[Vintage]],
        captured_at: datetime,
    ) -> list[str]:
        """Jump detection against the latest valid value of the nearest earlier key (§6),
        counting vintages already decided in the same receipt's transaction. Quality is taken as
        decided at the receipt's capture (Q = captured_at), so a replay decides identically."""
        if series.jump_threshold is None:
            return []
        known = {k: base.get(k, []) + pending.get(k, []) for k in {*base, *pending}}
        earlier = [vt for (sid, vt) in known if sid == series.series_id and vt < valid_time]
        for vt in sorted(earlier, reverse=True):
            valid = [
                v
                for v in known[(series.series_id, vt)]
                if v.captured_at <= captured_at
                and status_at(v, self._decisions, captured_at)[0] is QualityStatus.VALID
            ]
            if valid:
                change = abs(value - valid[-1].value)
                if change > series.jump_threshold:
                    return [f"jump {change} > {series.jump_threshold} versus {vt}"]
                return []
        return []

    # --- quality events --------------------------------------------------------------------------

    def _effective(self, v: Vintage) -> QualityStatus:
        """The current status (the latest decision): for monitoring gates, which ask about now."""
        events = self._decisions.get((v.series_id, v.valid_time, v.vintage_seq))
        return events[-1][1] if events else v.quality_status

    def set_quality(
        self,
        series_id: str,
        valid_time: date,
        vintage_seq: int,
        status: QualityStatus,
        actor: str,
        evidence: str,
        decided_at: datetime,
    ) -> None:
        """Append a quality decision (OBS-AMEND-Q001 §3). Releasing from quarantine needs the
        owner or the gate's rules. Refused (DecisionRefused, store unchanged) if decided_at is
        earlier than the vintage's capture, not later than its previous decision, or earlier than
        the moment it is recorded (OBS-INV-012)."""
        require_utc_instant("decided_at", decided_at)
        if actor not in RELEASE_ACTORS:
            raise PermissionError(f"{actor!r} may propose a quality change but not make it (§6)")
        k = (series_id, valid_time, vintage_seq)
        vintage = next(
            (v for v in self._vintages.get((series_id, valid_time), []) if v.vintage_seq == vintage_seq), None
        )
        if vintage is None:
            raise KeyError(k)
        recorded_at = self._clock()
        previous = self._decisions.get(k, [])
        _check_decision_clock(
            decided_at, recorded_at, vintage.captured_at, previous[-1][0] if previous else None
        )
        seq = len(previous) + 1
        record = {
            "series_id": series_id,
            "valid_time": valid_time,
            "vintage_seq": vintage_seq,
            "event_seq": seq,
            "status": status.value,
            "actor": actor,
            "evidence": evidence,
            "decided_at": decided_at,
            "recorded_at": recorded_at,
        }
        key = f"catalogue/quality/{series_id}/{valid_time.isoformat()}/{vintage_seq}/{seq:06d}.json"
        self.store.put(key, canonical_json(record))
        self._decisions.setdefault(k, []).append((decided_at, status))
        self._quality_events.append(_quality_event(key, json.loads(canonical_json(record))))

    # --- conflicts and owner resolutions (OBS-AMEND-Q002 revision 5) ------------------------------

    def conflicts(self, series_id: str, quality_as_of: datetime) -> dict[str, object]:
        """Diagnostics: per slot, the derived chain up to Q, the conflict in force and its
        resolution in force. Independent of any mode. Refused if completeness fails."""
        self._require_complete(series_id, quality_as_of)
        held = [v for v in self.all_vintages() if v.series_id == series_id and v.captured_at <= quality_as_of]
        in_force = resolutions_in_force(self._resolutions.get(series_id, []), quality_as_of)
        chains = conflict_chain(series_id, held)
        return {
            chain[-1].conflict_id: {
                "conflict": chain[-1],
                "chain": [c.conflict_id for c in chain],
                "resolution": in_force.get(chain[-1].conflict_id),
            }
            for chain in chains.values()
        }

    def resolve_conflict(
        self,
        series_id: str,
        conflict_id: str,
        outcome: str,
        member: tuple[str, str] | None,
        reason: str,
        actor: str,
        evidence: str,
        decided_at: datetime,
    ) -> Resolution:
        """Append an owner resolution. It must name the exact conflict in force at decided_at,
        derived from complete evidence; the store is unchanged on any refusal."""
        require_utc_instant("decided_at", decided_at)
        if actor not in RESOLUTION_ACTORS:
            raise PermissionError(f"{actor!r} may propose a resolution but not make it (S1a: owner only)")
        if outcome not in {"select", "reject_all"} or (outcome == "select") != (member is not None):
            raise DecisionRefused("outcome must be select(member) or reject_all")
        recorded_at = self._clock()
        if decided_at < recorded_at:
            raise DecisionRefused(
                f"decided_at {decided_at} is backdated: it precedes its recording {recorded_at}"
            )
        self._require_complete(series_id, decided_at)
        held = [v for v in self.all_vintages() if v.series_id == series_id and v.captured_at <= decided_at]
        target: Conflict | None = next(
            (c for c in derive_conflicts(series_id, held).values() if c.conflict_id == conflict_id), None
        )
        if target is None:
            raise DecisionRefused(f"{conflict_id} is not a conflict in force at {decided_at}")
        if member is not None and (member[0], canonical_value(_decimal(member[1]))) not in target.members:
            raise DecisionRefused(f"{member} is not a member of conflict {conflict_id}")
        earlier = [r for r in self._resolutions.get(series_id, []) if r.conflict_id == conflict_id]
        if earlier and decided_at <= max(r.decided_at for r in earlier):
            raise DecisionRefused("a resolution must be later than the conflict's previous resolution")
        res = Resolution(
            series_id,
            conflict_id,
            outcome,
            (member[0], canonical_value(_decimal(member[1]))) if member else None,
            reason,
            actor,
            evidence,
            decided_at,
            recorded_at,
        )
        self.store.put(_resolution_key(res), canonical_json(res.as_record()))
        self._resolutions.setdefault(series_id, []).append(res)
        return res

    # --- completeness and evidence pins ---------------------------------------------------------

    def _captures(self, source_id: str, upto: datetime) -> list[Receipt]:
        out = []
        for key in self.store.list(f"{CAPTURES_PREFIX}{source_id}/"):
            receipt = load_receipt_record(self.store, key)
            if receipt.captured_at <= upto:
                out.append(receipt)
        return sorted(out, key=lambda r: (r.captured_at, r.receipt_id))

    def evidence_digest(self, series_id: str, quality_as_of: datetime) -> str:
        """OBS-INV-018 pin over E(Q): each receipt's (source_id, captured_at, receipt_id) and its
        verified disposition (its capture mode, or "quarantined"). Computed only from evidence
        that completeness has verified, so it refuses exactly when a query would."""
        return self._require_complete(series_id, quality_as_of)

    def _require_complete(self, series_id: str, quality_as_of: datetime) -> str:
        """OBS-INV-019, returning the evidence digest (the SHA-256 of the verified E(Q) refs)."""
        return sha256_hex(canonical_json(self._evidence_refs(series_id, quality_as_of)))

    def _evidence_refs(self, series_id: str, quality_as_of: datetime) -> list[list]:
        """OBS-INV-019: every receipt of the series' source captured by Q is verified (see
        _check_processed), else IncompleteProcessing or ReceiptIntegrityError. Returns E(Q) as
        [source_id, captured_at, receipt_id, verified disposition], in capture order."""
        receipts = self._captures(self.series[series_id].source_id, quality_as_of)
        dispositions = self._check_processed(receipts, {series_id})
        # No held vintage without verified evidence: a vintage whose capture event is not in the
        # verified E(Q) (for example its capture record was removed) refuses.
        verified = {(r.receipt_id, r.captured_at) for r, _ in dispositions}
        for (sid, _), vs in self._vintages.items():
            for v in vs:
                if (
                    sid == series_id
                    and v.captured_at <= quality_as_of
                    and (v.receipt_id, v.captured_at) not in verified
                ):
                    raise IncompleteProcessing(
                        f"{sid} {v.valid_time} #{v.vintage_seq} has no verified capture event in E(Q)"
                    )
        return [[r.source_id, r.captured_at, r.receipt_id, d] for r, d in dispositions]

    # --- quality decisions pin (OBS-AMEND-Q002-R1, approved OD-0035) -----------------------------

    def quality_digest(self, series_id: str, quality_as_of: datetime) -> str:
        """SHA-256 of the canonical JSON {"schema": "hio-quality-digest/1", "series_id", "events"}
        over the series' quality decision events with decided_at <= Q. Each event carries the
        decided vintage by its evidence (series_id, valid_time, receipt_id, captured_at) and the
        decision (status, decided_at, actor, evidence); vintage_seq, event_seq and recorded_at
        are excluded. Ordered by (series_id, valid_time, receipt_id, captured_at, decided_at).
        No events gives "events": [], a fixed value per series. An event naming a vintage that
        is not stored refuses (IncompleteProcessing)."""
        events = []
        for e in self._quality_events:
            if e["series_id"] != series_id or e["decided_at"] > quality_as_of:
                continue
            vintage = next(
                (
                    v
                    for v in self._vintages.get((series_id, e["valid_time"]), [])
                    if v.vintage_seq == e["vintage_seq"]
                ),
                None,
            )
            if vintage is None:
                raise IncompleteProcessing(f"quality event {e['key']} names a vintage that is not stored")
            events.append(
                {
                    "series_id": series_id,
                    "valid_time": e["valid_time"],
                    "receipt_id": vintage.receipt_id,
                    "captured_at": vintage.captured_at,
                    "status": e["status"],
                    "decided_at": e["decided_at"],
                    "actor": e["actor"],
                    "evidence": e["evidence"],
                }
            )
        events.sort(
            key=lambda x: (
                x["series_id"],
                x["valid_time"],
                x["receipt_id"],
                x["captured_at"],
                x["decided_at"],
            )
        )
        return sha256_hex(
            canonical_json({"schema": QUALITY_DIGEST_SCHEMA, "series_id": series_id, "events": events})
        )

    def _object_refs(self, keys: list[str]) -> tuple:
        return tuple((k, sha256_hex(self.store.get(k))) for k in sorted(keys))

    def _quality_event_refs(self, series_id: str, quality_as_of: datetime) -> tuple:
        return self._object_refs(
            [
                e["key"]
                for e in self._quality_events
                if e["series_id"] == series_id and e["decided_at"] <= quality_as_of
            ]
        )

    def _resolution_refs(self, series_id: str, quality_as_of: datetime) -> tuple:
        return self._object_refs(
            [
                _resolution_key(r)
                for r in self._resolutions.get(series_id, [])
                if r.decided_at <= quality_as_of
            ]
        )

    def verify_pins(
        self,
        series_id: str,
        mode: KnowledgeMode,
        cutoff: datetime | None,
        quality_as_of: datetime | None,
        recorded: tuple[str, str, str, str],
    ) -> View:
        """Reconstruct the view at (mode, T, Q) from the store and refuse (PinMismatch) unless its
        four pins (evidence_digest, resolution_digest, quality_digest, algorithm_revision) equal
        the recorded ones."""
        view = self.view(series_id, mode, cutoff, quality_as_of)
        names = ("evidence_digest", "resolution_digest", "quality_digest", "algorithm_revision")
        rebuilt = (view.evidence_digest, view.resolution_digest, view.quality_digest, view.algorithm_revision)
        diffs = [
            f"{n}: recorded {r}, reconstructed {b}"
            for n, r, b in zip(names, recorded, rebuilt, strict=True)
            if r != b
        ]
        if diffs:
            raise PinMismatch(f"{series_id}: " + "; ".join(diffs))
        return view

    def _require_processed_before(self, receipt: Receipt) -> None:
        """Processing follows capture order (OBS-AMEND-Q002 §2: knowledge is E(Q) processed in
        capture order). A receipt is processed only once every earlier-captured receipt of its
        source is verified, so append-on-change decisions, and therefore results, cannot depend
        on processing order (OBS-INV-011). Otherwise a refusal; nothing is written."""
        earlier = [
            r
            for r in self._captures(receipt.source_id, receipt.captured_at)
            if r.captured_at < receipt.captured_at
        ]
        series = {s for s, d in self.series.items() if d.source_id == receipt.source_id}
        self._check_processed(earlier, series)

    def _check_processed(self, receipts: list[Receipt], series_ids: set[str]) -> list[tuple[Receipt, str]]:
        """The completeness trust boundary (VERIFY-2026-10-24-s1a-1-8). For each captured receipt,
        in capture order:
        1. its raw bytes are read and verified against the receipt id first, whatever else the
           store says (ReceiptIntegrityError otherwise);
        2. its disposition is re-derived with ingest's own rules (_validate), never taken from a
           marker or an outcome: a receipt the rules quarantine must have exactly the quarantine
           record ingest writes, and no processing outcome or vintage; a valid receipt must have
           no quarantine record and a processing outcome equal to its capture-order derivation
           (_verify_outcome).
        Anything the evidence does not warrant refuses (IncompleteProcessing). Returns
        (receipt, disposition) for the evidence pin."""
        out = []
        for receipt in receipts:
            try:
                raw = receipt_bytes(self.store, receipt)  # verifies existence and the content hash
            except (IntegrityError, OSError, ValueError) as exc:
                # The same contract as a selected vintage's receipt (F-REVIEW-2026-10-24-s1a-1-3).
                raise ReceiptIntegrityError(
                    f"captured receipt {receipt.receipt_id} is missing or corrupt: {exc}"
                ) from exc
            rows, reason = self._validate(receipt, raw)
            marker, outcome_key = _quarantine_key(receipt), _processed_key(receipt)
            has_marker, has_outcome = self.store.exists(marker), self.store.exists(outcome_key)
            if reason is not None:
                if not has_marker:
                    raise IncompleteProcessing(
                        f"receipt {receipt.receipt_id} must be quarantined ({reason}) but is not"
                    )
                if json.loads(self.store.get(marker)) != json.loads(
                    canonical_json(_quarantine_record(receipt, reason))
                ):
                    raise IncompleteProcessing(
                        f"receipt {receipt.receipt_id}: its quarantine record differs from the derived one"
                    )
                if has_outcome or self._vintages_of(receipt):
                    raise IncompleteProcessing(
                        f"receipt {receipt.receipt_id} is quarantined but has processing state"
                    )
                out.append((receipt, "quarantined"))
                continue
            if has_marker:
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id} is valid; its quarantine record is not warranted"
                )
            if not has_outcome:
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id} captured {instant_str(receipt.captured_at)} "
                    "has no processing outcome"
                )
            outcome = json.loads(self.store.get(outcome_key))
            try:
                self._verify_outcome(receipt, rows, outcome, series_ids)
            except (KeyError, TypeError, ValueError) as exc:
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id}: unreadable processing outcome: {exc}"
                ) from exc
            out.append((receipt, outcome["capture_mode"]))
        return out

    def _vintages_of(self, receipt: Receipt) -> list[Vintage]:
        """The stored vintages of one capture event (receipt_id, captured_at)."""
        return [
            v
            for vs in self._vintages.values()
            for v in vs
            if (v.receipt_id, v.captured_at) == (receipt.receipt_id, receipt.captured_at)
        ]

    def _verify_outcome(self, receipt: Receipt, rows, outcome: dict, series_ids: set[str]) -> None:
        """Re-derive the receipt's outcome with the same capture-order rules ingest used
        (_derive: latest-value and evidence-strength redundancy, reverts, knowability from the
        recorded capture mode, the jump gate) and require an exact match: the outcome rows, and
        every derived vintage stored exactly, with no other stored vintage from this capture
        event (receipt_id, captured_at). Any difference refuses (VERIFY-2026-10-24-s1a-1-7)."""

        def bad(why: str) -> IncompleteProcessing:
            return IncompleteProcessing(f"receipt {receipt.receipt_id}: processing outcome {why}")

        if (outcome["receipt_id"], parse_instant(outcome["captured_at"])) != (
            receipt.receipt_id,
            receipt.captured_at,
        ):
            raise bad("names another receipt")
        derived_rows, derived = self._derive(receipt, rows, CaptureMode(outcome["capture_mode"]))
        wanted = [r for r in json.loads(canonical_json(derived_rows)) if r["series_id"] in series_ids]
        recorded = [r for r in outcome["rows"] if r["series_id"] in series_ids]
        if recorded != wanted:
            raise bad(f"differs from its capture-order derivation: recorded {recorded}, derived {wanted}")
        expected = {
            (v.series_id, v.valid_time, v.vintage_seq): v
            for v in derived.new_vintages
            if v.series_id in series_ids
        }
        for k, v in expected.items():
            stored = next((s for s in self._vintages.get(k[:2], []) if s.vintage_seq == k[2]), None)
            if stored != v:
                raise bad(f"derives vintage {k[0]} {k[1]} #{k[2]}, which is not stored exactly")
        for (sid, vt_), stored_vs in self._vintages.items():
            for s in stored_vs:
                own = (s.receipt_id, s.captured_at) == (receipt.receipt_id, receipt.captured_at)
                if sid in series_ids and own and (sid, vt_, s.vintage_seq) not in expected:
                    raise bad(f"does not account for stored vintage {sid} {vt_} #{s.vintage_seq}")

    # --- queries ---------------------------------------------------------------------------------

    def view(
        self,
        series_id: str,
        mode: KnowledgeMode,
        cutoff: datetime | None = None,
        quality_as_of: datetime | None = None,
    ) -> View:
        """Select per the mode at (T, Q), after establishing completeness at Q (OBS-INV-019),
        then verify every selected vintage's receipt before it can be used: the capture record
        exists and names this receipt and source, and the raw bytes exist and match their hash.
        Any failure raises ReceiptIntegrityError (OBS-INV-004)."""
        q = effective_quality_cutoff(mode, cutoff, quality_as_of)
        evidence_refs = self._evidence_refs(series_id, q)
        digest = sha256_hex(canonical_json(evidence_refs))
        quality = self.quality_digest(series_id, q)
        selected = select(
            self.all_vintages(),
            self._decisions,
            series_id,
            mode,
            cutoff,
            quality_as_of,
            self._resolutions.get(series_id, []),
            digest,
            quality,
        )
        for v in selected.values.values():
            self._verify_receipt(v)
        return dataclasses.replace(
            selected,
            evidence_refs=tuple(tuple(r) for r in evidence_refs),
            quality_event_refs=self._quality_event_refs(series_id, q),
            resolution_refs=self._resolution_refs(series_id, q),
        )

    def sources_of(self, view: View) -> frozenset[str]:
        """The sources behind a view's selected vintages, read from their verified capture
        records (F-REVIEW-2026-10-24-s1a-1-1): the input to rights checks before a build."""
        out = set()
        for v in view.values.values():
            self._verify_receipt(v)
            out.add(
                load_receipt(
                    self.store, self.series[v.series_id].source_id, v.captured_at, v.receipt_id
                ).source_id
            )
        return frozenset(out)

    def _verify_receipt(self, v: Vintage) -> None:
        source_id = self.series[v.series_id].source_id
        try:
            if not self.store.exists(capture_record_key(source_id, v.captured_at, v.receipt_id)):
                raise ReceiptIntegrityError(
                    f"no capture record for {v.series_id} {v.valid_time} receipt {v.receipt_id}"
                )
            receipt = load_receipt(self.store, source_id, v.captured_at, v.receipt_id)
            if receipt.receipt_id != v.receipt_id or receipt.source_id != source_id:
                raise ReceiptIntegrityError(
                    f"capture record does not match vintage {v.series_id} {v.valid_time}"
                )
            receipt_bytes(self.store, receipt)  # verifies existence and the content hash
        except ReceiptIntegrityError:
            raise
        except (OSError, IntegrityError, ValueError) as exc:
            raise ReceiptIntegrityError(
                f"receipt {v.receipt_id} for {v.series_id} {v.valid_time} is missing or corrupt: {exc}"
            ) from exc

    def as_captured_by_hio(self, series_id: str, cutoff: datetime) -> View:
        """Q = T, fixed."""
        return self.view(series_id, KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff)

    def as_known_by_market(self, series_id: str, cutoff: datetime, quality_as_of: datetime) -> View:
        return self.view(series_id, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff, quality_as_of)

    def reconstructed(self, series_id: str, cutoff: datetime, quality_as_of: datetime) -> View:
        return self.view(series_id, KnowledgeMode.RECONSTRUCTED, cutoff, quality_as_of)

    def latest(self, series_id: str, quality_as_of: datetime) -> View:
        return self.view(series_id, KnowledgeMode.LATEST, None, quality_as_of)

    # --- monitoring gates ------------------------------------------------------------------------

    def missing_business_days(self, series_id: str, start: date, end: date) -> list[date]:
        """Calendar completeness: business days in [start, end] with no valid vintage (§6)."""
        series = self.series[series_id]
        have = {
            vt
            for (sid, vt), vs in self._vintages.items()
            if sid == series_id and any(self._effective(v) is QualityStatus.VALID for v in vs)
        }
        return [d for d in series.calendar.business_days(start, end) if d not in have]

    def is_stale(self, series_id: str, as_of: datetime) -> bool:
        """Staleness: the next expected valid date has not arrived by its release plus grace (§6)."""
        require_utc_instant("as_of", as_of)
        series = self.series[series_id]
        if series.schedule is None:
            raise ValueError(f"{series_id} has no schedule; staleness is undefined")
        valid = [
            vt
            for (sid, vt), vs in self._vintages.items()
            if sid == series_id and any(self._effective(v) is QualityStatus.VALID for v in vs)
        ]
        if not valid:
            return True
        expected = series.calendar.add_business_days(max(valid), 1)
        return as_of > series.schedule.release_instant(expected) + series.schedule.capture_grace


def _redundant(existing: list[Vintage], value: Decimal, knowable_at: datetime, strength: int) -> bool:
    """An incoming value is redundant (OBS-INV-001) when it repeats the latest-recorded value and
    adds no evidence: some vintage already holds that value with equal or stronger evidence that
    was knowable no later. A different value from the latest-recorded one is always a new
    vintage, so a revision, or a revert to an earlier value, is never lost."""
    if existing[-1].value != value:
        return False
    return any(
        v.value == value and v.knowable_basis.strength >= strength and v.knowable_at <= knowable_at
        for v in existing
    )


def _row_order(r) -> tuple:
    """Several vintages of one key in one receipt (a publisher's vintage archive) are recorded in
    the order of their evidence instants."""
    evidence = r.published_at or r.vintage_from or r.archived_at
    return (r.series_id, r.valid_time, evidence.isoformat() if evidence else "")


def _vintage_key(v: Vintage) -> str:
    return f"catalogue/vintages/{v.series_id}/{v.valid_time.isoformat()}/{v.vintage_seq:06d}.json"


def _check_decision_clock(
    decided_at: datetime, recorded_at: datetime, captured_at: datetime | None, previous: datetime | None
) -> None:
    """Q-001's decision clock (OBS-INV-012), for new and stored decisions alike: never earlier
    than its own recording (no backdating), strictly after the vintage's capture (the gate's
    verdict at captured_at is the first decision), and strictly after the previous decision."""
    if decided_at < recorded_at:
        raise DecisionRefused(
            f"decided_at {decided_at} is backdated: it precedes its recording {recorded_at}"
        )
    if captured_at is not None and decided_at <= captured_at:
        raise DecisionRefused(f"decided_at {decided_at} is not after the vintage's capture {captured_at}")
    if previous is not None and decided_at <= previous:
        raise DecisionRefused(
            f"decided_at {decided_at} is not after the vintage's previous decision {previous}"
        )


def _quality_event(key: str, e: dict) -> dict:
    return {
        "key": key,
        "series_id": e["series_id"],
        "valid_time": date.fromisoformat(e["valid_time"])
        if isinstance(e["valid_time"], str)
        else e["valid_time"],
        "vintage_seq": e["vintage_seq"],
        "status": e["status"],
        "actor": e["actor"],
        "evidence": e["evidence"],
        "decided_at": parse_instant(e["decided_at"]) if isinstance(e["decided_at"], str) else e["decided_at"],
    }


def _quarantine_key(receipt: Receipt) -> str:
    return f"catalogue/quarantine/receipts/{receipt.receipt_id}.json"


def _quarantine_record(receipt: Receipt, reason: str) -> dict:
    return {"receipt_id": receipt.receipt_id, "reason": reason}


def _processed_key(receipt: Receipt) -> str:
    """The receipt's processing outcome, beside its capture record (one per receipt)."""
    stamp = receipt.captured_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")
    return f"{PROCESSED_PREFIX}{receipt.source_id}/{stamp}-{receipt.receipt_id}.json"


def _outcome_row(row, knowable_at: datetime, basis, disposition: str, vintage_seq: int | None) -> dict:
    return {
        "series_id": row.series_id,
        "valid_time": row.valid_time.isoformat(),
        "value": canonical_value(row.value),
        "knowable_at": knowable_at,
        "knowable_basis": basis.value,
        "disposition": disposition,
        "vintage_seq": vintage_seq,
    }


def _resolution_key(r: Resolution) -> str:
    """Content-keyed: the same resolution always has the same key and bytes."""
    stamp = r.decided_at.astimezone(UTC).strftime("%Y%m%d-%H%M%S%f")
    digest = sha256_hex(canonical_json(r.as_record()))
    return f"{RESOLUTIONS_PREFIX}{r.series_id}/{r.conflict_id}/{stamp}-{digest}.json"


def _decimal(text: str) -> Decimal:
    value = Decimal(text)
    if not value.is_finite():
        raise DecisionRefused(f"not a finite value: {text!r}")
    return value
