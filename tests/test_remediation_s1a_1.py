"""Regression tests for REVIEW-2026-10-24-s1a-1 findings 1, 2, 3, 5 and 6 (OD-0023).

Each section starts with Codex's counterexample from the review record, reproduced as a test
that failed at the reviewed head (98e6a8e) and passes after the fix.
"""

import os

import pytest

from hio.storage.objectstore import LocalObjectStore, StagedWrites, WriteOnceViolation

# --- F-REVIEW-2026-10-24-s1a-1-6: multi-object writes are atomic ---------------------------------


def test_f6_codex_counterexample_leaves_no_partial_objects(tmp_path):
    """Codex: with catalogue/b already a directory and catalogue/a, catalogue/b staged, commit()
    raised on b but catalogue/a remained."""
    store = LocalObjectStore(tmp_path / "s")
    (store.root / "catalogue" / "b").mkdir(parents=True)
    staged = StagedWrites(store)
    staged.add("catalogue/a", b"1")
    staged.add("catalogue/b", b"2")
    with pytest.raises(WriteOnceViolation):
        staged.commit()
    assert not store.exists("catalogue/a")
    assert list(store.list()) == []


@pytest.mark.parametrize(
    "keys",
    [
        ["releases/ds/abc/data.csv", "releases/ds/abc/manifest.json"],  # one new directory group
        ["catalogue/x/1.json", "catalogue/y/2.json"],  # spread across existing prefixes
    ],
)
def test_f6_induced_failure_mid_commit_exposes_nothing(tmp_path, monkeypatch, keys):
    store = LocalObjectStore(tmp_path / "s")
    real_fsync = os.fsync
    calls = {"n": 0}

    def failing_fsync(fd):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("induced failure")
        return real_fsync(fd)

    staged = StagedWrites(store)
    for k in keys:
        staged.add(k, b"x")
    monkeypatch.setattr(os, "fsync", failing_fsync)
    with pytest.raises(OSError, match="induced"):
        staged.commit()
    monkeypatch.undo()
    assert list(store.list()) == []
    assert all(not store.exists(k) for k in keys)


def test_f6_an_interrupted_journalled_commit_is_rolled_back_when_the_store_is_reopened(tmp_path):
    """A crash after the first object of a journalled commit: the next open removes it."""
    store = LocalObjectStore(tmp_path / "s")
    store._journal_begin("txn1", ["catalogue/x/1.json", "catalogue/y/2.json"])
    store.put("catalogue/x/1.json", b"partial")
    reopened = LocalObjectStore(tmp_path / "s")
    assert list(reopened.list()) == []


def test_f6_successful_commits_and_write_once_still_hold(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    for keys in (
        ["releases/ds/abc/data.csv", "releases/ds/abc/manifest.json"],
        ["catalogue/p/1", "catalogue/q/2"],
    ):
        staged = StagedWrites(store)
        for k in keys:
            staged.add(k, k.encode())
        staged.commit()
        assert all(store.get(k) == k.encode() for k in keys)
    again = StagedWrites(store)
    again.add("releases/ds/abc/extra.csv", b"y")  # the group exists: falls back to the journal path
    again.commit()
    with pytest.raises(WriteOnceViolation):
        StagedWrites(store).add("releases/ds/abc/data.csv", b"z")
    assert all(p.stat().st_mode & 0o222 == 0 for p in (store.root / "releases").rglob("*") if p.is_file())


def test_f6_a_failing_row_leaves_no_partial_catalogue_transaction(tmp_path):
    """Ingest is one catalogue transaction: a row that cannot be placed in time (captured before
    its documented release) must not leave the earlier rows' vintages behind."""
    from hio.marketdata.knowability import UnplaceableValue
    from hio.marketdata.series import CaptureMode
    from hio.marketdata.vintages import VintageStore
    from tests.helpers import SERIES, ingest_text, receipt_text, utc

    vs = VintageStore(LocalObjectStore(tmp_path / "s"), SERIES)
    rows = [
        "synthetic.rate,2026-01-09,3.60",
        "synthetic.rate,2026-01-12,3.61",
    ]  # the 12th is not yet released
    with pytest.raises(UnplaceableValue):
        ingest_text(
            vs,
            tmp_path,
            "synthetic.daily_source",
            receipt_text("mixed", rows),
            utc(2026, 1, 11, 12),
            CaptureMode.SCHEDULED,
        )
    assert not any(k.startswith("catalogue/vintages/") for k in vs.store.list())
    assert vs.all_vintages() == []
    assert VintageStore(vs.store, SERIES).all_vintages() == []
