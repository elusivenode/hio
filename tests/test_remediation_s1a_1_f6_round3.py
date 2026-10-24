"""Regression tests for F-REVIEW-2026-10-24-s1a-1-6, round 3 (OD-0025).

VERIFY-2026-10-24-s1a-1-2 (commit 9a94c3a) rejected round 2:
- a rollback that could not remove catalogue/b left it readable through the live store until
  the store was reopened;
- recovery removed keys by *intended* name, so after a write-once collision it deleted another
  writer's object.

Contract tested here (single writer; no general concurrent transactions):
1. while a transaction is unresolved, its objects are not observable through get, exists, list
   or snapshot, from any open store;
2. rollback and recovery remove only objects this transaction created;
3. a failed rollback or a crash leaves a durable journal, and the next open recovers from it.
The crash tests kill a child process with os._exit, so no rollback or finally block runs.
"""

import os
import subprocess
import sys

import pytest

from hio.storage.objectstore import LocalObjectStore, StagedWrites, WriteOnceViolation


def staged_pair(root):
    store = LocalObjectStore(root)
    (store.root / "catalogue").mkdir(exist_ok=True)  # an existing directory: the journalled path
    staged = StagedWrites(store)
    staged.add("catalogue/a", b"a")
    staged.add("catalogue/b", b"b")
    return store, staged


def fail_for(real, suffix):
    def wrapper(path, *args, **kwargs):
        if os.fspath(path).endswith(suffix):
            raise OSError(f"induced {real.__name__} failure: {path}")
        return real(path, *args, **kwargs)

    return wrapper


def journal_files(store):
    d = store._journal_dir
    return sorted(p for p in d.iterdir() if p.is_file()) if d.is_dir() else []


def assert_invisible(store, key):
    assert not store.exists(key)
    assert key not in list(store.list())
    assert key not in store.snapshot()
    with pytest.raises(FileNotFoundError):
        store.get(key)


# --- 1. Codex's round-2 counterexample: a rollback that cannot finish -----------------------------


def test_f6_codex_round2_failed_rollback_exposes_nothing_before_or_after_reopen(tmp_path, monkeypatch):
    store, staged = staged_pair(tmp_path / "s")
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b"))
    monkeypatch.setattr(os, "unlink", fail_for(os.unlink, "catalogue/b"))
    with pytest.raises(OSError, match="induced chmod"):
        staged.commit()
    monkeypatch.undo()
    assert (store.root / "catalogue" / "b").is_file()  # still on disk: the rollback could not remove it
    for key in ("catalogue/a", "catalogue/b"):
        assert_invisible(store, key)  # ...but not observable through the live store
    assert store.snapshot() == {}
    assert len(journal_files(store)) == 1  # durable evidence for recovery
    reopened = LocalObjectStore(tmp_path / "s")
    assert reopened.snapshot() == {}
    assert journal_files(reopened) == []
    assert not (reopened.root / "catalogue" / "b").exists()


def test_f6_recovery_that_still_fails_keeps_the_journal_and_exposes_nothing(tmp_path, monkeypatch):
    store, staged = staged_pair(tmp_path / "s")
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b"))
    monkeypatch.setattr(os, "unlink", fail_for(os.unlink, "catalogue/b"))
    with pytest.raises(OSError):
        staged.commit()
    with pytest.raises(OSError, match="induced unlink"):
        LocalObjectStore(tmp_path / "s")  # opening fails closed while recovery cannot finish
    assert_invisible(store, "catalogue/b")
    assert len(journal_files(store)) == 1
    monkeypatch.undo()
    assert LocalObjectStore(tmp_path / "s").snapshot() == {}


# --- 2. Ownership: never remove another writer's object -------------------------------------------


def test_f6_codex_round2_collision_plus_failed_rollback_preserves_the_other_writers_object(
    tmp_path, monkeypatch
):
    store, staged = staged_pair(tmp_path / "s")
    real_put = LocalObjectStore.put

    def racing_put(self, key, data, *args, **kwargs):
        target = self.root / key
        if key == "catalogue/b" and not target.exists():
            target.write_bytes(b"other writer")  # another writer's file, outside this store's protocol
        return real_put(self, key, data, *args, **kwargs)

    monkeypatch.setattr(LocalObjectStore, "put", racing_put)
    monkeypatch.setattr(os, "unlink", fail_for(os.unlink, "catalogue/a"))  # rollback of a fails
    with pytest.raises(WriteOnceViolation):
        staged.commit()
    monkeypatch.undo()
    assert_invisible(store, "catalogue/a")
    assert store.get("catalogue/b") == b"other writer"
    reopened = LocalObjectStore(tmp_path / "s")
    assert reopened.snapshot() == {"catalogue/b": store.snapshot()["catalogue/b"]}
    assert reopened.get("catalogue/b") == b"other writer"
    assert journal_files(reopened) == []


def test_f6_a_legacy_intent_only_journal_is_refused_and_deletes_nothing(tmp_path):
    """A journal that lists intended keys without proof of creation cannot show ownership, so
    the store refuses to open rather than guess (the round-1/2 format)."""
    store = LocalObjectStore(tmp_path / "s")
    store.put("catalogue/b", b"committed")
    (store.root / ".journal").mkdir()
    (store.root / ".journal" / "old.json").write_text('["catalogue/b"]')
    with pytest.raises(RuntimeError, match="cannot prove ownership"):
        LocalObjectStore(tmp_path / "s")
    assert (store.root / "catalogue" / "b").read_bytes() == b"committed"


# --- 3. Crashes: a killed process leaves a durable journal ------------------------------------------

CHILD = r"""
import os, sys
from hio.storage.objectstore import LocalObjectStore, StagedWrites
root, fn, suffix = sys.argv[1:4]
store = LocalObjectStore(root)
staged = StagedWrites(store)
staged.add("catalogue/a", b"a")
staged.add("catalogue/b", b"b")
real = getattr(os, fn)
def die(*args, **kwargs):
    if any(isinstance(a, (str, os.PathLike)) and os.fspath(a).endswith(suffix) for a in args):
        os._exit(17)
    return real(*args, **kwargs)
setattr(os, fn, die)
staged.commit()
"""


def crash_child(root, fn, suffix):
    out = subprocess.run([sys.executable, "-c", CHILD, str(root), fn, suffix], capture_output=True, text=True)
    assert out.returncode == 17, out.stderr


@pytest.mark.parametrize(
    ("fn", "suffix", "on_disk"),
    [
        ("chmod", "catalogue/b", {"a", "b"}),  # killed after b was linked into place
        ("link", "catalogue/b", {"a"}),  # killed after b's claim, before its link
    ],
)
def test_f6_a_crash_mid_commit_is_invisible_to_an_open_store_and_recovered_on_reopen(
    tmp_path, fn, suffix, on_disk
):
    root = tmp_path / "s"
    reader = LocalObjectStore(root)  # opened before the crash
    (reader.root / "catalogue").mkdir()
    crash_child(root, fn, suffix)
    assert {p.name for p in (reader.root / "catalogue").iterdir() if not p.name.startswith(".")} == on_disk
    assert reader.snapshot() == {}
    for key in ("catalogue/a", "catalogue/b"):
        assert_invisible(reader, key)
    reopened = LocalObjectStore(root)
    assert reopened.snapshot() == {}
    assert journal_files(reopened) == []
    assert not any((reopened.root / "catalogue").iterdir())


def test_f6_a_torn_final_journal_line_is_ignored_by_recovery(tmp_path):
    """A claim is made durable before its link, so a torn last line means no link happened."""
    root = tmp_path / "s"
    (LocalObjectStore(root).root / "catalogue").mkdir()
    crash_child(root, "chmod", "catalogue/b")
    (journal,) = sorted((root / ".journal").iterdir())
    with open(journal, "a") as fh:
        fh.write('{"key": "catalogue/c", "de')
    reopened = LocalObjectStore(root)
    assert reopened.snapshot() == {}
    assert journal_files(reopened) == []


def test_f6_no_write_proceeds_while_a_transaction_is_unresolved(tmp_path, monkeypatch):
    """A freed inode can be reused by a later object (ext4 reuses them). A retry that wrote while
    the stale claim stood could have its committed object hidden and later removed, so every
    write first resolves the journal, and is refused while that cannot finish."""
    store, staged = staged_pair(tmp_path / "s")
    monkeypatch.setattr(os, "chmod", fail_for(os.chmod, "catalogue/b"))
    monkeypatch.setattr(os, "unlink", fail_for(os.unlink, "catalogue/b"))
    with pytest.raises(OSError):
        staged.commit()
    retry = StagedWrites(store)
    retry.add("catalogue/a", b"a")
    with pytest.raises(OSError, match="induced unlink"):
        retry.commit()  # refused: the earlier transaction still cannot be rolled back
    with pytest.raises(OSError, match="induced unlink"):
        store.put("catalogue/z", b"z")  # a single write is refused too
    monkeypatch.undo()
    assert store.snapshot() == {}
    retry = StagedWrites(store)
    for key in ("catalogue/a", "catalogue/b"):
        retry.add(key, key[-1].encode())
    retry.commit()  # recovers the old transaction first, then commits
    assert journal_files(store) == []
    reopened = LocalObjectStore(tmp_path / "s")
    assert reopened.get("catalogue/a") == b"a" and reopened.get("catalogue/b") == b"b"


def test_f6_committed_objects_stay_visible_and_a_later_commit_still_works(tmp_path):
    store, staged = staged_pair(tmp_path / "s")
    staged.commit()
    assert store.get("catalogue/a") == b"a" and store.get("catalogue/b") == b"b"
    assert journal_files(store) == []
    more = StagedWrites(store)
    more.add("catalogue/c", b"c")
    more.add("catalogue/d", b"d")
    more.commit()
    assert sorted(LocalObjectStore(tmp_path / "s").list()) == [
        "catalogue/a",
        "catalogue/b",
        "catalogue/c",
        "catalogue/d",
    ]
