"""The fixed series-to-dataset mapping of every shared publication (T-0009, OD-0065;
F-REVIEW-2026-10-25-t0009-1 and -2).

One published file can serve several datasets, each with its own rights. Which dataset owns which
series is fixed here, in code, and never read from the store: a provenance link written at capture
must agree with this mapping exactly, and attribution at publication is derived from it. A missing,
substituted, duplicated or inconsistent link therefore refuses; it can never move a series to a
different rights subject.

A publication absent from this mapping is a single-dataset publication: its receipts carry no link,
and the publication id is the rights subject, exactly as in S1a.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

SHARED_PUBLICATIONS: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        # RBA statistical table F1: AONIA and the Cash Rate TRI in one file (OD-0065).
        "rba.f1": MappingProxyType(
            {
                "rba.cash_rate": ("rba.cash_rate.aonia",),
                "rba.cash_rate_tri": ("rba.cash_rate.tri",),
            }
        ),
    }
)


class PublicationMappingError(ValueError):
    pass


def is_shared(publication_id: str) -> bool:
    return publication_id in SHARED_PUBLICATIONS


def link_datasets(publication_id: str) -> dict[str, list[str]]:
    """The exact `datasets` content a provenance link of this publication must hold."""
    return {d: sorted(series) for d, series in SHARED_PUBLICATIONS[publication_id].items()}


def owning_dataset(publication_id: str, series_id: str) -> str:
    """The one dataset of a shared publication that owns a series; anything else refuses."""
    owners = [d for d, series in SHARED_PUBLICATIONS[publication_id].items() if series_id in series]
    if len(owners) != 1:
        raise PublicationMappingError(
            f"series {series_id!r} is not owned by exactly one dataset of {publication_id}"
        )
    return owners[0]
