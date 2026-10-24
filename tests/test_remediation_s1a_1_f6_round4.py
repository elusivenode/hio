"""Regression tests for F-REVIEW-2026-10-24-s1a-1-6, round 4 (OD-0025).

VERIFY-2026-10-24-s1a-1-3 (commit ff0dd81) rejected round 3: `_journal_claim` treated a short
`os.write` of b's claim as complete, linked b, and recovery then ignored the truncated final
line, so after a crash b stayed visible in the live store and after reopening.

Contract added here: a claim is complete, parseable and durable before its object is linked; a
short write is finished or the write fails before the link; and a journal whose final line is
truncated is trusted only when no object exists at an intended key it does not claim. Otherwise
the store fails closed (reads and opening raise, nothing is deleted, the journal stays).
"""

import json
import subprocess
import sys

import pytest

from hio.storage.objectstore import LocalObjectStore

CHILD = r"""
import os, sys
from hio.storage.objectstore import LocalObjectStore, StagedWrites
root, mode = sys.argv[1:3]
store = LocalObjectStore(root)
staged = StagedWrites(store)
staged.add("catalogue/a", b"a")
staged.add("catalogue/b", b"b")
real_write, real_chmod = os.write, os.chmod
state = {"short": False}
def short_write(fd, data):
    if b'"catalogue/b"' in bytes(data) and not state["short"]:
        state["short"] = True
        open(os.path.join(root, ".short-injected"), "w").close()  # proof the injection ran
        return real_write(fd, data[: len(data) // 2])  # a valid, honest short write
    if mode == "fail-rest" and state["short"]:
        raise OSError("induced: the rest of the claim cannot be written")
    return real_write(fd, data)
def die(path, *args, **kwargs):
    if os.fspath(path).endswith("catalogue/b"):
        os._exit(17)  # after os.link made b visible, before any rollback
    return real_chmod(path, *args, **kwargs)
os.write, os.chmod = short_write, die
try:
    staged.commit()
except OSError as exc:
    print("raised:", exc)
    sys.exit(3)
"""


def run_child(root, mode):
    return subprocess.run([sys.executable, "-c", CHILD, str(root), mode], capture_output=True, text=True)


def journal_files(root):
    d = root / ".journal"
    return sorted(p for p in d.iterdir() if p.is_file()) if d.is_dir() else []


def assert_invisible(store, key):
    assert not store.exists(key)
    assert key not in list(store.list())
    assert key not in store.snapshot()
    with pytest.raises(FileNotFoundError):
        store.get(key)


def test_f6_codex_round3_short_claim_write_then_crash_exposes_nothing(tmp_path):
    root = tmp_path / "s"
    reader = LocalObjectStore(root)  # opened before the crash
    (reader.root / "catalogue").mkdir()
    out = run_child(root, "short")
    assert out.returncode == 17, out.stdout + out.stderr
    assert (root / ".short-injected").exists()
    for key in ("catalogue/b", "catalogue/a"):
        assert_invisible(reader, key)  # Codex: the live store exposed b
    (journal,) = journal_files(root)
    for line in journal.read_text().splitlines()[1:]:
        json.loads(line)  # every claim line is complete: the short write was finished
    reopened = LocalObjectStore(root)
    assert reopened.snapshot() == {}
    assert journal_files(root) == []
    assert not any((root / "catalogue").iterdir())


def test_f6_a_claim_that_cannot_be_completed_fails_before_the_link(tmp_path):
    root = tmp_path / "s"
    (LocalObjectStore(root).root / "catalogue").mkdir()
    out = run_child(root, "fail-rest")
    assert out.returncode == 3 and "induced" in out.stdout, out.stdout + out.stderr
    assert (root / ".short-injected").exists()
    assert not (root / "catalogue" / "b").exists()  # never linked
    assert LocalObjectStore(root).snapshot() == {}
    assert journal_files(root) == []


def write_journal(root, keys, claims, torn):
    d = root / ".journal"
    d.mkdir(exist_ok=True)
    header = {"format": "hio-objectstore-journal/3", "txn": "t", "keys": keys}
    lines = [json.dumps(header)] + [json.dumps(c) for c in claims]
    (d / "t.json").write_text("\n".join(lines) + "\n" + torn)


def test_f6_a_truncated_journal_with_an_unclaimed_object_fails_closed(tmp_path):
    """If an intended key holds an object the journal does not claim, and the final line is
    truncated, nothing can prove whose object it is: refuse, delete nothing, keep the journal."""
    root = tmp_path / "s"
    store = LocalObjectStore(root)
    (root / "catalogue").mkdir()
    (root / "catalogue" / "b").write_bytes(b"b")  # linked without a complete claim
    write_journal(root, ["catalogue/a", "catalogue/b"], [], torn='{"key": "catalogue/b", "de')
    for read in (lambda: store.get("catalogue/b"), lambda: store.exists("catalogue/b"), store.snapshot):
        with pytest.raises(RuntimeError, match="unclaimed"):
            read()
    with pytest.raises(RuntimeError, match="unclaimed"):
        LocalObjectStore(root)
    assert (root / "catalogue" / "b").read_bytes() == b"b"
    assert len(journal_files(root)) == 1


def test_f6_a_truncated_journal_with_no_unclaimed_object_is_recovered(tmp_path):
    """A truncated final claim whose object was never linked (the crash came first) is safe."""
    root = tmp_path / "s"
    LocalObjectStore(root)
    (root / "catalogue").mkdir()
    write_journal(root, ["catalogue/a", "catalogue/b"], [], torn='{"key": "catalogue/a", "de')
    reopened = LocalObjectStore(root)
    assert reopened.snapshot() == {}
    assert journal_files(root) == []
