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

from hio.contracts.canonical import canonical_json
from hio.contracts.layout import CAPTURES_PREFIX, LINKS_PREFIX, link_record_key, receipt_key
from hio.contracts.observation import parse_instant
from hio.contracts.publications import PublicationMappingError, is_shared, link_datasets, owning_dataset
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


def link_index(store: LocalObjectStore) -> dict[str, list[str]]:
    """receipt id -> provenance-link keys (shared receipts only), from one listing."""
    index: dict[str, list[str]] = {}
    for key in store.list(LINKS_PREFIX):
        index.setdefault(key.rsplit("-", 1)[-1].removesuffix(".json"), []).append(key)
    return index


def rights_sources(
    store: LocalObjectStore,
    receipt_id: str,
    series_id: str | None,
    index: dict[str, list[str]],
    links: dict[str, list[str]],
) -> frozenset[str]:
    """The rights subject behind one receipt used for one series (F-REVIEW-2026-10-25-t0009-1, -2).

    Whether a receipt is shared is decided by its publication id against the fixed mapping in
    `hio.contracts.publications`, never by whether a link happens to exist. For a shared publication
    the subject is the dataset that mapping assigns the series to, and every capture of the receipt
    must have exactly its expected provenance link, byte for byte: a missing, substituted, extra or
    inconsistent link refuses. A single-dataset receipt is its own subject and may have no link."""
    published_as = receipt_source(store, receipt_id, index)
    found = set(links.get(receipt_id, []))
    if not is_shared(published_as):
        if found:
            raise LineageError(f"single-dataset receipt {receipt_id} has provenance links: {sorted(found)}")
        return frozenset({published_as})
    if series_id is None:
        raise LineageError(f"shared receipt {receipt_id} is used by an input that names no series")
    try:
        owner = owning_dataset(published_as, series_id)
    except PublicationMappingError as exc:
        raise LineageError(str(exc)) from exc
    expected: dict[str, bytes] = {}
    for key in index[receipt_id]:
        captured_at = parse_instant(json.loads(store.get(key))["captured_at"])
        link = {
            "publication_id": published_as,
            "receipt_id": receipt_id,
            "captured_at": captured_at,
            "datasets": link_datasets(published_as),
        }
        expected[link_record_key(published_as, captured_at, receipt_id)] = canonical_json(link)
    if found != set(expected):
        raise LineageError(
            f"provenance links of shared receipt {receipt_id} are missing or unexpected: "
            f"missing {sorted(set(expected) - found)}, unexpected {sorted(found - set(expected))}"
        )
    for key, content in expected.items():
        try:
            stored = store.get(key)
        except (OSError, IntegrityError) as exc:
            raise LineageError(f"provenance link {key} cannot be read: {exc}") from exc
        if stored != content:
            raise LineageError(f"provenance link {key} does not match the fixed publication mapping")
    return frozenset({owner})


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
    store: LocalObjectStore,
    core: dict[str, Any],
    _depth: int = 0,
    _index: dict[str, list[str]] | None = None,
    _links: dict[str, list[str]] | None = None,
) -> frozenset[str]:
    """Every source behind a release core (stored or about to be stored), transitively."""
    index = _index if _index is not None else capture_index(store)
    links = _links if _links is not None else link_index(store)
    if _depth > _MAX_DEPTH:
        raise LineageError("lineage is too deep or cyclic")
    sources: set[str] = set()
    for item in core["inputs"]:
        if "upstream" in item:
            up = item["upstream"]
            upstream_core = _verified(store, up["dataset_id"], up["content_sha256"])
            sources |= release_sources(store, upstream_core, _depth + 1, index, links)
        elif "receipts" in item:
            if not item["receipts"]:
                raise LineageError(f"input {item.get('series_id')} names no receipts")
            for rid in item["receipts"]:
                sources |= rights_sources(store, rid, item.get("series_id"), index, links)
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
