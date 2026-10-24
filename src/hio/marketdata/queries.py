"""Knowledge query modes (observations standard §4). Pure and deterministic.

Each mode selects, per key, one vintage among the valid candidates, ordered by
(instant, basis strength, vintage_seq) and taking the greatest. The instant is captured_at for
as_captured_by_hio and knowable_at otherwise. Ties on the instant (same-time vintages) prefer
the stronger evidence, then the later-recorded vintage, so the result never depends on input
order. latest() takes the most recently recorded valid vintage (greatest vintage_seq).

A key with no qualifying vintage is absent from the result: it is never filled.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime

from hio.contracts.observation import Vintage
from hio.contracts.temporal import KnowableBasis, KnowledgeMode, QualityStatus, require_utc_instant, weakest


@dataclass(frozen=True)
class View:
    series_id: str
    mode: KnowledgeMode
    cutoff: datetime | None
    values: Mapping[date, Vintage]  # sorted by key

    @property
    def weakest_basis(self) -> KnowableBasis | None:
        return weakest(v.knowable_basis for v in self.values.values()) if self.values else None

    @property
    def label(self) -> str:
        """reconstructed results may not be described as point-in-time evidence (§4)."""
        return "point_in_time" if self.mode.point_in_time else self.mode.value


def select(
    vintages: Iterable[Vintage],
    quality: Mapping[tuple[str, date, int], QualityStatus],
    series_id: str,
    mode: KnowledgeMode,
    cutoff: datetime | None,
) -> View:
    """quality maps (series_id, valid_time, vintage_seq) to the effective quality status; a
    vintage not in the map has its recorded status."""
    if mode is KnowledgeMode.LATEST:
        if cutoff is not None:
            raise ValueError("latest() takes no cutoff")
    else:
        if cutoff is None:
            raise ValueError(f"{mode.value} needs a cutoff instant")
        require_utc_instant("cutoff", cutoff)

    best: dict[date, tuple[tuple, Vintage]] = {}
    for v in vintages:
        if v.series_id != series_id:
            continue
        status = quality.get((v.series_id, v.valid_time, v.vintage_seq), v.quality_status)
        if status is not QualityStatus.VALID:
            continue
        rank = _rank(v, mode, cutoff)
        if rank is None:
            continue
        current = best.get(v.valid_time)
        if current is None or rank > current[0]:
            best[v.valid_time] = (rank, v)
    values = {k: best[k][1] for k in sorted(best)}
    return View(series_id, mode, cutoff, values)


def _rank(v: Vintage, mode: KnowledgeMode, cutoff: datetime | None) -> tuple | None:
    strength = v.knowable_basis.strength
    if mode is KnowledgeMode.AS_CAPTURED_BY_HIO:
        assert cutoff is not None
        return (v.captured_at, strength, v.vintage_seq) if v.captured_at <= cutoff else None
    if mode is KnowledgeMode.AS_KNOWN_BY_MARKET:
        assert cutoff is not None
        if not v.knowable_basis.supports_market_knowledge or v.knowable_at > cutoff:
            return None
        return (v.knowable_at, strength, v.vintage_seq)
    if mode is KnowledgeMode.RECONSTRUCTED:
        assert cutoff is not None
        return (v.knowable_at, strength, v.vintage_seq) if v.knowable_at <= cutoff else None
    return (v.vintage_seq,)  # LATEST
