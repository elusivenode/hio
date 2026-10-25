"""Object store over a conditional-create blob backend (T-0009; the cloud interface, no network).

The backend protocol deliberately has **no overwrite and no delete**: the store layer can only create
a new object (an `If-None-Match: *` put), read, stat, list and list versions. Immutability is then a
property of the type, not of a convention, and a storage identity needs no delete permission.
Server-side controls (an immutability policy, versioning, a writer role without delete) are the
second layer; `get` also refuses an object that has more than one version, which is what an
out-of-band overwrite leaves behind when those controls are off.

Object storage has no multi-object transaction. `BlobStagedWrites` therefore commits in a fixed
order, so that a reader never sees a record that points at missing bytes or at an unfinished
release, and a failed commit is resumed by retrying: an object that already exists with identical
bytes is skipped, and one with different bytes refuses. The order is: raw bytes and release data
files; the release manifest; catalogue records; processing outcomes; capture-run records last.
Everything else (the S1a object-store semantics: write-once, content-addressed keys verified on
read) is the same as `LocalObjectStore`. Equivalence is tested, not assumed.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from hio.contracts.canonical import sha256_hex
from hio.storage.objectstore import _KEY, IntegrityError, WriteOnceViolation, _verify_content_addressed


class BlobExists(Exception):
    """A conditional create found the key already present."""


@dataclass(frozen=True)
class BlobInfo:
    key: str
    version_id: str
    written_at: datetime  # assigned by the storage provider, never by HIO (HIO-ADR-0012 C5)
    size: int


class BlobBackend(Protocol):
    def create(self, key: str, data: bytes) -> BlobInfo: ...  # raises BlobExists
    def read(self, key: str) -> bytes: ...  # raises KeyError
    def stat(self, key: str) -> BlobInfo | None: ...
    def keys(self, prefix: str) -> Iterator[str]: ...
    def versions(self, key: str) -> list[BlobInfo]: ...


def _rank(key: str) -> int:
    if key.startswith("catalogue/attempts/"):
        return 5
    if key.startswith("catalogue/processed/"):
        return 4
    if key.startswith("catalogue/captures/"):
        return 3  # a capture record appears only after its bytes and its provenance link
    if key.startswith("releases/") and key.endswith("/manifest.json"):
        return 1
    if key.startswith(("receipts/", "releases/", "artefacts/")):
        return 0
    return 2


class BlobObjectStore:
    def __init__(self, backend: BlobBackend) -> None:
        self.backend = backend

    @staticmethod
    def _check(key: str) -> str:
        if not _KEY.match(key) or ".." in key.split("/"):
            raise ValueError(f"invalid object key: {key!r}")
        return key

    def exists(self, key: str) -> bool:
        return self.backend.stat(self._check(key)) is not None

    def put(self, key: str, data: bytes) -> str:
        self._check(key)
        _verify_content_addressed(key, data)
        try:
            self.backend.create(key, data)
        except BlobExists:
            raise WriteOnceViolation(f"object already exists: {key}") from None
        return key

    def put_if_absent(self, key: str, data: bytes) -> bool:
        if self.exists(key):
            if self.get(key) != data:
                raise WriteOnceViolation(f"different bytes for existing key: {key}")
            return False
        self.put(key, data)
        return True

    def put_if_absent_check(self, key: str, data: bytes) -> bool:
        if not self.exists(key):
            return False
        if self.get(key) != data:
            raise WriteOnceViolation(f"different bytes for existing key: {key}")
        return True

    def get(self, key: str, sha256: str | None = None) -> bytes:
        self._check(key)
        versions = self.backend.versions(key)
        if not versions:
            raise FileNotFoundError(key)
        if len(versions) != 1:
            raise IntegrityError(f"{key} has {len(versions)} versions: it was overwritten or replaced")
        data = self.backend.read(key)
        _verify_content_addressed(key, data)
        if sha256 is not None and sha256_hex(data) != sha256:
            raise IntegrityError(f"hash mismatch for {key}")
        return data

    def list(self, prefix: str = "") -> Iterator[str]:
        for key in sorted(self.backend.keys(prefix)):
            if not any(part.startswith(".") for part in key.split("/")):
                yield key

    def snapshot(self) -> dict[str, str]:
        return {k: sha256_hex(self.get(k)) for k in self.list()}

    def write_time(self, key: str) -> datetime:
        """The provider-assigned write time of the object (the witness ADR-0012 C5 needs later)."""
        info = self.backend.stat(self._check(key))
        if info is None:
            raise FileNotFoundError(key)
        return info.written_at

    def staged(self) -> BlobStagedWrites:
        return BlobStagedWrites(self)


class BlobStagedWrites:
    def __init__(self, store: BlobObjectStore) -> None:
        self.store = store
        self._pending: dict[str, bytes] = {}

    def add(self, key: str, data: bytes) -> None:
        if key in self._pending:
            raise WriteOnceViolation(f"object is staged twice: {key}")
        self.store._check(key)
        _verify_content_addressed(key, data)
        self._pending[key] = data

    def commit(self) -> list[str]:
        keys = sorted(self._pending, key=lambda k: (_rank(k), k))
        todo = []
        for key in keys:  # refuse before writing anything if an existing object differs
            if self.store.exists(key):
                if self.store.get(key) != self._pending[key]:
                    raise WriteOnceViolation(f"different bytes for existing key: {key}")
            else:
                todo.append(key)
        for key in todo:
            self.store.put(key, self._pending[key])
        self._pending.clear()
        return keys
