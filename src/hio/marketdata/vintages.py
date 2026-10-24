"""The vintage store: append-on-change recording, quality gates and quality events
(observations standard §1, §6, §7).

Records are append-only JSON objects in the object store:
    catalogue/vintages/<series_id>/<valid_time>/<vintage_seq>.json
    catalogue/quality/<series_id>/<valid_time>/<vintage_seq>/<event_seq>.json
    catalogue/quarantine/receipts/<receipt_id>.json
The in-memory state is rebuilt from those records, so a reload gives identical query results.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from hio.contracts.canonical import canonical_json
from hio.contracts.observation import Receipt, Vintage
from hio.contracts.temporal import KnowledgeMode, QualityStatus, require_utc_instant
from hio.marketdata.capture import receipt_bytes
from hio.marketdata.knowability import determine
from hio.marketdata.parse import MalformedReceipt, parse_receipt
from hio.marketdata.queries import View, select
from hio.marketdata.series import CaptureMode, SeriesDef
from hio.storage.objectstore import LocalObjectStore, StagedWrites

# Only the gate's own rules or the owner may release a quarantined vintage (§6). An agent may
# propose; it may not decide.
RELEASE_ACTORS = frozenset({"owner", "gate"})


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
    def __init__(self, store: LocalObjectStore, series: Mapping[str, SeriesDef]) -> None:
        self.store = store
        self.series = dict(series)
        self._vintages: dict[tuple[str, date], list[Vintage]] = {}
        self._quality: dict[tuple[str, date, int], QualityStatus] = {}
        self._quality_seq: dict[tuple[str, date, int], int] = {}
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
        for key in self.store.list("catalogue/quality/"):
            e = json.loads(self.store.get(key))
            k = (e["series_id"], date.fromisoformat(e["valid_time"]), e["vintage_seq"])
            if e["event_seq"] != self._quality_seq.get(k, 0) + 1:
                raise ValueError(f"quality event seq gap for {k}")
            self._quality_seq[k] = e["event_seq"]
            self._quality[k] = QualityStatus(e["status"])

    def all_vintages(self) -> list[Vintage]:
        return [v for key in sorted(self._vintages) for v in self._vintages[key]]

    # --- ingest ------------------------------------------------------------------------------------

    def ingest(self, receipt: Receipt, mode: CaptureMode) -> IngestResult:
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
        # committed together, so a refused row leaves nothing behind (F-REVIEW-2026-10-24-s1a-1-6).
        staged = StagedWrites(self.store)
        pending: dict[tuple[str, date], list[Vintage]] = {}
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
                continue
            if existing and existing[-1].value != row.value:
                result.revisions.append((row.series_id, row.valid_time, existing[-1].value, row.value))
            reasons = self._jump_reasons(series, row.valid_time, row.value, pending)
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
            result.new_vintages.append(v)
            if reasons:
                result.quarantined.append(v)
        if result.new_vintages:
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
    ) -> list[str]:
        """Jump detection against the latest valid value of the nearest earlier key (§6),
        counting vintages already decided in the same receipt's transaction."""
        if series.jump_threshold is None:
            return []
        known = {k: self._vintages.get(k, []) + pending.get(k, []) for k in {*self._vintages, *pending}}
        earlier = [vt for (sid, vt) in known if sid == series.series_id and vt < valid_time]
        for vt in sorted(earlier, reverse=True):
            valid = [v for v in known[(series.series_id, vt)] if self._effective(v) is QualityStatus.VALID]
            if valid:
                change = abs(value - valid[-1].value)
                if change > series.jump_threshold:
                    return [f"jump {change} > {series.jump_threshold} versus {vt}"]
                return []
        return []

    # --- quality events --------------------------------------------------------------------------

    def _effective(self, v: Vintage) -> QualityStatus:
        return self._quality.get((v.series_id, v.valid_time, v.vintage_seq), v.quality_status)

    def set_quality(
        self,
        series_id: str,
        valid_time: date,
        vintage_seq: int,
        status: QualityStatus,
        actor: str,
        evidence: str,
        at: datetime,
    ) -> None:
        """Append a quality event. Releasing from quarantine needs the owner or the gate's rules."""
        require_utc_instant("at", at)
        if actor not in RELEASE_ACTORS:
            raise PermissionError(f"{actor!r} may propose a quality change but not make it (§6)")
        k = (series_id, valid_time, vintage_seq)
        if not any(v.vintage_seq == vintage_seq for v in self._vintages.get((series_id, valid_time), [])):
            raise KeyError(k)
        seq = self._quality_seq.get(k, 0) + 1
        record = {
            "series_id": series_id,
            "valid_time": valid_time,
            "vintage_seq": vintage_seq,
            "event_seq": seq,
            "status": status.value,
            "actor": actor,
            "evidence": evidence,
            "at": at,
        }
        self.store.put(
            f"catalogue/quality/{series_id}/{valid_time.isoformat()}/{vintage_seq}/{seq:06d}.json",
            canonical_json(record),
        )
        self._quality_seq[k] = seq
        self._quality[k] = status

    # --- queries ---------------------------------------------------------------------------------

    def view(self, series_id: str, mode: KnowledgeMode, cutoff: datetime | None = None) -> View:
        return select(self.all_vintages(), self._quality, series_id, mode, cutoff)

    def as_captured_by_hio(self, series_id: str, cutoff: datetime) -> View:
        return self.view(series_id, KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff)

    def as_known_by_market(self, series_id: str, cutoff: datetime) -> View:
        return self.view(series_id, KnowledgeMode.AS_KNOWN_BY_MARKET, cutoff)

    def reconstructed(self, series_id: str, cutoff: datetime) -> View:
        return self.view(series_id, KnowledgeMode.RECONSTRUCTED, cutoff)

    def latest(self, series_id: str) -> View:
        return self.view(series_id, KnowledgeMode.LATEST)

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
