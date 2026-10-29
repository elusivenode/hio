"""T-0015 F-1: a 403 `UnauthorizedBlobOverwrite` on the conditional create is `BlobExists` only when a
properties read confirms the exact key exists. Offline fakes only; no credential, no network."""

from __future__ import annotations

import pytest
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError,
)

from hio.storage.blobstore import BlobExists
from tests.test_t0010_azure_blob import backend
from tests.test_t0010_azure_fakes import FakeBlobClient, service_error


def overwrite_refusal() -> HttpResponseError:
    return service_error(HttpResponseError, 403, "UnauthorizedBlobOverwrite")


def test_403_overwrite_refusal_with_the_key_present_is_blob_exists():
    b, c = backend()
    c.overwrite_out_of_band("k/a", b"first")
    c.upload_error = overwrite_refusal()
    with pytest.raises(BlobExists):
        b.create("k/a", b"second")
    ops = [(op, name) for op, name, _kw in c.calls]
    assert ops == [("upload_blob", "k/a"), ("get_blob_properties", "k/a")]
    assert b.read("k/a") == b"first"
    assert len(b.versions("k/a")) == 1


def test_the_existence_check_reads_the_exact_key_with_a_timeout():
    b, c = backend()
    c.overwrite_out_of_band("k/a", b"first")
    c.upload_error = overwrite_refusal()
    with pytest.raises(BlobExists):
        b.create("k/a", b"second")
    ((_op, name, kwargs),) = [x for x in c.calls if x[0] == "get_blob_properties"]
    assert name == "k/a" and kwargs["timeout"] > 0


def test_403_overwrite_refusal_with_the_key_absent_raises_the_original_error():
    b, c = backend()
    error = overwrite_refusal()
    c.upload_error = error
    with pytest.raises(HttpResponseError) as raised:
        b.create("k/a", b"x")
    assert raised.value is error
    assert not isinstance(raised.value, BlobExists)


def test_a_sibling_key_does_not_confirm_existence():
    b, c = backend()
    c.overwrite_out_of_band("k/a/b", b"other")
    c.upload_error = overwrite_refusal()
    with pytest.raises(HttpResponseError) as raised:
        b.create("k/a", b"x")
    assert not isinstance(raised.value, BlobExists)


@pytest.mark.parametrize(
    "check_error",
    [
        service_error(HttpResponseError, 403, "AuthorizationPermissionMismatch"),
        service_error(HttpResponseError, 500, "InternalError"),
        service_error(ResourceNotFoundError, 404, "BlobNotFound"),
        ClientAuthenticationError("expired federated token"),
        ServiceRequestError("connection reset"),
        ConnectionError("injected"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_a_failing_existence_check_raises_the_original_error(monkeypatch, check_error):
    b, c = backend()
    c.overwrite_out_of_band("k/a", b"first")  # present, but the check cannot say so
    error = overwrite_refusal()
    c.upload_error = error

    def failing(*_args, **_kwargs):
        raise check_error

    monkeypatch.setattr(FakeBlobClient, "get_blob_properties", failing)
    with pytest.raises(HttpResponseError) as raised:
        b.create("k/a", b"second")
    assert raised.value is error
    assert not isinstance(raised.value, BlobExists)


@pytest.mark.parametrize(
    "code",
    [
        "AuthorizationPermissionMismatch",
        "AuthorizationFailure",
        "AuthenticationFailed",
        "BlobAlreadyExists",
        None,
    ],
)
def test_other_403_codes_propagate_without_an_existence_check(code):
    b, c = backend()
    c.overwrite_out_of_band("k/a", b"first")  # present, which must not matter
    error = service_error(HttpResponseError, 403, code)  # type: ignore[arg-type]
    c.upload_error = error
    with pytest.raises(HttpResponseError) as raised:
        b.create("k/a", b"second")
    assert raised.value is error
    assert not isinstance(raised.value, BlobExists)
    assert [op for op, _n, _kw in c.calls] == ["upload_blob"]


@pytest.mark.parametrize("status", [401, 404, 409, 412, 500])
def test_the_overwrite_refusal_code_with_another_status_is_not_mapped(status):
    b, c = backend()
    c.overwrite_out_of_band("k/a", b"first")
    error = service_error(HttpResponseError, status, "UnauthorizedBlobOverwrite")
    c.upload_error = error
    with pytest.raises(HttpResponseError) as raised:
        b.create("k/a", b"second")
    assert raised.value is error
    assert not isinstance(raised.value, BlobExists)
    assert [op for op, _n, _kw in c.calls] == ["upload_blob"]


@pytest.mark.parametrize("status,code", [(409, "BlobAlreadyExists"), (412, "ConditionNotMet")])
def test_409_and_412_still_map_without_an_existence_check(status, code):
    b, c = backend()
    c.upload_error = service_error(HttpResponseError, status, code)
    with pytest.raises(BlobExists):
        b.create("k/a", b"x")
    assert [op for op, _n, _kw in c.calls] == ["upload_blob"]


def test_a_successful_create_makes_no_existence_check():
    b, c = backend()
    b.create("k/a", b"x")
    assert [op for op, _n, _kw in c.calls].count("get_blob_properties") == 1  # only the version-bound read
