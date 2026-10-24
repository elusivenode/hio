"""Knowledge query modes (observations standard §4, as amended by OBS-AMEND-Q001 revision 4 and
OBS-AMEND-Q002 revision 5; OD-0029, OD-0030). Pure and deterministic.

Two cutoffs. T is the information cutoff (captured_at for as_captured_by_hio, knowable_at
otherwise). Q is HIO's decision cutoff: a vintage is held at Q if captured_at <= Q, and its
quality is the latest decision with decided_at <= Q (the ingest gate's verdict is the first
decision, at captured_at). Q = T, fixed, for as_captured_by_hio; it is explicit and required for
the other modes. A result depends only on evidence and decisions dated <= Q.

Ranking is by (instant, basis strength) only; vintage_seq and input order never decide. Two or
more held vintages of one key sharing a rank-clock instant and strength, with different values,
are a conflict, derived from the evidence and identified by a hash of its members' evidence
(receipt_id, value). An unresolved conflict at the selected rank makes the key absent; an owner
resolution in force at Q decides it. Every conflict held at Q is reported with its effect.

A key with no qualifying vintage is absent from the result: it is never filled.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from hio.contracts.canonical import canonical_json, decimal_str, sha256_hex
from hio.contracts.observation import Vintage
from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus, require_utc_instant, weakest

# Changed whenever the derivation or selection rules change, including what a result records
# (OBS-AMEND-Q002 §3; /3 adds quality_digest, OBS-AMEND-Q002-R1, OD-0035).
ALGORITHM_REVISION = "hio-obs-select/3"

CAPTURE_CLOCK, KNOWABILITY_CLOCK = "captured_at", "knowable_at"
SUPPRESSES_KEY, RESOLVED, OUTRANKED, NOT_ELIGIBLE_IN_MODE = (
    "suppresses_key",
    "resolved",
    "outranked",
    "not_eligible_in_mode",
)

# (decided_at, status), strictly increasing in decided_at. The ingest gate's verdict at
# captured_at is implicit and not listed.
Decisions = Mapping[tuple[str, date, int], Sequence[tuple[datetime, QualityStatus]]]


class InadmissibleForPredictivePointInTime(Exception):
    """A result with predictive_pit_admissible = false was offered to a path that requires
    point-in-time input (OBS-INV-014). There is no override."""


@dataclass(frozen=True)
class Resolution:
    """An owner's append-only resolution of one derived conflict (OBS-AMEND-Q002 §3, §6)."""

    series_id: str
    conflict_id: str
    outcome: str  # "select" or "reject_all"
    member: tuple[str, str] | None  # (receipt_id, canonical value) for "select"
    reason: str
    actor: str
    evidence: str
    decided_at: datetime
    recorded_at: datetime

    def as_record(self) -> dict:
        return {
            "series_id": self.series_id,
            "conflict_id": self.conflict_id,
            "outcome": self.outcome,
            "member": list(self.member) if self.member else None,
            "reason": self.reason,
            "actor": self.actor,
            "evidence": self.evidence,
            "decided_at": self.decided_at,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True)
class Conflict:
    series_id: str
    key: date
    rank_clock: str
    instant: datetime
    strength: int
    members: tuple[tuple[str, str], ...]  # sorted (receipt_id, canonical value)
    detected_at: datetime

    @property
    def conflict_id(self) -> str:
        return conflict_id(
            self.series_id, self.key, self.rank_clock, self.instant, self.strength, self.members
        )


@dataclass(frozen=True)
class ConflictReport:
    conflict: Conflict
    effect: str
    resolution: Resolution | None  # the resolution in force at Q, if any


@dataclass(frozen=True)
class View:
    series_id: str
    mode: KnowledgeMode
    cutoff: datetime | None  # T
    values: Mapping[date, Vintage]  # sorted by key
    quality_as_of: datetime | None = None  # Q
    eligibility_decided_at: Mapping[date, datetime] = field(default_factory=dict)
    conflicts: tuple[ConflictReport, ...] = ()
    evidence_digest: str = ""
    resolution_digest: str = ""
    algorithm_revision: str = ALGORITHM_REVISION
    quality_digest: str = ""  # OBS-AMEND-Q002-R1: the quality decisions in force at Q
    # Immutable references to the inputs behind the pins, so they can be reproduced independently:
    # E(Q) as (source_id, captured_at, receipt_id, disposition); quality and resolution events as
    # (storage key, SHA-256 of the stored bytes).
    # They identify the exact stored objects, so they take no part in result equality: a faithful
    # copy recorded at another time is the same result with the same four pins.
    evidence_refs: tuple = field(default=(), compare=False)
    quality_event_refs: tuple = field(default=(), compare=False)
    resolution_refs: tuple = field(default=(), compare=False)

    @property
    def weakest_basis(self) -> KnowableBasis | None:
        return weakest(v.knowable_basis for v in self.values.values()) if self.values else None

    @property
    def label(self) -> str:
        """§4: reconstructed and latest results may not be described as point-in-time evidence."""
        if self.mode.point_in_time:
            return "point_in_time"
        return "reconstructed" if self.mode is KnowledgeMode.RECONSTRUCTED else "descriptive"

    @property
    def quality_after_cutoff(self) -> bool:
        return self.mode is KnowledgeMode.AS_KNOWN_BY_MARKET and _later(self.quality_as_of, self.cutoff)

    @property
    def restated_quality(self) -> bool:
        if self.mode is KnowledgeMode.LATEST:
            return True
        return self.mode is KnowledgeMode.RECONSTRUCTED and _later(self.quality_as_of, self.cutoff)

    @property
    def predictive_pit_admissible(self) -> bool:
        """OBS-INV-014: true only for as_captured_by_hio, and for as_known_by_market with Q <= T.
        Computed from the mode and the two cutoffs; no caller can set it."""
        if self.mode is KnowledgeMode.AS_CAPTURED_BY_HIO:
            return True
        if self.mode is KnowledgeMode.AS_KNOWN_BY_MARKET:
            return not _later(self.quality_as_of, self.cutoff)
        return False

    def validated_after_cutoff(self, key: date) -> bool:
        """Was the eligibility decision in force at Q for this key's value made after T?"""
        decided = self.eligibility_decided_at[key]
        return self.cutoff is None or decided > self.cutoff


def require_predictive_pit(view: View) -> View:
    """The enforcement point for any path that requires point-in-time input (OBS-INV-014)."""
    if not view.predictive_pit_admissible:
        raise InadmissibleForPredictivePointInTime(
            f"{view.series_id}: {view.mode.value} at T={view.cutoff}, Q={view.quality_as_of} is not "
            "admissible to predictive point-in-time work (OBS-AMEND-Q001 §4)"
        )
    return view


def effective_quality_cutoff(
    mode: KnowledgeMode, cutoff: datetime | None, quality_as_of: datetime | None
) -> datetime:
    """Q per mode (OBS-AMEND-Q001 §4). Raises on a missing or overridden cutoff."""
    if mode is KnowledgeMode.LATEST:
        if cutoff is not None:
            raise ValueError("latest() takes no information cutoff")
    else:
        if cutoff is None:
            raise ValueError(f"{mode.value} needs an information cutoff T")
        require_utc_instant("cutoff", cutoff)
    if mode is KnowledgeMode.AS_CAPTURED_BY_HIO:
        if quality_as_of is not None and quality_as_of != cutoff:
            raise ValueError("as_captured_by_hio fixes Q = T; it cannot be overridden")
        assert cutoff is not None
        return cutoff
    if quality_as_of is None:
        raise ValueError(f"{mode.value} needs an explicit HIO decision cutoff Q (quality_as_of)")
    require_utc_instant("quality_as_of", quality_as_of)
    return quality_as_of


def status_at(v: Vintage, decisions: Decisions, q: datetime) -> tuple[QualityStatus, datetime]:
    """The quality decision in force at q: (status, decided_at)."""
    status, decided = v.quality_status, v.captured_at
    for at, s in decisions.get((v.series_id, v.valid_time, v.vintage_seq), ()):
        if at <= q:
            status, decided = s, at
    return status, decided


def canonical_value(value: Decimal) -> str:
    """3.6 and 3.60 are the same value."""
    return decimal_str(value)


def evidence_of(v: Vintage) -> tuple[str, str]:
    return (v.receipt_id, canonical_value(v.value))


def conflict_id(
    series_id: str,
    key: date,
    rank_clock: str,
    instant: datetime,
    strength: int,
    members: Iterable[tuple[str, str]],
) -> str:
    return sha256_hex(
        canonical_json(
            {
                "series_id": series_id,
                "key": key,
                "rank_clock": rank_clock,
                "instant": instant,
                "strength": strength,
                "members": [{"receipt_id": r, "value": val} for r, val in sorted(set(members))],
            }
        )
    )


def _slot(v: Vintage, clock: str) -> tuple:
    instant = v.captured_at if clock == CAPTURE_CLOCK else v.knowable_at
    return (v.valid_time, clock, instant, v.knowable_basis.strength)


def _slots(series_id: str, held: Iterable[Vintage]) -> dict[tuple, list[Vintage]]:
    slots: dict[tuple, list[Vintage]] = {}
    for v in held:
        if v.series_id == series_id:
            for clock in (CAPTURE_CLOCK, KNOWABILITY_CLOCK):
                slots.setdefault(_slot(v, clock), []).append(v)
    return slots


def _conflict_of(series_id: str, slot: tuple, members: list[Vintage]) -> Conflict | None:
    evidence = sorted({evidence_of(v) for v in members})
    if len({val for _, val in evidence}) < 2:
        return None
    key, clock, instant, strength = slot
    return Conflict(
        series_id, key, clock, instant, strength, tuple(evidence), max(v.captured_at for v in members)
    )


def derive_conflicts(series_id: str, held: Iterable[Vintage]) -> dict[tuple, Conflict]:
    """The conflict in force for every slot of the held vintages (OBS-AMEND-Q002 §2): all members
    of a (key, clock, instant, strength) slot, if they hold two or more different values."""
    out = {}
    for slot, members in _slots(series_id, held).items():
        c = _conflict_of(series_id, slot, members)
        if c is not None:
            out[slot] = c
    return out


def conflict_chain(series_id: str, held: Iterable[Vintage]) -> dict[tuple, list[Conflict]]:
    """Per slot, the canonical conflict chain up to the held evidence: the conflict in force as
    each member's captured_at is reached (members with equal captured_at join together)."""
    chains = {}
    for slot, members in _slots(series_id, held).items():
        chain: list[Conflict] = []
        for t in sorted({v.captured_at for v in members}):
            c = _conflict_of(series_id, slot, [v for v in members if v.captured_at <= t])
            if c is not None and (not chain or chain[-1].members != c.members):
                chain.append(c)
        if chain:
            chains[slot] = chain
    return chains


def resolutions_in_force(resolutions: Iterable[Resolution], q: datetime) -> dict[str, Resolution]:
    out: dict[str, Resolution] = {}
    for r in sorted(resolutions, key=lambda r: (r.conflict_id, r.decided_at)):
        if r.decided_at <= q:
            out[r.conflict_id] = r
    return out


def resolution_digest(series_id: str, resolutions: Iterable[Resolution], q: datetime) -> str:
    events = sorted(
        (r.as_record() for r in resolutions if r.series_id == series_id and r.decided_at <= q),
        key=canonical_json,
    )
    return sha256_hex(canonical_json(events))


def select(
    vintages: Iterable[Vintage],
    decisions: Decisions,
    series_id: str,
    mode: KnowledgeMode,
    cutoff: datetime | None,
    quality_as_of: datetime | None = None,
    resolutions: Iterable[Resolution] = (),
    evidence_digest: str = "",
    quality_digest: str = "",
) -> View:
    q = effective_quality_cutoff(mode, cutoff, quality_as_of)
    resolutions = [r for r in resolutions if r.series_id == series_id]
    held = [v for v in vintages if v.series_id == series_id and v.captured_at <= q]
    clock = CAPTURE_CLOCK if mode is KnowledgeMode.AS_CAPTURED_BY_HIO else KNOWABILITY_CLOCK
    conflicts = derive_conflicts(series_id, held)
    in_force = resolutions_in_force(resolutions, q)

    by_key: dict[date, list[tuple[Vintage, datetime]]] = {}
    for v in held:
        status, decided = status_at(v, decisions, q)
        if status is QualityStatus.VALID and _passes(v, mode, cutoff):
            by_key.setdefault(v.valid_time, []).append((v, decided))

    values: dict[date, Vintage] = {}
    decided_at: dict[date, datetime] = {}
    top_slots: set[tuple] = set()
    for key, cands in by_key.items():
        top = max(_slot(v, clock)[2:] for v, _ in cands)
        slot = (key, clock, *top)
        top_slots.add(slot)
        # Evidence first; among evidence-identical observations (same receipt and value), the one
        # HIO held first. vintage_seq only separates exact duplicates and never changes the value.
        group = sorted(
            (c for c in cands if _slot(c[0], clock)[2:] == top),
            key=lambda c: (evidence_of(c[0]), c[0].captured_at, c[0].vintage_seq),
        )
        conflict = conflicts.get(slot)
        chosen = None
        if conflict is None:
            chosen = group[0]  # one value in the group; evidence order makes the pick stable
        else:
            res = in_force.get(conflict.conflict_id)
            if res is not None and res.outcome == "select":
                chosen = next((c for c in group if evidence_of(c[0]) == res.member), None)
        if chosen is not None:
            values[key], decided_at[key] = chosen

    reports = []
    for slot, c in sorted(conflicts.items(), key=lambda kv: kv[1].conflict_id):
        res = in_force.get(c.conflict_id)
        if slot in top_slots:
            effect = RESOLVED if res is not None else SUPPRESSES_KEY
        elif slot[1] != clock or not _slot_eligible(slot, held, decisions, q, mode, cutoff):
            effect = NOT_ELIGIBLE_IN_MODE
        else:
            effect = OUTRANKED
        reports.append(ConflictReport(c, effect, res))

    keys = sorted(values)
    return View(
        series_id,
        mode,
        cutoff,
        {k: values[k] for k in keys},
        quality_as_of=q,
        eligibility_decided_at={k: decided_at[k] for k in keys},
        conflicts=tuple(reports),
        evidence_digest=evidence_digest,
        resolution_digest=resolution_digest(series_id, resolutions, q),
        quality_digest=quality_digest,
    )


def _passes(v: Vintage, mode: KnowledgeMode, cutoff: datetime | None) -> bool:
    if mode is KnowledgeMode.AS_CAPTURED_BY_HIO:
        assert cutoff is not None
        return v.captured_at <= cutoff
    if mode is KnowledgeMode.AS_KNOWN_BY_MARKET:
        assert cutoff is not None
        return v.knowable_basis.supports_market_knowledge and v.knowable_at <= cutoff
    if mode is KnowledgeMode.RECONSTRUCTED:
        assert cutoff is not None
        return v.knowable_at <= cutoff
    return True  # LATEST


def _slot_eligible(slot, held, decisions, q, mode, cutoff) -> bool:
    """Does any member of the slot qualify in this mode (quality at Q and the mode's filter)?
    A slot whose members are all excluded, by the mode or by quality, is not_eligible_in_mode."""
    return any(
        _slot(v, slot[1]) == slot
        and _passes(v, mode, cutoff)
        and status_at(v, decisions, q)[0] is QualityStatus.VALID
        for v in held
    )


def _later(q: datetime | None, t: datetime | None) -> bool:
    return q is not None and t is not None and q > t
