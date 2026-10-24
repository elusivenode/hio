"""Regression tests for F-REVIEW-2026-10-24-s1a-1-6, round 2 (OD-0024).

VERIFY-2026-10-24-s1a-1-1 (commit 0255cb2) rejected the first F6 remediation with a new
counterexample: on the journalled path (catalogue/ already exists), an OSError from os.chmod
after os.link has made catalogue/b visible left catalogue/b in the store, and the journal was
deleted, so reopening the store did not remove it either. These tests failed at 18c80f2.
"""

import os

import pytest

from hio.storage.objectstore import LocalObjectStore, StagedWrites, WriteOnceViolation


def staged_pair(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    (store.root / "catalogue").mkdir()  # an existing directory: the journalled path
    staged = StagedWrites(store)
    staged.add("catalogue/a", b"a")
    staged.add("catalogue/b", b"b")
    return store, staged


def fail_for(real, suffix, times=None):
    """Wrap an os function so it raises OSError for paths ending in suffix (always, or `times`)."""
    left = {"n": times}

    def wrapper(path, *args, **kwargs):
        if os.fspath(path).endswith(suffix) and (left["n"] is None or left["n"] > 0):
            if left["n"] is not None:
                left["n"] -= 1
            raise OSError(f"induced {real.__name__} failure: {path}")
        return real(path, *args, **kwargs)

    return wrapper


def journals(store):
    return sorted(p.name for p in store._journal_dir.glob("*.json")) if store._journal_dir.is_dir() else []


@pytest.mark.parametrize("times", [None, 1], ids=["persistent", "once"])
def test_f6_codex_counterexample_chmod_failure_after_link_leaves_nothing(tmp_path, monkeypatch, times):
    """Codex: inject OSError at os.chmod for catalogue/b after os.link created it."""
    store, staged = staged_pair(tmp_path)
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b", times))
    with pytest.raises(OSError, match="induced chmod"):
        staged.commit()
    assert store.snapshot() == {}
    assert journals(store) == []
    monkeypatch.undo()
    assert LocalObjectStore(tmp_path / "s").snapshot() == {}


def test_f6_a_rollback_that_cannot_finish_keeps_its_journal_for_recovery(tmp_path, monkeypatch):
    """If the rollback itself cannot remove an object, the journal must survive so the next open
    of the store removes it; deleting the journal first is what made Codex's case permanent."""
    store, staged = staged_pair(tmp_path)
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b"))
    monkeypatch.setattr(os, "unlink", fail_for(os.unlink, "catalogue/b"))
    with pytest.raises(OSError, match="induced chmod"):
        staged.commit()
    assert len(journals(store)) == 1
    monkeypatch.undo()
    reopened = LocalObjectStore(tmp_path / "s")
    assert reopened.snapshot() == {}
    assert journals(reopened) == []


def test_f6_rollback_never_removes_an_object_this_commit_did_not_write(tmp_path, monkeypatch):
    """A key that another writer creates between the pre-commit check and the write raises
    WriteOnceViolation; the rollback removes this commit's catalogue/a but keeps the other
    writer's catalogue/b."""
    store, staged = staged_pair(tmp_path)
    real_put = LocalObjectStore.put

    def racing_put(self, key, data):
        if key == "catalogue/b" and not self.exists(key):
            real_put(self, key, b"other writer")
        return real_put(self, key, data)

    monkeypatch.setattr(LocalObjectStore, "put", racing_put)
    with pytest.raises(WriteOnceViolation):
        staged.commit()
    monkeypatch.undo()
    assert not store.exists("catalogue/a")
    assert store.get("catalogue/b") == b"other writer"
    assert journals(store) == []


def test_f6_a_failed_single_put_removes_its_own_object(tmp_path, monkeypatch):
    """put() is write-once and atomic on its own: a failure after the link removes the object."""
    store = LocalObjectStore(tmp_path / "s")
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b", 1))
    with pytest.raises(OSError, match="induced chmod"):
        store.put("catalogue/b", b"b")
    assert not store.exists("catalogue/b")
    store.put("catalogue/b", b"b")  # and the key is still writable once
    assert store.get("catalogue/b") == b"b"
