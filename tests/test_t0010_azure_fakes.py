"""Offline fake of the Azure `ContainerClient` surface that `hio.storage.azure_blob` uses (T-0010 W-2).

It models what the tests need and nothing more: write-once conditional create, versions with
provider-assigned whole-second `last_modified`, paginated listings, and fault injection. It holds no
credential and touches no network; the Azure SDK is imported only for its exception types.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError

CLOCK = datetime(2026, 10, 30, 1, 2, 3, 456789, tzinfo=UTC)


def service_error(cls: type[HttpResponseError], status: int, code: str) -> HttpResponseError:
    error = cls("injected service error")
    error.status_code = status
    error.error_code = code
    return error


@dataclass
class Props:
    name: str
    version_id: str | None
    last_modified: datetime | None
    size: int | None
    is_current_version: bool = True


@dataclass
class _Version:
    props: Props
    data: bytes


class _Download:
    def __init__(self, version: _Version) -> None:
        self._data = version.data
        self.properties = Props(**{**version.props.__dict__})

    def readall(self) -> bytes:
        return self._data


class _Pager:
    def __init__(self, items: list[Props], page_size: int, log: list[int]) -> None:
        self._items, self._page_size, self._log = items, page_size, log

    def __iter__(self):  # a real ItemPaged also iterates items; the backend must use by_page
        raise AssertionError("the backend must page explicitly with by_page()")

    def by_page(self):
        for start in range(0, len(self._items), self._page_size):
            self._log.append(start)
            yield iter(self._items[start : start + self._page_size])


class FakeContainer:
    def __init__(
        self,
        *,
        versioning: bool = True,
        page_size: int = 2,
        clock: Callable[[], datetime] = lambda: CLOCK,
    ) -> None:
        self.versioning = versioning
        self.page_size = page_size
        self._clock = clock
        self._lock = threading.Lock()
        self._blobs: dict[str, list[_Version]] = {}
        self._counter = 0
        self.calls: list[tuple[str, str, dict]] = []  # (operation, blob name, keyword arguments)
        self.pages_requested: list[int] = []
        self.upload_error: BaseException | None = None
        self.omit_last_modified = False
        self.omit_upload_version = False
        self.size_delta = 0

    def get_blob_client(self, name: str) -> FakeBlobClient:
        return FakeBlobClient(self, name)

    def list_blobs(self, name_starts_with=None, include=None, **kwargs):
        self.calls.append(("list_blobs", name_starts_with or "", {"include": include, **kwargs}))
        items: list[Props] = []
        for name in sorted(self._blobs):
            if not name.startswith(name_starts_with or ""):
                continue
            versions = self._blobs[name]
            if include and "versions" in include:
                items += [Props(**{**v.props.__dict__}) for v in versions]
            else:
                items.append(Props(**{**versions[-1].props.__dict__, "version_id": None}))
        return _Pager(items, self.page_size, self.pages_requested)

    # --- out-of-band actions, as a privileged identity would take them ---------------------------
    def overwrite_out_of_band(self, name: str, data: bytes) -> None:
        self._add(name, data)

    def _add(self, name: str, data: bytes) -> Props:
        self._counter += 1
        stamp = self._clock().replace(microsecond=0)  # Azure's Last-Modified has whole-second resolution
        version_id = f"vid-{self._counter}" if self.versioning else None
        last_modified = None if self.omit_last_modified else stamp
        versions = self._blobs.setdefault(name, [])
        for earlier in versions:
            earlier.props.is_current_version = False
        props = Props(name, version_id, last_modified, len(data) + self.size_delta)
        versions.append(_Version(props, data))
        return props


class FakeBlobClient:
    def __init__(self, container: FakeContainer, name: str) -> None:
        self._c, self._name = container, name

    def upload_blob(self, data, **kwargs):
        c = self._c
        c.calls.append(("upload_blob", self._name, {"data_len": len(data), **kwargs}))
        if c.upload_error is not None:
            raise c.upload_error
        with c._lock:
            if kwargs.get("match_condition") == MatchConditions.IfMissing and c._blobs.get(self._name):
                raise service_error(ResourceExistsError, 409, "BlobAlreadyExists")
            props = c._add(self._name, data)
        return {
            "etag": '"0x8DCA"',
            "last_modified": props.last_modified,
            "version_id": None if c.omit_upload_version else props.version_id,
        }

    def get_blob_properties(self, **kwargs):
        c = self._c
        c.calls.append(("get_blob_properties", self._name, kwargs))
        return Props(**{**self._find(kwargs.get("version_id")).props.__dict__})

    def download_blob(self, **kwargs):
        self._c.calls.append(("download_blob", self._name, kwargs))
        return _Download(self._find(kwargs.get("version_id")))

    def _find(self, version_id: str | None) -> _Version:
        versions = self._c._blobs.get(self._name)
        if not versions:
            raise service_error(ResourceNotFoundError, 404, "BlobNotFound")
        if version_id is None:
            return versions[-1]
        for v in versions:
            if v.props.version_id == version_id:
                return v
        raise service_error(ResourceNotFoundError, 404, "BlobNotFound")
