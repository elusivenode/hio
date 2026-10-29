"""T-0012 P-2: the B-2 storage probe, offline. Fake containers only; no network, no credential, no Azure.

Each check is exercised passing and failing, including an overwrite that wrongly succeeds and a C5
observation whose provider timestamp is a whole second earlier than `completed_at`."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from azure.core.exceptions import HttpResponseError

from tests.test_t0010_azure_fakes import FakeBlobClient, FakeContainer, service_error

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("storage_probe", REPO / "tools" / "storage_probe.py")
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)

T = datetime(2026, 10, 30, 1, 2, 3, tzinfo=UTC)  # a whole second: the fake's Last-Modified equals it
RUN = "20261030T010203Z-test"


class _Client(FakeBlobClient):
    """Refuses an overwrite and a delete like the create-only role, unless the container says otherwise."""

    def upload_blob(self, data, **kwargs):
        if kwargs.get("overwrite") is True and self._c.overwrite_outcome == "refuse":
            self._c.calls.append(("upload_blob", self._name, {"data_len": len(data), **kwargs}))
            raise service_error(HttpResponseError, 403, "AuthorizationPermissionMismatch")
        if kwargs.get("overwrite") is True and self._c.overwrite_outcome == "server_error":
            raise service_error(HttpResponseError, 500, "InternalError")
        if self._c.ignore_if_missing:
            kwargs.pop("match_condition", None)
        return super().upload_blob(data, **kwargs)

    def delete_blob(self, **kwargs):
        c = self._c
        c.calls.append(("delete_blob", self._name, kwargs))
        if c.delete_outcome == "refuse":
            raise service_error(HttpResponseError, 409, "BlobImmutableDueToPolicy")
        if c.delete_outcome == "not_found":
            raise service_error(HttpResponseError, 404, "BlobNotFound")
        c._blobs.pop(self._name, None)


class Container(FakeContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.overwrite_outcome = "refuse"  # refuse | succeed | server_error
        self.delete_outcome = "refuse"  # refuse | succeed | not_found
        self.ignore_if_missing = False  # a store whose conditional create does not hold

    def get_blob_client(self, name):
        return _Client(self, name)


def run(container=None, **kwargs):
    container = container or Container(clock=lambda: T)
    kwargs.setdefault("now", lambda: T)
    kwargs.setdefault("repeats", 3)
    return probe.run_checks(container, run_id=RUN, **kwargs)


def by_name(results):
    return {r["check"]: r for r in results}


def test_every_check_passes_against_a_well_behaved_store():
    results = run()
    assert [r["check"] for r in results] == [
        "create_fresh_key",
        "create_again_raises_blob_exists",
        "overwrite_refused",
        "delete_refused",
        "exactly_one_version",
        "c5_timing",
    ]
    assert all(r["passed"] for r in results), results
    assert all(set(r) == {"check", "passed", "detail"} for r in results)


def test_keys_are_fresh_under_the_run_id():
    container = Container(clock=lambda: T)
    run(container, repeats=2)
    created = [name for op, name, _ in container.calls if op == "upload_blob" and name.startswith("probe/")]
    # the first key is created, then the refused repeat, then the overwrite attempt
    assert created[:3] == [f"probe/{RUN}/1"] * 3
    assert sorted(set(created)) == [f"probe/{RUN}/{n}" for n in (1, 2, 3)]


def test_create_failure_fails_the_check():
    container = Container(clock=lambda: T)
    container.upload_error = service_error(HttpResponseError, 403, "AuthorizationPermissionMismatch")
    result = by_name(run(container))["create_fresh_key"]
    assert not result["passed"] and "HTTP 403" in result["detail"]


def test_second_create_that_succeeds_fails_the_check_and_the_version_check():
    container = Container(clock=lambda: T)
    container.ignore_if_missing = True
    results = by_name(run(container))
    assert not results["create_again_raises_blob_exists"]["passed"]
    assert "SUCCEEDED" in results["create_again_raises_blob_exists"]["detail"]
    assert not results["exactly_one_version"]["passed"]
    assert "2 versions" in results["exactly_one_version"]["detail"]


def test_an_overwrite_that_wrongly_succeeds_fails_the_check():
    container = Container(clock=lambda: T)
    container.overwrite_outcome = "succeed"
    results = by_name(run(container))
    assert not results["overwrite_refused"]["passed"]
    assert "SUCCEEDED" in results["overwrite_refused"]["detail"]
    assert not results["exactly_one_version"]["passed"]  # the overwrite left a second version


def test_the_overwrite_is_attempted_through_the_sdk_client_with_overwrite_true():
    container = Container(clock=lambda: T)
    run(container)
    attempts = [kw for op, _, kw in container.calls if op == "upload_blob" and kw.get("overwrite") is True]
    assert len(attempts) == 1 and "match_condition" not in attempts[0]


def test_an_overwrite_error_that_is_not_a_refusal_is_inconclusive_and_fails():
    container = Container(clock=lambda: T)
    container.overwrite_outcome = "server_error"
    result = by_name(run(container))["overwrite_refused"]
    assert not result["passed"] and "inconclusive" in result["detail"] and "HTTP 500" in result["detail"]


def test_a_delete_that_wrongly_succeeds_fails_the_check():
    container = Container(clock=lambda: T)
    container.delete_outcome = "succeed"
    result = by_name(run(container))["delete_refused"]
    assert not result["passed"] and "SUCCEEDED" in result["detail"]


def test_a_delete_error_that_is_not_a_refusal_is_inconclusive_and_fails():
    container = Container(clock=lambda: T)
    container.delete_outcome = "not_found"
    result = by_name(run(container))["delete_refused"]
    assert not result["passed"] and "inconclusive" in result["detail"]


def test_a_refused_delete_passes_and_reports_only_type_status_and_code():
    result = by_name(run())["delete_refused"]
    assert result["passed"]
    assert "HttpResponseError HTTP 409 BlobImmutableDueToPolicy" in result["detail"]
    assert "injected service error" not in result["detail"]  # never the provider's message text


def test_a_check_that_raises_unexpectedly_fails_without_aborting_the_report():
    container = Container(clock=lambda: T)
    container.omit_last_modified = True  # ProviderMetadataError inside create's metadata read
    results = run(container)
    assert len(results) == 6 and not by_name(results)["create_fresh_key"]["passed"]


# --- C5 -------------------------------------------------------------------------------------------------


def c5(container_clock, now, *, repeats=4, delta=600.0):
    container = Container(clock=container_clock)
    return by_name(run(container, now=now, repeats=repeats, delta_seconds=delta))["c5_timing"]


def test_c5_passes_when_every_s_is_within_the_window_and_reports_each_observation():
    # the provider stamps 01:02:03 and completed_at reads 01:02:03.000: a difference of exactly zero
    result = c5(lambda: T, lambda: T)
    assert result["passed"]
    detail = result["detail"]
    assert detail["violations"] == 0 and detail["errors"] == 0 and detail["tolerance"] == "none"
    assert detail["min_diff_ms"] == detail["max_diff_ms"] == 0.0
    assert len(detail["observations"]) == 4
    first = detail["observations"][0]
    assert set(first) == {"key", "completed_at", "s", "diff_ms", "within"} and first["within"]
    assert first["completed_at"] == first["s"] == "2026-10-30T01:02:03.000000+00:00"


def test_c5_s_after_completed_at_within_delta_is_not_a_violation():
    result = c5(lambda: T, lambda: T - timedelta(milliseconds=250))
    assert result["passed"] and result["detail"]["min_diff_ms"] == result["detail"]["max_diff_ms"] == 250.0


def test_c5_s_a_whole_second_earlier_than_completed_at_is_a_violation():
    # completed_at 01:02:04.100, provider s 01:02:03: the whole-second Last-Modified is a second behind
    result = c5(lambda: T, lambda: T + timedelta(seconds=1, milliseconds=100), repeats=3)
    detail = result["detail"]
    assert not result["passed"]
    assert detail["violations"] == 3
    assert detail["min_diff_ms"] == detail["max_diff_ms"] == -1100.0
    assert all(not o["within"] for o in detail["observations"])


def test_c5_applies_no_tolerance_even_one_millisecond_early_fails():
    result = c5(lambda: T, lambda: T + timedelta(milliseconds=1), repeats=2)
    assert not result["passed"] and result["detail"]["violations"] == 2
    assert result["detail"]["max_diff_ms"] == -1.0


def test_c5_s_beyond_delta_is_a_violation():
    result = c5(lambda: T + timedelta(seconds=601), lambda: T, repeats=2, delta=600.0)
    assert not result["passed"] and result["detail"]["violations"] == 2
    assert result["detail"]["min_diff_ms"] == 601000.0


def test_c5_s_exactly_at_the_delta_boundary_is_within():
    result = c5(lambda: T + timedelta(seconds=600), lambda: T, repeats=1, delta=600.0)
    assert result["passed"]


def test_c5_counts_mixed_observations_and_reports_min_and_max():
    readings = iter([T, T + timedelta(seconds=2), T - timedelta(milliseconds=40)])
    result = c5(lambda: T, lambda: next(readings), repeats=3)
    detail = result["detail"]
    assert not result["passed"] and detail["violations"] == 1
    assert (detail["min_diff_ms"], detail["max_diff_ms"]) == (-2000.0, 40.0)
    assert [o["within"] for o in detail["observations"]] == [True, False, True]


def test_c5_a_failed_create_is_an_error_not_a_pass():
    container = Container(clock=lambda: T)
    container.upload_error = service_error(HttpResponseError, 500, "InternalError")
    detail = by_name(run(container, repeats=2))["c5_timing"]
    assert not detail["passed"]
    assert detail["detail"]["errors"] == 2 and detail["detail"]["violations"] == 2
    assert detail["detail"]["min_diff_ms"] is None


def test_c5_uses_a_fresh_key_for_every_repeat():
    container = Container(clock=lambda: T)
    run(container, repeats=5)
    keys = [n for op, n, kw in container.calls if op == "upload_blob" and kw.get("overwrite") is False]
    assert len(keys) == len(set(keys)) + 1  # only the refused repeat of the first key repeats


# --- main -----------------------------------------------------------------------------------------------

ENV = {
    "HIO_PROBE_ACCOUNT_URL": "https://hioprobe123.blob.core.windows.net",
    "HIO_PROBE_CONTAINER": "probe-container-name",
    "AZURE_TENANT_ID": "tenant-value-xyz",
    "AZURE_PROBE_CLIENT_ID": "client-value-xyz",
}


class Builders:
    def __init__(self, container):
        self.container = container
        self.credential_args = None
        self.container_args = None
        self.closed = False

    def credential(self, tenant, client, environ):
        self.credential_args = (tenant, client, environ)
        builders = self

        class Credential:
            def close(self):
                builders.closed = True

        return Credential()

    def build(self, url, name, credential):
        self.container_args = (url, name, credential)
        return self.container


def invoke(argv, container=None, environ=ENV):
    builders = Builders(container or Container(clock=lambda: T))
    code = probe.main(
        argv,
        environ=environ,
        credential_builder=builders.credential,
        container_builder=builders.build,
        now=lambda: T,
        run_id=RUN,
    )
    return code, builders


def test_main_passes_prints_one_json_report_and_exits_zero(capsys):
    code, builders = invoke(["--repeats", "2"])
    out = capsys.readouterr().out
    report = json.loads(out)
    assert code == 0 and report["passed"] is True
    assert report["run_id"] == RUN and report["started_at"] == "2026-10-30T01:02:03.000000+00:00"
    assert report["account_host"] == "hioprobe123.blob.core.windows.net"
    assert len(report["results"]) == 6
    assert builders.credential_args == ("tenant-value-xyz", "client-value-xyz", ENV)
    assert builders.container_args[:2] == (ENV["HIO_PROBE_ACCOUNT_URL"], "probe-container-name")
    assert builders.closed


def test_main_never_prints_environment_values_other_than_the_account_host(capsys):
    invoke(["--repeats", "1"])
    out = capsys.readouterr().out
    for name in ("HIO_PROBE_CONTAINER", "AZURE_TENANT_ID", "AZURE_PROBE_CLIENT_ID"):
        assert ENV[name] not in out
    assert ENV["HIO_PROBE_ACCOUNT_URL"] not in out  # the host, not the URL


def test_main_defaults_to_twenty_repeats(capsys):
    invoke([])
    results = json.loads(capsys.readouterr().out)["results"]
    assert results[-1]["detail"]["repeats"] == 20 and len(results[-1]["detail"]["observations"]) == 20
    assert results[-1]["detail"]["delta_seconds"] == 600.0


def test_main_exits_one_when_a_check_fails(capsys):
    container = Container(clock=lambda: T)
    container.overwrite_outcome = "succeed"
    code, _ = invoke(["--repeats", "1"], container)
    report = json.loads(capsys.readouterr().out)
    assert code == 1 and report["passed"] is False
    assert [r["check"] for r in report["results"] if not r["passed"]] == [
        "overwrite_refused",
        "exactly_one_version",
    ]


def test_main_writes_the_report_file_when_asked(tmp_path, capsys):
    target = tmp_path / "report.json"
    code, _ = invoke(["--repeats", "1", "--report-file", str(target)])
    assert code == 0 and json.loads(target.read_text()) == json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("missing", list(ENV))
def test_main_refuses_with_exit_two_naming_only_the_missing_variable(missing, capsys):
    environ = {k: v for k, v in ENV.items() if k != missing}
    code, builders = invoke([], environ=environ)
    captured = capsys.readouterr()
    assert code == 2 and captured.out == ""
    assert missing in captured.err
    assert not any(v in captured.err for v in environ.values())
    assert builders.credential_args is None  # refused before any credential or client


def test_main_refuses_when_the_client_cannot_be_built_without_leaking_the_message(capsys):
    def credential(*_args):
        raise RuntimeError("secret-token-text")

    code = probe.main(
        [], environ=ENV, credential_builder=credential, container_builder=None, now=lambda: T, run_id=RUN
    )
    captured = capsys.readouterr()
    assert code == 2 and "secret-token-text" not in captured.err + captured.out
    assert "RuntimeError" in captured.err


def test_main_rejects_nonsense_arguments():
    assert invoke(["--repeats", "0"])[0] == 2
    assert invoke(["--delta-seconds", "0"])[0] == 2


def test_the_script_imports_no_network_client_of_its_own():
    source = (REPO / "tools" / "storage_probe.py").read_text()
    for module in ("socket", "requests", "httpx", "urllib.request", "http.client", "DefaultAzureCredential"):
        assert module not in source, module
