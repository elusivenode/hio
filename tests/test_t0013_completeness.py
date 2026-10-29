"""T-0013 A-1: per-slot completeness. `expected_slots` and `missed_slots` in `hio.sources.schedule`, and the
capture job's check after every live run. Offline: fake blob backends and a fake container only.

Reference instants (2026): Sydney is on AEDT (UTC+11) until 4 April 2027 and from 4 October 2026; New York
is on EDT (UTC-4) until Sunday 1 November 2026 and from Sunday 14 March 2027, EST (UTC-5) between.
Sydney 09:45 / 16:30 is therefore 22:45Z the day before / 05:30Z in November; New York 08:30 / 15:00 is
13:30Z / 20:00Z in November. The window of a slot closes `LATENESS` (3 hours) after its due instant."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from hio.contracts.canonical import sha256_hex
from hio.contracts.layout import ATTEMPTS_PREFIX
from hio.jobs import s1b1_capture
from hio.jobs.s1b1_capture import WEEKDAYS, LiveBuilders, check_completeness
from hio.marketdata.runrecord import Execution, RunRecord
from hio.reference.calendar import BusinessCalendar, CalendarCoverageError
from hio.sources.datasets import PUBLICATIONS
from hio.sources.schedule import (
    LATENESS,
    MISSED_HORIZON,
    SLOTS,
    expected_slots,
    load_attempt_records,
    missed_slots,
)
from hio.sources.transport import FixtureTransport, HttpResponse
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from tests.helpers import AllowAllGate
from tests.test_s1b1_capture import FILES, FX, HEADERS
from tests.test_t0010_azure_fakes import FakeContainer
from tests.test_t0010_capture_cli import ENV, calendar, urls

EXEC = Execution("github_actions", "1", "1", "capture", "a" * 40)
US = timedelta.resolution
RBA = ("rba.f1", "rba.expert_judgement")
NYFED = ("nyfed.sofr", "nyfed.sofr_index")


def at(
    month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0, micro: int = 0, year: int = 2026
):
    return datetime(year, month, day, hour, minute, second, micro, tzinfo=UTC)


def rits(holidays=(), coverage=(date(2026, 1, 1), date(2027, 12, 31))) -> BusinessCalendar:
    return BusinessCalendar(
        "rits",
        frozenset(holidays),
        coverage=coverage,
        citation="synthetic test calendar",
        as_of=date(2026, 10, 28),
        content_sha256="0" * 64,
    )


def calendars(**kw):
    return {"rits": rits(**kw), "weekdays": WEEKDAYS}


def rec(
    pid, name, due, *, outcome="verified_unchanged", delay=timedelta(minutes=1), took=timedelta(seconds=2)
):
    """One attempt record for a publication, slot and due instant."""
    started = due + delay
    failed = outcome == "failed"
    digest = None if failed else "a" * 64
    return RunRecord(
        source_id=pid,
        execution=EXEC,
        request={
            "method": "GET",
            "url": f"https://fixture.invalid/{pid}",
            "final_url": None,
            "user_agent": "t",
        },
        status=None if failed else 200,
        headers=(),
        response_sha256=digest,
        response_bytes=None if failed else 10,
        attempted_at=started,
        completed_at=started + took,
        outcome=outcome,
        receipt_id=digest,
        error_class="network" if failed else None,
        slot=name,
        slot_due_at=due,
        keys_checked=None if failed else (),
    )


def keys_of(pairs):
    return [(s.publication_id, s.name, d) for s, d in pairs]


def dues(pid, name, start, end, cals=None):
    return [
        d
        for s, d in expected_slots(start, end, cals or calendars())
        if (s.publication_id, s.name) == (pid, name)
    ]


# --- the reference window: now = Wed 4 Nov 2026 12:00Z ----------------------------------------------------

NOW = at(11, 4, 12)
IN_WINDOW = [  # slots whose window closed in (NOW - 24h, NOW]
    ("nyfed.sofr", "first", at(11, 3, 13, 30)),
    ("nyfed.sofr_index", "first", at(11, 3, 13, 30)),
    ("nyfed.sofr", "final", at(11, 3, 20)),
    ("nyfed.sofr_index", "final", at(11, 3, 20)),
    ("rba.expert_judgement", "first", at(11, 3, 22, 45)),
    ("rba.f1", "first", at(11, 3, 22, 45)),
    ("rba.expert_judgement", "final", at(11, 4, 5, 30)),
    ("rba.f1", "final", at(11, 4, 5, 30)),
]


def all_records(skip=lambda _pid, _name: False):
    return [rec(p, n, d) for p, n, d in IN_WINDOW if not skip(p, n)]


def test_the_reference_window_expects_each_publication_slot_once():
    assert sorted(
        keys_of(expected_slots(NOW - MISSED_HORIZON - LATENESS + US, NOW - LATENESS + US, calendars()))
    ) == (sorted(IN_WINDOW))
    assert missed_slots(NOW, calendars(), all_records()) == []


# --- which slots are missed ---------------------------------------------------------------------------


def test_one_publication_missing_while_the_others_write():
    records = all_records(lambda pid, _name: pid == "nyfed.sofr")
    assert keys_of(missed_slots(NOW, calendars(), records)) == [
        ("nyfed.sofr", "first", at(11, 3, 13, 30)),
        ("nyfed.sofr", "final", at(11, 3, 20)),
    ]


def test_with_nothing_attempted_every_expected_slot_is_missed():
    assert sorted(keys_of(missed_slots(NOW, calendars(), []))) == sorted(IN_WINDOW)


@pytest.mark.parametrize("name", ["first", "final"])
def test_first_and_final_are_judged_separately(name):
    records = all_records(lambda pid, n: (pid, n) == ("rba.f1", name))
    (missed,) = missed_slots(NOW, calendars(), records)
    assert (missed[0].publication_id, missed[0].name) == ("rba.f1", name)


@pytest.mark.parametrize("outcome", ["failed", "verified_unchanged", "verified_changed"])
def test_any_outcome_counts_as_attempted(outcome):
    """A failed attempt raised its own alarm when it ran; it is attempted, never captured."""
    records = [rec(p, n, d, outcome=outcome) for p, n, d in IN_WINDOW]
    assert missed_slots(NOW, calendars(), records) == []


def test_a_record_for_another_slot_due_instant_or_publication_does_not_match():
    pid, name, due = IN_WINDOW[0]  # nyfed.sofr first
    wrong = [
        rec(pid, "final", due),  # the right due instant, the other slot
        rec(pid, name, due - timedelta(days=1)),  # the right slot, the previous day's due instant
        rec(pid, name, due + timedelta(minutes=1)),  # an instant close to the due instant, not equal to it
        rec("nyfed.sofr_index", name, due),  # the right slot, another publication
    ]
    others = [rec(p, n, d) for p, n, d in IN_WINDOW[1:]]
    missed = keys_of(missed_slots(NOW, calendars(), [*wrong, *others]))
    assert (pid, name, due) in missed


def test_a_manual_record_without_a_slot_answers_for_nothing():
    manual = replace(rec("rba.f1", "first", at(11, 3, 22, 45)), slot=None, slot_due_at=None)
    records = [r for r in all_records() if (r.source_id, r.slot) != ("rba.f1", "first")] + [manual]
    assert keys_of(missed_slots(NOW, calendars(), records)) == [("rba.f1", "first", at(11, 3, 22, 45))]


def test_a_late_record_within_lateness_counts():
    records = [
        rec(p, n, d, delay=LATENESS - timedelta(seconds=1)) if p == "rba.f1" else rec(p, n, d)
        for p, n, d in IN_WINDOW
    ]
    assert missed_slots(NOW, calendars(), records) == []


# --- boundaries ---------------------------------------------------------------------------------------

NY_FINAL = ("nyfed.sofr", "final", at(11, 3, 20))  # window closes 23:00Z


def test_a_slot_is_missed_exactly_when_its_window_closes():
    close = NY_FINAL[2] + LATENESS
    assert NY_FINAL not in keys_of(missed_slots(close - US, calendars(), []))
    assert NY_FINAL in keys_of(missed_slots(close, calendars(), []))
    assert NY_FINAL in keys_of(missed_slots(close + timedelta(minutes=5), calendars(), []))


def test_a_slot_still_inside_its_window_is_not_missed():
    for minutes in (0, 1, 90, 179):
        assert NY_FINAL not in keys_of(
            missed_slots(NY_FINAL[2] + timedelta(minutes=minutes), calendars(), [])
        )


def test_the_horizon_boundary_is_exclusive_at_its_old_end():
    close = NY_FINAL[2] + LATENESS
    assert NY_FINAL in keys_of(missed_slots(close + MISSED_HORIZON - US, calendars(), []))
    assert NY_FINAL not in keys_of(missed_slots(close + MISSED_HORIZON, calendars(), []))


def test_the_horizon_is_a_parameter():
    close = NY_FINAL[2] + LATENESS
    assert NY_FINAL in keys_of(
        missed_slots(close + timedelta(hours=40), calendars(), [], horizon=timedelta(hours=48))
    )
    assert NY_FINAL not in keys_of(missed_slots(close + timedelta(hours=40), calendars(), []))


def test_a_horizon_walk_reports_each_slot_in_exactly_one_hourly_run():
    """Slide `now` hour by hour with nothing attempted: every business-day slot is reported at least once
    within the horizon, and once it has aged out of it, never again."""
    seen = {}
    start = at(11, 2)
    for hour in range(0, 24 * 6):
        now = start + timedelta(hours=hour)
        for key in keys_of(missed_slots(now, calendars(), [])):
            seen.setdefault(key, []).append(now)
    for key, runs in seen.items():
        close = key[2] + LATENESS
        assert min(runs) - close < timedelta(hours=1)  # first reported within an hour of closing
        assert max(runs) - close <= MISSED_HORIZON  # never reported beyond the horizon
    assert ("rba.f1", "first", at(11, 2, 22, 45)) in seen  # Tuesday's Sydney first slot


# --- no-due runs, weekends -----------------------------------------------------------------------------


def test_a_weekend_run_expects_nothing_so_the_silence_is_not_a_miss():
    assert missed_slots(at(11, 8, 12), calendars(), []) == []  # Sunday 12:00Z: Friday's slots aged out
    assert missed_slots(
        at(11, 7, 22, 59), calendars(), []
    )  # Saturday 22:59Z: Friday's NY final is still in range
    assert missed_slots(at(11, 7, 23), calendars(), []) == []  # 23:00Z: its window closed a full horizon ago


def test_a_run_after_the_weekend_judges_only_business_days():
    # Monday 9 Nov 14:00Z: back to Sunday 14:00Z. Sydney Monday's slots (first Sun 22:45Z, final Mon 05:30Z)
    # have closed; New York Monday's first (13:30Z) is still inside its window.
    got = keys_of(missed_slots(at(11, 9, 14), calendars(), []))
    assert sorted(got) == [
        ("rba.expert_judgement", "final", at(11, 9, 5, 30)),
        ("rba.expert_judgement", "first", at(11, 8, 22, 45)),
        ("rba.f1", "final", at(11, 9, 5, 30)),
        ("rba.f1", "first", at(11, 8, 22, 45)),
    ]  # nothing from Saturday or Sunday local days, nor Friday


# --- calendars: DST, date crossings, holidays, weekdays, expiry -----------------------------------------


def test_sydney_enters_daylight_time_on_4_october_2026_new_york_unchanged():
    start, end = at(10, 1), at(10, 7)
    assert dues("rba.f1", "first", start, end) == [
        at(10, 1, 23, 45),  # Fri 2 Oct, AEST (UTC+10)
        at(10, 4, 22, 45),  # Mon 5 Oct, AEDT (UTC+11)
        at(10, 5, 22, 45),
        at(10, 6, 22, 45),
    ]
    assert dues("nyfed.sofr", "first", start, end) == [
        at(10, 1, 12, 30),
        at(10, 2, 12, 30),
        at(10, 5, 12, 30),
        at(10, 6, 12, 30),
    ]


def test_new_york_leaves_daylight_time_on_1_november_2026_sydney_unchanged():
    start, end = at(10, 29), at(11, 4)
    assert dues("nyfed.sofr", "first", start, end) == [
        at(10, 29, 12, 30),  # Thu, EDT (UTC-4)
        at(10, 30, 12, 30),
        at(11, 2, 13, 30),  # Mon 2 Nov, EST (UTC-5)
        at(11, 3, 13, 30),
    ]
    assert dues("nyfed.sofr", "final", start, end) == [
        at(10, 29, 19),
        at(10, 30, 19),
        at(11, 2, 20),
        at(11, 3, 20),
    ]
    assert dues("rba.f1", "first", start, end) == [
        at(10, 29, 22, 45),
        at(11, 1, 22, 45),
        at(11, 2, 22, 45),
        at(11, 3, 22, 45),
    ]


def test_new_york_enters_daylight_time_on_14_march_2027_sydney_unchanged():
    start, end = at(3, 11, year=2027), at(3, 17, year=2027)
    assert dues("nyfed.sofr", "first", start, end) == [
        at(3, 11, 13, 30, year=2027),  # Thu 11 Mar, EST
        at(3, 12, 13, 30, year=2027),
        at(3, 15, 12, 30, year=2027),  # Mon 15 Mar, EDT
        at(3, 16, 12, 30, year=2027),
    ]
    assert dues("rba.f1", "first", start, end) == [
        at(3, 11, 22, 45, year=2027),
        at(3, 14, 22, 45, year=2027),
        at(3, 15, 22, 45, year=2027),
        at(3, 16, 22, 45, year=2027),
    ]


def test_sydney_leaves_daylight_time_on_4_april_2027_new_york_unchanged():
    start, end = at(4, 1, year=2027), at(4, 7, year=2027)
    assert dues("rba.f1", "first", start, end) == [
        at(4, 1, 22, 45, year=2027),  # Fri 2 Apr, AEDT
        at(4, 4, 23, 45, year=2027),  # Mon 5 Apr, AEST
        at(4, 5, 23, 45, year=2027),
        at(4, 6, 23, 45, year=2027),
    ]
    assert dues("rba.f1", "final", start, end) == [
        at(4, 1, 5, 30, year=2027),
        at(4, 2, 5, 30, year=2027),
        at(4, 5, 6, 30, year=2027),  # 16:30 AEST is 06:30Z
        at(4, 6, 6, 30, year=2027),
    ]
    assert dues("nyfed.sofr", "first", start, end) == [
        at(4, 1, 12, 30, year=2027),
        at(4, 2, 12, 30, year=2027),  # Good Friday: no SIFMA calendar, a weekday, so expected
        at(4, 5, 12, 30, year=2027),
        at(4, 6, 12, 30, year=2027),
    ]


def test_missed_uses_the_transition_offset_for_the_window_close():
    """The first Monday after New York leaves daylight time: 08:30 EST is 13:30Z, closing 16:30Z. An
    implementation that kept the EDT offset would close at 15:30Z."""
    first = ("nyfed.sofr", "first", at(11, 2, 13, 30))
    assert first not in keys_of(missed_slots(at(11, 2, 15, 30), calendars(), []))
    assert first not in keys_of(missed_slots(at(11, 2, 16, 29, 59, 999999), calendars(), []))
    assert first in keys_of(missed_slots(at(11, 2, 16, 30), calendars(), []))


def test_missed_uses_the_transition_offset_for_sydney_too():
    """The first Monday after Sydney leaves daylight time (5 Apr 2027): 09:45 AEST is 23:45Z the day
    before."""
    first = ("rba.f1", "first", at(4, 4, 23, 45, year=2027))  # closes 02:45Z Monday
    assert first not in keys_of(missed_slots(at(4, 5, 2, 44, 59, 999999, year=2027), calendars(), []))
    assert first in keys_of(missed_slots(at(4, 5, 2, 45, year=2027), calendars(), []))


def test_a_utc_date_is_not_a_local_date():
    """Sunday 1 Nov UTC holds Monday 2 Nov in Sydney (the first slots, 22:45Z) and Sunday in New York."""
    got = keys_of(expected_slots(at(11, 1), at(11, 2), calendars()))
    assert sorted(got) == [
        ("rba.expert_judgement", "first", at(11, 1, 22, 45)),
        ("rba.f1", "first", at(11, 1, 22, 45)),
    ]


def test_a_utc_friday_holds_sydney_finals_and_new_york_both_but_not_sydney_saturday():
    got = keys_of(expected_slots(at(11, 6), at(11, 7), calendars()))
    assert sorted(got) == sorted(
        [
            ("nyfed.sofr", "first", at(11, 6, 13, 30)),
            ("nyfed.sofr", "final", at(11, 6, 20)),
            ("nyfed.sofr_index", "first", at(11, 6, 13, 30)),
            ("nyfed.sofr_index", "final", at(11, 6, 20)),
            ("rba.expert_judgement", "final", at(11, 6, 5, 30)),
            ("rba.f1", "final", at(11, 6, 5, 30)),
        ]
    )  # Sydney's Saturday 7 Nov first slot (22:45Z on the 6th) is not a business day


def test_a_rits_holiday_removes_the_rba_slots_only():
    holiday = rits(holidays=[date(2026, 11, 4)])
    cals = {"rits": holiday, "weekdays": WEEKDAYS}
    got = keys_of(expected_slots(at(11, 3), at(11, 5), cals))
    assert ("rba.f1", "final", at(11, 3, 5, 30)) in got  # Tuesday 3 Nov (local)
    assert ("rba.f1", "first", at(11, 4, 22, 45)) in got  # Thursday 5 Nov (local)
    assert not [k for k in got if k[0].startswith("rba") and k[2] in (at(11, 3, 22, 45), at(11, 4, 5, 30))]
    assert ("nyfed.sofr", "first", at(11, 4, 13, 30)) in got
    # and a missed check does not report the holiday's slots
    missed = keys_of(missed_slots(at(11, 4, 12), cals, []))
    assert not [k for k in missed if k[0].startswith("rba")]
    assert ("nyfed.sofr", "final", at(11, 3, 20)) in missed


def test_new_york_slots_run_on_weekdays_only_and_do_not_skip_us_holidays():
    got = keys_of(expected_slots(at(11, 6), at(11, 9), calendars()))  # Friday through Sunday UTC
    assert {k[2].date() for k in got if k[0] == "nyfed.sofr"} == {date(2026, 11, 6)}
    thanksgiving = keys_of(expected_slots(at(11, 26), at(11, 27), calendars()))
    assert ("nyfed.sofr", "first", at(11, 26, 13, 30)) in thanksgiving  # a check on a US holiday is harmless


def test_a_calendar_that_ends_before_the_horizon_fails_visibly():
    short = calendars(coverage=(date(2026, 1, 1), date(2026, 11, 3)))
    with pytest.raises(CalendarCoverageError):
        missed_slots(NOW, short, [])  # the window needs Wednesday 4 November in Sydney
    with pytest.raises(CalendarCoverageError):
        expected_slots(at(11, 2), at(11, 6), short)


def test_a_calendar_that_starts_after_the_horizon_fails_visibly():
    late = calendars(coverage=(date(2026, 11, 6), date(2027, 12, 31)))
    with pytest.raises(CalendarCoverageError):
        missed_slots(at(11, 5, 12), late, [])  # the window needs Thursday 5 November in Sydney


def test_expected_slots_asks_the_calendar_only_about_days_the_range_needs():
    snug = calendars(coverage=(date(2026, 11, 3), date(2026, 11, 3)))
    assert dues("rba.f1", "final", at(11, 3, 5), at(11, 3, 6), snug) == [at(11, 3, 5, 30)]


def test_an_empty_or_inverted_range_expects_nothing():
    assert expected_slots(at(11, 3), at(11, 3), calendars()) == []
    assert expected_slots(at(11, 4), at(11, 3), calendars()) == []


def test_a_full_business_day_expects_every_slot_once_per_publication():
    """Over any 24 hours of a business-day stretch each of the eight table slots falls exactly once."""
    got = expected_slots(at(11, 3), at(11, 4), calendars())
    assert len(got) == len(SLOTS)
    assert {(s.publication_id, s.name) for s, _ in got} == {(s.publication_id, s.name) for s in SLOTS}


# --- reading the attempt records -----------------------------------------------------------------------


@pytest.fixture
def store():
    return BlobObjectStore(FakeBlobBackend())


def put(store, *records):
    for r in records:
        store.put(r.key, r.canonical())


def test_attempts_are_listed_once_whatever_the_number_of_slots():
    backend = FakeBlobBackend()
    listed = []
    real = backend.keys
    backend.keys = lambda prefix: (listed.append(prefix), real(prefix))[1]
    store = BlobObjectStore(backend)
    put(store, *all_records(lambda pid, _n: pid.startswith("nyfed")))
    listed.clear()
    assert check_completeness(NOW, store, rits()) is False
    assert listed == [ATTEMPTS_PREFIX]


def test_records_started_before_the_horizon_are_not_read(store):
    old = rec("rba.f1", "first", at(10, 1, 22, 45))
    put(store, old)
    assert load_attempt_records(store, NOW - MISSED_HORIZON - LATENESS) == []
    assert [r.key for r in load_attempt_records(store, at(10, 1))] == [old.key]


def test_a_record_that_fails_verification_raises_or_is_collected(store):
    good = rec("rba.f1", "first", at(11, 3, 22, 45))
    put(store, good)
    bad_hash = f"{ATTEMPTS_PREFIX}rba.f1/20261103-230000000000-{'b' * 64}.json"
    store.backend.create(bad_hash, b"{}")  # the name promises another content hash
    not_json = b"not json"
    bad_json = f"{ATTEMPTS_PREFIX}rba.f1/20261103-230100000000-{sha256_hex(not_json)}.json"
    store.backend.create(bad_json, not_json)  # the hash is right; the content is not a record
    strange = f"{ATTEMPTS_PREFIX}rba.f1/notes.txt"
    store.backend.create(strange, b"x")
    since = at(11, 3)
    with pytest.raises(Exception):  # noqa: B017 - which error depends on the corruption; each must raise
        load_attempt_records(store, since)
    unreadable: list[str] = []
    assert [r.key for r in load_attempt_records(store, since, unreadable)] == [good.key]
    assert sorted(unreadable) == sorted([bad_hash, bad_json, strange])


def test_an_unrecognised_key_raises_its_own_error(store):
    store.backend.create(f"{ATTEMPTS_PREFIX}rba.f1/notes.txt", b"x")
    with pytest.raises(ValueError, match="not an attempt-record key"):
        load_attempt_records(store, at(11, 3))


def test_a_corrupt_record_fails_the_check_visibly(store, capsys):
    put(store, *all_records())
    store.backend.create(f"{ATTEMPTS_PREFIX}rba.f1/20261104-100000000000-{'c' * 64}.json", b"{}")
    assert check_completeness(NOW, store, rits()) is False
    captured = capsys.readouterr()
    assert (
        "completeness check failed" in captured.err and captured.out == ""
    )  # no verdict from unread evidence


def test_the_check_prints_each_missed_slot_and_returns_false(store, capsys):
    put(store, *all_records(lambda pid, n: (pid, n) == ("nyfed.sofr", "final")))
    assert check_completeness(NOW, store, rits()) is False
    assert capsys.readouterr().out.splitlines() == [
        "missed nyfed.sofr final 2026-11-03T20:00:00+00:00",
    ]


def test_a_complete_record_set_passes_silently(store, capsys):
    put(store, *all_records())
    assert check_completeness(NOW, store, rits()) is True
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")


# --- the capture job -----------------------------------------------------------------------------------


def clock_from(start):
    t = [start]

    def clock():
        t[0] += timedelta(seconds=1)
        return t[0]

    return clock


def live(tmp_path, monkeypatch, at_text, container, *, cal=None, transport=None, clock_start=None):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    builders = LiveBuilders(
        gate=AllowAllGate,
        transport=lambda: transport or FixtureTransport({}),
        credential=lambda *_: object(),
        container=lambda *_: container,
        urls=urls,
        clock=clock_from(clock_start or datetime.fromisoformat(at_text) + timedelta(minutes=5)),
    )
    argv = ["--rits-calendar", cal or calendar(tmp_path), "--at", at_text]
    return s1b1_capture.main(argv, environ=ENV, builders=builders)


def seed(container, *records):
    for r in records:
        container.overwrite_out_of_band(r.key, r.canonical())


def fixture_script():
    return {
        f"https://fixture.invalid/{pid}": [
            HttpResponse(200, HEADERS, (FX / FILES[pid]).read_bytes(), f"https://fixture.invalid/{pid}")
        ]
        for pid in PUBLICATIONS
    }


def test_a_run_with_no_due_slot_still_checks_and_fails_on_a_missed_slot(tmp_path, monkeypatch, capsys):
    """Saturday 7 Nov 12:00Z: nothing is due, but Friday's New York slots closed with no attempt record."""
    container = FakeContainer()
    rc = live(tmp_path, monkeypatch, "2026-11-07T12:00:00Z", container)
    out = capsys.readouterr().out
    assert rc == 1
    assert "due " not in out and "ran " not in out
    assert out.splitlines() == [
        "missed nyfed.sofr first 2026-11-06T13:30:00+00:00",
        "missed nyfed.sofr_index first 2026-11-06T13:30:00+00:00",
        "missed nyfed.sofr final 2026-11-06T20:00:00+00:00",
        "missed nyfed.sofr_index final 2026-11-06T20:00:00+00:00",
    ]
    assert not [c for c in container.calls if c[0] == "upload_blob"]  # the check writes nothing


def test_a_run_with_no_due_slot_and_every_slot_attempted_exits_zero(tmp_path, monkeypatch, capsys):
    container = FakeContainer()
    seed(
        container,
        *[
            rec(p, n, d, outcome="failed" if n == "first" else "verified_unchanged")
            for p, n, d in [
                ("nyfed.sofr", "first", at(11, 6, 13, 30)),
                ("nyfed.sofr_index", "first", at(11, 6, 13, 30)),
                ("nyfed.sofr", "final", at(11, 6, 20)),
                ("nyfed.sofr_index", "final", at(11, 6, 20)),
            ]
        ],
    )
    assert live(tmp_path, monkeypatch, "2026-11-07T12:00:00Z", container) == 0
    assert capsys.readouterr().out == ""


def test_a_weekend_run_is_not_a_miss(tmp_path, monkeypatch, capsys):
    assert live(tmp_path, monkeypatch, "2026-11-08T12:00:00Z", FakeContainer()) == 0
    assert capsys.readouterr().out == ""


def test_the_check_runs_after_capture_and_both_outcomes_show(tmp_path, monkeypatch, capsys):
    """Wed 4 Nov 22:45Z: the Sydney firsts are due and captured, and the earlier gaps are reported."""
    container = FakeContainer()
    now_text = "2026-11-03T22:45:00Z"
    rc = live(tmp_path, monkeypatch, now_text, container, transport=FixtureTransport(fixture_script()))
    out = capsys.readouterr().out.splitlines()
    assert rc == 1
    ran = {line for line in out if line.startswith("ran ")}
    assert {"ran rba.f1 first verified_changed", "ran rba.expert_judgement first verified_changed"} <= ran
    assert out.index(next(line for line in out if line.startswith("ran "))) < out.index(
        next(line for line in out if line.startswith("missed "))
    )  # capture first, check after
    assert "missed nyfed.sofr first 2026-11-03T13:30:00+00:00" in out
    assert "missed rba.f1 final 2026-11-03T05:30:00+00:00" in out
    assert not [
        line for line in out if "2026-11-03T22:45:00" in line and line.startswith("missed")
    ]  # due now


def test_a_failed_capture_exit_code_is_unchanged_and_a_failed_record_is_not_a_miss(
    tmp_path, monkeypatch, capsys
):
    container = FakeContainer()
    script = {
        f"https://fixture.invalid/{pid}": [HttpResponse(503, HEADERS, b"", f"https://fixture.invalid/{pid}")]
        for pid in PUBLICATIONS
    }
    rc = live(tmp_path, monkeypatch, "2026-11-01T22:45:00Z", container, transport=FixtureTransport(script))
    out = capsys.readouterr().out
    assert rc == 1
    assert "ran rba.f1 first failed" in out and "missed" not in out


def test_the_attempts_prefix_is_listed_once_by_the_check_in_a_live_run(tmp_path, monkeypatch):
    container = FakeContainer()
    live(
        tmp_path, monkeypatch, "2026-11-03T22:45:00Z", container, transport=FixtureTransport(fixture_script())
    )
    whole = [c for c in container.calls if c[0] == "list_blobs" and c[1] == ATTEMPTS_PREFIX]
    assert len(whole) == 1


def test_an_expired_calendar_fails_the_run_after_capture(tmp_path, monkeypatch, capsys):
    """The calendar covers the run's own day but not the 24 hours before it: captured, then exit 1."""
    cal = calendar(tmp_path, "short.yaml", start="2026-11-02", end="2026-12-31")
    container = FakeContainer()
    rc = live(
        tmp_path,
        monkeypatch,
        "2026-11-01T22:45:00Z",
        container,
        cal=cal,
        transport=FixtureTransport(fixture_script()),
        clock_start=datetime(2026, 11, 1, 22, 50, tzinfo=UTC),
    )
    captured = capsys.readouterr()
    assert rc == 1
    assert "ran rba.f1 first" in captured.out  # capture was not prevented
    assert "completeness check failed" in captured.err and "CalendarCoverageError" in captured.err
    assert "missed" not in captured.out


def test_a_corrupt_record_in_the_horizon_fails_the_live_run(tmp_path, monkeypatch, capsys):
    container = FakeContainer()
    seed(container, *all_records())
    container.overwrite_out_of_band(f"{ATTEMPTS_PREFIX}rba.f1/20261104-100000000000-{'d' * 64}.json", b"{}")
    assert live(tmp_path, monkeypatch, "2026-11-04T12:00:00Z", container) == 1
    err = capsys.readouterr().err
    assert "completeness check failed" in err


def test_a_provider_error_names_only_its_type(capsys):
    class Boom(FakeBlobBackend):
        def keys(self, _prefix):
            raise ConnectionError("https://secret.example/account?sig=SECRET")

    assert check_completeness(NOW, BlobObjectStore(Boom()), rits()) is False
    err = capsys.readouterr().err
    assert "ConnectionError" in err and "SECRET" not in err


def test_dry_run_is_unchanged_by_the_check(tmp_path, capsys):
    """A dry run on a day with a gap prints only the due slots, builds nothing and exits 0."""

    class Exploding:
        def __call__(self, *_a, **_k):
            raise AssertionError("a dry run built something")

    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom, urls=boom)
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", "2026-11-07T12:00:00Z", "--dry-run"],
        environ={},
        builders=builders,
    )
    assert rc == 0 and capsys.readouterr().out == ""


def test_the_live_refusal_still_exits_two_before_any_check(tmp_path, capsys):
    class Exploding:
        def __call__(self, *_a, **_k):
            raise AssertionError("built before the live path was authorised")

    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom, urls=boom)
    assert s1b1_capture.LIVE_AUTHORISATION is None
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", "2026-11-07T12:00:00Z"], environ={}, builders=builders
    )
    captured = capsys.readouterr()
    assert rc == 2 and "missed" not in captured.out and "completeness" not in captured.err


def test_a_store_of_the_local_kind_is_read_the_same_way(tmp_path):
    """`check_completeness` is duck-typed over the two store classes."""
    from hio.storage.objectstore import LocalObjectStore

    local = LocalObjectStore(tmp_path / "s")
    for r in all_records():
        local.put(r.key, r.canonical())
    assert check_completeness(NOW, local, rits()) is True
