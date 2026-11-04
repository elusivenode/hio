"""The minimal local research reader (T-0021, OD-0159): named releases, pinned by content hash, into one
panel.

For each pin, `resolve_for_use` verifies the bytes and lineage and checks the current status and the
current rights
of the release's actual sources, at every read. It only returns the release's knowledge declarations, so
this reader
enforces those itself, then refuses mixed numeraires or series classes. Nothing is cached, so every read
rechecks.
Exploratory use only: reading here approves nothing and proves nothing about what the data means.
"""

from __future__ import annotations

import csv
import hashlib
import io
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from hio.contracts.canonical import canonical_json
from hio.contracts.observation import parse_instant
from hio.contracts.status import Status
from hio.contracts.temporal import KnowableBasis, KnowledgeMode
from hio.jobs.s1a import spec_document
from hio.portfolio.fixed_allocation import Interval, Panel, align
from hio.publish.status import RefusedUse, resolve_for_use
from hio.rights.gate import RightsGate
from hio.storage.objectstore import LocalObjectStore

REPO = Path(__file__).resolve().parent.parent
RETURN_CLASSES = frozenset({"total_return", "excess_return", "strategy_return"})  # RA §12
CONSUMER_CLASS = "hio_internal"


class ReaderRefused(RefusedUse):
    """The release exists and may be used, but not in this request."""


@dataclass(frozen=True)
class Pin:
    sleeve: str
    dataset_id: str
    content_sha256: str
    data_file: str = "data.csv"
    return_column: str = "r"


def check_knowledge(core: Mapping[str, Any], mode: KnowledgeMode, cutoff: datetime) -> None:
    """The request must match what the release declares, so every pin shares one mode and cutoff. Neither
    can be
    relabelled here: a latest or reconstructed release is never point-in-time evidence."""
    declared = KnowledgeMode(core["knowledge_mode"])
    name = core["dataset_id"]
    if declared is not mode:
        raise ReaderRefused(f"{name} is {declared.value}, not the requested {mode.value}")
    stated = core["knowledge_cutoff"]
    if stated is None or parse_instant(stated) != cutoff:
        raise ReaderRefused(f"{name} has knowledge cutoff {stated}, not the requested {cutoff.isoformat()}")
    basis = KnowableBasis(core["weakest_knowable_basis"])
    if mode is KnowledgeMode.AS_KNOWN_BY_MARKET and not basis.supports_market_knowledge:
        raise ReaderRefused(f"{name} has basis {basis.value}, which can't support as_known_by_market")


def spec_economics(spec_ref: str) -> tuple[str, str]:
    """The series class and numeraire the release's own pinned spec declares."""
    factor_id, version = spec_ref.split("@", 1)
    spec = spec_document(factor_id, version)
    return spec["classification"]["series_class"], spec["return_convention"]["numeraire"]


def check_basis(economics: Mapping[str, tuple[str, str]]) -> None:
    classes = {series_class for series_class, _ in economics.values()}
    numeraires = {numeraire for _, numeraire in economics.values()}
    if not classes <= RETURN_CLASSES:
        raise ReaderRefused(f"not a return series: {sorted(classes - RETURN_CLASSES)}")
    if len(classes) != 1:
        raise ReaderRefused(f"mixed series classes: {sorted(classes)}")
    if len(numeraires) != 1:
        raise ReaderRefused(f"mixed numeraires: {sorted(numeraires)}")


def _intervals(body: bytes, pin: Pin) -> list[Interval]:
    rows = csv.DictReader(io.StringIO(body.decode("utf-8")))
    if pin.return_column not in (rows.fieldnames or []):
        raise ReaderRefused(f"{pin.dataset_id} has no column {pin.return_column}")
    return [
        Interval(
            date.fromisoformat(row["period_start"]),
            date.fromisoformat(row["period_end"]),
            Decimal(row[pin.return_column]),
        )
        for row in rows
    ]


def read_panel(
    store: LocalObjectStore,
    pins: Sequence[Pin],
    *,
    mode: KnowledgeMode,
    cutoff: datetime,
    gate: RightsGate,
) -> tuple[Panel, list[dict[str, Any]]]:
    """The aligned panel, and what was read. Any refusal happens before any return is used."""
    if len({p.sleeve for p in pins}) != len(pins):
        raise ReaderRefused("two pins name one sleeve")
    cores: dict[str, dict[str, Any]] = {}
    for pin in pins:
        core = resolve_for_use(
            store,
            pin.dataset_id,
            pin.content_sha256,
            required=Status.EXPLORATORY,
            consumer_class=CONSUMER_CLASS,
            gate=gate,
        )
        check_knowledge(core, mode, cutoff)
        cores[pin.sleeve] = core
    check_basis({s: spec_economics(c["spec_ref"]) for s, c in cores.items()})

    series, read = {}, []
    for pin in pins:
        core = cores[pin.sleeve]
        entry = next((f for f in core["files"] if f["path"] == pin.data_file), None)
        if entry is None:
            raise ReaderRefused(f"{pin.dataset_id} has no file {pin.data_file}")
        key = f"releases/{pin.dataset_id}/{pin.content_sha256}/{pin.data_file}"
        series[pin.sleeve] = _intervals(store.get(key, entry["sha256"]), pin)
        read.append(
            {
                "sleeve": pin.sleeve,
                "dataset_id": pin.dataset_id,
                "content_sha256": pin.content_sha256,
                "spec_ref": core["spec_ref"],
                "code_ref": core["code_ref"],
                "return_column": pin.return_column,
                "knowledge_mode": core["knowledge_mode"],
                "knowledge_cutoff": core["knowledge_cutoff"],
                "weakest_knowable_basis": core["weakest_knowable_basis"],
            }
        )
    return align(series), read


def code_identity(repo: Path = REPO) -> dict[str, str]:
    """What ran. A dirty tree refuses, because a run record must name its code exactly."""
    git = ("git", "-C", str(repo))
    status = subprocess.run((*git, "status", "--porcelain"), capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise ValueError("the working tree has uncommitted changes")
    commit = subprocess.run((*git, "rev-parse", "HEAD"), capture_output=True, text=True, check=True)
    lock = hashlib.sha256((repo / "uv.lock").read_bytes()).hexdigest()
    return {"commit": commit.stdout.strip(), "lock_sha256": lock}


def run_record(
    read: Sequence[Mapping[str, Any]],
    panel: Panel,
    *,
    parameters: Mapping[str, Any],
    code: Mapping[str, str],
) -> bytes:
    """Metadata only: identities, parameters and counts. It holds no return, so it may be recorded where the
    values themselves may not be."""
    return canonical_json(
        {
            "code": dict(code),
            "inputs": sorted(read, key=lambda r: r["sleeve"]),
            "parameters": dict(parameters),
            "periods": len(panel.dates) - 1,
            "omitted_dates": dict(panel.omitted_dates),
        }
    )
