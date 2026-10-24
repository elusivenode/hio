"""Releases: canonical rendering, manifest core, content identity, writing (releases standard §1–§2, §6).

Canonical rendering (fixed in S1a, recorded per file as `rendering`): CSV, UTF-8, LF line
endings, a header row, rows sorted, every value a string already in canonical form.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from hio.contracts.canonical import canonical_json, sha256_hex
from hio.contracts.manifest import content_sha256, release_id, validate_manifest_core
from hio.contracts.rights import Operation, RightsGate
from hio.storage.objectstore import LocalObjectStore, StagedWrites

CSV_RENDERING = "csv-utf8-lf-header-sorted-v1"


def render_csv(columns: Sequence[str], rows: Iterable[Sequence[str]]) -> bytes:
    body = sorted(tuple(r) for r in rows)
    for r in body:
        if len(r) != len(columns) or not all(isinstance(v, str) for v in r):
            raise ValueError(f"row does not match the columns or holds a non-string: {r}")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(body)
    return buf.getvalue().encode("utf-8")


@dataclass(frozen=True)
class Release:
    core: dict[str, Any]
    files: Mapping[str, bytes]

    @property
    def content_sha256(self) -> str:
        return content_sha256(self.core)

    @property
    def release_id(self) -> str:
        return release_id(self.content_sha256)

    @property
    def prefix(self) -> str:
        return f"releases/{self.core['dataset_id']}/{self.content_sha256}"


def make_release(core_fields: dict[str, Any], files: Mapping[str, bytes]) -> Release:
    """Attach the file hashes to the core and validate it. core_fields holds every core field
    except `files`."""
    core = dict(core_fields)
    core["files"] = [
        {"path": name, "sha256": sha256_hex(data), "rendering": CSV_RENDERING}
        for name, data in sorted(files.items())
    ]
    core["inputs"] = sorted(core["inputs"], key=canonical_json)
    validate_manifest_core(core)
    return Release(core, dict(files))


def write_release(
    store: LocalObjectStore, gate: RightsGate, release: Release, source_ids: Iterable[str]
) -> bool:
    """Store a release after the store_derived check. Returns False if this exact release
    (same content hash) is already stored: a deterministic rebuild is a no-op."""
    gate.authorise(Operation.STORE_DERIVED, source_ids)
    manifest_key = f"{release.prefix}/manifest.json"
    if store.exists(manifest_key):
        verify_release(store, release.core["dataset_id"], release.content_sha256)
        return False
    staged = StagedWrites(store)
    for name, data in sorted(release.files.items()):
        staged.add(f"{release.prefix}/{name}", data)
    staged.add(manifest_key, canonical_json(release.core))
    staged.commit()
    return True


def verify_release(store: LocalObjectStore, dataset_id: str, sha: str) -> dict[str, Any]:
    """Load a pinned release and verify every byte against its hash; return the core."""
    raw = store.get(f"releases/{dataset_id}/{sha}/manifest.json")
    core = json.loads(raw)
    if raw != canonical_json(core) or content_sha256(core) != sha:
        raise ValueError(f"manifest does not match its content hash {sha}")
    for f in core["files"]:
        store.get(f"releases/{dataset_id}/{sha}/{f['path']}", f["sha256"])
    return core
