"""T-0013 A-3: the soak reconciliation report (`tools/soak_report.py`), offline against a fake blob backend.

The report is the soak's gap and punctuality record (T-0009 §7): for any period it names each expected slot
as captured, verified_unchanged, failed or missing, with start lateness and completion time, and it exits 0
whatever it finds."""

from __future__ import annotations

import importlib.util
import json
from datetime import timedelta
from pathlib import Path

import pytest

from hio.contracts.layout import ATTEMPTS_PREFIX
from hio.jobs.s1b1_capture import WEEKDAYS
from hio.sources.schedule import LATENESS, SLOTS, expected_slots
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from tests.test_t0010_capture_cli import calendar
from tests.test_t0013_completeness import at, put, rec, rits

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("soak_report", REPO / "tools" / "soak_report.py")
soak = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(soak)

PUBS = sorted({s.publication_id for s in SLOTS})
CALS = {"rits": rits(), "weekdays": WEEKDAYS}


def z(moment):
    return moment.isoformat()  # the report's own format: UTC with an explicit offset


def run(tmp_path, capsys, start, end, records=(), *, backend=None, cal=None):
    backend = backend or FakeBlobBackend()
    put(BlobObjectStore(backend), *records)
    argv = [
        "--start",
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--end",
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--rits-calendar",
        cal or calendar(tmp_path, end="2027-12-31"),
    ]
    rc = soak.main(argv, environ={}, backend_builder=lambda _env: backend)
    captured = capsys.readouterr()
    return rc, (json.loads(captured.out) if captured.out else None), captured


def slot_entry(report, pid, name, due):
    (entry,) = [
        s for s in report["slots"] if (s["publication_id"], s["slot"], s["due_at"]) == (pid, name, z(due))
    ]
    return entry


def everything(start, end, **kw):
    return [rec(s.publication_id, s.name, d, **kw) for s, d in expected_slots(start, end, CALS)]


# --- the shape ----------------------------------------------------------------------------------------


def test_a_complete_period_reconciles_every_slot_and_prints_only_json(tmp_path, capsys):
    start, end = at(11, 2), at(11, 6)  # Mon 2 to Thu 5 Nov, UTC days
    rc, report, captured = run(tmp_path, capsys, start, end, everything(start, end))
    assert rc == 0 and captured.err == ""
    assert captured.out.startswith("{") and captured.out.rstrip().endswith("}")
    assert report["period"] == {"start": z(start), "end": z(end)}
    assert report["lateness_seconds"] == LATENESS.total_seconds()
    assert report["unreadable_records"] == []
    assert len(report["slots"]) == len(expected_slots(start, end, CALS))
    assert {s["status"] for s in report["slots"]} == {"verified_unchanged"}
    assert sorted(report["summary"]) == PUBS


def test_each_entry_carries_lateness_and_completion(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 13, 30)
    rc, report, _ = run(
        tmp_path,
        capsys,
        start,
        end,
        [rec("nyfed.sofr", "first", due, delay=timedelta(minutes=7, seconds=30), took=timedelta(seconds=12))],
    )
    assert rc == 0
    assert slot_entry(report, "nyfed.sofr", "first", due) == {
        "publication_id": "nyfed.sofr",
        "slot": "first",
        "due_at": z(due),
        "status": "verified_unchanged",
        "attempts": 1,
        "started_at": z(due + timedelta(minutes=7, seconds=30)),
        "start_lateness_seconds": 450.0,
        "completed_at": z(due + timedelta(minutes=7, seconds=42)),
        "error_class": None,
    }


def test_a_missing_slot_has_no_times(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    _, report, _ = run(tmp_path, capsys, start, end)
    entry = slot_entry(report, "nyfed.sofr", "final", at(11, 3, 20))
    assert entry["status"] == "missing" and entry["attempts"] == 0
    assert entry["started_at"] is entry["start_lateness_seconds"] is entry["completed_at"] is None


# --- statuses -----------------------------------------------------------------------------------------


def test_a_gap_older_than_the_jobs_horizon_is_still_reported(tmp_path, capsys):
    """The job's check looks back 24 hours; the report has no horizon. One slot of a week-old period is
    absent, and the report names it."""
    start, end = at(11, 2), at(11, 4)
    gap = ("nyfed.sofr", "final", at(11, 2, 20))
    records = [r for r in everything(start, end) if (r.source_id, r.slot, r.slot_due_at) != gap]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    assert [s for s in report["slots"] if s["status"] == "missing"] == [
        slot_entry(report, gap[0], gap[1], gap[2])
    ]
    assert report["summary"]["nyfed.sofr"]["missing"] == 1
    assert report["summary"]["nyfed.sofr_index"]["missing"] == 0


def test_a_slot_whose_every_attempt_failed_is_failed_not_captured(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 13, 30)
    records = [
        rec("nyfed.sofr", "first", due, outcome="failed", delay=timedelta(minutes=1)),
        rec("nyfed.sofr", "first", due, outcome="failed", delay=timedelta(minutes=65)),
    ]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    entry = slot_entry(report, "nyfed.sofr", "first", due)
    assert entry["status"] == "failed" and entry["attempts"] == 2
    assert entry["error_class"] == "network" and entry["start_lateness_seconds"] == 60.0
    assert report["summary"]["nyfed.sofr"] == {
        "expected": 2,
        "captured": 0,
        "verified_unchanged": 0,
        "failed": 1,
        "missing": 1,
    }


def test_a_retry_that_succeeded_decides_the_slot(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 13, 30)
    records = [
        rec("nyfed.sofr", "first", due, outcome="failed", delay=timedelta(minutes=1)),
        rec("nyfed.sofr", "first", due, outcome="verified_unchanged", delay=timedelta(minutes=61)),
    ]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    entry = slot_entry(report, "nyfed.sofr", "first", due)
    assert (entry["status"], entry["attempts"], entry["start_lateness_seconds"]) == (
        "verified_unchanged",
        2,
        3660.0,
    )
    assert entry["error_class"] is None


def test_captured_means_new_data_and_outranks_unchanged(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 22, 45)
    records = [
        rec("rba.f1", "first", due, outcome="verified_unchanged", delay=timedelta(minutes=1)),
        rec("rba.f1", "first", due, outcome="verified_changed", delay=timedelta(minutes=2)),
    ]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    assert slot_entry(report, "rba.f1", "first", due)["status"] == "captured"
    assert report["summary"]["rba.f1"]["captured"] == 1


def test_a_late_start_within_lateness_is_reported_with_its_lateness(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 20)
    late = LATENESS - timedelta(seconds=1)
    _, report, _ = run(
        tmp_path, capsys, start, end, [rec("nyfed.sofr", "final", due, delay=late, took=timedelta(seconds=3))]
    )
    entry = slot_entry(report, "nyfed.sofr", "final", due)
    assert entry["status"] == "verified_unchanged"
    assert entry["start_lateness_seconds"] == 10799.0 < report["lateness_seconds"]
    assert entry["completed_at"] == z(due + late + timedelta(seconds=3))


def test_records_that_name_another_slot_instant_or_publication_leave_the_slot_missing(tmp_path, capsys):
    start, end = at(11, 3), at(11, 4)
    due = at(11, 3, 13, 30)
    records = [
        rec("nyfed.sofr", "final", due),  # the other slot at this instant
        rec("nyfed.sofr", "first", due - timedelta(days=1)),  # the previous day's due instant
        rec("nyfed.sofr_index", "first", due),  # another publication
    ]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    assert slot_entry(report, "nyfed.sofr", "first", due)["status"] == "missing"
    assert slot_entry(report, "nyfed.sofr_index", "first", due)["status"] == "verified_unchanged"
    assert len(report["slots"]) == len(expected_slots(start, end, CALS))  # outside records add no entries


def test_summary_counts_are_per_publication(tmp_path, capsys):
    start, end = (
        at(11, 3),
        at(11, 4),
    )  # 2 NY slots per NY publication; Sydney: first (22:45Z) only on this UTC day
    records = [
        rec("nyfed.sofr", "first", at(11, 3, 13, 30), outcome="verified_changed"),
        rec("nyfed.sofr", "final", at(11, 3, 20), outcome="failed"),
        rec("nyfed.sofr_index", "first", at(11, 3, 13, 30)),
    ]
    _, report, _ = run(tmp_path, capsys, start, end, records)
    summary = report["summary"]
    assert summary["nyfed.sofr"] == {
        "expected": 2,
        "captured": 1,
        "verified_unchanged": 0,
        "failed": 1,
        "missing": 0,
    }
    assert summary["nyfed.sofr_index"] == {
        "expected": 2,
        "captured": 0,
        "verified_unchanged": 1,
        "failed": 0,
        "missing": 1,
    }
    assert summary["rba.f1"]["expected"] == summary["rba.expert_judgement"]["expected"] == 2
    for counts in summary.values():
        assert counts["expected"] == sum(
            counts[k] for k in ("captured", "verified_unchanged", "failed", "missing")
        )


# --- periods ------------------------------------------------------------------------------------------


def test_an_empty_period_reports_no_slots_and_exits_zero(tmp_path, capsys):
    start, end = at(11, 7, 6), at(11, 8, 6)  # Saturday morning to Sunday morning UTC: no business-day slot
    rc, report, _ = run(tmp_path, capsys, start, end)
    assert rc == 0 and report["slots"] == [] and report["unreadable_records"] == []
    assert sorted(report["summary"]) == PUBS
    assert all(set(c.values()) == {0} for c in report["summary"].values())


def test_nothing_attempted_all_period_is_all_missing_and_still_exit_zero(tmp_path, capsys):
    start, end = at(11, 2), at(11, 9)
    rc, report, _ = run(tmp_path, capsys, start, end)
    assert rc == 0
    assert {s["status"] for s in report["slots"]} == {"missing"}
    assert sum(c["missing"] for c in report["summary"].values()) == len(report["slots"]) > 0


def test_a_rits_holiday_is_not_an_expected_slot(tmp_path, capsys):
    cal = calendar(
        tmp_path, "holiday.yaml", end="2027-12-31", closed="[{date: 2026-11-04, reason: synthetic}]"
    )
    _, report, _ = run(tmp_path, capsys, at(11, 3), at(11, 5), cal=cal)
    rba = {s["due_at"] for s in report["slots"] if s["publication_id"] == "rba.f1"}
    assert (
        z(at(11, 3, 22, 45)) not in rba and z(at(11, 4, 5, 30)) not in rba
    )  # Wednesday 4 November in Sydney
    assert z(at(11, 3, 5, 30)) in rba and z(at(11, 4, 22, 45)) in rba


@pytest.mark.parametrize(
    ("start", "end", "pid", "name", "expected"),
    [
        (  # Sydney enters daylight time on 4 Oct 2026
            at(10, 1),
            at(10, 7),
            "rba.f1",
            "first",
            [at(10, 1, 23, 45), at(10, 4, 22, 45), at(10, 5, 22, 45), at(10, 6, 22, 45)],
        ),
        (  # New York leaves daylight time on 1 Nov 2026
            at(10, 29),
            at(11, 4),
            "nyfed.sofr",
            "first",
            [at(10, 29, 12, 30), at(10, 30, 12, 30), at(11, 2, 13, 30), at(11, 3, 13, 30)],
        ),
        (  # New York enters daylight time on 14 Mar 2027
            at(3, 11, year=2027),
            at(3, 17, year=2027),
            "nyfed.sofr_index",
            "final",
            [
                at(3, 11, 20, year=2027),
                at(3, 12, 20, year=2027),
                at(3, 15, 19, year=2027),
                at(3, 16, 19, year=2027),
            ],
        ),
        (  # Sydney leaves daylight time on 4 Apr 2027
            at(4, 1, year=2027),
            at(4, 7, year=2027),
            "rba.expert_judgement",
            "final",
            [
                at(4, 1, 5, 30, year=2027),
                at(4, 2, 5, 30, year=2027),
                at(4, 5, 6, 30, year=2027),
                at(4, 6, 6, 30, year=2027),
            ],
        ),
    ],
)
def test_the_four_daylight_saving_transitions(tmp_path, capsys, start, end, pid, name, expected):
    records = [rec(pid, name, d, delay=timedelta(minutes=5)) for d in expected]
    rc, report, _ = run(tmp_path, capsys, start, end, records)
    assert rc == 0
    got = [s for s in report["slots"] if (s["publication_id"], s["slot"]) == (pid, name)]
    assert [s["due_at"] for s in got] == [z(d) for d in expected]
    assert {s["status"] for s in got} == {"verified_unchanged"}
    assert {s["start_lateness_seconds"] for s in got} == {
        300.0
    }  # lateness is measured from the true due instant


# --- reading and exit codes -----------------------------------------------------------------------------


def test_the_report_reads_through_the_backend_and_never_writes(tmp_path, capsys):
    backend = FakeBlobBackend()
    start, end = at(11, 3), at(11, 4)
    put(BlobObjectStore(backend), *everything(start, end))
    backend.fail_after = 0  # any further create raises
    keys = []
    real = backend.keys
    backend.keys = lambda prefix: (keys.append(prefix), real(prefix))[1]
    rc, report, _ = run(tmp_path, capsys, start, end, backend=backend)
    assert rc == 0 and {s["status"] for s in report["slots"]} == {"verified_unchanged"}
    assert keys == [ATTEMPTS_PREFIX]  # the attempts are listed once


def test_a_record_that_fails_verification_is_listed_and_does_not_stop_the_report(tmp_path, capsys):
    backend = FakeBlobBackend()
    bad = f"{ATTEMPTS_PREFIX}rba.f1/20261103-230000000000-{'b' * 64}.json"
    backend.create(bad, b"{}")
    start, end = at(11, 3), at(11, 4)
    rc, report, _ = run(tmp_path, capsys, start, end, everything(start, end), backend=backend)
    assert rc == 0 and report["unreadable_records"] == [bad]
    assert {s["status"] for s in report["slots"]} == {"verified_unchanged"}


def test_a_record_that_started_before_the_period_is_not_read(tmp_path, capsys):
    backend = FakeBlobBackend()
    backend.create(f"{ATTEMPTS_PREFIX}rba.f1/20261001-000000000000-{'b' * 64}.json", b"{}")  # unreadable, old
    rc, report, _ = run(tmp_path, capsys, at(11, 3), at(11, 4), backend=backend)
    assert rc == 0 and report["unreadable_records"] == []


def test_it_exits_two_only_when_no_report_can_be_made(tmp_path, capsys):
    ok_cal = calendar(tmp_path, end="2027-12-31")
    start, end = at(11, 3), at(11, 4)
    # an inverted period
    rc, report, captured = run(tmp_path, capsys, end, start)
    assert (rc, report) == (2, None) and "--end must be after --start" in captured.err
    # a calendar that does not reach the period
    short = calendar(tmp_path, "short.yaml", end="2026-11-02")
    rc, report, captured = run(tmp_path, capsys, start, end, cal=short)
    assert (rc, report) == (2, None) and "CalendarCoverageError" in captured.err

    # a store that cannot be listed
    class Broken(FakeBlobBackend):
        def keys(self, _prefix):
            raise ConnectionError("https://secret.example/?sig=SECRET")

    rc, report, captured = run(tmp_path, capsys, start, end, backend=Broken(), cal=ok_cal)
    assert (rc, report) == (2, None)
    assert "ConnectionError" in captured.err and "SECRET" not in captured.err


def test_the_default_backend_refuses_without_its_environment(tmp_path, capsys):
    argv = [
        "--start",
        "2026-11-03T00:00:00Z",
        "--end",
        "2026-11-04T00:00:00Z",
        "--rits-calendar",
        calendar(tmp_path),
    ]
    assert soak.main(argv, environ={}) == 2
    err = capsys.readouterr().err
    assert "HIO_STORAGE_ACCOUNT_URL" in err and "HIO_STORAGE_CONTAINER" in err


def test_instants_need_a_z_suffix(tmp_path, capsys):
    argv = [
        "--start",
        "2026-11-03T00:00:00+10:00",
        "--end",
        "2026-11-04T00:00:00Z",
        "--rits-calendar",
        calendar(tmp_path),
    ]
    with pytest.raises(SystemExit) as stop:
        soak.main(argv, environ={}, backend_builder=lambda _env: FakeBlobBackend())
    assert stop.value.code == 2
    assert "Z suffix" in capsys.readouterr().err
