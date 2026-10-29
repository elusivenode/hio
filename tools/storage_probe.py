"""B-2 storage-validation probe (T-0012 P-2; OD-0127). Run by `.github/workflows/storage-probe.yml`.

Checks, against a short-lived PROBE account (never the evidence store), whether Azure Blob Storage
behaves as HIO's write-once design and HIO-ADR-0012 §4.3.3 C5 assume. It decides nothing: it records
what the provider did, one `{check, passed, detail}` per check, and prints one JSON report.

    1 create          a fresh key `probe/<run id>/<n>` is created
    2 conditional     creating the same key again raises `BlobExists`
    3 no overwrite    an overwrite through the SDK client (`overwrite=True`) is REFUSED
    4 no delete       a delete through the SDK client is REFUSED
    5 one version     `versions(key)` lists exactly one version, with a provider version id
    6 C5 timing       `--repeats` fresh creates; for each, `completed_at <= s <= completed_at + delta`
                      where `completed_at` is the UTC clock right after the create returns and `s` is
                      the provider's `Last-Modified`. Every observation is reported. NO tolerance is
                      applied: the check passes only with zero violations.

Checks 3 and 4 PASS only on a refusal (an authorization or immutability error). A success fails the
check, and a transport or server error fails it as inconclusive: it is not evidence of a refusal.

Environment (all injectable): HIO_PROBE_ACCOUNT_URL, HIO_PROBE_CONTAINER, AZURE_TENANT_ID,
AZURE_PROBE_CLIENT_ID. The credential is `hio.storage.azure_auth.github_oidc_credential`. Nothing but the
account HOST is printed from the environment; no token, id or message text from the provider is printed,
only an error's type, HTTP status and error code.

Exit status: 0 all checks passed; 1 a check failed; 2 refused before any request (missing environment).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

from azure.core.exceptions import HttpResponseError

from hio.storage.azure_auth import github_oidc_credential
from hio.storage.azure_blob import AzureBlobBackend, container_client
from hio.storage.blobstore import BlobExists

ENV_ACCOUNT_URL = "HIO_PROBE_ACCOUNT_URL"
ENV_CONTAINER = "HIO_PROBE_CONTAINER"
ENV_TENANT_ID = "AZURE_TENANT_ID"
ENV_CLIENT_ID = "AZURE_PROBE_CLIENT_ID"
REQUIRED_ENV = (ENV_ACCOUNT_URL, ENV_CONTAINER, ENV_TENANT_ID, ENV_CLIENT_ID)

DEFAULT_REPEATS = 20
DEFAULT_DELTA_SECONDS = 600.0  # HIO-ADR-0012 C5 delta (10 minutes)
REFUSAL_STATUSES = frozenset({401, 403, 409})  # authorization failure or immutability conflict

Now = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def describe(error: BaseException) -> str:
    """The error's type, HTTP status and error code. Never its message: it can carry request details."""
    parts = [type(error).__name__]
    status = getattr(error, "status_code", None)
    if isinstance(status, int):
        parts.append(f"HTTP {status}")
    code = getattr(error, "error_code", None)
    code = getattr(code, "value", code)
    if isinstance(code, str) and code:
        parts.append(code)
    return " ".join(parts)


def _result(check: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"check": check, "passed": passed, "detail": detail}


def _guard(check: str, run: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """An unexpected exception fails the check; it never aborts the report."""
    try:
        return run()
    except Exception as error:
        return _result(check, False, f"unexpected {describe(error)}")


def check_create(backend: AzureBlobBackend, key: str) -> dict[str, Any]:
    check = "create_fresh_key"

    def run() -> dict[str, Any]:
        info = backend.create(key, b"hio storage probe: first write")
        return _result(check, True, f"created {key} as version {info.version_id}")

    return _guard(check, run)


def check_create_again_refused(backend: AzureBlobBackend, key: str) -> dict[str, Any]:
    check = "create_again_raises_blob_exists"

    def run() -> dict[str, Any]:
        try:
            backend.create(key, b"hio storage probe: second write")
        except BlobExists:
            return _result(check, True, f"BlobExists for {key}")
        return _result(check, False, f"a second create of {key} SUCCEEDED (expected BlobExists)")

    return _guard(check, run)


def _expect_refusal(check: str, attempt: Callable[[], object], what: str) -> dict[str, Any]:
    try:
        attempt()
    except HttpResponseError as error:
        status = getattr(error, "status_code", None)
        if status in REFUSAL_STATUSES:
            return _result(check, True, f"{what} refused: {describe(error)}")
        return _result(check, False, f"inconclusive, not a refusal: {describe(error)}")
    except Exception as error:
        return _result(check, False, f"inconclusive, not a refusal: {describe(error)}")
    return _result(check, False, f"{what} SUCCEEDED (expected an authorization or immutability error)")


def check_overwrite_refused(container: Any, key: str) -> dict[str, Any]:
    return _expect_refusal(
        "overwrite_refused",
        lambda: container.get_blob_client(key).upload_blob(
            b"hio storage probe: overwrite", overwrite=True, timeout=30
        ),
        f"overwrite of {key}",
    )


def check_delete_refused(container: Any, key: str) -> dict[str, Any]:
    return _expect_refusal(
        "delete_refused",
        lambda: container.get_blob_client(key).delete_blob(timeout=30),
        f"delete of {key}",
    )


def check_one_version(backend: AzureBlobBackend, key: str) -> dict[str, Any]:
    check = "exactly_one_version"

    def run() -> dict[str, Any]:
        found = backend.versions(key)
        ids = [v.version_id for v in found]
        if len(found) == 1 and ids[0]:
            return _result(check, True, f"one version of {key}: {ids[0]}")
        return _result(check, False, f"{len(found)} versions of {key} (expected exactly one): {ids}")

    return _guard(check, run)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="microseconds")


def check_c5_timing(
    backend: AzureBlobBackend,
    key_for: Callable[[], str],
    *,
    repeats: int,
    delta: timedelta,
    now: Now,
) -> dict[str, Any]:
    """`repeats` fresh creates; each observation is `completed_at`, the provider's `s` (stat) and
    `s - completed_at` in milliseconds. A violation is any observation outside
    `completed_at <= s <= completed_at + delta`; no tolerance is applied."""
    check = "c5_timing"
    observations: list[dict[str, Any]] = []
    for _ in range(repeats):
        key = key_for()
        try:
            backend.create(key, b"hio storage probe: timing write")
            completed_at = now()
            info = backend.stat(key)
        except Exception as error:
            observations.append({"key": key, "error": describe(error), "within": False})
            continue
        if info is None:
            observations.append({"key": key, "error": "stat found no blob after create", "within": False})
            continue
        s = info.written_at
        observations.append(
            {
                "key": key,
                "completed_at": _iso(completed_at),
                "s": _iso(s),
                "diff_ms": (s - completed_at) / timedelta(milliseconds=1),
                "within": completed_at <= s <= completed_at + delta,
            }
        )
    measured = [o["diff_ms"] for o in observations if "diff_ms" in o]
    violations = sum(1 for o in observations if not o["within"])
    detail = {
        "repeats": repeats,
        "delta_seconds": delta.total_seconds(),
        "tolerance": "none",
        "violations": violations,
        "errors": sum(1 for o in observations if "error" in o),
        "min_diff_ms": min(measured) if measured else None,
        "max_diff_ms": max(measured) if measured else None,
        "observations": observations,
    }
    return _result(check, violations == 0 and len(observations) == repeats and repeats > 0, detail)


def run_checks(
    container: Any,
    *,
    run_id: str,
    repeats: int = DEFAULT_REPEATS,
    delta_seconds: float = DEFAULT_DELTA_SECONDS,
    now: Now = utc_now,
) -> list[dict[str, Any]]:
    backend = AzureBlobBackend(container)
    counter = iter(range(1, 10**9))

    def next_key() -> str:
        return f"probe/{run_id}/{next(counter)}"

    key = next_key()
    return [
        check_create(backend, key),
        check_create_again_refused(backend, key),
        check_overwrite_refused(container, key),
        check_delete_refused(container, key),
        check_one_version(backend, key),
        check_c5_timing(backend, next_key, repeats=repeats, delta=timedelta(seconds=delta_seconds), now=now),
    ]


def new_run_id() -> str:
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}"


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    credential_builder: Callable[..., Any] = github_oidc_credential,
    container_builder: Callable[..., Any] = container_client,
    now: Now = utc_now,
    run_id: str | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="storage_probe")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--delta-seconds", type=float, default=DEFAULT_DELTA_SECONDS)
    parser.add_argument("--report-file", help="also write the JSON report to this file")
    args = parser.parse_args(argv)
    if args.repeats < 1 or args.delta_seconds <= 0:
        print("refused: --repeats must be at least 1 and --delta-seconds positive", file=sys.stderr)
        return 2
    environ = os.environ if environ is None else environ
    missing = [name for name in REQUIRED_ENV if not environ.get(name)]
    if missing:
        print(
            f"refused: required environment variables are missing or empty: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    account_url = environ[ENV_ACCOUNT_URL]
    host = urlsplit(account_url).hostname
    started = now()
    run = run_id or new_run_id()
    credential = None
    try:
        credential = credential_builder(environ[ENV_TENANT_ID], environ[ENV_CLIENT_ID], environ)
        container = container_builder(account_url, environ[ENV_CONTAINER], credential)
        results = run_checks(
            container, run_id=run, repeats=args.repeats, delta_seconds=args.delta_seconds, now=now
        )
    except Exception as error:
        print(f"refused: could not build the client ({describe(error)})", file=sys.stderr)
        return 2
    finally:
        close = getattr(credential, "close", None)
        if callable(close):
            close()
    report = {
        "run_id": run,
        "started_at": _iso(started),
        "account_host": host,
        "passed": all(r["passed"] for r in results),
        "results": results,
    }
    text = json.dumps(report, indent=2)
    if args.report_file:
        with open(args.report_file, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
