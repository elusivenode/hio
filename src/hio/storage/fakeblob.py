"""An in-memory blob backend with the semantics HIO relies on (conditional create, versions,
provider-assigned write time, optional server-side immutability). It contains no network code and is
the test double for the cloud store: it lets the whole pipeline run against the BlobBackend contract.

`overwrite` and `delete` exist ONLY here, as the out-of-band actions of a privileged or compromised
identity. They are not part of the BlobBackend protocol, so HIO code cannot call them.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime

from hio.storage.blobstore import BlobExists, BlobInfo


class ImmutabilityViolation(Exception):
    """The server-side immutability policy refused an overwrite or delete."""


class FakeBlobBackend:
    def __init__(self, immutable: bool = True, clock: Callable[[], datetime] | None = None) -> None:
        self.immutable = immutable
        self._clock = clock or (lambda: datetime.now(UTC))
        self._blobs: dict[str, list[tuple[BlobInfo, bytes]]] = {}
        self.fail_after: int | None = None  # fault injection: raise after this many successful creates
        self._creates = 0

    def create(self, key: str, data: bytes) -> BlobInfo:
        if self.fail_after is not None and self._creates >= self.fail_after:
            raise ConnectionError("injected backend failure")
        if self._blobs.get(key):
            raise BlobExists(key)
        info = BlobInfo(key, f"v{len(self._blobs.get(key, [])) + 1}", self._clock(), len(data))
        self._blobs.setdefault(key, []).append((info, data))
        self._creates += 1
        return info

    def read(self, key: str) -> bytes:
        return self._blobs[key][-1][1]

    def stat(self, key: str) -> BlobInfo | None:
        return self._blobs[key][-1][0] if self._blobs.get(key) else None

    def keys(self, prefix: str) -> Iterator[str]:
        return (k for k, v in self._blobs.items() if v and k.startswith(prefix))

    def versions(self, key: str) -> list[BlobInfo]:
        return [i for i, _ in self._blobs.get(key, [])]

    # --- out-of-band actions (not in the protocol) ------------------------------------------------
    def overwrite(self, key: str, data: bytes) -> BlobInfo:
        if self.immutable:
            raise ImmutabilityViolation(f"overwrite refused: {key}")
        info = BlobInfo(key, f"v{len(self._blobs[key]) + 1}", self._clock(), len(data))
        self._blobs[key].append((info, data))  # versioning keeps the earlier version
        return info

    def delete(self, key: str) -> None:
        if self.immutable:
            raise ImmutabilityViolation(f"delete refused: {key}")
        self._blobs[key].clear()  # the current version is gone; versions of it are not recoverable here
