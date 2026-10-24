"""Local-filesystem object store (S1a; architecture §2 object layout, releases standard §1).

Objects are write-once: a second write to an existing key is refused by code (S1-A3), and
stored files are made read-only. Reads verify the content hash when the caller supplies one,
and content-addressed keys are verified automatically (OBS-INV-004).

StagedWrites collects several objects and writes none of them until commit(), so a refused
operation leaves the store unchanged (rights standard §3: no partial output).
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Iterator
from pathlib import Path

from hio.contracts.canonical import sha256_hex

_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]*(/[a-z0-9][a-z0-9._-]*)*$")
_HASH_SEGMENT = re.compile(r"^[0-9a-f]{64}$")


class WriteOnceViolation(Exception):
    pass


class IntegrityError(Exception):
    pass


class LocalObjectStore:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not _KEY.match(key) or ".." in key.split("/"):
            raise ValueError(f"invalid object key: {key!r}")
        return self.root / key

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def put(self, key: str, data: bytes) -> str:
        """Write once. Refuses any second write to the same key, identical bytes included."""
        path = self._path(key)
        _verify_content_addressed(key, data)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            try:
                os.link(tmp, path)  # atomic, and fails if the key exists
            except FileExistsError:
                raise WriteOnceViolation(f"object already exists: {key}") from None
            os.chmod(path, 0o444)
        finally:
            os.unlink(tmp)
        return key

    def put_if_absent(self, key: str, data: bytes) -> bool:
        """Content-addressed idempotent write: True if written; False if the identical object
        already exists (a duplicate receipt is a no-op, observations standard §6). Different
        bytes under an existing key raise."""
        if self.exists(key):
            if self.get(key) != data:
                raise WriteOnceViolation(f"different bytes for existing key: {key}")
            return False
        self.put(key, data)
        return True

    def get(self, key: str, sha256: str | None = None) -> bytes:
        data = self._path(key).read_bytes()
        _verify_content_addressed(key, data)
        if sha256 is not None and sha256_hex(data) != sha256:
            raise IntegrityError(f"hash mismatch for {key}")
        return data

    def list(self, prefix: str = "") -> Iterator[str]:
        base = self.root
        for path in sorted(base.rglob("*")):
            if path.is_file() and not path.name.startswith(".tmp-"):
                key = path.relative_to(base).as_posix()
                if key.startswith(prefix):
                    yield key

    def snapshot(self) -> dict[str, str]:
        """key -> sha256 of every object; used to prove that refused operations write nothing."""
        return {k: sha256_hex(self._path(k).read_bytes()) for k in self.list()}


def _verify_content_addressed(key: str, data: bytes) -> None:
    """Receipts are keyed by the SHA-256 of their bytes: receipts/<source>/<yyyy>/<mm>/<sha>."""
    last = key.rsplit("/", 1)[-1]
    if key.startswith("receipts/") and _HASH_SEGMENT.match(last) and sha256_hex(data) != last:
        raise IntegrityError(f"receipt bytes do not match their key: {key}")


class StagedWrites:
    """All-or-nothing writes: nothing reaches the store until commit()."""

    def __init__(self, store: LocalObjectStore) -> None:
        self.store = store
        self._pending: dict[str, bytes] = {}

    def add(self, key: str, data: bytes) -> None:
        if key in self._pending or self.store.exists(key):
            raise WriteOnceViolation(f"object already exists or is staged: {key}")
        self.store._path(key)  # validate the key now, not at commit
        _verify_content_addressed(key, data)
        self._pending[key] = data

    def commit(self) -> list[str]:
        for key in self._pending:
            if self.store.exists(key):
                raise WriteOnceViolation(f"object appeared before commit: {key}")
        written = [self.store.put(k, v) for k, v in sorted(self._pending.items())]
        self._pending.clear()
        return written
