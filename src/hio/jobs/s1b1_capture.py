"""The scheduled capture entry point for S1b-1.0 (T-0009 §2.5; F-REVIEW-2026-10-25-t0009-7).

`run_due` is the production caller of `run_capture`: it asks the due gate which slots are due now,
skips a slot that already has a verified record, and passes the gate's slot and due instant to the
run record. A caller cannot supply its own due time.

`main` is what the (disabled) workflow definition runs. With `--dry-run` it prints the slots due at an
instant and makes no request. Without it, it takes the **live path** (T-0010 W-3; OD-0115, OD-0119 C-1,
C-3, C-8), which is wired but NOT enabled: it refuses (exit 2) unless `LIVE_AUTHORISATION` names the
owner decision that grants Authorisation B (T-0009 §8). Only a later Authorisation B change sets that
constant. The refusal comes before anything is built: no transport, storage client or credential
exists, and no environment variable is read, until the constant is set.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any

from hio.contracts.observation import parse_instant
from hio.contracts.rights import RightsGate
from hio.marketdata.runrecord import Execution
from hio.reference.calendar import BusinessCalendar, load_reference_calendar
from hio.rights.gate import GateContext
from hio.rights.gate import RightsGate as GenuineRightsGate
from hio.rights.register import load_genuine
from hio.sources.datasets import PUBLICATIONS
from hio.sources.http_transport import HttpTransport
from hio.sources.run import RunResult, run_capture
from hio.sources.schedule import already_verified, due_slots
from hio.sources.transport import Transport
from hio.storage.azure_auth import OidcError, github_oidc_credential
from hio.storage.azure_blob import AzureBlobBackend, container_client
from hio.storage.blobstore import BlobObjectStore
from hio.storage.objectstore import LocalObjectStore

WEEKDAYS = BusinessCalendar("weekdays")

# Authorisation B (T-0009 §8) is the owner's explicit grant of live operation. Until a later change
# sets this to the id of the OD record that grants it (for example "OD-0123"), the live path refuses.
LIVE_AUTHORISATION: str | None = None

# Every request names HIO and where its code lives, so a publisher can identify and contact the requester.
USER_AGENT = "HIO-s1b1-capture/1 (+https://github.com/elusivenode/hio)"

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCES_REGISTER = REPO_ROOT / "registers" / "sources.yaml"

ENV_ACCOUNT_URL = "HIO_STORAGE_ACCOUNT_URL"
ENV_CONTAINER = "HIO_STORAGE_CONTAINER"
ENV_TENANT_ID = "AZURE_TENANT_ID"
ENV_CLIENT_ID = "AZURE_CLIENT_ID"
REQUIRED_ENV = (ENV_ACCOUNT_URL, ENV_CONTAINER, ENV_TENANT_ID, ENV_CLIENT_ID)


def run_due(
    now: datetime,
    *,
    store: LocalObjectStore,
    gate: RightsGate,
    transport: Transport,
    rits: BusinessCalendar,
    clock: Callable[[], datetime],
    execution: Execution,
    user_agent: str,
    urls: Mapping[str, str],
) -> list[RunResult]:
    if not rits.is_cited:
        raise ValueError("the due gate needs the dated, cited RITS calendar")
    results = []
    for slot, due in due_slots(now, {"rits": rits, "weekdays": WEEKDAYS}):
        if already_verified(store, slot, due):
            continue
        results.append(
            run_capture(
                PUBLICATIONS[slot.publication_id],
                transport=transport,
                store=store,
                gate=gate,
                clock=clock,
                execution=execution,
                user_agent=user_agent,
                url=urls[slot.publication_id],
                slot=slot.name,
                slot_due_at=due,
            )
        )
    return results


def merge_calendars(calendars: Sequence[BusinessCalendar]) -> BusinessCalendar:
    """One calendar from several dated, cited files of the same calendar (for example 2026 and 2027).

    The files must name the same calendar id and weekend, and their coverages must follow one another
    with no overlap and no gap: an overlap could disagree about a date, and a gap would be read as
    business days nobody cited. Anything else refuses."""
    if not calendars:
        raise ValueError("at least one RITS calendar is required")
    if len(calendars) == 1:
        return calendars[0]
    if not all(c.is_cited for c in calendars):
        raise ValueError("every calendar to merge must be dated and cited")
    ordered = sorted(calendars, key=lambda c: c.coverage[0])  # type: ignore[index]
    first = ordered[0]
    for other in ordered[1:]:
        if other.calendar_id != first.calendar_id or other.weekend != first.weekend:
            raise ValueError("calendars to merge must share one calendar id and weekend")
    for before, after in pairwise(ordered):
        _, end = before.coverage  # type: ignore[misc]
        start, _ = after.coverage  # type: ignore[misc]
        if start <= end:
            raise ValueError(f"calendar coverages overlap: {before.identity} and {after.identity}")
        if start != end + timedelta(days=1):
            raise ValueError(f"calendar coverages leave a gap between {end} and {start}")
    holidays = frozenset().union(*(c.holidays for c in ordered))
    digest = hashlib.sha256("\n".join(str(c.content_sha256) for c in ordered).encode()).hexdigest()
    return replace(
        first,
        holidays=holidays,
        coverage=(ordered[0].coverage[0], ordered[-1].coverage[1]),  # type: ignore[index]
        citation="\n".join(str(c.citation) for c in ordered),
        as_of=max(c.as_of for c in ordered),  # type: ignore[type-var]
        content_sha256=digest,
    )


def _genuine_gate() -> RightsGate:
    return GenuineRightsGate(load_genuine(SOURCES_REGISTER), GateContext(on_external_host=True))


def _default_urls() -> Mapping[str, str]:
    return {pid: spec.url for pid, spec in PUBLICATIONS.items() if spec.url}


@dataclass(frozen=True)
class LiveBuilders:
    """How the live path builds what it uses. The defaults are the real constructors; tests inject fakes."""

    gate: Callable[[], RightsGate] = _genuine_gate
    transport: Callable[[], Transport] = HttpTransport
    credential: Callable[[str, str, Mapping[str, str]], Any] = github_oidc_credential
    container: Callable[[str, str, Any], Any] = container_client
    urls: Callable[[], Mapping[str, str]] = _default_urls
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)


def live_capture(
    now: datetime,
    rits: BusinessCalendar,
    environ: Mapping[str, str],
    builders: LiveBuilders,
) -> int:
    """The live run. Refuses (2) before building anything unless Authorisation B is recorded, then when the
    environment is incomplete. Messages name variables, never values."""
    if LIVE_AUTHORISATION is None:
        print(
            "refused: live capture is not authorised (T-0009 Authorisation B; LIVE_AUTHORISATION is unset)",
            file=sys.stderr,
        )
        return 2
    missing = [name for name in REQUIRED_ENV if not environ.get(name)]
    if missing:
        print(
            f"refused: required environment variables are missing or empty: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    urls = builders.urls()
    unconfigured = sorted(set(PUBLICATIONS) - set(urls))
    if unconfigured:
        print(f"refused: no approved URL is configured for: {', '.join(unconfigured)}", file=sys.stderr)
        return 2
    try:
        credential = builders.credential(environ[ENV_TENANT_ID], environ[ENV_CLIENT_ID], environ)
    except OidcError as error:  # its message never carries a token or a URL
        print(f"refused: the storage credential could not be built: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"refused: the storage credential could not be built ({type(error).__name__})", file=sys.stderr)
        return 2
    client = builders.container(environ[ENV_ACCOUNT_URL], environ[ENV_CONTAINER], credential)
    store = BlobObjectStore(AzureBlobBackend(client))
    results = run_due(
        now,
        store=store,  # type: ignore[arg-type]  # run_due is typed for LocalObjectStore; the store is duck-typed
        gate=builders.gate(),
        transport=builders.transport(),
        rits=rits,
        clock=builders.clock,
        execution=Execution.from_environ(environ),
        user_agent=USER_AGENT,
        urls=urls,
    )
    for result in results:
        record = result.record
        print(f"ran {record.source_id} {record.slot} {record.outcome}")
    return 1 if any(r.record.outcome == "failed" for r in results) else 0


def main(
    argv: list[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    builders: LiveBuilders | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="hio.jobs.s1b1_capture")
    parser.add_argument(
        "--rits-calendar",
        required=True,
        action="append",
        help="a dated, cited RITS calendar file; repeat for several periods (they are merged)",
    )
    parser.add_argument("--at", help="the UTC instant to evaluate (default: now)")
    parser.add_argument("--dry-run", action="store_true", help="print the due slots; make no request")
    args = parser.parse_args(argv)
    now = parse_instant(args.at) if args.at else datetime.now(UTC)
    rits = merge_calendars([load_reference_calendar(p) for p in args.rits_calendar])
    for slot, due in due_slots(now, {"rits": rits, "weekdays": WEEKDAYS}):
        print(f"due {slot.publication_id} {slot.name} {due.isoformat()}")
    if args.dry_run:
        return 0
    return live_capture(now, rits, os.environ if environ is None else environ, builders or LiveBuilders())


if __name__ == "__main__":
    raise SystemExit(main())
