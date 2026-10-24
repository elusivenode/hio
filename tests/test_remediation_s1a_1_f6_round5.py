"""Regression tests for F-REVIEW-2026-10-24-s1a-1-6, round 5 (OD-0025).

VERIFY-2026-10-24-s1a-1-4 (commit 873fc69) rejected round 4: `get` checked the journal and then
opened the object, so one reader paused between the two could return an object that the sole
writer had linked but not yet committed.

Publication point tested here: an object is committed when its transaction's journal is removed
after a successful commit. A supported read opens the object first and only then validates,
while holding it open, that no unresolved journal claims that file and that the key still
names it. Each test interleaves one writer thread and one reader thread (separate store
instances) with events, so the timing is forced, not hoped for.
"""

import io
import os
import threading

import pytest

from hio.storage.objectstore import LocalObjectStore, StagedWrites

KEY = "catalogue/b"
TIMEOUT = 10


class Interleaving:
    """Pause the reader just before it first touches KEY's file, run the writer until b is
    linked and paused (journal unresolved), then let the reader continue."""

    def __init__(self, monkeypatch, reader_hooks):
        self.reader_at_access = threading.Event()
        self.writer_linked = threading.Event()
        self.release_writer = threading.Event()
        self.reader_thread = None
        real_chmod = os.chmod

        def writer_chmod(path, *args, **kwargs):
            if os.fspath(path).endswith(KEY) and threading.current_thread() is not self.reader_thread:
                self.writer_linked.set()  # b is linked; the journal is still unresolved
                assert self.release_writer.wait(TIMEOUT)
            return real_chmod(path, *args, **kwargs)

        monkeypatch.setattr(os, "chmod", writer_chmod)
        for hook in reader_hooks:
            self._pause_reader(monkeypatch, *hook)

    def _pause_reader(self, monkeypatch, owner, name, any_target=False):
        real = getattr(owner, name)
        state = {"paused": False}

        def hooked(*args, **kwargs):
            target = args[0] if args else None
            if (
                threading.current_thread() is self.reader_thread
                and not state["paused"]
                and (
                    any_target or (isinstance(target, (str, os.PathLike)) and os.fspath(target).endswith(KEY))
                )
            ):
                state["paused"] = True
                self.reader_at_access.set()
                assert self.writer_linked.wait(TIMEOUT)
            return real(*args, **kwargs)

        monkeypatch.setattr(owner, name, hooked)

    def run(self, root, read):
        reader_store = LocalObjectStore(root)
        writer_store = LocalObjectStore(root)
        staged = StagedWrites(writer_store)
        staged.add(KEY, b"b")
        result = {}

        def reader():
            try:
                result["value"] = read(reader_store)
            except BaseException as exc:
                result["error"] = exc

        def writer():
            try:
                staged.commit()
            except BaseException as exc:
                result["writer_error"] = exc

        self.reader_thread = threading.Thread(target=reader)
        self.reader_thread.start()
        assert self.reader_at_access.wait(TIMEOUT), "the reader never reached the object"
        writer_thread = threading.Thread(target=writer)
        writer_thread.start()
        assert self.writer_linked.wait(TIMEOUT)
        assert (root / ".journal").is_dir() and any((root / ".journal").iterdir())
        self.reader_thread.join(TIMEOUT)  # the reader finishes while the writer is unresolved
        assert not self.reader_thread.is_alive()
        self.release_writer.set()
        writer_thread.join(TIMEOUT)
        assert "writer_error" not in result, result
        assert LocalObjectStore(root).get(KEY) == b"b"  # and it is committed afterwards
        return result


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "s"
    LocalObjectStore(r)
    (r / "catalogue").mkdir()  # an existing directory: the journalled path
    return r


# The reader is paused at whichever file access it makes first for KEY: the unfixed code reads
# through pathlib (io.open), the fixed code through os.open.
READ_HOOKS = [(io, "open"), (os, "open")]


def test_f6_codex_round4_get_paused_before_its_read_cannot_return_an_uncommitted_object(root, monkeypatch):
    result = Interleaving(monkeypatch, READ_HOOKS).run(root, lambda s: s.get(KEY))
    assert result.get("value") != b"b", "get returned b while its transaction was unresolved"
    assert isinstance(result.get("error"), FileNotFoundError), result


def test_f6_list_paused_before_enumerating_cannot_list_an_uncommitted_object(root, monkeypatch):
    from pathlib import Path

    result = Interleaving(monkeypatch, [(Path, "rglob", True)]).run(root, lambda s: list(s.list()))
    assert "error" not in result, result
    assert KEY not in result["value"]


def test_f6_snapshot_paused_before_enumerating_cannot_include_an_uncommitted_object(root, monkeypatch):
    from pathlib import Path

    result = Interleaving(monkeypatch, [(Path, "rglob", True)]).run(root, lambda s: s.snapshot())
    assert "error" not in result, result
    assert KEY not in result["value"]


def test_f6_exists_paused_before_its_check_cannot_report_an_uncommitted_object(root, monkeypatch):
    from pathlib import Path

    result = Interleaving(monkeypatch, [(Path, "is_file"), (os, "open")]).run(root, lambda s: s.exists(KEY))
    assert result == {"value": False}, result


def test_f6_a_read_that_overlaps_a_rollback_does_not_return_the_rolled_back_object(root, monkeypatch):
    """The reader opens b while it is linked and unresolved; the writer then rolls back and
    resolves its journal before the reader validates. The reader must not return b."""
    reader_store = LocalObjectStore(root)
    writer_store = LocalObjectStore(root)
    opened, rolled_back = threading.Event(), threading.Event()
    real_chmod, real_fstat = os.chmod, os.fstat
    reader_thread = None

    def writer_chmod(path, *args, **kwargs):
        if os.fspath(path).endswith(KEY) and threading.current_thread() is not reader_thread:
            assert opened.wait(TIMEOUT)  # let the reader open b first
            raise OSError("induced: roll this transaction back")
        return real_chmod(path, *args, **kwargs)

    def reader_fstat(fd, *args, **kwargs):
        st = real_fstat(fd, *args, **kwargs)
        if threading.current_thread() is reader_thread and not opened.is_set():
            opened.set()  # the reader holds b open
            assert rolled_back.wait(TIMEOUT)  # ...and validates only after the rollback resolved
        return st

    monkeypatch.setattr(os, "chmod", writer_chmod)
    monkeypatch.setattr(os, "fstat", reader_fstat)
    staged = StagedWrites(writer_store)
    staged.add(KEY, b"b")
    result = {}

    def reader():
        assert writer_linked_b.wait(TIMEOUT)
        try:
            result["value"] = reader_store.get(KEY)
        except BaseException as exc:
            result["error"] = exc

    writer_linked_b = threading.Event()
    real_link = os.link

    def writer_link(src, dst, *args, **kwargs):
        out = real_link(src, dst, *args, **kwargs)
        if os.fspath(dst).endswith(KEY):
            writer_linked_b.set()
        return out

    monkeypatch.setattr(os, "link", writer_link)
    reader_thread = threading.Thread(target=reader)
    reader_thread.start()
    with pytest.raises(OSError, match="induced"):
        staged.commit()
    assert not (root / KEY).exists() and not any((root / ".journal").iterdir())  # resolved
    rolled_back.set()
    reader_thread.join(TIMEOUT)
    assert not reader_thread.is_alive()
    assert result.get("value") != b"b", "get returned an object whose transaction rolled back"
    assert isinstance(result.get("error"), FileNotFoundError), result
