"""Azure Blob Storage backend for `BlobBackend` (T-0010 W-2; OD-0117 decision 4). Not wired to any job.

STATUS: UNVERIFIED against a real account. Two things this module cannot establish by itself, and
that stay open until H4 (OD-0117) tests them on a real, owner-provisioned account:

- **Azure immutability enforcement** (version-level WORM, a writer role without delete or overwrite)
  is a server-side control. This module only never *asks* for an overwrite or a delete.
- **C5 suitability of whole-second `Last-Modified`** (HIO-ADR-0012 C5). Azure reports the version's
  `Last-Modified` at one-second resolution. Whether that is fine enough for the C5 timing test is
  not decided here; `written_at` is passed through exactly as the provider gave it.

What it does (all through an INJECTED container client; this module never builds a credential and the
tests never touch a network):

- `create` is one Put Blob with `If-None-Match: *` (`overwrite=False` and `MatchConditions.IfMissing`).
  Data above `max_single_put_size` is refused before any request, so the SDK can never switch to a
  staged block-list upload (which would not be a single conditional create). Only a genuine 409
  `BlobAlreadyExists` or 412 `ConditionNotMet` becomes `BlobExists`, plus (T-0015 F-1) a 403
  `UnauthorizedBlobOverwrite` when a properties read confirms the exact key exists (a writer role
  without overwrite permission gets that code for an existing key; B-2). If that read fails or finds
  nothing, the original 403 is raised. Other auth, policy, throttling,
  server and transport errors propagate unchanged as their own types. The SDK's retry policy can
  turn a lost response into a spurious `BlobExists` for bytes this caller did write; the store layer
  resolves that on retry (identical bytes at an existing key are skipped, different bytes refuse).
- `written_at` is the exact version's `BlobProperties.last_modified` (UTC-aware, unaltered); the
  version id is the provider's. A missing timestamp, version id or size, or a non-UTC timestamp,
  raises `ProviderMetadataError`; the local clock is never used and nothing is invented.
- `versions` lists `include=["versions"]` and keeps only blobs whose name EQUALS the key (a prefix
  listing also returns `a/b` for key `a`). A listing without version ids (versioning off) raises
  instead of reporting one fabricated version.
- `read` returns the current version, or the exact `version_id` when given.
- `keys` and `versions` page explicitly (`by_page`), so a continuation token is always followed.

No overwrite and no delete exist here, matching the `BlobBackend` protocol.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.storage.blob import ContainerClient

from hio.storage.blobstore import BlobExists, BlobInfo

# The SDK's own default for max_single_put_size; HIO objects (receipts, records, release files) are far
# smaller. Larger data is refused rather than uploaded in blocks.
MAX_OBJECT_BYTES = 64 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 30
PAGE_SIZE = 5000

_EXISTS_STATUS = {409, 412}
_EXISTS_CODES = {"BlobAlreadyExists", "ConditionNotMet"}
_OVERWRITE_REFUSAL_CODE = "UnauthorizedBlobOverwrite"
_NOT_FOUND_CODES = {"BlobNotFound"}


class ProviderMetadataError(Exception):
    """The provider returned no (or malformed) timestamp, version id or size; HIO never fills it in."""


class BlobTooLarge(ValueError):
    """The object is larger than the single-put limit; it is refused rather than uploaded in blocks."""


def container_client(
    account_url: str,
    container_name: str,
    credential: Any,
    *,
    connection_timeout: float = 10.0,
    read_timeout: float = 30.0,
) -> ContainerClient:
    """A container client configured for this backend: https only, a single-put limit equal to
    `MAX_OBJECT_BYTES`, bounded connect and read timeouts. The credential is passed in, never built here."""
    if not account_url.startswith("https://"):
        raise ValueError("the storage account URL must be https")
    return ContainerClient(
        account_url,
        container_name,
        credential=credential,
        max_single_put_size=MAX_OBJECT_BYTES,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
    )


def _code(error: BaseException) -> str | None:
    code = getattr(error, "error_code", None)
    return getattr(code, "value", code)


def _is_already_exists(error: HttpResponseError) -> bool:
    return getattr(error, "status_code", None) in _EXISTS_STATUS and _code(error) in _EXISTS_CODES


def _is_overwrite_refusal(error: HttpResponseError) -> bool:
    """A 403 `UnauthorizedBlobOverwrite`: what a writer role without overwrite permission gets from the
    conditional create when the key already exists (B-2, T-0015 F-1). Only a conflict signal once a
    properties read confirms the key; never proof that this caller's bytes are stored."""
    return getattr(error, "status_code", None) == 403 and _code(error) == _OVERWRITE_REFUSAL_CODE


def _is_blob_not_found(error: ResourceNotFoundError) -> bool:
    return _code(error) in _NOT_FOUND_CODES


def _info(key: str, props: Any) -> BlobInfo:
    version_id = getattr(props, "version_id", None)
    if not isinstance(version_id, str) or not version_id:
        raise ProviderMetadataError(
            f"{key}: the provider returned no version id (is blob versioning enabled?)"
        )
    written_at = getattr(props, "last_modified", None)
    if not isinstance(written_at, datetime) or written_at.utcoffset() != timedelta(0):
        raise ProviderMetadataError(
            f"{key}: the provider returned no UTC Last-Modified for version {version_id}"
        )
    size = getattr(props, "size", None)
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ProviderMetadataError(f"{key}: the provider returned no size for version {version_id}")
    return BlobInfo(key, version_id, written_at, size)


class AzureBlobBackend:
    def __init__(
        self,
        container: Any,
        *,
        max_single_put_size: int = MAX_OBJECT_BYTES,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """`container` is an injected `azure.storage.blob.ContainerClient` (or a fake with the same calls).
        It must be configured with a `max_single_put_size` of at least `max_single_put_size`
        (`container_client` does that)."""
        if max_single_put_size <= 0 or timeout <= 0:
            raise ValueError("max_single_put_size and timeout must be positive")
        self._container = container
        self._max_single_put_size = max_single_put_size
        self._timeout = timeout

    def create(self, key: str, data: bytes) -> BlobInfo:
        if not isinstance(data, bytes):
            raise TypeError("blob data must be bytes")
        if len(data) > self._max_single_put_size:
            raise BlobTooLarge(
                f"{key}: {len(data)} bytes exceeds the single-put limit {self._max_single_put_size}"
            )
        blob = self._container.get_blob_client(key)
        try:
            result = blob.upload_blob(
                data,
                length=len(data),
                overwrite=False,
                match_condition=MatchConditions.IfMissing,  # If-None-Match: *
                timeout=self._timeout,
            )
        except HttpResponseError as error:
            if _is_already_exists(error) or (_is_overwrite_refusal(error) and self._key_exists(blob)):
                raise BlobExists(key) from None
            raise
        version_id = result.get("version_id") if isinstance(result, dict) else None
        if not isinstance(version_id, str) or not version_id:
            raise ProviderMetadataError(
                f"{key}: the upload returned no version id (is blob versioning enabled?)"
            )
        info = _info(key, blob.get_blob_properties(version_id=version_id, timeout=self._timeout))
        if info.version_id != version_id or info.size != len(data):
            raise ProviderMetadataError(f"{key}: the stored version does not match the upload")
        return info

    def _key_exists(self, blob: Any) -> bool:
        """True only when a properties read of the exact key succeeds. A not-found answer, any other
        failure and any inconclusive result are False, so the caller re-raises the original error."""
        try:
            blob.get_blob_properties(timeout=self._timeout)
        except Exception:
            return False
        return True

    def read(self, key: str, version_id: str | None = None) -> bytes:
        """The bytes of the current version, or of exactly `version_id` when given."""
        blob = self._container.get_blob_client(key)
        try:
            downloader = blob.download_blob(version_id=version_id, timeout=self._timeout)
            data = downloader.readall()
        except ResourceNotFoundError as error:
            if _is_blob_not_found(error):
                raise KeyError(key) from None
            raise
        served = getattr(getattr(downloader, "properties", None), "version_id", None)
        if version_id is not None and served is not None and served != version_id:
            raise ProviderMetadataError(f"{key}: asked for version {version_id}, the provider served another")
        return data

    def stat(self, key: str) -> BlobInfo | None:
        """The current version's `BlobInfo`, or None when the blob does not exist."""
        try:
            props = self._container.get_blob_client(key).get_blob_properties(timeout=self._timeout)
        except ResourceNotFoundError as error:
            if _is_blob_not_found(error):
                return None
            raise
        return _info(key, props)

    def keys(self, prefix: str) -> Iterator[str]:
        for item in self._pages(name_starts_with=prefix):
            name = getattr(item, "name", None)
            if not isinstance(name, str):
                raise ProviderMetadataError("the provider returned a listing entry without a name")
            yield name

    def versions(self, key: str) -> list[BlobInfo]:
        found = [
            item
            for item in self._pages(name_starts_with=key, include=["versions"])
            if getattr(item, "name", None) == key  # the exact name, not every blob that starts with it
        ]
        return [_info(key, item) for item in found]

    def _pages(self, **kwargs: Any) -> Iterator[Any]:
        pager = self._container.list_blobs(results_per_page=PAGE_SIZE, timeout=self._timeout, **kwargs)
        for page in pager.by_page():
            yield from page
