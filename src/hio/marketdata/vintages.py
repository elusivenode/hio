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

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from hio.contracts.canonical import canonical_json, instant_str, sha256_hex
from hio.contracts.layout import CAPTURES_PREFIX
from hio.contracts.observation import Receipt, Vintage, parse_instant
from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus, require_utc_instant
from hio.marketdata.capture import capture_record_key, load_receipt, load_receipt_record, receipt_bytes
from hio.marketdata.knowability import determine
from hio.marketdata.parse import MalformedReceipt, parse_receipt
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
    ) -> None:
        """clock is the recording clock for decisions (OBS-INV-012: no decision is dated before
        the moment it is recorded). Tests inject one; the default is the system clock."""
        self.store = store
        self.series = dict(series)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._vintages: dict[tuple[str, date], list[Vintage]] = {}
        # (series_id, valid_time, vintage_seq) -> [(decided_at, status)], strictly increasing
        self._decisions: dict[tuple[str, date, int], list[tuple[datetime, QualityStatus]]] = {}
        self._resolutions: dict[str, list[Resolution]] = {}
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
            if previous and decided <= previous[-1][0]:
                raise ValueError(f"quality events for {k} are not strictly increasing in decided_at")
            self._decisions.setdefault(k, []).append((decided, QualityStatus(e["status"])))
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
        try:
            rows = parse_receipt(receipt_bytes(self.store, receipt))
            unknown = sorted({r.series_id for r in rows} - set(self.series))
            if unknown:
                raise MalformedReceipt(f"unknown series {unknown}")
            if any(self.series[r.series_id].source_id != receipt.source_id for r in rows):
                raise MalformedReceipt("a row's series belongs to another source")
        except MalformedReceipt as exc:
            # The whole receipt is quarantined; no observation is created from it (S1-A14).
            key = f"catalogue/quarantine/receipts/{receipt.receipt_id}.json"
            if not self.store.exists(key):
                self.store.put(key, canonical_json({"receipt_id": receipt.receipt_id, "reason": str(exc)}))
            result.receipt_quarantined = str(exc)
            return result

        # One catalogue transaction per receipt: every vintage is decided first, then all are
        # committed together with the receipt's processing outcome, so a refused row leaves
        # nothing behind (F-REVIEW-2026-10-24-s1a-1-6) and every processed receipt is accounted
        # for (OBS-INV-019; VERIFY-2026-10-24-s1a-1-6).
        outcome_key = _processed_key(receipt)
        if self.store.exists(outcome_key):
            raise IncompleteProcessing(f"receipt {receipt.receipt_id} is already processed")
        staged = StagedWrites(self.store)
        pending: dict[tuple[str, date], list[Vintage]] = {}
        outcome_rows: list[dict] = []
        for row in sorted(rows, key=_row_order):
            series = self.series[row.series_id]
            existing = self._vintages.get((row.series_id, row.valid_time), []) + pending.get(
                (row.series_id, row.valid_time), []
            )
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
            reasons = self._jump_reasons(series, row.valid_time, row.value, pending, receipt.captured_at)
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
            staged.add(_vintage_key(v), canonical_json(v.as_record()))
            pending.setdefault((v.series_id, v.valid_time), []).append(v)
            outcome_rows.append(_outcome_row(row, k.knowable_at, k.basis, "vintage", v.vintage_seq))
            result.new_vintages.append(v)
            if reasons:
                result.quarantined.append(v)
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
        for key, vs in pending.items():
            self._vintages.setdefault(key, []).extend(vs)
        return result

    def _jump_reasons(
        self,
        series: SeriesDef,
        valid_time: date,
        value: Decimal,
        pending: dict[tuple[str, date], list[Vintage]],
        captured_at: datetime,
    ) -> list[str]:
        """Jump detection against the latest valid value of the nearest earlier key (§6),
        counting vintages already decided in the same receipt's transaction. Quality is taken as
        decided at the receipt's capture (Q = captured_at), so a replay decides identically."""
        if series.jump_threshold is None:
            return []
        known = {k: self._vintages.get(k, []) + pending.get(k, []) for k in {*self._vintages, *pending}}
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
        last = previous[-1][0] if previous else vintage.captured_at
        if decided_at < recorded_at:
            raise DecisionRefused(
                f"decided_at {decided_at} is backdated: it precedes its recording {recorded_at}"
            )
        if decided_at <= last:
            raise DecisionRefused(
                f"decided_at {decided_at} is not after the vintage's previous decision {last}"
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
        self.store.put(
            f"catalogue/quality/{series_id}/{valid_time.isoformat()}/{vintage_seq}/{seq:06d}.json",
            canonical_json(record),
        )
        self._decisions.setdefault(k, []).append((decided_at, status))

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
        """OBS-INV-018 pin over E(Q): each receipt's (source_id, captured_at, receipt_id) and how
        it was processed (its capture mode, "quarantined", or "unprocessed"). The capture mode is
        pinned because the receipt bytes alone do not determine the derived vintages."""
        source_id = self.series[series_id].source_id
        pins = [
            [r.source_id, r.captured_at, r.receipt_id, self._processing_of(r)]
            for r in self._captures(source_id, quality_as_of)
        ]
        return sha256_hex(canonical_json(pins))

    def _processing_of(self, receipt: Receipt) -> str:
        if self.store.exists(f"catalogue/quarantine/receipts/{receipt.receipt_id}.json"):
            return "quarantined"
        key = _processed_key(receipt)
        if not self.store.exists(key):
            return "unprocessed"
        return json.loads(self.store.get(key))["capture_mode"]

    def _require_complete(self, series_id: str, quality_as_of: datetime) -> str:
        """OBS-INV-019. Every receipt of the series' source captured by Q (bytes verified) must be
        accounted for by its own processing outcome (or its quarantine record), verified against
        the receipt's rows and the stored vintages (see _check_processed). Otherwise
        IncompleteProcessing. Returns the evidence digest."""
        self._check_processed(self._captures(self.series[series_id].source_id, quality_as_of), {series_id})
        return self.evidence_digest(series_id, quality_as_of)

    def _require_processed_before(self, receipt: Receipt) -> None:
        """Processing follows capture order (OBS-AMEND-Q002 §2: knowledge is E(Q) processed in
        capture order). A receipt is processed only once every earlier-captured receipt of its
        source is reflected, so append-on-change decisions, and therefore results, cannot depend
        on processing order (OBS-INV-011). Otherwise IncompleteProcessing; nothing is written."""
        earlier = [
            r
            for r in self._captures(receipt.source_id, receipt.captured_at)
            if r.captured_at < receipt.captured_at
        ]
        series = {s for s, d in self.series.items() if d.source_id == receipt.source_id}
        self._check_processed(earlier, series)

    def _check_processed(self, receipts: list[Receipt], series_ids: set[str]) -> None:
        """For each receipt: a quarantine record, or a processing outcome whose rows equal the
        receipt's rows (series, key, value; identity and content, not counts), where every
        "vintage" row names a stored vintage from this receipt with exactly the recorded content,
        and every "redundant" row is re-derived from the recorded capture mode and justified by an
        earlier-or-same capture with equal or stronger evidence knowable no later (the
        append-on-change rule). Value equality alone never proves a no-op."""
        for receipt in receipts:
            if self.store.exists(f"catalogue/quarantine/receipts/{receipt.receipt_id}.json"):
                continue
            key = _processed_key(receipt)
            if not self.store.exists(key):
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id} captured {instant_str(receipt.captured_at)} has no "
                    "processing outcome"
                )
            try:
                raw = receipt_bytes(self.store, receipt)  # verifies existence and the content hash
            except (IntegrityError, OSError, ValueError) as exc:
                # Captured evidence that cannot be verified fails closed as an integrity failure,
                # the same contract as a selected vintage's receipt (F-REVIEW-2026-10-24-s1a-1-3).
                raise ReceiptIntegrityError(
                    f"captured receipt {receipt.receipt_id} is missing or corrupt: {exc}"
                ) from exc
            try:
                rows = parse_receipt(raw)
            except MalformedReceipt as exc:
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id} is malformed but not quarantined: {exc}"
                ) from exc
            outcome = json.loads(self.store.get(key))
            try:
                self._verify_outcome(receipt, rows, outcome, series_ids)
            except (KeyError, TypeError, ValueError) as exc:
                raise IncompleteProcessing(
                    f"receipt {receipt.receipt_id}: unreadable processing outcome: {exc}"
                ) from exc

    def _verify_outcome(self, receipt: Receipt, rows, outcome: dict, series_ids: set[str]) -> None:
        def bad(why: str) -> IncompleteProcessing:
            return IncompleteProcessing(f"receipt {receipt.receipt_id}: processing outcome {why}")

        if (outcome["receipt_id"], parse_instant(outcome["captured_at"])) != (
            receipt.receipt_id,
            receipt.captured_at,
        ):
            raise bad("names another receipt")
        mode = CaptureMode(outcome["capture_mode"])
        recorded = [r for r in outcome["rows"] if r["series_id"] in series_ids]
        expected = sorted(
            (r.series_id, r.valid_time.isoformat(), canonical_value(r.value))
            for r in rows
            if r.series_id in series_ids
        )
        if sorted((r["series_id"], r["valid_time"], r["value"]) for r in recorded) != expected:
            raise bad("does not match the receipt's rows")
        by_row = {(r.series_id, r.valid_time.isoformat(), canonical_value(r.value)): r for r in rows}
        named = {
            (r["series_id"], r["valid_time"], r["vintage_seq"])
            for r in recorded
            if r["disposition"] == "vintage"
        }
        # A capture event is (receipt_id, captured_at): identical bytes captured again later (a
        # revert) are a separate event with their own outcome.
        for (sid, vt_), stored_vs in self._vintages.items():
            for v in stored_vs:
                own = (v.receipt_id, v.captured_at) == (receipt.receipt_id, receipt.captured_at)
                if sid in series_ids and own and (sid, vt_.isoformat(), v.vintage_seq) not in named:
                    raise bad(f"does not account for stored vintage {sid} {vt_} #{v.vintage_seq}")
        for r in recorded:
            vt = date.fromisoformat(r["valid_time"])
            knowable, basis = parse_instant(r["knowable_at"]), KnowableBasis(r["knowable_basis"])
            stored = self._vintages.get((r["series_id"], vt), [])
            if r["disposition"] == "vintage":
                if not any(
                    v.vintage_seq == r["vintage_seq"]
                    and v.receipt_id == receipt.receipt_id
                    and v.captured_at == receipt.captured_at
                    and canonical_value(v.value) == r["value"]
                    and (v.knowable_at, v.knowable_basis) == (knowable, basis)
                    for v in stored
                ):
                    raise bad(f"names a vintage that is not stored as recorded: {r}")
            elif r["disposition"] == "redundant":
                row = by_row[(r["series_id"], r["valid_time"], r["value"])]
                derived = determine(
                    row, self.series[r["series_id"]], receipt.captured_at, mode, revision=False
                )
                if (derived.knowable_at, derived.basis) != (knowable, basis):
                    raise bad(f"records evidence its capture mode does not derive: {r}")
                # Justified only by an earlier capture, or by a vintage this outcome records itself
                # (one decided earlier in the same receipt's transaction).
                if not any(
                    canonical_value(v.value) == r["value"]
                    and (
                        v.captured_at < receipt.captured_at
                        or (
                            (v.receipt_id, v.captured_at) == (receipt.receipt_id, receipt.captured_at)
                            and (r["series_id"], r["valid_time"], v.vintage_seq) in named
                        )
                    )
                    and v.knowable_basis.strength >= basis.strength
                    and v.knowable_at <= knowable
                    for v in stored
                ):
                    raise bad(f"claims a no-op that no earlier vintage justifies: {r}")
            else:
                raise bad(f"has an unknown disposition: {r['disposition']!r}")

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
        digest = self._require_complete(series_id, q)
        selected = select(
            self.all_vintages(),
            self._decisions,
            series_id,
            mode,
            cutoff,
            quality_as_of,
            self._resolutions.get(series_id, []),
            digest,
        )
        for v in selected.values.values():
            self._verify_receipt(v)
        return selected

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
