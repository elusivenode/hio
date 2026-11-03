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
                      where `completed_at` is the publisher-completion surrogate (the UTC clock read
                      immediately before the write, as HIO-ADR-0012 defines it) and `s` is the
                      provider's `Last-Modified`. Every observation is reported. NO tolerance is
                      applied: the check passes only with zero violations of that existing rule.
                      T-0015 F-2 adds, in `detail`: the candidate rule `floor_s(completed_at) <= s <=
                      completed_at + delta` beside it (also no tolerance, informational), per-create
                      `timing_records` (pre-PUT, post-PUT and post-metadata instants, monotonic
                      durations, the raw `Date`, `Last-Modified`, `x-ms-version-id` and
                      `x-ms-request-id` headers captured from the SDK PUT, and `Date` brackets on the
                      runner-to-storage clock offset) and the runner's `timedatectl show` state.
                      A header or state that is absent is reported as absent, never invented.

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
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

from azure.core import MatchConditions
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
CAPTURED_HEADERS = ("Date", "Last-Modified", "x-ms-version-id", "x-ms-request-id")

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


def _headers_of(response: Any) -> dict[str, str]:
    """The raw response headers (lower-cased names) from an SDK `raw_response_hook` argument."""
    headers = getattr(getattr(response, "http_response", None), "headers", None)
    if headers is None:
        return {}
    return {str(name).lower(): str(value) for name, value in headers.items()}


class _HeaderCapture:
    """A `raw_response_hook` that keeps the headers of the last response it saw (a retried request
    calls it once per attempt)."""

    def __init__(self) -> None:
        self.calls = 0
        self.headers: dict[str, str] = {}

    def __call__(self, response: Any) -> None:
        self.calls += 1
        self.headers = _headers_of(response)


def _parse_http_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        moment = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if moment.tzinfo is None or moment.utcoffset() is None:
        return None
    return moment.astimezone(UTC)


def _ms(span: timedelta) -> float:
    return span / timedelta(milliseconds=1)


def read_clock_sync() -> dict[str, Any]:
    """The runner's clock-synchronisation state from `timedatectl show`, or why it is unavailable."""
    try:
        completed = subprocess.run(
            ["timedatectl", "show"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {"available": False, "reason": type(error).__name__}
    if completed.returncode != 0:
        return {"available": False, "reason": f"timedatectl exited {completed.returncode}"}
    fields = dict(line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line)
    wanted = ("NTP", "NTPSynchronized", "TimeUSec", "Timezone")
    return {"available": True, **{name: fields[name] for name in wanted if name in fields}}


def _time_record(
    key: str,
    *,
    completed_at: datetime,
    pre_put: datetime,
    post_put: datetime,
    post_metadata: datetime,
    mono: tuple[float, float, float, float],
    capture: _HeaderCapture,
) -> dict[str, Any]:
    """One observation's instruments: the instants, monotonic durations, captured headers and the
    `Date` brackets on the runner-to-storage clock offset (server minus runner)."""
    headers = {name: capture.headers.get(name.lower()) for name in CAPTURED_HEADERS}
    date = _parse_http_date(headers["Date"])
    record: dict[str, Any] = {
        "key": key,
        "completed_at_surrogate": _iso(completed_at),
        "pre_put": _iso(pre_put),
        "post_put": _iso(post_put),
        "post_metadata": _iso(post_metadata),
        "durations_ms": {
            "pre_put_to_post_put": (mono[2] - mono[1]) * 1000,
            "post_put_to_post_metadata": (mono[3] - mono[2]) * 1000,
            "surrogate_to_post_metadata": (mono[3] - mono[0]) * 1000,
        },
        "headers_captured": capture.calls > 0,
        "response_hook_calls": capture.calls,
        "headers": headers,
        "missing_headers": [name for name, value in headers.items() if value is None],
    }
    if date is None:
        record["offset_bracket_ms"] = None
        if headers["Date"] is not None:
            record["missing_headers"].append("Date (unparseable)")
    else:
        # The server stamped Date within [Date, Date + 1 s) of its clock, while the response was
        # received between pre_put and post_put on the runner's clock.
        record["offset_bracket_ms"] = {
            "lower": _ms(date - post_put),
            "upper": _ms(date + timedelta(seconds=1) - pre_put),
        }
    return record


def check_c5_timing(
    container: Any,
    backend: AzureBlobBackend,
    key_for: Callable[[], str],
    *,
    repeats: int,
    delta: timedelta,
    now: Now,
    clock: Now = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    clock_sync: Callable[[], dict[str, Any]] = read_clock_sync,
) -> dict[str, Any]:
    """`repeats` fresh creates. For each: `completed_at` is the publisher-completion surrogate, read
    from `now` once, immediately before the write (HIO-ADR-0012); `s` is the provider's `Last-Modified`
    (stat). The PUT goes through the SDK client with a raw-response hook, so the `Date`,
    `Last-Modified`, `x-ms-version-id` and `x-ms-request-id` headers are captured.

    Two rules are reported side by side, both with NO tolerance:
    - existing:  `completed_at <= s <= completed_at + delta` (this alone decides `passed`);
    - candidate: `floor_s(completed_at) <= s <= completed_at + delta`, informational.
    The other instants (`pre_put`, `post_put`, `post_metadata`) come from `clock`, with monotonic
    durations from `monotonic`; `observations` keeps its T-0012 shape and `timing_records` holds the
    instruments."""
    check = "c5_timing"
    observations: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    candidate_violations = 0
    data = b"hio storage probe: timing write"
    for _ in range(repeats):
        key = key_for()
        capture = _HeaderCapture()
        try:
            completed_at = now()
            mono0 = monotonic()
            pre_put = clock()
            mono1 = monotonic()
            container.get_blob_client(key).upload_blob(
                data,
                length=len(data),
                overwrite=False,
                match_condition=MatchConditions.IfMissing,  # If-None-Match: *, as the backend does
                timeout=30,
                raw_response_hook=capture,
            )
            post_put = clock()
            mono2 = monotonic()
            info = backend.stat(key)
            post_metadata = clock()
            mono3 = monotonic()
        except Exception as error:
            observations.append({"key": key, "error": describe(error), "within": False})
            records.append({"key": key, "error": describe(error)})
            candidate_violations += 1
            continue
        if info is None:
            observations.append({"key": key, "error": "stat found no blob after create", "within": False})
            records.append({"key": key, "error": "stat found no blob after create"})
            candidate_violations += 1
            continue
        s = info.written_at
        floor_s = completed_at.replace(microsecond=0)
        within = completed_at <= s <= completed_at + delta
        candidate_within = floor_s <= s <= completed_at + delta
        candidate_violations += 0 if candidate_within else 1
        observations.append(
            {
                "key": key,
                "completed_at": _iso(completed_at),
                "s": _iso(s),
                "diff_ms": _ms(s - completed_at),
                "within": within,
            }
        )
        record = _time_record(
            key,
            completed_at=completed_at,
            pre_put=pre_put,
            post_put=post_put,
            post_metadata=post_metadata,
            mono=(mono0, mono1, mono2, mono3),
            capture=capture,
        )
        record["floor_s_completed_at"] = _iso(floor_s)
        record["s"] = _iso(s)
        record["existing_rule_within"] = within
        record["candidate_rule_within"] = candidate_within
        records.append(record)
    measured = [o["diff_ms"] for o in observations if "diff_ms" in o]
    violations = sum(1 for o in observations if not o["within"])
    brackets = [r["offset_bracket_ms"] for r in records if r.get("offset_bracket_ms")]
    detail = {
        "repeats": repeats,
        "delta_seconds": delta.total_seconds(),
        "tolerance": "none",
        "violations": violations,
        "errors": sum(1 for o in observations if "error" in o),
        "min_diff_ms": min(measured) if measured else None,
        "max_diff_ms": max(measured) if measured else None,
        "rules": {
            "existing": {"rule": "completed_at <= s <= completed_at + delta", "violations": violations},
            "candidate": {
                "rule": "floor_s(completed_at) <= s <= completed_at + delta",
                "violations": candidate_violations,
            },
            "tolerance": "none",
        },
        "offset_bounds_ms": {
            "observations_with_bracket": len(brackets),
            "lower_max": max((b["lower"] for b in brackets), default=None),
            "upper_min": min((b["upper"] for b in brackets), default=None),
        },
        "clock_sync": clock_sync(),
        "observations": observations,
        "timing_records": records,
    }
    return _result(check, violations == 0 and len(observations) == repeats and repeats > 0, detail)


def run_checks(
    container: Any,
    *,
    run_id: str,
    repeats: int = DEFAULT_REPEATS,
    delta_seconds: float = DEFAULT_DELTA_SECONDS,
    now: Now = utc_now,
    clock: Now = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    clock_sync: Callable[[], dict[str, Any]] = read_clock_sync,
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
        check_c5_timing(
            container,
            backend,
            next_key,
            repeats=repeats,
            delta=timedelta(seconds=delta_seconds),
            now=now,
            clock=clock,
            monotonic=monotonic,
            clock_sync=clock_sync,
        ),
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
