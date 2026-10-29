"""Soak reconciliation report (T-0013 A-3; T-0009 §7). The soak's gap and punctuality record.

For a period [start, end) it reconciles every expected capture slot (`hio.sources.schedule.expected_slots`:
a slot instance on a business day of its publisher's calendar, due in the period) against the attempt
records in the evidence store, and prints one JSON report. Each slot is exactly one of:

    captured             a `verified_changed` attempt exists (new data was captured)
    verified_unchanged   no capture, but a `verified_unchanged` attempt exists (checked, nothing new)
    failed               attempts exist and every one of them failed
    missing              no attempt record names this publication, slot and due instant

with the start lateness (the attempt's `attempted_at` minus the slot's due instant, in seconds) and the
completion time of the deciding attempt: the earliest attempt of the best outcome. Summary counts are per
publication. Unlike the capture job's 24-hour check, the report covers any period, so a gap older than
the job's alert horizon is still on record.

It reports and does not judge: the exit status is 0 whenever a report is written, however many slots are
missing. It exits 2 only when no report can be produced (bad arguments, missing environment, a calendar
that does not cover the period, an unreadable store). An attempt record that fails verification does not
stop the report: its key is listed under `unreadable_records`.

Reads only, through the `BlobBackend` protocol, with the identity of whoever runs it (the owner's reader
identity at run time, OD-0119 C-5): the default backend uses `DefaultAzureCredential` and the account and
container named in HIO_STORAGE_ACCOUNT_URL and HIO_STORAGE_CONTAINER. Tests inject a fake backend.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from hio.contracts.observation import parse_instant
from hio.jobs.s1b1_capture import ENV_ACCOUNT_URL, ENV_CONTAINER, WEEKDAYS, merge_calendars
from hio.marketdata.runrecord import RunRecord
from hio.reference.calendar import BusinessCalendar, load_reference_calendar
from hio.sources.schedule import LATENESS, SLOTS, Slot, expected_slots, load_attempt_records
from hio.storage.blobstore import BlobBackend, BlobObjectStore

STATUS_OF_OUTCOME = {
    "verified_changed": "captured",
    "verified_unchanged": "verified_unchanged",
    "failed": "failed",
}
STATUSES = ("captured", "verified_unchanged", "failed", "missing")
_BEST_FIRST = tuple(STATUS_OF_OUTCOME)  # an outcome earlier in this order decides the slot

BackendBuilder = Callable[[Mapping[str, str]], BlobBackend]


def default_backend(environ: Mapping[str, str]) -> BlobBackend:
    """The reader's own identity (az login, environment or managed identity), never a stored secret."""
    missing = [name for name in (ENV_ACCOUNT_URL, ENV_CONTAINER) if not environ.get(name)]
    if missing:
        raise ValueError(f"required environment variables are missing or empty: {', '.join(missing)}")
    from azure.identity import DefaultAzureCredential

    from hio.storage.azure_blob import AzureBlobBackend, container_client

    return AzureBlobBackend(
        container_client(environ[ENV_ACCOUNT_URL], environ[ENV_CONTAINER], DefaultAzureCredential())
    )


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def reconcile(expected: Iterable[tuple[Slot, datetime]], records: Iterable[RunRecord]) -> dict[str, Any]:
    """The report body: one entry per expected slot, and the per-publication counts."""
    by_slot: dict[tuple[str, str | None, datetime | None], list[RunRecord]] = {}
    for record in records:
        by_slot.setdefault((record.source_id, record.slot, record.slot_due_at), []).append(record)
    summary = {
        pid: {"expected": 0, **dict.fromkeys(STATUSES, 0)}
        for pid in sorted({s.publication_id for s in SLOTS})
    }
    slots = []
    for slot, due in expected:
        attempts = by_slot.get((slot.publication_id, slot.name, due), [])
        entry: dict[str, Any] = {
            "publication_id": slot.publication_id,
            "slot": slot.name,
            "due_at": _iso(due),
            "status": "missing",
            "attempts": len(attempts),
            "started_at": None,
            "start_lateness_seconds": None,
            "completed_at": None,
            "error_class": None,
        }
        if attempts:
            deciding = min(attempts, key=lambda r: (_BEST_FIRST.index(r.outcome), r.attempted_at))
            entry.update(
                status=STATUS_OF_OUTCOME[deciding.outcome],
                started_at=_iso(deciding.attempted_at),
                start_lateness_seconds=(deciding.attempted_at - due).total_seconds(),
                completed_at=_iso(deciding.completed_at),
                error_class=deciding.error_class,
            )
        slots.append(entry)
        summary[slot.publication_id]["expected"] += 1
        summary[slot.publication_id][entry["status"]] += 1
    return {"slots": slots, "summary": summary}


def report(
    start: datetime,
    end: datetime,
    calendars: Mapping[str, BusinessCalendar],
    backend: BlobBackend,
) -> dict[str, Any]:
    unreadable: list[str] = []
    # The expected slots come first: a calendar that does not cover the period raises before any read.
    expected = expected_slots(start, end, calendars)
    records = load_attempt_records(BlobObjectStore(backend), start, unreadable)  # type: ignore[arg-type]
    body = reconcile(expected, records)
    return {
        "period": {"start": _iso(start), "end": _iso(end)},
        "lateness_seconds": LATENESS.total_seconds(),
        **body,
        "unreadable_records": sorted(unreadable),
    }


def _instant(text: str) -> datetime:
    try:
        return parse_instant(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    backend_builder: BackendBuilder = default_backend,
) -> int:
    parser = argparse.ArgumentParser(
        prog="soak_report", description="Reconcile expected capture slots with attempts."
    )
    parser.add_argument(
        "--start", required=True, type=_instant, help="period start, UTC with a Z suffix (inclusive)"
    )
    parser.add_argument(
        "--end", required=True, type=_instant, help="period end, UTC with a Z suffix (exclusive)"
    )
    parser.add_argument(
        "--rits-calendar",
        required=True,
        action="append",
        help="a dated, cited RITS calendar file covering the period; repeat for several (they are merged)",
    )
    args = parser.parse_args(argv)
    if args.end <= args.start:
        print("refused: --end must be after --start", file=sys.stderr)
        return 2
    try:
        rits = merge_calendars([load_reference_calendar(p) for p in args.rits_calendar])
        backend = backend_builder(os.environ if environ is None else environ)
        body = report(args.start, args.end, {"rits": rits, "weekdays": WEEKDAYS}, backend)
    except Exception as error:  # no report can be produced; name the type, never provider text
        detail = f": {error}" if isinstance(error, ValueError) else ""
        print(f"no report: {type(error).__name__}{detail}", file=sys.stderr)
        return 2
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
