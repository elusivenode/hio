"""Source lineage derived from verified records (F-REVIEW-2026-10-24-s1a-1-1, OD-0023).

Rights decisions use the sources this module derives, never source ids supplied by a caller:
- a release's `inputs` name receipts (for observation inputs) and upstream releases;
- each receipt maps to its source through its capture records, whose raw bytes must exist and
  match the receipt hash;
- each upstream release must be stored and verify against its content hash, and its own lineage
  is followed in turn.
Anything missing, corrupt or unrecognised raises LineageError: lineage fails closed.
"""

from __future__ import annotations

import json
import re
from typing import Any

from hio.contracts.layout import CAPTURES_PREFIX, receipt_key
from hio.contracts.observation import parse_instant
from hio.storage.objectstore import IntegrityError, LocalObjectStore

_SHA = re.compile(r"^[0-9a-f]{64}$")
_MAX_DEPTH = 32


class LineageError(Exception):
    pass


def capture_index(store: LocalObjectStore) -> dict[str, list[str]]:
    """receipt id -> capture-record keys, from one listing."""
    index: dict[str, list[str]] = {}
    for key in store.list(CAPTURES_PREFIX):
        rid = key.rsplit("-", 1)[-1].removesuffix(".json")
        index.setdefault(rid, []).append(key)
    return index


def receipt_source(
    store: LocalObjectStore, receipt_id: str, index: dict[str, list[str]] | None = None
) -> str:
    if not _SHA.match(receipt_id):
        raise LineageError(f"not a receipt id: {receipt_id!r}")
    records = (index if index is not None else capture_index(store)).get(receipt_id, [])
    if not records:
        raise LineageError(f"no capture record for receipt {receipt_id}")
    sources = set()
    for key in records:
        r = json.loads(store.get(key))
        if r["receipt_id"] != receipt_id or not key.startswith(f"{CAPTURES_PREFIX}{r['source_id']}/"):
            raise LineageError(f"capture record {key} does not match its key")
        try:
            store.get(receipt_key(r["source_id"], parse_instant(r["captured_at"]), receipt_id), receipt_id)
        except (OSError, IntegrityError) as exc:
            raise LineageError(f"receipt {receipt_id} bytes are missing or corrupt: {exc}") from exc
        sources.add(r["source_id"])
    if len(sources) != 1:
        raise LineageError(f"receipt {receipt_id} is attributed to several sources: {sorted(sources)}")
    return sources.pop()


def release_sources(
    store: LocalObjectStore, core: dict[str, Any], _depth: int = 0, _index: dict[str, list[str]] | None = None
) -> frozenset[str]:
    """Every source behind a release core (stored or about to be stored), transitively."""
    index = _index if _index is not None else capture_index(store)
    if _depth > _MAX_DEPTH:
        raise LineageError("lineage is too deep or cyclic")
    sources: set[str] = set()
    for item in core["inputs"]:
        if "upstream" in item:
            up = item["upstream"]
            upstream_core = _verified(store, up["dataset_id"], up["content_sha256"])
            sources |= release_sources(store, upstream_core, _depth + 1, index)
        elif "receipts" in item:
            if not item["receipts"]:
                raise LineageError(f"input {item.get('series_id')} names no receipts")
            sources |= {receipt_source(store, rid, index) for rid in item["receipts"]}
        else:
            raise LineageError(f"unrecognised input: {sorted(item)}")
    if not sources:
        raise LineageError(f"release {core.get('dataset_id')} has no derivable source")
    return frozenset(sources)


def locate_release(store: LocalObjectStore, sha: str) -> str:
    """The dataset id of the stored release with this content hash."""
    found = [k.split("/")[1] for k in store.list("releases/") if k.endswith(f"/{sha}/manifest.json")]
    if len(found) != 1:
        raise LineageError(f"expected one stored release with content hash {sha}; found {len(found)}")
    return found[0]


def stored_release_sources(store: LocalObjectStore, sha: str) -> tuple[str, dict[str, Any], frozenset[str]]:
    dataset_id = locate_release(store, sha)
    core = _verified(store, dataset_id, sha)
    return dataset_id, core, release_sources(store, core)


def _verified(store: LocalObjectStore, dataset_id: str, sha: str) -> dict[str, Any]:
    from hio.publish.release import verify_release  # local: release imports this module

    try:
        return verify_release(store, dataset_id, sha)
    except (OSError, IntegrityError, ValueError) as exc:
        raise LineageError(f"release {dataset_id}@{sha} is missing or does not verify: {exc}") from exc
