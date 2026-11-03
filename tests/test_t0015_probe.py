"""T-0015 F-2: C5 timing instrumentation in the B-2 storage probe, offline. Fake containers only.

The fake's `Last-Modified` is whole-second (a floor of its clock), like the provider's; a fake
response-header hook stands in for the SDK's `raw_response_hook`. No network, credential or Azure."""

from __future__ import annotations

import json
import subprocess
from datetime import timedelta
from email.utils import format_datetime
from types import SimpleNamespace

import pytest
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError

from tests.test_t0010_azure_fakes import service_error
from tests.test_t0012_script import RUN, Container, T, _Client, by_name, probe, run

ALL_HEADERS = ("Date", "Last-Modified", "x-ms-version-id", "x-ms-request-id")


class _HookClient(_Client):
    """Calls the `raw_response_hook` the way the SDK does: `response.http_response.headers`."""

    def upload_blob(self, data, **kwargs):
        hook = kwargs.get("raw_response_hook")
        self._c.hooks[self._name] = hook
        result = super().upload_blob(data, **{k: v for k, v in kwargs.items() if k != "raw_response_hook"})
        if hook is not None and self._c.response_headers is not None and kwargs.get("overwrite") is False:
            hook(SimpleNamespace(http_response=SimpleNamespace(headers=self._c.response_headers(result))))
        return result


class HookContainer(Container):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.response_headers = None  # callable(upload result) -> headers mapping, or None: no hook call
        self.hooks = {}  # blob name -> the raw_response_hook the last upload passed

    def get_blob_client(self, name):
        return _HookClient(self, name)


def http_date(moment):
    return format_datetime(moment, usegmt=True)


def headers_for(date, *, drop=()):
    def build(result):
        full = {
            "date": http_date(date),  # the SDK's header mapping is case-insensitive; names vary
            "Last-Modified": http_date(result["last_modified"]),
            "X-MS-Version-Id": result["version_id"],
            "x-ms-request-id": "req-0001",
        }
        return {k: v for k, v in full.items() if k.lower() not in {d.lower() for d in drop}}

    return build


def no_sync():
    return {"available": False, "reason": "test"}


def c5(container, *, now, repeats=1, **kwargs):
    kwargs.setdefault("clock_sync", no_sync)
    results = run(container, now=now, repeats=repeats, **kwargs)
    return by_name(results)["c5_timing"]


def floored_container():
    """The provider stamps the whole second T while the publisher's surrogate reads T + 0.4 s."""
    return HookContainer(clock=lambda: T + timedelta(milliseconds=400))


SURROGATE = T + timedelta(milliseconds=400)


# --- the two rules, side by side -----------------------------------------------------------------------


def test_a_floored_s_passes_the_candidate_rule_where_the_existing_rule_fails():
    result = c5(floored_container(), now=lambda: SURROGATE, repeats=3)
    detail = result["detail"]
    assert not result["passed"]  # the existing rule alone decides `passed`
    assert detail["rules"]["existing"]["violations"] == detail["violations"] == 3
    assert detail["rules"]["candidate"]["violations"] == 0
    assert detail["rules"]["tolerance"] == detail["tolerance"] == "none"
    for record in detail["timing_records"]:
        assert record["existing_rule_within"] is False and record["candidate_rule_within"] is True
        assert record["floor_s_completed_at"] == record["s"] == "2026-10-30T01:02:03.000000+00:00"
        assert record["completed_at_surrogate"] == "2026-10-30T01:02:03.400000+00:00"


def test_a_real_violation_fails_both_rules():
    # the surrogate reads 01:02:04.5 but the provider stamped 01:02:03: more than a floor away
    result = c5(HookContainer(clock=lambda: T), now=lambda: T + timedelta(seconds=1, milliseconds=500))
    detail = result["detail"]
    assert not result["passed"]
    assert detail["rules"]["existing"]["violations"] == 1 and detail["rules"]["candidate"]["violations"] == 1
    record = detail["timing_records"][0]
    assert record["existing_rule_within"] is False and record["candidate_rule_within"] is False


def test_s_beyond_delta_fails_both_rules():
    container = HookContainer(clock=lambda: T + timedelta(seconds=700))
    detail = c5(container, now=lambda: T, delta_seconds=600.0)["detail"]
    assert detail["rules"]["existing"]["violations"] == detail["rules"]["candidate"]["violations"] == 1


def test_a_whole_second_s_equal_to_completed_at_passes_both_rules_without_tolerance():
    result = c5(HookContainer(clock=lambda: T), now=lambda: T, repeats=2)
    assert result["passed"]
    assert result["detail"]["rules"]["existing"]["violations"] == 0
    assert result["detail"]["rules"]["candidate"]["violations"] == 0


def test_a_failed_create_counts_against_both_rules_and_has_an_error_record():
    container = HookContainer(clock=lambda: T)
    container.upload_error = service_error(HttpResponseError, 500, "InternalError")
    detail = c5(container, now=lambda: T, repeats=2)["detail"]
    assert detail["rules"]["existing"]["violations"] == detail["rules"]["candidate"]["violations"] == 2
    assert all(set(r) == {"key", "error"} and "HTTP 500" in r["error"] for r in detail["timing_records"])
    assert detail["offset_bounds_ms"]["observations_with_bracket"] == 0


def test_the_existing_observation_shape_is_unchanged():
    detail = c5(HookContainer(clock=lambda: T), now=lambda: T)["detail"]
    assert set(detail["observations"][0]) == {"key", "completed_at", "s", "diff_ms", "within"}


# --- the write, the surrogate and the instants -----------------------------------------------------------


def test_the_surrogate_is_read_once_immediately_before_the_write():
    container = HookContainer(clock=lambda: T)
    seen = []

    def now():
        seen.append(
            len([c for c in container.calls if c[0] == "upload_blob" and c[2].get("overwrite") is False])
        )
        return T

    c5(container, now=now, repeats=2)
    # `run_checks` created and refused-repeated one key before C5; the two timing writes follow
    assert len(seen) == 2 and seen[1] == seen[0] + 1


def test_the_put_goes_through_the_sdk_client_conditionally_with_a_raw_response_hook():
    container = HookContainer(clock=lambda: T)
    c5(container, now=lambda: T)
    timing = [kw for op, name, kw in container.calls if op == "upload_blob" and name == f"probe/{RUN}/2"]
    assert len(timing) == 1
    assert timing[0]["overwrite"] is False and timing[0]["match_condition"] == MatchConditions.IfMissing
    assert callable(container.hooks[f"probe/{RUN}/2"])


def test_instants_and_monotonic_durations_are_recorded():
    pre, post, meta = (
        T + timedelta(seconds=1),
        T + timedelta(seconds=1, milliseconds=250),
        T + timedelta(seconds=2),
    )
    instants = iter([pre, post, meta])
    ticks = iter([10.0, 10.001, 10.251, 10.3])
    container = HookContainer(clock=lambda: T)
    detail = c5(container, now=lambda: T, clock=lambda: next(instants), monotonic=lambda: next(ticks))[
        "detail"
    ]
    record = detail["timing_records"][0]
    assert (record["pre_put"], record["post_put"], record["post_metadata"]) == (
        "2026-10-30T01:02:04.000000+00:00",
        "2026-10-30T01:02:04.250000+00:00",
        "2026-10-30T01:02:05.000000+00:00",
    )
    durations = record["durations_ms"]
    assert durations["pre_put_to_post_put"] == pytest.approx(250.0)
    assert durations["post_put_to_post_metadata"] == pytest.approx(49.0)
    assert durations["surrogate_to_post_metadata"] == pytest.approx(300.0)


# --- headers ---------------------------------------------------------------------------------------------


def test_the_response_headers_are_captured_case_insensitively():
    container = HookContainer(clock=lambda: T)
    container.response_headers = headers_for(T)
    record = c5(container, now=lambda: T)["detail"]["timing_records"][0]
    assert record["headers_captured"] is True and record["response_hook_calls"] == 1
    assert set(record["headers"]) == set(ALL_HEADERS)
    assert record["headers"]["Date"] == http_date(T)
    assert record["headers"]["Last-Modified"] == http_date(T)
    assert record["headers"]["x-ms-version-id"].startswith("vid-")
    assert record["headers"]["x-ms-request-id"] == "req-0001"
    assert record["missing_headers"] == []


def test_a_missing_response_hook_call_reports_every_header_as_absent_and_invents_nothing():
    container = HookContainer(clock=lambda: T)  # the fake never calls the hook
    detail = c5(container, now=lambda: T)["detail"]
    record = detail["timing_records"][0]
    assert record["headers_captured"] is False and record["response_hook_calls"] == 0
    assert record["headers"] == dict.fromkeys(ALL_HEADERS)
    assert record["missing_headers"] == list(ALL_HEADERS)
    assert record["offset_bracket_ms"] is None
    assert detail["offset_bounds_ms"] == {
        "observations_with_bracket": 0,
        "lower_max": None,
        "upper_min": None,
    }


@pytest.mark.parametrize("name", ALL_HEADERS)
def test_one_missing_header_is_reported_and_the_others_are_kept(name):
    container = HookContainer(clock=lambda: T)
    container.response_headers = headers_for(T, drop=(name,))
    record = c5(container, now=lambda: T)["detail"]["timing_records"][0]
    assert record["missing_headers"] == [name]
    assert record["headers"][name] is None
    assert all(v for k, v in record["headers"].items() if k != name)
    assert (record["offset_bracket_ms"] is None) == (name == "Date")


def test_an_unparseable_date_gives_no_bracket_and_is_flagged():
    container = HookContainer(clock=lambda: T)
    container.response_headers = lambda _result: {"Date": "not a date", "x-ms-request-id": "r"}
    record = c5(container, now=lambda: T)["detail"]["timing_records"][0]
    assert record["offset_bracket_ms"] is None
    assert "Date (unparseable)" in record["missing_headers"]
    assert record["headers"]["Date"] == "not a date"  # reported as received


def test_headers_in_the_report_are_those_of_the_last_response_when_the_hook_runs_twice():
    class Retrying(_HookClient):
        def upload_blob(self, data, **kwargs):
            hook = kwargs.get("raw_response_hook")
            if hook is not None and kwargs.get("overwrite") is False:
                hook(SimpleNamespace(http_response=SimpleNamespace(headers={"x-ms-request-id": "first"})))
            return super().upload_blob(data, **kwargs)

    class RetryContainer(HookContainer):
        def get_blob_client(self, name):
            return Retrying(self, name)

    container = RetryContainer(clock=lambda: T)
    container.response_headers = headers_for(T)
    record = c5(container, now=lambda: T)["detail"]["timing_records"][0]
    assert record["response_hook_calls"] == 2 and record["headers"]["x-ms-request-id"] == "req-0001"


# --- clock-offset brackets ---------------------------------------------------------------------------------


def test_date_brackets_bound_the_runner_to_storage_offset():
    pre, post = T + timedelta(milliseconds=200), T + timedelta(milliseconds=700)
    instants = iter([pre, post, post + timedelta(milliseconds=50)])
    container = HookContainer(clock=lambda: T)
    container.response_headers = headers_for(T)  # Date 01:02:03 (whole second)
    detail = c5(container, now=lambda: T, clock=lambda: next(instants))["detail"]
    bracket = detail["timing_records"][0]["offset_bracket_ms"]
    assert bracket == {"lower": -700.0, "upper": 800.0}  # Date - post_put; Date + 1 s - pre_put
    assert detail["offset_bounds_ms"] == {
        "observations_with_bracket": 1,
        "lower_max": -700.0,
        "upper_min": 800.0,
    }


def test_offset_bounds_intersect_the_observations():
    stamps = iter(
        [
            T + timedelta(milliseconds=100),  # obs 1: pre
            T + timedelta(milliseconds=300),  # post
            T + timedelta(milliseconds=350),  # post_metadata
            T + timedelta(milliseconds=500),  # obs 2: pre
            T + timedelta(milliseconds=900),  # post
            T + timedelta(milliseconds=950),  # post_metadata
        ]
    )
    container = HookContainer(clock=lambda: T)
    container.response_headers = headers_for(T)
    detail = c5(container, now=lambda: T, repeats=2, clock=lambda: next(stamps))["detail"]
    first, second = (r["offset_bracket_ms"] for r in detail["timing_records"])
    assert first == {"lower": -300.0, "upper": 900.0} and second == {"lower": -900.0, "upper": 500.0}
    assert detail["offset_bounds_ms"] == {
        "observations_with_bracket": 2,
        "lower_max": -300.0,
        "upper_min": 500.0,
    }


# --- the runner's clock state -----------------------------------------------------------------------------


def test_the_injected_clock_sync_state_is_reported():
    state = {"available": True, "NTPSynchronized": "yes"}
    detail = c5(HookContainer(clock=lambda: T), now=lambda: T, clock_sync=lambda: state)["detail"]
    assert detail["clock_sync"] == state


def test_clock_sync_absence_is_reported(monkeypatch):
    def missing(*_args, **_kwargs):
        raise FileNotFoundError("timedatectl")

    monkeypatch.setattr(probe.subprocess, "run", missing)
    assert probe.read_clock_sync() == {"available": False, "reason": "FileNotFoundError"}


def fake_timedatectl(monkeypatch, returncode, stdout):
    def completed(args, **_kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(probe.subprocess, "run", completed)


def test_clock_sync_failure_exit_is_reported_as_unavailable(monkeypatch):
    fake_timedatectl(monkeypatch, 1, "")
    assert probe.read_clock_sync() == {"available": False, "reason": "timedatectl exited 1"}


def test_clock_sync_keeps_only_the_synchronisation_fields(monkeypatch):
    out = "Timezone=UTC\nLocalRTC=no\nNTP=yes\nNTPSynchronized=yes\nTimeUSec=Fri 2026-10-30 01:02:03 UTC\n"
    fake_timedatectl(monkeypatch, 0, out + "Secret=x\n")
    assert probe.read_clock_sync() == {
        "available": True,
        "NTP": "yes",
        "NTPSynchronized": "yes",
        "TimeUSec": "Fri 2026-10-30 01:02:03 UTC",
        "Timezone": "UTC",
    }


def test_the_report_is_json_serialisable_with_every_instrument():
    container = HookContainer(clock=lambda: T)
    container.response_headers = headers_for(T)
    result = c5(container, now=lambda: T, repeats=2)
    text = json.dumps(result)
    assert "timing_records" in text and "offset_bounds_ms" in text and "clock_sync" in text


def test_the_other_five_checks_are_unchanged():
    results = run(HookContainer(clock=lambda: T), clock_sync=no_sync)
    assert [r["check"] for r in results][:5] == [
        "create_fresh_key",
        "create_again_raises_blob_exists",
        "overwrite_refused",
        "delete_refused",
        "exactly_one_version",
    ]
    assert all(r["passed"] for r in results[:5])
