"""T-0010 W-4: the completion checks C1-C7 and finality (HIO-ADR-0012 §4.3.3, §4.3.4) on synthetic
inputs. One test per check showing it catches its violation, the ADR's three worked cases, and a passing
positive case. Instants are UTC; the window close W_doc is 05:00Z on 2026-10-27 (16:00 Sydney). No
network, no real data: bodies are synthetic CSV, the store is the in-memory blob fake or a temp dir.
These verdicts label nothing final (T-0010 A-9)."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from email.utils import format_datetime

import pytest

from hio.contracts.canonical import canonical_json, decimal_str, sha256_hex
from hio.contracts.layout import capture_record_key, receipt_key
from hio.contracts.observation import Receipt, Vintage
from hio.contracts.temporal import KnowableBasis, QualityStatus
from hio.marketdata.finality import (
    CHECK_NAMES,
    FinalityPolicy,
    evaluate_records,
    release_finality,
    vintage_finality,
)
from hio.marketdata.runrecord import Execution, RunRecord, value_digest
from hio.storage.blobstore import BlobObjectStore
from hio.storage.fakeblob import FakeBlobBackend
from hio.storage.objectstore import LocalObjectStore

SRC = "synthetic.rate"
SID = "synthetic.rate.aonia"
VALID = date(2026, 10, 26)
SHA = "0123456789abcdef0123456789abcdef01234567"
W = datetime(2026, 10, 27, 5, 0, tzinfo=UTC)  # W_doc(k): 16:00 Sydney


def T(h: int, m: int, s: int = 0, day: int = 27) -> datetime:
    return datetime(2026, 10, day, h, m, s, tzinfo=UTC)


def parse_keys(body: bytes) -> list[tuple[str, str, str]]:
    """The synthetic series schema: `series_id,valid_time,value` rows."""
    rows = [line.split(",") for line in body.decode().splitlines()[1:]]
    return sorted((sid, vt, value_digest(decimal_str(Decimal(v)))) for sid, vt, v in rows)


POLICY = FinalityPolicy("github_actions", {"commit": SHA, "lock_sha256": "0" * 64}, parse_keys)

REPO = "synthetic-owner/hio"
CAPTURE_WORKFLOW_REF = f"{REPO}/.github/workflows/s1b1-capture.yml@refs/heads/main"


def ci(run_id: str | None = "1001", attempt: str | None = "1", job: str | None = "capture", sha=SHA, **over):
    """An execution of the capture workflow on main, started by a schedule; `over` replaces any field."""
    fields = {
        "workflow_ref": CAPTURE_WORKFLOW_REF,
        "ref": "refs/heads/main",
        "event": "schedule",
    } | over
    return Execution("github_actions", run_id, attempt, job, sha, **fields)


def body_of(value: str) -> bytes:
    return f"series_id,valid_time,value\n{SID},{VALID.isoformat()},{value}\n".encode()


def vintage(seq: int, value: str, captured_at: datetime) -> Vintage:
    return Vintage(
        SID, VALID, seq, Decimal(value), sha256_hex(body_of(value)), captured_at, captured_at,
        KnowableBasis.CAPTURED_ON_SCHEDULE, "Australia/Sydney", QualityStatus.VALID,
    )  # fmt: skip


class Env:
    """A store plus the writes a capture run makes. `now` is the provider's clock for blob stores."""

    def __init__(self, store, backend=None) -> None:
        self.store, self.backend, self.now = store, backend, T(0, 0)
        self.runs = 0

    def capture(self, body: bytes, captured_at: datetime) -> None:
        self.now = captured_at
        rid = sha256_hex(body)
        self.store.put_if_absent_check(receipt_key(SRC, captured_at, rid), body) or self.store.put(
            receipt_key(SRC, captured_at, rid), body
        )
        receipt = Receipt(rid, SRC, captured_at, {"fixture": "synthetic"}, len(body))
        self.store.put(capture_record_key(SRC, captured_at, rid), canonical_json(receipt.as_record()))

    def attempt(
        self,
        body: bytes,
        attempted: datetime,
        completed: datetime,
        written: datetime,
        *,
        outcome: str = "verified_changed",
        date_header: datetime | str | None = "auto",
        headers: list[list[str]] | None = None,
        execution: Execution | None = None,
        keys: list[tuple[str, str, str]] | None = None,
        response_bytes: int | None = None,
    ) -> RunRecord:
        if outcome == "verified_changed":
            self.capture(body, completed)
        if headers is None:
            when = attempted + timedelta(seconds=5) if date_header == "auto" else date_header
            shown = format_datetime(when, usegmt=True) if isinstance(when, datetime) else when
            headers = [["Content-Type", "text/csv"], *([["Date", shown]] if shown is not None else [])]
        self.runs += 1
        rid = sha256_hex(body)
        record = RunRecord(
            source_id=SRC,
            execution=execution or ci(str(1000 + self.runs)),
            request={"method": "GET", "url": "https://synthetic.invalid/rate.csv"},
            status=200,
            headers=headers,
            response_sha256=rid,
            response_bytes=len(body) if response_bytes is None else response_bytes,
            attempted_at=attempted,
            completed_at=completed,
            outcome=outcome,
            receipt_id=rid,
            keys_checked=keys if keys is not None else parse_keys(body),
        )
        self.now = written
        self.store.put(record.key, record.canonical())
        return record

    def good(self, value: str = "3.60", base: datetime | None = None) -> tuple[RunRecord, Vintage]:
        """A verified_changed run after the window that passes every check, and its vintage."""
        base = base or T(5, 30)
        completed = base + timedelta(seconds=8)
        rec = self.attempt(body_of(value), base, completed, base + timedelta(seconds=10))
        return rec, vintage(1, value, completed)


@pytest.fixture
def env() -> Env:
    backend = FakeBlobBackend(immutable=True)
    e = Env(BlobObjectStore(backend), backend)
    backend._clock = lambda: e.now
    return e


def codes(ev, name: str) -> set[str]:
    return {r.code for r in ev.check(name).reasons}


def one(env: Env, v: list[Vintage], w_doc: datetime | None = W):
    (ev,) = evaluate_records(env.store, SRC, POLICY, w_doc=w_doc, vintages=v)
    return ev


def verdict(env: Env, v: Vintage, held: list[Vintage], cutoff: datetime, w_doc: datetime | None = W):
    return vintage_finality(env.store, SRC, v, held, cutoff, w_doc=w_doc, policy=POLICY)


# --- positive ---------------------------------------------------------------------------------------------


def test_a_clean_post_window_check_passes_c1_to_c7_and_the_vintage_is_final(env):
    rec, v1 = env.good()
    ev = one(env, [v1])
    assert ev.passed and ev.failed == () and ev.category is None
    assert tuple(c.name for c in ev.checks) == CHECK_NAMES
    assert ev.write_time == T(5, 30, 10) and ev.key == rec.key
    verdict_ = verdict(env, v1, [v1], T(5, 31))
    assert verdict_.final and verdict_.category is None and verdict_.evidence == (rec.key,)
    assert verdict_ == verdict(env, v1, [v1], T(5, 31))  # deterministic


def test_a_verified_unchanged_check_with_a_fresh_envelope_is_final(env):
    held = body_of("3.60")
    env.capture(held, T(22, 30, 8, day=26))
    v1 = vintage(1, "3.60", T(22, 30, 8, day=26))
    unchanged = env.attempt(held, T(5, 30), T(5, 30, 8), T(5, 30, 10), outcome="verified_unchanged")
    ev = one(env, [v1])
    assert ev.passed
    assert verdict(env, v1, [v1], T(5, 45)).evidence == (unchanged.key,)


def test_the_cutoff_is_inclusive_of_the_write_time(env):
    _, v1 = env.good()
    assert verdict(env, v1, [v1], T(5, 30, 10)).final
    late = verdict(env, v1, [v1], T(5, 30, 9))
    assert not late.final and late.category == "delayed"


# --- one test per check ---------------------------------------------------------------------------------


def test_c1_a_record_whose_key_hash_does_not_match_its_content_is_not_evidence(env):
    rec, v1 = env.good()
    forged_key = rec.key.replace(rec.record_sha256, "0" * 64)
    env2 = Env(BlobObjectStore(FakeBlobBackend()))
    env2.store.put(forged_key, rec.canonical())
    ev = one(env2, [v1])
    assert ev.record is None and codes(ev, "C1") == {"record_unreadable"}
    assert ev.category == "inconsistent" and not ev.passed


def test_c1_a_rewritten_record_is_refused_even_if_the_new_bytes_are_well_formed():
    backend = FakeBlobBackend(immutable=False)
    env = Env(BlobObjectStore(backend), backend)
    rec, v1 = env.good()
    backend.overwrite(rec.key, rec.canonical())  # a second version of the same key
    ev = one(env, [v1])
    assert ev.record is None and "record_unreadable" in codes(ev, "C1")


def test_c1_a_record_missing_a_required_field_is_not_evidence(env):
    rec, v1 = env.good()
    cut = {k: v for k, v in json.loads(rec.canonical()).items() if k != "execution"}
    data = canonical_json(cut)
    env2 = Env(BlobObjectStore(FakeBlobBackend()))
    env2.store.put(rec.key.replace(rec.record_sha256, sha256_hex(data)), data)
    ev = one(env2, [v1])
    assert ev.record is None and ev.category == "missing" and ev.failed == CHECK_NAMES


def test_c2_a_response_with_no_held_capture_is_not_bound(env):
    rec, v1 = env.good()
    env2 = Env(BlobObjectStore(FakeBlobBackend()))
    env2.store.put(rec.key, rec.canonical())  # the attempt record only: no capture, no bytes
    assert "no_capture_record" in codes(one(env2, [v1]), "C2")


def test_c2_a_recorded_length_that_differs_from_the_stored_bytes_fails(env):
    body = body_of("3.60")
    env.attempt(body, T(5, 30), T(5, 30, 8), T(5, 30, 10), response_bytes=len(body) + 1)
    assert codes(one(env, [vintage(1, "3.60", T(5, 30, 8))]), "C2") == {"length_mismatch"}


def test_c2_receipt_bytes_that_no_longer_hash_to_the_receipt_id_fail():
    backend = FakeBlobBackend(immutable=False)
    env = Env(BlobObjectStore(backend), backend)
    rec, v1 = env.good()
    backend.overwrite(receipt_key(SRC, rec.completed_at, rec.receipt_id), b"tampered")
    assert codes(one(env, [v1]), "C2") == {"receipt_bytes"}


def test_c3_a_digest_the_stored_bytes_do_not_reproduce_fails(env):
    wrong = [(SID, VALID.isoformat(), value_digest("3.61"))]
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), keys=wrong)
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert (
        codes(ev, "C3") == {"digest_not_reproduced", "held_value_differs"} and ev.category == "inconsistent"
    )


def test_c3_a_key_that_the_stored_bytes_do_not_contain_is_a_failed_check(env):
    absent = [(SID, "2026-10-25", value_digest("3.60"))]
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), keys=absent)
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert "key_not_in_body" in codes(ev, "C3") and ev.category == "failed"


def test_c3_the_held_vintage_must_carry_the_checked_value(env):
    rec, _ = env.good("3.60")
    assert codes(one(env, [vintage(1, "3.99", rec.completed_at)]), "C3") == {"held_value_differs"}
    assert codes(one(env, []), "C3") == {"no_held_vintage"}


def test_c3_a_body_the_series_schema_rejects_is_a_failed_check(env):
    env.good()

    def refuses(_: bytes):
        raise ValueError("schema")

    policy = FinalityPolicy("github_actions", SHA, refuses)
    (ev,) = evaluate_records(env.store, SRC, policy, w_doc=W, vintages=[vintage(1, "3.60", T(5, 30, 8))])
    assert codes(ev, "C3") == {"parse_failed"} and ev.category == "failed"


@pytest.mark.parametrize(
    ("headers", "code", "category"),
    [
        ([["Content-Type", "text/csv"]], "date_missing", "missing"),
        ([["Date", "yesterday-ish"]], "date_unparseable", "missing"),
        ([["Date", "Tue, 27 Oct 2026 05:30:05"]], "date_without_zone", "missing"),
        (
            [["Date", "Tue, 27 Oct 2026 05:30:05 GMT"], ["date", "Tue, 27 Oct 2026 05:30:06 GMT"]],
            "date_repeated",
            "inconsistent",
        ),
    ],
)
def test_c4_a_missing_or_unreadable_date_header_fails(env, headers, code, category):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), headers=headers)
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert codes(ev, "C4") == {code} and ev.check("C4").category == category and ev.failed == ("C4",)


@pytest.mark.parametrize(
    ("date_header", "code"),
    [
        (T(4, 58), "date_precedes_window"),
        (T(5, 10), "date_too_old"),  # after W_doc, but completed 20 min after generation (> δ)
        (T(5, 33), "date_after_completion"),  # the publisher's clock ahead of ours by more than ε
    ],
)
def test_c4_a_date_outside_the_window_or_the_skew_bounds_fails(env, date_header, code):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), date_header=date_header)
    assert code in codes(one(env, [vintage(1, "3.60", T(5, 30, 8))]), "C4")


@pytest.mark.parametrize("date_header", [T(5, 20, 8), T(5, 32, 8)])  # exactly δ before, exactly ε after
def test_c4_the_skew_bounds_are_inclusive(env, date_header):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), date_header=date_header)
    assert one(env, [vintage(1, "3.60", T(5, 30, 8))]).check("C4").passed


def test_c5_a_check_attempted_before_the_window_closed_fails(env):
    env.attempt(body_of("3.60"), T(4, 59, 50), T(5, 0, 5), T(5, 0, 7), date_header=T(5, 0, 0))
    ev = one(env, [vintage(1, "3.60", T(5, 0, 5))])
    assert (
        codes(ev, "C5") == {"attempted_before_window"} and ev.failed == ("C5",) and ev.category == "delayed"
    )


@pytest.mark.parametrize(
    ("written", "code"),
    [(T(5, 41), "written_too_late"), (T(5, 29, 59), "written_before_completion")],
)
def test_c5_a_write_time_outside_completed_at_plus_delta_fails(env, written, code):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), written)
    assert codes(one(env, [vintage(1, "3.60", T(5, 30, 8))]), "C5") == {code}


def test_c5_a_store_that_cannot_supply_a_provider_write_time_fails(tmp_path):
    local = Env(LocalObjectStore(tmp_path / "store"))
    _, v1 = local.good()
    ev = one(local, [v1])
    assert codes(ev, "C5") == {"no_provider_write_time"} and ev.write_time is None
    assert ev.failed == ("C5",) and ev.category == "unverified"
    refused = verdict(local, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "unverified"


def test_c5_a_missing_w_doc_fails_c4_and_c5(env):
    _, v1 = env.good()
    assert one(env, [v1], w_doc=None).failed == ("C4", "C5")
    assert verdict(env, v1, [v1], T(6, 0), w_doc=None).category == "missing"


@pytest.mark.parametrize(
    ("execution", "code", "category"),
    [
        (Execution("other"), "platform_other", "unverified"),
        (replace(ci(), platform="gitlab"), "platform_mismatch", "inconsistent"),
        (ci(sha="f" * 40), "sha_not_code_ref", "inconsistent"),
        (ci(sha=None), "sha_missing", "missing"),
        (ci("10x1"), "run_id_malformed", "inconsistent"),
        (ci(attempt="0"), "run_attempt_malformed", "inconsistent"),
        (ci(attempt=None), "run_attempt_missing", "missing"),
        (ci(job=None), "job_missing", "missing"),
    ],
)
def test_c6_an_execution_that_is_not_bound_to_the_ci_platform_and_the_pinned_code_fails(
    env, execution, code, category
):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=execution)
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert code in codes(ev, "C6") and ev.check("C6").category == category
    assert not {"C1", "C2", "C3", "C4", "C5"} & set(ev.failed)


def test_c6_a_dirty_or_unpinned_code_ref_cannot_bind_any_run(env):
    _, v1 = env.good()
    dirty = FinalityPolicy("github_actions", {"commit": SHA + "+dirty"}, parse_keys)
    (ev,) = evaluate_records(env.store, SRC, dirty, w_doc=W, vintages=[v1])
    assert codes(ev, "C6") == {"code_ref_not_pinned"}


@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_c6_a_scheduled_or_dispatched_run_of_the_capture_workflow_on_main_passes(env, event):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=ci(event=event))
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert ev.passed and ev.check("C6").passed


@pytest.mark.parametrize(
    ("execution", "code", "category"),
    [
        (
            ci(workflow_ref=f"{REPO}/.github/workflows/ci.yml@refs/heads/main"),
            "workflow_not_capture",
            "unverified",
        ),
        (
            ci(workflow_ref=f"{REPO}/.github/workflows/s1b1-capture.yml@refs/heads/feature"),
            "workflow_not_capture",
            "unverified",
        ),
        (
            ci(workflow_ref=f"{REPO}/.github/workflows/s1b1-capture.yml.bak@refs/heads/main"),
            "workflow_not_capture",
            "unverified",
        ),
        (ci(ref="refs/heads/feature"), "ref_not_main", "unverified"),
        (ci(ref="refs/pull/7/merge"), "ref_not_main", "unverified"),
        (ci(event="pull_request"), "event_not_scheduled_or_dispatched", "unverified"),
        (ci(event="push"), "event_not_scheduled_or_dispatched", "unverified"),
        (ci(workflow_ref=None), "workflow_ref_missing", "missing"),
        (ci(ref=None), "ref_missing", "missing"),
        (ci(event=None), "event_missing", "missing"),
        (ci(workflow_ref=""), "workflow_ref_missing", "missing"),
        # the reviewer's counterexample: an unrelated CI job of the same repository, platform and sha
        (
            ci(
                job="unrelated_ci_job",
                workflow_ref=f"{REPO}/.github/workflows/unrelated.yml@refs/heads/main",
                event="push",
            ),
            "workflow_not_capture",
            "unverified",
        ),
    ],
)
def test_c6_a_run_of_another_workflow_ref_or_event_is_not_completion_evidence(env, execution, code, category):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=execution)
    v1 = vintage(1, "3.60", T(5, 30, 8))
    ev = one(env, [v1])
    assert code in codes(ev, "C6") and ev.check("C6").category == category
    assert ev.failed == ("C6",)
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == category


def test_c6_a_record_written_before_the_workflow_fields_loads_but_can_never_pass(env):
    legacy = Execution("github_actions", "1001", "1", "capture", SHA)
    rec = env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=legacy)
    assert b"workflow_ref" not in rec.canonical()  # the old canonical bytes, so the old hash still holds
    ev = one(env, [vintage(1, "3.60", T(5, 30, 8))])
    assert ev.record is not None and ev.check("C1").passed
    assert codes(ev, "C6") == {"workflow_ref_missing", "ref_missing", "event_missing"}
    assert ev.failed == ("C6",) and ev.category == "missing"


def test_c7_two_records_claiming_the_same_execution_both_fail(env):
    same = ci("5555")
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=same)
    env.attempt(
        body_of("3.60"), T(5, 40), T(5, 40, 8), T(5, 40, 10), outcome="verified_unchanged", execution=same
    )
    a, b = evaluate_records(env.store, SRC, POLICY, w_doc=W, vintages=[vintage(1, "3.60", T(5, 30, 8))])
    assert codes(a, "C7") == codes(b, "C7") == {"execution_claimed_twice"}
    assert a.failed == b.failed == ("C7",) and a.category == "inconsistent"


def test_c7_a_new_run_attempt_of_the_same_run_is_a_different_execution(env):
    env.attempt(
        body_of("3.60"),
        T(5, 30),
        T(5, 30, 8),
        T(5, 30, 10),
        execution=ci("5555"),
    )
    env.attempt(
        body_of("3.60"),
        T(5, 40),
        T(5, 40, 8),
        T(5, 40, 10),
        outcome="verified_unchanged",
        execution=ci("5555", "2"),
    )
    evs = evaluate_records(env.store, SRC, POLICY, w_doc=W, vintages=[vintage(1, "3.60", T(5, 30, 8))])
    assert all(e.check("C7").passed for e in evs)


# --- the ADR's worked cases (§4.3.4) --------------------------------------------------------------------


def test_worked_case_f2_a_revision_before_the_window_close_is_not_final_until_a_post_window_check(env):
    """AONIA is revised at 15:50, W_doc is 16:00, the final check runs at 16:30, a build at 16:10 has no
    record with attempted_at >= W_doc and s <= 16:10."""
    first = env.attempt(  # the first check, the evening before: before the window, so no evidence
        body_of("3.60"), T(22, 30, day=26), T(22, 30, 8, day=26), T(22, 30, 10, day=26)
    )
    v1 = vintage(1, "3.60", T(22, 30, 8, day=26))
    # the publisher revises at 04:50Z (15:50); HIO's final check at 05:30Z (16:30) sees the revision
    final = env.attempt(body_of("3.65"), T(5, 30), T(5, 30, 8), T(5, 30, 10))
    v2 = vintage(2, "3.65", T(5, 30, 8))
    held = [v1, v2]

    build = verdict(env, v1, held, T(5, 10))  # the build at 16:10 holds v1
    assert not build.final and build.category == "delayed"
    assert "stored_after_cutoff" in " ".join(build.reasons) or "attempted_before_window" in " ".join(
        build.reasons
    )

    after = verdict(env, v2, held, T(5, 40))  # after the 16:30 verified_changed check and its write time
    assert after.final and after.evidence == (final.key,)
    assert first.key != final.key
    superseded = verdict(env, v1, held, T(5, 40))
    assert not superseded.final and superseded.category == "inconsistent"
    assert "superseded" in superseded.reasons[0]


def test_worked_case_a_cached_response_dated_before_the_window_does_not_count(env):
    """The check runs at 16:05 but the response carries Date 15:58 and Age: 420; C4 fails."""
    body = body_of("3.60")
    env.capture(body, T(22, 30, day=26))
    v1 = vintage(1, "3.60", T(22, 30, day=26))
    cached = format_datetime(T(4, 58), usegmt=True)  # 15:58 Sydney
    env.attempt(
        body, T(5, 5), T(5, 5, 3), T(5, 5, 5), outcome="verified_unchanged",
        headers=[["Content-Type", "text/csv"], ["Date", cached], ["Age", "420"]],
    )  # fmt: skip
    ev = one(env, [v1])
    assert ev.failed == ("C4",) and codes(ev, "C4") == {"date_precedes_window"}
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "delayed"
    retried = env.attempt(body, T(5, 20), T(5, 20, 3), T(5, 20, 5), outcome="verified_unchanged")
    assert verdict(env, v1, [v1], T(6, 0)).evidence == (retried.key,)  # "retried": the retry counts


def test_worked_case_a_forged_unchanged_completion_copying_the_held_hash_fails_only_at_c4(env):
    """A verified_unchanged record copying the held receipt's hash and length, with no request after
    W_doc: it passes C1-C3 and C5-C7 and fails C4 (the genuine response carried a pre-window Date)."""
    body = body_of("3.60")
    env.capture(body, T(22, 30, day=26))
    v1 = vintage(1, "3.60", T(22, 30, day=26))
    env.attempt(body, T(5, 20), T(5, 20, 4), T(5, 20, 6), outcome="verified_unchanged", date_header=T(4, 30))
    ev = one(env, [v1])
    assert ev.failed == ("C4",)
    assert {"C1", "C2", "C3", "C5", "C6", "C7"} == {c.name for c in ev.checks if c.passed}
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "delayed"


# --- finality: refusal categories and conditions --------------------------------------------------------


def test_missing_no_record_for_the_key(env):
    v1 = vintage(1, "3.60", T(5, 30, 8))
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "missing" and refused.evidence == ()


def test_missing_a_vintage_captured_after_the_cutoff_has_no_evidence_at_it(env):
    _, v1 = env.good()
    refused = verdict(env, v1, [v1], T(5, 0))
    assert not refused.final and refused.category == "missing"


def test_failed_only_failed_attempts_since_the_window(env):
    failed = RunRecord(
        SRC, Execution("github_actions", "9001", "1", "capture", SHA), {"method": "GET", "url": "https://synthetic.invalid/x"},
        None, [], None, None, T(5, 30), T(5, 30, 1), "failed", error_class="network",
    )  # fmt: skip
    env.now = T(5, 30, 2)
    env.store.put(failed.key, failed.canonical())
    v1 = vintage(1, "3.60", T(5, 1))
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "failed"
    (ev,) = evaluate_records(env.store, SRC, POLICY, w_doc=W, vintages=[v1])
    assert ev.category == "failed" and codes(ev, "C2") == {"failed_record"}


def test_delayed_a_check_stored_after_the_cutoff_supports_only_a_later_cutoff(env):
    _, v1 = env.good()
    early = verdict(env, v1, [v1], T(5, 30, 9))
    assert not early.final and early.category == "delayed" and "stored_after_cutoff" in early.reasons[0]
    assert verdict(env, v1, [v1], T(5, 30, 10)).final


def test_inconsistent_a_value_that_differs_from_the_vintage(env):
    env.good("3.60")
    other = vintage(1, "3.70", T(5, 30, 8))
    refused = verdict(env, other, [other], T(6, 0))
    assert not refused.final and refused.category == "inconsistent"
    assert "value_differs_from_vintage" in " ".join(refused.reasons)


def test_inconsistent_two_post_window_records_that_disagree_are_quarantined_not_final(env):
    env.good("3.60")
    env.attempt(body_of("3.65"), T(5, 40), T(5, 40, 8), T(5, 40, 10))
    v1, v2 = vintage(1, "3.60", T(5, 30, 8)), vintage(2, "3.65", T(5, 40, 8))
    for v in (v1, v2):
        refused = verdict(env, v, [v1, v2], T(6, 0))
        if v is v2:
            assert not refused.final and refused.quarantine and refused.category == "inconsistent"
    early = verdict(env, v1, [v1, v2], T(5, 35))  # before the second record exists, v1 is final
    assert early.final and not early.quarantine


def test_unverified_a_manual_run_is_not_evidence(env):
    env.attempt(body_of("3.60"), T(5, 30), T(5, 30, 8), T(5, 30, 10), execution=Execution("other"))
    v1 = vintage(1, "3.60", T(5, 30, 8))
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "unverified"


def test_an_unreadable_record_is_reported_and_never_counted_as_evidence(env):
    env.now = T(5, 30)
    env.store.put(f"catalogue/attempts/{SRC}/20261027-053000000000-{'0' * 64}.json", b"{}")
    v1 = vintage(1, "3.60", T(5, 1))
    refused = verdict(env, v1, [v1], T(6, 0))
    assert not refused.final and refused.category == "missing"
    assert any(r.startswith("unreadable attempt record") for r in refused.reasons)


# --- a release is final only if every input vintage is --------------------------------------------------


def test_a_release_is_final_only_if_every_input_vintage_is_final(env):
    rec, v1 = env.good("3.60")
    unsupported = vintage(1, "3.60", T(5, 31))
    cutoff = T(6, 0)
    ok = verdict(env, v1, [v1], cutoff)
    bad = Verdict_for_other_key(env, unsupported, cutoff)
    assert release_finality([ok], cutoff).final
    assert release_finality([ok], cutoff).evidence == (rec.key,)
    mixed = release_finality([ok, bad], cutoff)
    assert not mixed.final and mixed.refused == (bad,) and mixed.category == bad.category


def Verdict_for_other_key(env, v, cutoff):
    other = Vintage(
        "synthetic.rate.other", v.valid_time, 1, v.value, v.receipt_id, v.captured_at, v.knowable_at,
        v.knowable_basis, v.source_timezone, v.quality_status,
    )  # fmt: skip
    return verdict(env, other, [other], cutoff)


def test_a_release_with_no_inputs_or_a_mismatched_cutoff_is_not_final(env):
    _, v1 = env.good()
    assert not release_finality([], T(6, 0)).final
    assert release_finality([], T(6, 0)).category == "missing"
    ok = verdict(env, v1, [v1], T(6, 0))
    mismatched = release_finality([ok], T(7, 0))
    assert not mismatched.final and mismatched.category == "inconsistent"
