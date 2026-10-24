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


# --- F-REVIEW-2026-10-24-s1a-1-3: receipt integrity before selection or use ---------------------------

from datetime import UTC, date, datetime  # noqa: E402

from hio.contracts.temporal import KnowledgeMode  # noqa: E402
from hio.jobs import s1a  # noqa: E402
from hio.marketdata.capture import receipt_key  # noqa: E402
from hio.marketdata.vintages import ReceiptIntegrityError, VintageStore  # noqa: E402
from hio.rights.gate import RightsGate  # noqa: E402
from hio.rights.register import load_synthetic  # noqa: E402
from tests.helpers import FIXTURES  # noqa: E402

WORLD = FIXTURES / "s1a_world"
RIGHTS = dict(load_synthetic(FIXTURES / "rights.yaml"))
CUTOFF = datetime(2026, 1, 29, tzinfo=UTC)
CODE = {"commit": "0" * 40, "lock_sha256": "1" * 64}


def world_store(root):
    world = s1a.load_world(WORLD)
    store = LocalObjectStore(root)
    vs = VintageStore(store, world.series)
    s1a.run_captures(world, vs, RightsGate(RIGHTS), s1a.capture_instants(date(2026, 1, 5), CUTOFF))
    return world, store, vs


def damage_receipt_of(vs, store, series_id, how):
    v = next(v for v in vs.all_vintages() if v.series_id == series_id)
    path = store.root / receipt_key(vs.series[series_id].source_id, v.captured_at, v.receipt_id)
    path.chmod(0o644)
    if how == "delete":
        path.unlink()
    else:
        path.write_bytes(b"# SYNTHETIC tampered\n")
    return v


@pytest.mark.parametrize("how", ["delete", "corrupt"])
def test_f3_codex_counterexample_a_missing_or_corrupt_receipt_blocks_selection_and_build(tmp_path, how):
    """Codex: after deleting the raw receipt of a valid AUD vintage, a new VintageStore returned
    it in as_captured_by_hio and build_releases produced an AUD release."""
    world, store, vs = world_store(tmp_path / "s")
    damage_receipt_of(vs, store, s1a.CASH_RATE, how)
    reopened = VintageStore(store, world.series)
    with pytest.raises(ReceiptIntegrityError):
        reopened.as_captured_by_hio(s1a.CASH_RATE, CUTOFF)
    with pytest.raises(ReceiptIntegrityError):
        s1a.build_releases(
            world, reopened, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
        )


def test_f3_intact_receipts_still_select_and_build(tmp_path):
    world, store, _ = world_store(tmp_path / "s")
    reopened = VintageStore(store, world.series)
    assert reopened.as_captured_by_hio(s1a.CASH_RATE, CUTOFF).values
    s1a.build_releases(
        world, reopened, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )


# --- F-REVIEW-2026-10-24-s1a-1-5: the rebuild check verifies the stored bytes ---------------------


def published_store(root):
    world, store, vs = world_store(root)
    gate = RightsGate(RIGHTS)
    releases = s1a.build_releases(world, vs, gate, RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE)
    s1a.publish_releases(vs, gate, releases, CUTOFF)
    return world, store, releases


def corrupt(store, key, data=b"corrupt"):
    path = store.root / key
    path.chmod(0o644)
    path.write_bytes(data)


@pytest.mark.parametrize("target", ["data.csv", "manifest.json"])
def test_f5_codex_counterexample_corrupt_stored_bytes_fail_the_rebuild_check(tmp_path, target):
    """Codex: after changing the AUD release data.csv to b'corrupt', rebuild_check returned True
    while verify_release raised IntegrityError."""
    world, store, releases = published_store(tmp_path / "s")
    corrupt(store, f"{releases['cash.aud.overnight'].prefix}/{target}")
    result = s1a.rebuild_check(
        world, store, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    assert result["cash.aud.overnight"] is False
    assert all(result[d] is True for d in result if d != "cash.aud.overnight")
    report = s1a.rebuild_report(
        world, store, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    assert report["cash.aud.overnight"].startswith(("corrupt", "differs"))


def test_f5_an_intact_store_still_reproduces(tmp_path):
    world, store, _ = published_store(tmp_path / "s")
    result = s1a.rebuild_check(
        world, store, RightsGate(RIGHTS), RIGHTS, KnowledgeMode.AS_CAPTURED_BY_HIO, CUTOFF, CODE
    )
    assert set(result.values()) == {True}


# --- F-REVIEW-2026-10-24-s1a-1-2: approval is specific to its consumer class ---------------------

from hio.contracts.status import Status  # noqa: E402
from hio.publish.status import RefusedUse, append_status, resolve_for_use  # noqa: E402
from hio.rights.model import ALL_PERMISSIONS, Permission, RightsRecord, Verification  # noqa: E402

PERMISSIVE = {
    sid: RightsRecord(
        sid, Verification.OWNER_VERIFIED, {p: Permission.parse("allow") for p in ALL_PERMISSIONS}
    )
    for sid in ("synthetic.rba", "synthetic.nyfed")
}
AUD = "cash.aud.overnight"


def approve(store, sha, cls):
    append_status(
        store,
        sha,
        Status.APPROVED_FOR_CONSUMER,
        "owner",
        "fixture",
        CUTOFF,
        gate=RightsGate(PERMISSIVE),
        source_ids=("synthetic.rba",),
        consumer_class=cls,
    )


def withdraw(store, sha, cls=None):
    append_status(store, sha, Status.WITHDRAWN, "owner", "fixture", CUTOFF, consumer_class=cls)


def use(store, sha, cls):
    return resolve_for_use(
        store,
        AUD,
        sha,
        required=Status.APPROVED_FOR_CONSUMER,
        consumer_class=cls,
        gate=RightsGate(PERMISSIVE),
        source_ids=("synthetic.rba",),
    )


def test_f2_codex_counterexample_hio_internal_approval_does_not_authorise_smsf_app(tmp_path):
    """Codex: after an owner approved_for_consumer(hio_internal), resolving with
    required=APPROVED_FOR_CONSUMER and consumer_class='smsf_app' returned the core."""
    _, store, releases = published_store(tmp_path / "s")
    sha = releases[AUD].content_sha256
    approve(store, sha, "hio_internal")
    use(store, sha, "hio_internal")
    with pytest.raises(RefusedUse):
        use(store, sha, "smsf_app")


def test_f2_independent_approvals_and_class_scoped_withdrawal(tmp_path):
    _, store, releases = published_store(tmp_path / "s")
    sha = releases[AUD].content_sha256
    approve(store, sha, "hio_internal")
    approve(store, sha, "smsf_app")
    use(store, sha, "hio_internal")
    use(store, sha, "smsf_app")
    withdraw(store, sha, "smsf_app")  # withdraws the smsf_app approval only
    with pytest.raises(RefusedUse):
        use(store, sha, "smsf_app")
    use(store, sha, "hio_internal")  # the other class's approval stands
    approve(store, sha, "smsf_app")  # a class may be approved again after its own withdrawal
    use(store, sha, "smsf_app")


def test_f2_a_global_withdrawal_refuses_every_class_and_is_terminal(tmp_path):
    _, store, releases = published_store(tmp_path / "s")
    sha = releases[AUD].content_sha256
    approve(store, sha, "hio_internal")
    withdraw(store, sha)
    for cls in ("hio_internal", "smsf_app"):
        with pytest.raises(RefusedUse, match="withdrawn"):
            use(store, sha, cls)
    with pytest.raises(Exception, match="terminal"):
        approve(store, sha, "hio_internal")
