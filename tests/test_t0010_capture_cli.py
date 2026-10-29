"""T-0010 W-3 (OD-0115; OD-0119 C-1, C-3, C-8): the live capture path is wired and NOT enabled.

No real network and no real Azure: the transport is a `FixtureTransport`, the storage client a fake
container, the credential a stand-in object. `LIVE_AUTHORISATION` is monkeypatched only inside tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from hio.contracts.layout import ATTEMPTS_PREFIX
from hio.jobs import s1b1_capture
from hio.jobs.s1b1_capture import LiveBuilders, merge_calendars
from hio.reference.calendar import load_reference_calendar
from hio.sources.datasets import PUBLICATIONS
from hio.sources.transport import FixtureTransport, HttpResponse
from tests.helpers import AllowAllGate
from tests.test_s1b1_capture import FILES, FX, HEADERS
from tests.test_t0010_azure_fakes import FakeContainer

REPO = Path(__file__).resolve().parent.parent
NOW = "2026-11-01T22:45:00Z"  # Sydney first checks are due
CANARY = "canary-value-must-not-print"
ENV = {
    "HIO_STORAGE_ACCOUNT_URL": "https://account.invalid",
    "HIO_STORAGE_CONTAINER": "box",
    "AZURE_TENANT_ID": "tenant-x",
    "AZURE_CLIENT_ID": "client-x",
    "GITHUB_ACTIONS": "true",
    "GITHUB_REPOSITORY": "synthetic-owner/hio",
    "GITHUB_WORKFLOW_REF": "synthetic-owner/hio/.github/workflows/s1b1-capture.yml@refs/heads/main",
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "schedule",
    "GITHUB_RUN_ID": "99",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_JOB": "capture",
    "GITHUB_SHA": "b" * 40,
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN": CANARY,
}


def calendar(tmp_path, name="rits.yaml", start="2026-09-01", end="2026-12-31", closed="[]", cid="rits"):
    path = tmp_path / name
    path.write_text(
        f"calendar_id: {cid}\nkind: reference\nas_of: 2026-10-28\n"
        'source: {citation: "test", url: "https://example.invalid/rits", rights_source_id: "test.only"}\n'
        f"coverage: {{start: {start}, end: {end}}}\nweekend: [5, 6]\nclosed: {closed}\n"
    )
    return str(path)


def urls():
    return {pid: f"https://fixture.invalid/{pid}" for pid in PUBLICATIONS}


def tick():
    t = [datetime(2026, 11, 1, 22, 50, tzinfo=UTC)]

    def clock():
        t[0] += timedelta(seconds=1)
        return t[0]

    return clock


class Exploding:
    """A builder that must never be called."""

    def __call__(self, *_args, **_kwargs):
        raise AssertionError("built before the live path was authorised")


def fakes(transport, container, credentials):
    def credential(tenant, client, _environ):
        credentials.append((tenant, client))
        return object()

    return LiveBuilders(
        gate=AllowAllGate,
        transport=lambda: transport,
        credential=credential,
        container=lambda _url, _name, _credential: container,
        urls=urls,
        clock=tick(),
    )


# --- refusal ------------------------------------------------------------------------------------------


def test_the_default_refuses_before_building_anything_and_needs_no_environment(tmp_path, capsys):
    assert s1b1_capture.LIVE_AUTHORISATION is None
    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom, urls=boom)
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW], environ={}, builders=builders
    )
    assert rc == 2
    assert "Authorisation B" in capsys.readouterr().err


def test_the_default_builders_are_not_called_even_with_a_complete_environment(tmp_path, monkeypatch, capsys):
    for name in ("BlobObjectStore", "AzureBlobBackend", "run_due", "Execution"):
        monkeypatch.setattr(s1b1_capture, name, Exploding())
    assert s1b1_capture.main(["--rits-calendar", calendar(tmp_path), "--at", NOW], environ=ENV) == 2
    assert "Authorisation B" in capsys.readouterr().err


def test_missing_environment_refuses_cleanly_and_leaks_no_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom, urls=urls)
    partial = {"HIO_STORAGE_ACCOUNT_URL": "https://account.invalid", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": CANARY}
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW], environ=partial, builders=builders
    )
    err = capsys.readouterr().err
    assert rc == 2
    for name in ("HIO_STORAGE_CONTAINER", "AZURE_TENANT_ID", "AZURE_CLIENT_ID"):
        assert name in err
    assert CANARY not in err and "account.invalid" not in err


def test_an_unconfigured_publication_url_refuses(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom)  # real url source
    assert (
        s1b1_capture.main(
            ["--rits-calendar", calendar(tmp_path), "--at", NOW], environ=ENV, builders=builders
        )
        == 2
    )
    assert "no approved URL" in capsys.readouterr().err


def test_a_credential_failure_prints_no_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")

    def credential(_tenant, _client, env):
        raise ValueError(f"leaky {env['ACTIONS_ID_TOKEN_REQUEST_TOKEN']}")

    builders = LiveBuilders(gate=Exploding(), transport=Exploding(), credential=credential, urls=urls)
    assert (
        s1b1_capture.main(
            ["--rits-calendar", calendar(tmp_path), "--at", NOW], environ=ENV, builders=builders
        )
        == 2
    )
    assert CANARY not in capsys.readouterr().err


def test_dry_run_is_unchanged_and_builds_nothing(tmp_path, capsys):
    boom = Exploding()
    builders = LiveBuilders(gate=boom, transport=boom, credential=boom, container=boom, urls=boom)
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW, "--dry-run"], environ={}, builders=builders
    )
    assert rc == 0
    assert "due rba.f1 first 2026-11-01T22:45:00+00:00" in capsys.readouterr().out


# --- the authorised path, entirely on fakes -----------------------------------------------------------


def test_an_authorised_run_captures_a_due_slot_into_the_fake_store_with_a_run_record(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    script = {
        f"https://fixture.invalid/{pid}": [
            HttpResponse(200, HEADERS, (FX / FILES[pid]).read_bytes(), f"https://fixture.invalid/{pid}")
        ]
        for pid in PUBLICATIONS
    }
    transport, container, credentials = FixtureTransport(script), FakeContainer(), []
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW],
        environ=ENV,
        builders=fakes(transport, container, credentials),
    )
    out = capsys.readouterr().out
    assert rc == 0, out
    assert credentials == [("tenant-x", "client-x")]
    assert "ran rba.f1 first verified_changed" in out and "ran rba.expert_judgement first" in out
    assert transport.requests  # the scripted fixture transport answered the requests
    keys = [name for op, name, _ in container.calls if op == "upload_blob"]
    assert any(k.startswith(ATTEMPTS_PREFIX) for k in keys)  # a run record is in the fake store
    assert any(k.startswith("receipts/") for k in keys)
    # the execution is copied unaltered from the environment
    attempt = next(k for k in keys if k.startswith(ATTEMPTS_PREFIX))
    body = container._blobs[attempt][-1].data.decode()
    assert '"platform":"github_actions"' in body.replace(" ", "") and '"run_id":"99"' in body.replace(" ", "")
    assert CANARY not in body


def test_a_run_of_another_workflow_records_platform_other(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    script = {
        f"https://fixture.invalid/{pid}": [
            HttpResponse(200, HEADERS, (FX / FILES[pid]).read_bytes(), f"https://fixture.invalid/{pid}")
        ]
        for pid in PUBLICATIONS
    }
    other = ENV | {"GITHUB_WORKFLOW_REF": "synthetic-owner/hio/.github/workflows/ci.yml@refs/heads/main"}
    transport, container = FixtureTransport(script), FakeContainer()
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW],
        environ=other,
        builders=fakes(transport, container, []),
    )
    assert rc == 0, capsys.readouterr().out
    keys = [name for op, name, _ in container.calls if op == "upload_blob"]
    attempt = next(k for k in keys if k.startswith(ATTEMPTS_PREFIX))
    body = container._blobs[attempt][-1].data.decode().replace(" ", "")
    assert '"platform":"other"' in body and '"platform":"github_actions"' not in body
    assert (
        '"workflow_ref":"synthetic-owner/hio/.github/workflows/ci.yml@refs/heads/main"' in body
    )  # raw value kept


def test_a_second_run_is_a_no_op_for_verified_slots(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    script = {
        f"https://fixture.invalid/{pid}": [
            HttpResponse(200, HEADERS, (FX / FILES[pid]).read_bytes(), f"https://fixture.invalid/{pid}")
        ]
        * 2
        for pid in PUBLICATIONS
    }
    transport, container = FixtureTransport(script), FakeContainer()
    argv = ["--rits-calendar", calendar(tmp_path), "--at", NOW]
    assert s1b1_capture.main(argv, environ=ENV, builders=fakes(transport, container, [])) == 0
    requests = len(transport.requests)
    capsys.readouterr()
    assert s1b1_capture.main(argv, environ=ENV, builders=fakes(transport, container, [])) == 0
    assert len(transport.requests) == requests and "ran" not in capsys.readouterr().out


def test_a_failed_capture_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(s1b1_capture, "LIVE_AUTHORISATION", "OD-9999")
    script = {
        f"https://fixture.invalid/{pid}": [HttpResponse(503, HEADERS, b"", f"https://fixture.invalid/{pid}")]
        for pid in PUBLICATIONS
    }
    rc = s1b1_capture.main(
        ["--rits-calendar", calendar(tmp_path), "--at", NOW],
        environ=ENV,
        builders=fakes(FixtureTransport(script), FakeContainer(), []),
    )
    assert rc == 1


def test_the_user_agent_names_hio_and_the_repository():
    assert (
        "HIO" in s1b1_capture.USER_AGENT and "https://github.com/elusivenode/hio" in s1b1_capture.USER_AGENT
    )


# --- several calendar files --------------------------------------------------------------------------


def test_several_calendars_merge(tmp_path):
    a = load_reference_calendar(
        calendar(tmp_path, "a.yaml", "2026-01-01", "2026-12-31", "[{date: 2026-12-25, reason: Christmas}]")
    )
    b = load_reference_calendar(
        calendar(tmp_path, "b.yaml", "2027-01-01", "2027-12-31", "[{date: 2027-01-01, reason: New Year}]")
    )
    m = merge_calendars([b, a])  # order does not matter
    assert m.coverage == (date(2026, 1, 1), date(2027, 12, 31))
    assert m.holidays == {date(2026, 12, 25), date(2027, 1, 1)}
    assert not m.is_business_day(date(2027, 1, 1)) and m.is_business_day(date(2026, 12, 24))
    assert m.is_cited and a.content_sha256 != m.content_sha256 != b.content_sha256
    assert merge_calendars([a]) is a


def test_overlapping_gapped_or_mismatched_calendars_refuse(tmp_path):
    a = load_reference_calendar(calendar(tmp_path, "a.yaml", "2026-01-01", "2026-12-31"))
    overlap = load_reference_calendar(calendar(tmp_path, "b.yaml", "2026-12-31", "2027-12-31"))
    gap = load_reference_calendar(calendar(tmp_path, "c.yaml", "2027-01-02", "2027-12-31"))
    other = load_reference_calendar(calendar(tmp_path, "d.yaml", "2027-01-01", "2027-12-31", cid="other"))
    with pytest.raises(ValueError, match="overlap"):
        merge_calendars([a, overlap])
    with pytest.raises(ValueError, match="gap"):
        merge_calendars([a, gap])
    with pytest.raises(ValueError, match="share one calendar id"):
        merge_calendars([a, other])


def test_the_command_line_accepts_the_calendar_option_repeatedly(tmp_path, capsys):
    a = calendar(tmp_path, "a.yaml", "2026-01-01", "2026-12-31")
    b = calendar(tmp_path, "b.yaml", "2027-01-01", "2027-12-31")
    assert s1b1_capture.main(["--rits-calendar", a, "--rits-calendar", b, "--at", NOW, "--dry-run"]) == 0
    assert "due rba.f1 first" in capsys.readouterr().out
    with pytest.raises(ValueError, match="overlap"):
        s1b1_capture.main(["--rits-calendar", a, "--rits-calendar", a, "--dry-run"])
