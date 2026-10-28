"""Storage controls and equivalence (T-0009 A-4, OD-0065): the cloud-store interface, tested against
an in-memory backend that has the semantics HIO relies on. No network, no credential, no provider."""

from __future__ import annotations

import json
import typing
from datetime import UTC, datetime, timedelta

import pytest

from hio.contracts.layout import ATTEMPTS_PREFIX, CAPTURES_PREFIX
from hio.contracts.temporal import KnowledgeMode
from hio.jobs.s1b1 import vintage_store
from hio.marketdata.vintages import ReceiptIntegrityError
from hio.publish.release import verify_release, write_release
from hio.sources.datasets import PUBLICATIONS
from hio.storage.blobstore import BlobBackend, BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend, ImmutabilityViolation
from hio.storage.objectstore import IntegrityError, LocalObjectStore, WriteOnceViolation
from tests.helpers import AllowAllGate
from tests.test_s1b1_releases import AUD_DAYS, build_world, capture_once, f1_csv

CLOCK = datetime(2026, 10, 30, tzinfo=UTC)


def blob(immutable: bool = True) -> BlobObjectStore:
    return BlobObjectStore(FakeBlobBackend(immutable=immutable, clock=lambda: CLOCK))


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    local = build_world(LocalObjectStore(tmp_path_factory.mktemp("eq") / "store"))
    cloud = build_world(blob())
    return local, cloud


def test_the_pipeline_is_byte_equivalent_on_the_local_and_cloud_stores(pair):
    (lstore, *_, lrel), (cstore, *_, crel) = pair
    assert lstore.snapshot() == cstore.snapshot()  # every key, every byte: receipts, records, links, vintages
    assert {k: r.content_sha256 for k, r in lrel.items()} == {k: r.content_sha256 for k, r in crel.items()}
    assert all(lrel[k].files == crel[k].files for k in lrel)


def test_releases_written_to_either_store_verify_identically(pair, tmp_path):
    from hio.jobs.s1a import publish_releases

    (lstore, lcals, _v, cutoff, _r, _c, lrel), (cstore, ccals, *_x, crel) = pair
    for store, cals, rel in ((lstore, lcals, lrel), (cstore, ccals, crel)):
        target = LocalObjectStore(tmp_path / "t") if store is lstore else blob()
        for key in store.snapshot():
            target.put(key, store.get(key))
        out = publish_releases(vintage_store(target, cals), AllowAllGate(), rel, cutoff)
        assert all(v["written"] for v in out.values())
        for r in rel.values():
            verify_release(target, r.core["dataset_id"], r.content_sha256)


def test_the_store_layer_cannot_overwrite_or_delete(pair):
    cstore = pair[1][0]
    assert not hasattr(cstore, "delete") and not hasattr(cstore, "overwrite")
    assert not {"delete", "overwrite"} & set(
        typing.get_protocol_members(BlobBackend)
    )  # absent from the contract
    key = next(iter(cstore.list(CAPTURES_PREFIX)))
    with pytest.raises(WriteOnceViolation):
        cstore.put(key, b"anything")
    assert cstore.put_if_absent(key, cstore.get(key)) is False  # an identical re-write is a no-op
    with pytest.raises(WriteOnceViolation):
        cstore.put_if_absent(key, b"different")


def test_a_server_side_immutability_policy_refuses_overwrite_and_delete(pair):
    cstore = pair[1][0]
    key = next(iter(cstore.list("receipts/")))
    with pytest.raises(ImmutabilityViolation):
        cstore.backend.overwrite(key, b"tampered")
    with pytest.raises(ImmutabilityViolation):
        cstore.backend.delete(key)
    assert cstore.get(key)  # still intact


def test_an_out_of_band_overwrite_is_detected_when_the_policy_is_off():
    store = blob(immutable=False)
    for day in AUD_DAYS[1:3]:
        at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
        capture_once(store, AllowAllGate(), "rba.f1", f1_csv(day), at)
    key = next(iter(store.list(CAPTURES_PREFIX)))
    store.backend.overwrite(key, b'{"receipt_id":"x"}')  # a privileged identity replaces a record
    with pytest.raises(IntegrityError, match="2 versions"):
        store.get(key)
    deleted = next(iter(store.list("receipts/")))
    store.backend.delete(deleted)  # and a deleted object fails closed too
    with pytest.raises(FileNotFoundError):
        store.get(deleted)
    with pytest.raises((FileNotFoundError, IntegrityError)):
        store.snapshot()


def test_a_replaced_receipt_makes_every_dependent_view_refuse():
    store, cals, _vs, cutoff, *_ = build_world(blob(immutable=False))
    victim = next(iter(store.list("receipts/rba.f1/")))
    store.backend.overwrite(victim, b"not the published file")
    with pytest.raises(ReceiptIntegrityError):
        vintage_store(store, cals).view("rba.cash_rate.aonia", KnowledgeMode.AS_CAPTURED_BY_HIO, cutoff, None)


def test_provider_write_time_is_exposed_for_later_completion_checks():
    store = blob()
    store.put("catalogue/notes/a.json", b"{}")
    assert store.write_time("catalogue/notes/a.json") == CLOCK


@pytest.mark.parametrize("fail_after", [0, 1, 2, 3])
def test_a_failed_commit_is_resumed_by_retrying_and_matches_a_clean_run(fail_after):
    day = AUD_DAYS[3]
    at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
    clean = blob()
    capture_once(clean, AllowAllGate(), "rba.f1", f1_csv(day), at)
    store = blob()
    store.backend.fail_after = fail_after
    with pytest.raises(ConnectionError):
        capture_once(store, AllowAllGate(), "rba.f1", f1_csv(day), at)
    # the run record is written last, so a failed run leaves no completion evidence;
    # a capture record never appears without its bytes and its provenance link
    assert not list(store.list(ATTEMPTS_PREFIX))
    if list(store.list(CAPTURES_PREFIX)):
        assert list(store.list("receipts/")) and list(store.list("catalogue/links/"))
    store.backend.fail_after = None
    # a real retry runs later; the same instant would (correctly) be refused as a clock that did not advance
    capture_once(
        store, AllowAllGate(), "rba.f1", f1_csv(day), at if fail_after < 3 else at + timedelta(hours=1)
    )
    if fail_after < 3:
        assert store.snapshot() == clean.snapshot()
    else:
        # Everything but the run record had been written, so the retry finds the capture already held:
        # the same evidence, and a run record that truthfully says "unchanged". The earlier run left no
        # completion record, which is the visible trace of the crash.
        without = lambda s: {k: v for k, v in s.snapshot().items() if not k.startswith(ATTEMPTS_PREFIX)}  # noqa: E731
        assert without(store) == without(clean)
        (record,) = [json.loads(store.get(k)) for k in store.list(ATTEMPTS_PREFIX)]
        assert record["outcome"] == "verified_unchanged"


def test_a_failed_release_write_leaves_no_manifest_and_resumes():
    world = build_world(blob())
    cstore, _cals, _vs, _cutoff, _rights, _code, rel = world
    target = blob()
    for key in cstore.snapshot():
        target.put(key, cstore.get(key))
    release = rel["cash.usd.overnight"]
    target.backend.fail_after = target.backend._creates + 1  # one data file, then failure
    with pytest.raises(ConnectionError):
        write_release(target, AllowAllGate(), release)
    assert not target.exists(f"{release.prefix}/manifest.json")  # a release exists only with its manifest
    target.backend.fail_after = None
    assert write_release(target, AllowAllGate(), release) is True
    verify_release(target, "cash.usd.overnight", release.content_sha256)


def test_the_publications_in_use_match_the_storage_layout():
    assert set(PUBLICATIONS) == {"rba.f1", "rba.expert_judgement", "nyfed.sofr", "nyfed.sofr_index"}
