"""T-0010 W-2: the Azure Blob backend, tested only against an offline fake of the SDK client surface.

No credential, no network, no Azurite. Azure immutability enforcement and the C5 suitability of
whole-second Last-Modified are UNVERIFIED pending H4 (OD-0117); these tests do not claim either.
"""

from __future__ import annotations

import threading
import typing
from datetime import UTC, datetime, timedelta, timezone

import pytest
from azure.core import MatchConditions
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceExistsError,
    ResourceModifiedError,
    ResourceNotFoundError,
    ServiceRequestError,
)

from hio.contracts.canonical import sha256_hex
from hio.contracts.layout import CAPTURES_PREFIX
from hio.storage import azure_blob
from hio.storage.azure_blob import AzureBlobBackend, BlobTooLarge, ProviderMetadataError
from hio.storage.blobstore import BlobBackend, BlobExists, BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from hio.storage.objectstore import IntegrityError, WriteOnceViolation
from tests.helpers import AllowAllGate
from tests.test_s1b1_releases import AUD_DAYS, build_world, capture_once, f1_csv
from tests.test_t0010_azure_fakes import CLOCK, FakeContainer, service_error


def backend(container: FakeContainer | None = None, **kwargs) -> tuple[AzureBlobBackend, FakeContainer]:
    container = container or FakeContainer()
    return AzureBlobBackend(container, **kwargs), container


def addressed(data: bytes) -> str:
    return f"artefacts/{sha256_hex(data)}.bin"


# --- conditional create ----------------------------------------------------------------------------


def test_create_is_one_put_with_if_none_match_and_returns_the_provider_version():
    b, c = backend()
    info = b.create("catalogue/notes/a.json", b"{}")
    ((op, name, kwargs),) = [x for x in c.calls if x[0] == "upload_blob"]
    assert (op, name) == ("upload_blob", "catalogue/notes/a.json")
    assert kwargs["overwrite"] is False
    assert kwargs["match_condition"] == MatchConditions.IfMissing  # If-None-Match: *
    assert kwargs["length"] == 2 and kwargs["timeout"] > 0
    assert info.key == "catalogue/notes/a.json" and info.version_id == "vid-1" and info.size == 2
    assert info.written_at == CLOCK.replace(microsecond=0)  # the provider's whole-second value, unaltered


def test_create_binds_written_at_to_the_exact_version_it_created():
    b, c = backend()
    b.create("k/a", b"x")
    props_calls = [kw for op, _n, kw in c.calls if op == "get_blob_properties"]
    assert props_calls == [{"version_id": "vid-1", "timeout": props_calls[0]["timeout"]}]


def test_create_conflict_raises_blob_exists_and_leaves_the_first_bytes():
    b, _c = backend()
    b.create("k/a", b"first")
    with pytest.raises(BlobExists):
        b.create("k/a", b"second")
    assert b.read("k/a") == b"first"
    assert len(b.versions("k/a")) == 1


def test_competing_creates_have_exactly_one_winner():
    b, _c = backend()
    wins, losses, barrier = [], [], threading.Barrier(8)

    def attempt(i: int) -> None:
        barrier.wait()
        try:
            b.create("k/race", f"writer-{i}".encode())
            wins.append(i)
        except BlobExists:
            losses.append(i)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(wins) == 1 and len(losses) == 7
    assert b.read("k/race") == f"writer-{wins[0]}".encode()
    assert len(b.versions("k/race")) == 1


@pytest.mark.parametrize("status", [409, 412])
@pytest.mark.parametrize("code", ["BlobAlreadyExists", "ConditionNotMet"])
@pytest.mark.parametrize("cls", [ResourceExistsError, ResourceModifiedError, HttpResponseError])
def test_a_genuine_409_or_412_condition_failure_maps_to_blob_exists(cls, code, status):
    b, c = backend()
    c.upload_error = service_error(cls, status, code)
    with pytest.raises(BlobExists):
        b.create("k/a", b"x")


@pytest.mark.parametrize(
    "error",
    [
        service_error(HttpResponseError, 409, "BlobImmutableDueToPolicy"),  # a policy refusal is not "exists"
        service_error(HttpResponseError, 409, "LeaseIdMissing"),
        service_error(ResourceExistsError, 409, "ContainerAlreadyExists"),  # same SDK class, other meaning
        service_error(HttpResponseError, 412, "TargetConditionNotMet"),
        service_error(HttpResponseError, 403, "AuthorizationPermissionMismatch"),
        service_error(HttpResponseError, 403, "BlobAlreadyExists"),  # right code, wrong status
        service_error(HttpResponseError, 500, "InternalError"),
        service_error(HttpResponseError, 503, "ServerBusy"),
        service_error(HttpResponseError, 409, None),
        ClientAuthenticationError("expired federated token"),
        ServiceRequestError("connection reset"),
        ConnectionError("injected"),
    ],
    ids=lambda e: f"{type(e).__name__}-{getattr(e, 'status_code', None)}-{getattr(e, 'error_code', None)}",
)
def test_every_other_error_propagates_and_is_not_blob_exists(error):
    b, c = backend()
    c.upload_error = error
    with pytest.raises(type(error)) as raised:
        b.create("k/a", b"x")
    assert raised.value is error
    assert not isinstance(raised.value, BlobExists)
    assert b.stat("k/a") is None  # nothing was written


def test_upload_size_is_refused_before_any_request():
    b, c = backend(max_single_put_size=4)
    assert b.create("k/ok", b"1234").size == 4  # exactly the limit is allowed
    with pytest.raises(BlobTooLarge):
        b.create("k/big", b"12345")
    assert all(name != "k/big" for _op, name, _kw in c.calls)  # no request of any kind for it
    assert b.stat("k/big") is None


def test_the_default_limit_matches_the_sdk_single_put_default_and_is_configured_on_the_client(monkeypatch):
    seen = {}

    class Capture:
        def __init__(self, *args, **kwargs):
            seen["args"], seen["kwargs"] = args, kwargs

    monkeypatch.setattr(azure_blob, "ContainerClient", Capture)
    sentinel = object()
    azure_blob.container_client("https://acct.blob.core.windows.net", "hio", sentinel)
    assert seen["kwargs"]["max_single_put_size"] == azure_blob.MAX_OBJECT_BYTES == 64 * 1024 * 1024
    assert seen["kwargs"]["credential"] is sentinel
    assert seen["kwargs"]["connection_timeout"] > 0 and seen["kwargs"]["read_timeout"] > 0
    with pytest.raises(ValueError, match="https"):
        azure_blob.container_client("http://acct.blob.core.windows.net", "hio", sentinel)


def test_create_rejects_non_bytes():
    b, _c = backend()
    with pytest.raises(TypeError):
        b.create("k/a", "text")  # type: ignore[arg-type]


# --- stat, version binding, fail closed -------------------------------------------------------------


def test_stat_returns_the_current_version_with_provider_metadata_and_none_when_absent():
    b, _c = backend()
    assert b.stat("k/a") is None
    created = b.create("k/a", b"abc")
    assert b.stat("k/a") == created
    assert created.written_at.tzinfo is not None and created.written_at.utcoffset() == timedelta(0)


def test_a_missing_blob_is_none_but_a_missing_container_is_not_swallowed():
    b, c = backend()

    class Gone:
        def get_blob_properties(self, **_kw):
            raise service_error(ResourceNotFoundError, 404, "ContainerNotFound")

    c.get_blob_client = lambda _name: Gone()  # type: ignore[method-assign]
    with pytest.raises(ResourceNotFoundError):
        b.stat("k/a")


def test_read_returns_current_bytes_and_can_bind_to_a_version():
    b, c = backend()
    first = b.create("k/a", b"one")
    c.overwrite_out_of_band("k/a", b"two")  # a second version, as a privileged identity would leave
    assert b.read("k/a") == b"two"
    assert b.read("k/a", version_id=first.version_id) == b"one"
    download = [kw for op, _n, kw in c.calls if op == "download_blob"]
    assert download[0]["version_id"] is None and download[1]["version_id"] == first.version_id


def test_read_refuses_a_version_the_provider_did_not_serve():
    b, c = backend()
    b.create("k/a", b"one")
    original = c.get_blob_client("k/a").download_blob

    class Mismatch:
        def download_blob(self, **kw):
            download = original(**kw)
            download.properties.version_id = "other"
            return download

    c.get_blob_client = lambda _name: Mismatch()  # type: ignore[method-assign]
    with pytest.raises(ProviderMetadataError, match="another"):
        b.read("k/a", version_id="vid-1")


def test_read_of_a_missing_key_is_a_key_error():
    b, _c = backend()
    with pytest.raises(KeyError):
        b.read("k/none")


def test_read_of_an_unknown_version_propagates_the_service_error():
    b, _c = backend()
    b.create("k/a", b"one")
    with pytest.raises(KeyError):  # BlobNotFound for that version id
        b.read("k/a", version_id="vid-404")


@pytest.mark.parametrize("flag", ["omit_last_modified", "omit_upload_version"])
def test_create_fails_closed_when_the_provider_omits_the_timestamp_or_version(flag):
    b, c = backend()
    setattr(c, flag, True)
    with pytest.raises(ProviderMetadataError):
        b.create("k/a", b"x")


def test_create_fails_closed_without_versioning():
    b, _c = backend(FakeContainer(versioning=False))
    with pytest.raises(ProviderMetadataError, match="version"):
        b.create("k/a", b"x")


def test_create_fails_closed_when_the_stored_size_differs_from_the_upload():
    b, c = backend()
    c.size_delta = 1
    with pytest.raises(ProviderMetadataError, match="does not match"):
        b.create("k/a", b"x")


@pytest.mark.parametrize(
    "stamp",
    [
        None,
        "2026-10-30T00:00:00Z",
        datetime(2026, 10, 30, tzinfo=None),  # noqa: DTZ001 (a naive timestamp is the point)
        datetime(2026, 10, 30, tzinfo=timezone(timedelta(hours=11))),
    ],
    ids=["none", "string", "naive", "non-utc"],
)
def test_stat_fails_closed_on_a_missing_naive_or_non_utc_timestamp(stamp):
    b, c = backend()
    b.create("k/a", b"x")
    c._blobs["k/a"][-1].props.last_modified = stamp
    with pytest.raises(ProviderMetadataError):
        b.stat("k/a")


def test_stat_never_substitutes_the_local_clock():
    b, c = backend(FakeContainer(clock=lambda: datetime(2000, 1, 1, tzinfo=UTC)))
    info = b.create("k/a", b"x")
    assert info.written_at == datetime(2000, 1, 1, tzinfo=UTC)  # the provider's value, not now()
    c._blobs["k/a"][-1].props.last_modified = None
    with pytest.raises(ProviderMetadataError):
        b.stat("k/a")  # no fallback value is invented


def test_written_at_is_the_provider_value_object_unaltered():
    b, c = backend()
    b.create("k/a", b"x")
    provider_value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    c._blobs["k/a"][-1].props.last_modified = provider_value
    assert b.stat("k/a").written_at is provider_value


# --- versions and keys -------------------------------------------------------------------------------


def test_versions_are_filtered_to_the_exact_key_and_paginated():
    b, c = backend()
    c.page_size = 2
    for name in ["k/a", "k/a/b", "k/a.json", "k/ab", "k/b"]:
        b.create(name, name.encode())
    c.overwrite_out_of_band("k/a", b"second")
    c.overwrite_out_of_band("k/a", b"third")
    c.pages_requested.clear()
    found = b.versions("k/a")
    assert [i.key for i in found] == ["k/a"] * 3
    assert [i.version_id for i in found] == ["vid-1", "vid-6", "vid-7"]
    assert len(c.pages_requested) >= 3  # the listing was walked page by page, not read from the first page
    call = [x for x in c.calls if x[0] == "list_blobs"][-1]
    assert call[2]["include"] == ["versions"] and call[1] == "k/a"


def test_versions_of_an_absent_key_is_empty_and_a_prefix_is_not_a_match():
    b, _c = backend()
    b.create("k/abc", b"x")
    assert b.versions("k/ab") == []


def test_versions_raise_when_versioning_data_is_absent():
    b, c = backend()
    b.create("k/a", b"x")
    c.versioning = False
    c._blobs["k/a"][-1].props.version_id = None
    with pytest.raises(ProviderMetadataError, match="version id"):
        b.versions("k/a")  # never a fabricated single version


def test_versions_raise_on_a_missing_timestamp():
    b, c = backend()
    b.create("k/a", b"x")
    c._blobs["k/a"][-1].props.last_modified = None
    with pytest.raises(ProviderMetadataError):
        b.versions("k/a")


def test_keys_walks_every_page_and_filters_by_prefix():
    b, c = backend()
    c.page_size = 3
    names = [f"releases/r{i}/data.csv" for i in range(8)] + ["receipts/x", "catalogue/y"]
    for n in names:
        b.create(n, b"x")
    c.pages_requested.clear()
    assert sorted(b.keys("releases/")) == sorted(n for n in names if n.startswith("releases/"))
    assert len(c.pages_requested) == 3  # 8 matches at 3 per page
    assert sorted(b.keys("")) == sorted(names)


def test_keys_is_lazy_and_does_not_list_versions():
    b, c = backend()
    b.create("k/a", b"x")
    it = b.keys("k/")
    assert not [x for x in c.calls if x[0] == "list_blobs"]  # nothing requested until iterated
    assert list(it) == ["k/a"]
    assert [x for x in c.calls if x[0] == "list_blobs"][-1][2]["include"] is None


# --- the store over the Azure backend ------------------------------------------------------------------


def test_the_backend_has_no_overwrite_or_delete_and_matches_the_protocol():
    b, _c = backend()
    assert not {"delete", "overwrite"} & set(dir(b))
    assert set(typing.get_protocol_members(BlobBackend)) <= set(dir(b))


def azure_store() -> BlobObjectStore:
    return BlobObjectStore(AzureBlobBackend(FakeContainer(page_size=7)))


def fake_store() -> BlobObjectStore:
    return BlobObjectStore(FakeBlobBackend(clock=lambda: CLOCK))


def test_blob_object_store_semantics_match_fakeblob():
    for store in (azure_store(), fake_store()):
        data = b"content"
        key = addressed(data)
        assert not store.exists(key)
        assert store.put(key, data) == key
        assert store.exists(key) and store.get(key) == data
        with pytest.raises(WriteOnceViolation):
            store.put(key, data)
        assert store.put_if_absent(key, data) is False
        with pytest.raises(WriteOnceViolation):
            store.put_if_absent(key, b"different")
        with pytest.raises(FileNotFoundError):
            store.get(addressed(b"never written"))
        with pytest.raises(ValueError):
            store.put("../escape", b"x")
        assert list(store.list("artefacts/")) == [key]
        assert store.snapshot() == {key: sha256_hex(data)}
        assert store.write_time(key).tzinfo is not None
        with pytest.raises(FileNotFoundError):
            store.write_time(addressed(b"never written"))


def test_a_content_address_mismatch_is_refused_over_the_azure_backend():
    store = azure_store()
    with pytest.raises(IntegrityError, match="do not match their key"):
        store.put(f"receipts/src/2026/10/{'0' * 64}", b"not that content")
    assert not store.exists(f"receipts/src/2026/10/{'0' * 64}")


def test_an_out_of_band_overwrite_is_detected_through_the_azure_versions():
    store = azure_store()
    key = addressed(b"payload")
    store.put(key, b"payload")
    store.backend._container.overwrite_out_of_band(key, b"tampered")
    with pytest.raises(IntegrityError, match="2 versions"):
        store.get(key)


def test_staged_writes_commit_and_resume_over_the_azure_backend():
    store = azure_store()
    staged = store.staged()
    for text in (b"a", b"b", b"c"):
        staged.add(addressed(text), text)
    assert staged.commit() == sorted(addressed(t) for t in (b"a", b"b", b"c"))
    again = store.staged()
    again.add(addressed(b"a"), b"a")  # an identical object is skipped
    again.commit()
    assert len(store.snapshot()) == 3


def test_the_pipeline_is_byte_equivalent_over_the_azure_and_fakeblob_backends():
    azure_world = build_world(azure_store())
    fake_world = build_world(fake_store())
    (astore, *_a, arel), (fstore, *_f, frel) = azure_world, fake_world
    assert astore.snapshot() == fstore.snapshot()
    assert {k: r.content_sha256 for k, r in arel.items()} == {k: r.content_sha256 for k, r in frel.items()}
    assert all(arel[k].files == frel[k].files for k in arel)
    key = next(iter(astore.list(CAPTURES_PREFIX)))
    assert astore.write_time(key).utcoffset() == timedelta(0)


def test_a_failed_run_over_the_azure_backend_resumes_like_fakeblob():
    day = AUD_DAYS[3]
    at = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) - timedelta(hours=11)
    clean = azure_store()
    capture_once(clean, AllowAllGate(), "rba.f1", f1_csv(day), at)
    store = azure_store()
    container = store.backend._container
    real = container.get_blob_client
    state = {"uploads": 0}

    def flaky(name):
        client = real(name)
        upload = client.upload_blob

        def failing(data, **kw):
            state["uploads"] += 1
            if state["uploads"] == 3:
                raise ConnectionError("injected backend failure")
            return upload(data, **kw)

        client.upload_blob = failing  # type: ignore[method-assign]
        return client

    container.get_blob_client = flaky  # type: ignore[method-assign]
    with pytest.raises(ConnectionError):
        capture_once(store, AllowAllGate(), "rba.f1", f1_csv(day), at)
    container.get_blob_client = real  # type: ignore[method-assign]
    capture_once(store, AllowAllGate(), "rba.f1", f1_csv(day), at)
    assert store.snapshot() == clean.snapshot()
