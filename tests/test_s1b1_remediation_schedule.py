"""Adversarial regressions for F-REVIEW-2026-10-25-t0009-7 (OD-0067): a disabled scheduled-workflow
definition and a tested local-time due gate. The gate, not the caller, supplies the slot and its due
instant; nothing here makes a real request or enables a schedule."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from hio.jobs import s1b1_capture
from hio.jobs.s1b1_capture import WEEKDAYS, run_due
from hio.sources.datasets import PUBLICATIONS
from hio.sources.schedule import CRON_UTC, LATENESS, SLOTS, due_slots
from hio.sources.transport import FixtureTransport, HttpResponse
from hio.storage.objectstore import LocalObjectStore
from tests.helpers import AllowAllGate
from tests.test_s1b1_capture import EXEC, FILES, FX, HEADERS, UA, go
from tests.test_s1b1_releases import RITS

REPO = Path(__file__).resolve().parent.parent
DEFINITION = REPO / "infra" / "workflows" / "s1b1-capture.yml"
CALS = {"rits": RITS, "weekdays": WEEKDAYS}


def utc(*a) -> datetime:
    return datetime(*a, tzinfo=UTC)


def names(due):
    return {(s.publication_id, s.name, d) for s, d in due}


# --- the definition is complete and disabled ------------------------------------------------------


def test_f7_the_definition_fires_on_exactly_the_gate_cron_slots_and_is_not_enabled():
    doc = yaml.safe_load(DEFINITION.read_text())
    crons = [c["cron"] for c in doc[True]["schedule"]]  # YAML 1.1 reads the key `on` as True
    assert crons == [f"{hm} * * *" for hm in CRON_UTC]
    assert doc["permissions"] == {"contents": "read", "id-token": "write"}
    job = doc["jobs"]["capture"]
    assert job["environment"] == "capture"
    text = DEFINITION.read_text()
    assert "secrets." not in text
    assert not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text)
    env = next(s["env"] for s in job["steps"] if "hio.jobs.s1b1_capture" in s.get("run", ""))
    assert env == {
        name: f"${{{{ vars.{name} }}}}"
        for name in ("HIO_STORAGE_ACCOUNT_URL", "HIO_STORAGE_CONTAINER", "AZURE_TENANT_ID", "AZURE_CLIENT_ID")
    }
    assert "--dry-run" not in text and "hio.jobs.s1b1_capture" in text and "rits-*.yaml" in text
    assert not DEFINITION.is_relative_to(REPO / ".github")


def test_f7_no_enabled_workflow_has_a_schedule():
    for wf in (REPO / ".github" / "workflows").glob("*.y*ml"):
        on = yaml.safe_load(wf.read_text())[True]
        assert not (isinstance(on, dict) and "schedule" in on), wf.name


def _firings(day: date) -> list[datetime]:
    out = []
    for offset in (-1, 0, 1):
        d = day + timedelta(days=offset)
        for hm in CRON_UTC:
            minute, hour = (int(x) for x in hm.split())
            out.append(datetime(d.year, d.month, d.day, hour, minute, tzinfo=UTC))
    return out


def test_f7_every_slot_on_every_day_of_two_years_has_a_firing_and_a_retry_inside_its_window():
    """Across both Sydney and New York daylight-saving switches (2026 and 2027)."""
    day = date(2026, 1, 1)
    while day <= date(2027, 12, 31):
        if day.weekday() < 5:
            firings = _firings(day)
            for slot in SLOTS:
                due = slot.due_at(day)
                inside = [t for t in firings if due <= t < due + LATENESS]
                assert len(inside) >= 2, (slot, day)
                for t in inside:  # the gate agrees that the slot is due at each such firing
                    assert (slot.publication_id, slot.name, due) in names(
                        due_slots(t, {"rits": WEEKDAYS, "weekdays": WEEKDAYS})
                    )
        day += timedelta(days=1)


# --- the due gate ---------------------------------------------------------------------------------


def test_f7_due_times_follow_local_time_across_daylight_saving():
    # Sydney 09:45 in AEDT (UTC+11) and in AEST (UTC+10); New York 08:30 in EDT and EST.
    aedt = names(due_slots(utc(2026, 11, 1, 22, 45), CALS))
    assert ("rba.f1", "first", utc(2026, 11, 1, 22, 45)) in aedt
    winter = names(due_slots(utc(2026, 7, 5, 23, 45), {"rits": WEEKDAYS, "weekdays": WEEKDAYS}))
    assert ("rba.f1", "first", utc(2026, 7, 5, 23, 45)) in winter
    assert ("nyfed.sofr", "first", utc(2026, 10, 30, 12, 30)) in names(
        due_slots(utc(2026, 10, 30, 12, 30), CALS)
    )
    assert ("nyfed.sofr", "first", utc(2026, 11, 2, 13, 30)) in names(
        due_slots(utc(2026, 11, 2, 13, 30), CALS)
    )
    assert not due_slots(utc(2026, 11, 2, 12, 30), CALS)  # 07:30 EST: not yet due


def test_f7_a_slot_is_due_only_inside_its_window():
    due = utc(2026, 11, 1, 22, 45)  # Mon 2 Nov 09:45 Sydney
    assert not [s for s, d in due_slots(due - timedelta(minutes=1), CALS) if s.publication_id == "rba.f1"]
    assert [
        s for s, d in due_slots(due + LATENESS - timedelta(seconds=1), CALS) if s.publication_id == "rba.f1"
    ]
    assert not [s for s, d in due_slots(due + LATENESS, CALS) if s.publication_id == "rba.f1"]


def test_f7_no_rba_slot_is_due_on_a_rits_closure_or_a_weekend():
    closed = utc(2026, 11, 2, 22, 45)  # Tue 3 Nov 09:45 Sydney: the synthetic RITS closure
    assert not [s for s, _ in due_slots(closed, CALS) if s.calendar == "rits"]
    assert [s for s, _ in due_slots(closed + timedelta(days=1), CALS) if s.calendar == "rits"]
    assert not due_slots(utc(2026, 10, 31, 22, 45), CALS)  # Sun 1 Nov in Sydney, Sat in New York


def test_f7_a_date_outside_the_cited_rits_coverage_refuses_rather_than_running():
    with pytest.raises(ValueError, match="outside the coverage"):
        due_slots(utc(2027, 1, 4, 22, 45), CALS)


# --- the production caller ------------------------------------------------------------------------


def _urls():
    return {pid: f"https://fixture.invalid/{pid}" for pid in PUBLICATIONS}


def _responses(n=3):
    return {
        _urls()[pid]: [HttpResponse(200, HEADERS, (FX / FILES[pid]).read_bytes(), _urls()[pid])] * n
        for pid in PUBLICATIONS
    }


def _tick(start):
    t = [start]

    def clock():
        t[0] += timedelta(seconds=1)
        return t[0]

    return clock


def test_f7_run_due_records_the_gate_slot_and_is_idempotent(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    transport = FixtureTransport(_responses())
    now = utc(2026, 11, 1, 22, 45)  # Sydney first checks due
    kw = dict(
        store=store,
        gate=AllowAllGate(),
        transport=transport,
        rits=RITS,
        execution=EXEC,
        user_agent=UA,
        urls=_urls(),
    )
    results = run_due(now, clock=_tick(now), **kw)
    assert {(r.record.source_id, r.record.slot, r.record.slot_due_at) for r in results} == {
        ("rba.f1", "first", now),
        ("rba.expert_judgement", "first", now),
    }
    requests = len(transport.requests)
    retry = now + timedelta(hours=1)
    assert run_due(retry, clock=_tick(retry), **kw) == []  # verified: the retry firing is a no-op
    assert len(transport.requests) == requests


def test_f7_a_failed_slot_is_retried_at_the_next_firing(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    url = _urls()["rba.f1"]
    script = _responses()
    script[url] = [
        HttpResponse(503, HEADERS, b"", url),
        HttpResponse(200, HEADERS, (FX / FILES["rba.f1"]).read_bytes(), url),
    ]
    transport = FixtureTransport(script)
    now = utc(2026, 11, 1, 22, 45)
    kw = dict(
        store=store,
        gate=AllowAllGate(),
        transport=transport,
        rits=RITS,
        execution=EXEC,
        user_agent=UA,
        urls=_urls(),
    )
    first = {r.record.source_id: r.record for r in run_due(now, clock=_tick(now), **kw)}
    assert first["rba.f1"].outcome == "failed"
    retry = now + timedelta(hours=1)
    again = {r.record.source_id: r.record for r in run_due(retry, clock=_tick(retry), **kw)}
    assert set(again) == {"rba.f1"} and again["rba.f1"].outcome == "verified_changed"
    assert again["rba.f1"].slot_due_at == now  # the same slot, not a new one


def test_f7_a_caller_cannot_record_an_inconsistent_or_premature_slot(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    url = "https://fixture.invalid/rba.f1"
    transport = FixtureTransport(
        {url: [HttpResponse(200, HEADERS, (FX / FILES["rba.f1"]).read_bytes(), url)]}
    )
    at = utc(2026, 11, 1, 22, 0)
    clock = _tick(at)
    for kw in (
        {"slot": "first"},
        {"slot_due_at": at},
        {"slot": "midday", "slot_due_at": at},
        {"slot": "first", "slot_due_at": at + timedelta(hours=1)},  # not yet due
    ):
        with pytest.raises(ValueError, match="slot"):
            go("rba.f1", transport, store, clock, **kw)
    assert transport.requests == [] and store.snapshot() == {}  # refused before any request


def test_f7_the_record_itself_rejects_inconsistent_slot_facts(tmp_path):
    store = LocalObjectStore(tmp_path / "s")
    url = "https://fixture.invalid/rba.f1"
    transport = FixtureTransport(
        {url: [HttpResponse(200, HEADERS, (FX / FILES["rba.f1"]).read_bytes(), url)]}
    )
    rec = go(
        "rba.f1",
        transport,
        store,
        _tick(utc(2026, 11, 1, 22, 45)),
        slot="first",
        slot_due_at=utc(2026, 11, 1, 22, 45),
    ).record
    with pytest.raises(ValueError, match="together"):
        replace(rec, slot=None)
    with pytest.raises(ValueError, match="before its slot is due"):
        replace(rec, slot_due_at=rec.attempted_at + timedelta(seconds=1))


def test_f7_the_entry_point_only_prints_due_slots_and_refuses_live_capture(tmp_path, capsys):
    cal = tmp_path / "rits.yaml"
    cal.write_text(
        "calendar_id: rits\nkind: reference\nas_of: 2026-10-28\n"
        'source: {citation: "test", url: "https://example.invalid/rits", rights_source_id: "test.only"}\n'
        "coverage: {start: 2026-09-01, end: 2026-12-31}\nweekend: [5, 6]\nclosed: []\n"
    )
    assert s1b1_capture.main(["--rits-calendar", str(cal), "--at", "2026-11-01T22:45:00Z", "--dry-run"]) == 0
    assert "due rba.f1 first 2026-11-01T22:45:00+00:00" in capsys.readouterr().out
    assert s1b1_capture.main(["--rits-calendar", str(cal), "--at", "2026-11-01T22:45:00Z"]) == 2
    assert "refused" in capsys.readouterr().err
    with pytest.raises(ValueError, match="test data"):  # a synthetic calendar is never used live
        s1b1_capture.main(
            ["--rits-calendar", str(REPO / "tests/fixtures/synthetic/s1b1/calendar_rits.yaml"), "--dry-run"]
        )
