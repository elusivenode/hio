"""The scheduled capture entry point for S1b-1.0 (T-0009 §2.5; F-REVIEW-2026-10-25-t0009-7).

`run_due` is the production caller of `run_capture`: it asks the due gate which slots are due now,
skips a slot that already has a verified record, and passes the gate's slot and due instant to the
run record. A caller cannot supply its own due time.

`main` is what the (disabled) workflow definition runs. It never makes a request: no network
transport exists in `src/` and live capture needs Authorisation B (T-0009 §8). With `--dry-run` it
prints the slots due at an instant; without it, it refuses.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from hio.contracts.observation import parse_instant
from hio.contracts.rights import RightsGate
from hio.marketdata.runrecord import Execution
from hio.reference.calendar import BusinessCalendar, load_reference_calendar
from hio.sources.datasets import PUBLICATIONS
from hio.sources.run import RunResult, run_capture
from hio.sources.schedule import already_verified, due_slots
from hio.sources.transport import Transport
from hio.storage.objectstore import LocalObjectStore

WEEKDAYS = BusinessCalendar("weekdays")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hio.jobs.s1b1_capture")
    parser.add_argument("--rits-calendar", required=True, help="a dated, cited RITS calendar file")
    parser.add_argument("--at", help="the UTC instant to evaluate (default: now)")
    parser.add_argument("--dry-run", action="store_true", help="print the due slots; make no request")
    args = parser.parse_args(argv)
    now = parse_instant(args.at) if args.at else datetime.now(UTC)
    rits = load_reference_calendar(args.rits_calendar)
    for slot, due in due_slots(now, {"rits": rits, "weekdays": WEEKDAYS}):
        print(f"due {slot.publication_id} {slot.name} {due.isoformat()}")
    if args.dry_run:
        return 0
    print("refused: live capture is not authorised (T-0009 Authorisation B)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
