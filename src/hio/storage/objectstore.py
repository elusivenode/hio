"""Local-filesystem object store (S1a; architecture §2 object layout, releases standard §1).

Objects are write-once: a second write to an existing key is refused by code (S1-A3), and
stored files are made read-only. Reads verify the content hash when the caller supplies one,
and content-addressed keys are verified automatically (OBS-INV-004).

StagedWrites collects several objects and writes none of them until commit(), so a refused
operation leaves the store unchanged (rights standard §3: no partial output). commit() is
all-or-nothing (F-REVIEW-2026-10-24-s1a-1-6):
- a group of objects under one new directory (a release) is built in a hidden staging area and
  appears with a single atomic directory rename;
- any other set is written under an intent journal: a failure rolls back the objects this
  commit wrote, and a journal left by a crash is rolled back when the store is next opened.
Hidden staging and journal directories are never listed as objects.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import tempfile
import uuid
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
        self._recover()

    # --- transaction support (StagedWrites) -------------------------------------------------------

    @property
    def _journal_dir(self) -> Path:
        return self.root / ".journal"

    @property
    def _staging_dir(self) -> Path:
        return self.root / ".staging"

    def _journal_begin(self, txn: str, keys: list[str]) -> None:
        self._journal_dir.mkdir(exist_ok=True)
        path = self._journal_dir / f"{txn}.json"
        path.write_text(json.dumps(sorted(keys)))
        _fsync_path(path)

    def _journal_end(self, txn: str) -> None:
        (self._journal_dir / f"{txn}.json").unlink(missing_ok=True)

    def _remove(self, key: str) -> None:
        """Remove an object written by an unfinished commit (never used on committed objects)."""
        path = self._path(key)
        if path.is_file():
            path.chmod(0o644)
            path.unlink()

    def _recover(self) -> None:
        """Roll back any commit interrupted by a crash, and clear abandoned staging areas."""
        if self._journal_dir.is_dir():
            for journal in sorted(self._journal_dir.glob("*.json")):
                for key in json.loads(journal.read_text()):
                    self._remove(key)
                journal.unlink()
        if self._staging_dir.is_dir():
            shutil.rmtree(self._staging_dir, onexc=_make_writable_and_retry)

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

    def put_if_absent_check(self, key: str, data: bytes) -> bool:
        """True if identical bytes already exist under key; False if the key is absent. Different
        bytes under an existing key raise. Writes nothing."""
        if not self.exists(key):
            return False
        if self.get(key) != data:
            raise WriteOnceViolation(f"different bytes for existing key: {key}")
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
            rel = path.relative_to(base)
            if path.is_file() and not any(part.startswith(".") for part in rel.parts):
                key = rel.as_posix()
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
        """All or nothing (see the module docstring)."""
        for key in self._pending:
            if self.store.exists(key):
                raise WriteOnceViolation(f"object appeared before commit: {key}")
        keys = sorted(self._pending)
        group = _new_group(self.store, keys)
        if group is not None:
            self._commit_group(group)
        else:
            self._commit_journalled(keys)
        self._pending.clear()
        return keys

    def _commit_group(self, group: str) -> None:
        """Build the whole new directory in staging, then rename it into place atomically."""
        txn = uuid.uuid4().hex
        stage_root = self.store._staging_dir / txn
        try:
            for key, data in sorted(self._pending.items()):
                path = stage_root / key
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "wb") as fh:
                    fh.write(data)
                    fh.flush()
                    os.fsync(fh.fileno())
                path.chmod(0o444)
            target = self.store.root / group
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.rename(stage_root / group, target)  # atomic; fails if the directory now exists
            except OSError as exc:
                if target.exists():
                    raise WriteOnceViolation(f"object group already exists: {group}") from exc
                raise
        finally:
            if stage_root.exists():
                shutil.rmtree(stage_root, onexc=_make_writable_and_retry)

    def _commit_journalled(self, keys: list[str]) -> None:
        txn = uuid.uuid4().hex
        self.store._journal_begin(txn, keys)
        written: list[str] = []
        try:
            for key in keys:
                self.store.put(key, self._pending[key])
                written.append(key)
        except BaseException:
            for key in written:
                self.store._remove(key)
            self.store._journal_end(txn)
            raise
        self.store._journal_end(txn)


def _new_group(store: LocalObjectStore, keys: list[str]) -> str | None:
    """The deepest common directory of the keys, if it does not exist yet; else None."""
    common = posixpath.commonpath([posixpath.dirname(k) for k in keys]) if keys else ""
    if not common or (store.root / common).exists():
        return None
    return common


def _fsync_path(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _make_writable_and_retry(func, path, _exc) -> None:
    os.chmod(path, 0o755 if os.path.isdir(path) else 0o644)
    func(path)
