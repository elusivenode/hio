"""Local-filesystem object store (S1a; architecture §2 object layout, releases standard §1).

Objects are write-once: a second write to an existing key is refused by code (S1-A3), and
stored files are made read-only. Reads verify the content hash when the caller supplies one,
and content-addressed keys are verified automatically (OBS-INV-004).

StagedWrites collects several objects and writes none of them until commit(), so a refused
operation leaves the store unchanged (rights standard §3: no partial output). commit() is
all-or-nothing (F-REVIEW-2026-10-24-s1a-1-6):
- a group of objects under one new directory (a release) is built in a hidden staging area and
  appears with a single atomic directory rename;
- any other set is written under a journal that durably claims each object by file identity
  (device, inode) before linking it (round 3, VERIFY-2026-10-24-s1a-1-2):
  - while a journal is unresolved, the objects it owns are not observable through get, exists,
    list or snapshot, from any open store;
  - rollback and recovery remove only objects whose identity matches a claim, never another
    writer's object at the same key;
  - a failed rollback or a crash leaves the journal, and the next open rolls back. If that still
    cannot finish, opening fails.

  A single writer is assumed; this is not general concurrent-transaction support.

Publication point (round 5, VERIFY-2026-10-24-s1a-1-4): a journalled object is committed when its
journal is removed after a successful commit. Reads (get, exists, list, snapshot) open the object
first and then, holding it open, confirm that no unresolved journal claims that file and that
the key still names it, so a concurrent reader never returns an uncommitted or rolled-back object.
Hidden staging and journal directories are never listed as objects.
"""

from __future__ import annotations

import contextlib
import functools
import json
import os
import posixpath
import re
import shutil
import stat
import tempfile
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

from hio.contracts.canonical import sha256_hex

_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]*(/[a-z0-9][a-z0-9._-]*)*$")
_HASH_SEGMENT = re.compile(r"^[0-9a-f]{64}$")
_JOURNAL_FORMAT = "hio-objectstore-journal/3"  # JSON lines: a header with the intended keys, then claims


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

    def _journal_begin(self, txn: str, keys: list[str]) -> Path:
        """Create a durable journal for one transaction, after resolving any earlier one. The
        header names the intended keys, so a truncated claim can be checked against them."""
        self._resolve_before_write()
        self._journal_dir.mkdir(exist_ok=True)
        path = self._journal_dir / f"{txn}.json"
        header = {"format": _JOURNAL_FORMAT, "txn": txn, "keys": sorted(keys)}
        with open(path, "x") as fh:
            fh.write(json.dumps(header) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        _fsync_path(self._journal_dir)
        return path

    def _journal_claim(self, journal: Path, key: str, st: os.stat_result) -> None:
        """Durably record, before the link, the identity of the file about to be placed at key.
        The link places that same inode, so an object at key belongs to this transaction only
        if its (device, inode) matches; another writer's object never does. The whole line is
        written (short writes are continued) and fsynced, or this raises and no link follows."""
        line = memoryview((json.dumps({"key": key, "dev": st.st_dev, "ino": st.st_ino}) + "\n").encode())
        fd = os.open(journal, os.O_WRONLY | os.O_APPEND)  # never re-creates a vanished journal
        try:
            while line:
                written = os.write(fd, line)
                if written <= 0:
                    raise OSError(f"journal claim for {key} made no progress")
                line = line[written:]
            os.fsync(fd)
        finally:
            os.close(fd)

    def _journal_end(self, journal: Path) -> None:
        journal.unlink(missing_ok=True)
        _fsync_path(self._journal_dir)  # a resurrected journal would roll back committed objects

    def _claims(self, journal: Path) -> list[tuple[str, int, int]]:
        lines = journal.read_text().splitlines()
        try:
            header = json.loads(lines[0]) if lines else None
        except json.JSONDecodeError:
            if len(lines) == 1:
                return []  # torn header: no claim can follow it
            raise
        if header is None:
            return []
        if not isinstance(header, dict) or header.get("format") != _JOURNAL_FORMAT:
            raise RuntimeError(
                f"journal {journal} lists intended keys only and cannot prove ownership of any "
                "object; the store will not open until it is inspected"
            )
        claims = []
        torn = False
        for n, line in enumerate(lines[1:], start=2):
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                if n == len(lines):
                    torn = True  # a crash while the final claim was being written
                    break
                raise
            claims.append((c["key"], c["dev"], c["ino"]))
        if torn:
            # A claim is complete and durable before its link, so a torn claim's object was never
            # linked. Trust that only when it is checkable: no intended key may hold an object
            # this journal does not claim. Otherwise nothing proves whose object it is.
            claimed = {k for k, _, _ in claims}
            unclaimed = [k for k in header["keys"] if k not in claimed and self._path(k).exists()]
            if unclaimed:
                raise RuntimeError(
                    f"journal {journal} ends in a truncated claim and intended keys {unclaimed} "
                    "hold unclaimed objects; the store fails closed until it is inspected"
                )
        return claims

    def _owned(self, key: str, dev: int, ino: int) -> bool:
        try:
            st = os.lstat(self._path(key))
        except FileNotFoundError:
            return False
        return (st.st_dev, st.st_ino) == (dev, ino)

    def _claimed(self, key: str, dev: int, ino: int) -> bool:
        """True if an unresolved journal claims this exact file at key."""
        if not self._journal_dir.is_dir():
            return False
        for journal in self._journal_dir.glob("*.json"):
            try:
                claims = self._claims(journal)
            except FileNotFoundError:
                continue  # resolved meanwhile; the caller's identity check decides
            if (key, dev, ino) in claims:
                return True
        return False

    def _is_committed(self, key: str, st: os.stat_result) -> bool:
        """The publication point for reads. The caller holds the file open (so its inode cannot
        be freed and reused) and calls this only afterwards. A writer claims a file before
        linking it and removes a rolled-back file before deleting its journal, so: if no
        unresolved journal claims this file now and the key still names it, its transaction
        committed (or it never belonged to one)."""
        if self._claimed(key, st.st_dev, st.st_ino):
            return False
        try:
            now = os.lstat(self._path(key))
        except FileNotFoundError:
            return False
        return (now.st_dev, now.st_ino) == (st.st_dev, st.st_ino)

    def _open_committed(self, key: str) -> tuple[int, os.stat_result] | None:
        """Open key's object and validate it; the caller closes the descriptor."""
        try:
            fd = os.open(self._path(key), os.O_RDONLY)
        except (FileNotFoundError, NotADirectoryError):
            return None
        try:
            st = os.fstat(fd)
            if stat.S_ISREG(st.st_mode) and self._is_committed(key, st):
                return fd, st
        except BaseException:
            os.close(fd)
            raise
        os.close(fd)
        return None

    def _read_committed(self, key: str) -> bytes:
        """Read key's object, then validate it while still holding it open."""
        fd = os.open(self._path(key), os.O_RDONLY)
        try:
            st = os.fstat(fd)
            chunks = []
            while chunk := os.read(fd, 1 << 20):
                chunks.append(chunk)
            if not stat.S_ISREG(st.st_mode) or not self._is_committed(key, st):
                raise FileNotFoundError(f"object not committed: {key}")
            return b"".join(chunks)
        finally:
            os.close(fd)

    def _rollback(self, journal: Path) -> None:
        """Remove the objects this journal's transaction created, then the journal. Raises if
        an object cannot be removed; the journal then stays, hiding it until recovery."""
        for key, dev, ino in self._claims(journal):
            if self._owned(key, dev, ino):
                self._remove(key)
            for tmp in self._path(key).parent.glob(".tmp-*"):  # a crash leaves the claimed temp file
                st = os.lstat(tmp)
                if (st.st_dev, st.st_ino) == (dev, ino):
                    os.unlink(tmp)
        self._journal_end(journal)

    def _remove(self, key: str) -> None:
        """Remove an object written by an unfinished commit (never used on committed objects).
        Raises if the object cannot be removed, so the caller keeps its journal."""
        path = self._path(key)
        if not path.is_file():
            return
        try:
            path.unlink()  # POSIX needs no write permission on the file itself
        except PermissionError:
            path.chmod(0o644)
            path.unlink()

    def _resolve_before_write(self) -> None:
        """No new write while a transaction is unresolved: a freed inode could be reused for the
        new object, and the stale claim would then hide and later remove it. Recover first; if
        recovery cannot finish, the write is refused (raises)."""
        if self._journal_dir.is_dir() and any(self._journal_dir.glob("*.json")):
            self._recover()

    def _recover(self) -> None:
        """Roll back any unresolved commit (a crash or a failed rollback), and clear abandoned
        staging areas. If a rollback still cannot finish, opening fails and the journal stays."""
        if self._journal_dir.is_dir():
            for journal in sorted(self._journal_dir.glob("*.json")):
                self._rollback(journal)
        if self._staging_dir.is_dir():
            shutil.rmtree(self._staging_dir, onexc=_make_writable_and_retry)

    def _path(self, key: str) -> Path:
        if not _KEY.match(key) or ".." in key.split("/"):
            raise ValueError(f"invalid object key: {key!r}")
        return self.root / key

    def exists(self, key: str) -> bool:
        opened = self._open_committed(key)
        if opened is None:
            return False
        os.close(opened[0])
        return True

    def put(self, key: str, data: bytes, *, claim: Callable[[os.stat_result], None] | None = None) -> str:
        """Write once. Refuses any second write to the same key, identical bytes included.
        A failure after the object became visible removes it again before re-raising.
        `claim` (used by journalled commits) receives the new file's identity before the link."""
        path = self._path(key)
        _verify_content_addressed(key, data)
        if claim is None:  # a transaction's own writes run under its (already resolved) journal
            self._resolve_before_write()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        linked = False
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            if claim is not None:
                claim(os.stat(tmp))
            try:
                os.link(tmp, path)  # atomic, and fails if the key exists
            except FileExistsError:
                raise WriteOnceViolation(f"object already exists: {key}") from None
            linked = True
            os.chmod(path, 0o444)
            os.unlink(tmp)
        except BaseException:
            if linked:
                with contextlib.suppress(OSError):  # a journalled caller retries and keeps its journal
                    self._remove(key)
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise
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
        data = self._read_committed(key)
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
                if key.startswith(prefix) and self.exists(key):  # validated per object
                    yield key

    def snapshot(self) -> dict[str, str]:
        """key -> sha256 of every object; used to prove that refused operations write nothing."""
        out = {}
        for k in self.list():
            try:
                out[k] = sha256_hex(self._read_committed(k))
            except FileNotFoundError:
                continue  # rolled back after it was listed
        return out


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
        store = self.store
        journal = store._journal_begin(uuid.uuid4().hex, keys)
        try:
            for key in keys:
                claim = functools.partial(store._journal_claim, journal, key)
                store.put(key, self._pending[key], claim=claim)
        except BaseException:
            # Removes only objects this transaction created (by identity). If that cannot
            # finish, the journal stays: its objects remain hidden, and the next open rolls back.
            with contextlib.suppress(OSError):
                store._rollback(journal)
            raise
        for parent in sorted({store._path(k).parent for k in keys}):
            _fsync_path(parent)  # the links are durable before the journal that could undo them goes
        store._journal_end(journal)


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
