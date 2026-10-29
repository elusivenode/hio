"""F-REVIEW-2026-10-29-t0010-1-2 (OD-0121): a run from another GitHub workflow is not capture evidence.

`Execution.from_environ` records the CI platform only for a scheduled or dispatched run of the capture
workflow on main (HIO-ADR-0012 §4.3.3); every other run is 'other', with the raw values still recorded."""

from __future__ import annotations

import json

import pytest

from hio.marketdata.runrecord import CAPTURE_WORKFLOW_PATH, Execution

REPO = "synthetic-owner/hio"
CAPTURE_REF = f"{REPO}/{CAPTURE_WORKFLOW_PATH}@refs/heads/main"
ENV = {
    "GITHUB_ACTIONS": "true",
    "GITHUB_REPOSITORY": REPO,
    "GITHUB_WORKFLOW_REF": CAPTURE_REF,
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "schedule",
    "GITHUB_RUN_ID": "9",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_JOB": "capture",
    "GITHUB_SHA": "b" * 40,
}


def test_the_capture_workflow_path_is_the_one_the_adr_names():
    assert CAPTURE_WORKFLOW_PATH == ".github/workflows/s1b1-capture.yml"


@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_a_scheduled_or_dispatched_run_of_the_capture_workflow_on_main_is_ci(event):
    e = Execution.from_environ(ENV | {"GITHUB_EVENT_NAME": event})
    assert e == Execution(
        "github_actions", "9", "2", "capture", "b" * 40, CAPTURE_REF, "refs/heads/main", event
    )


@pytest.mark.parametrize(
    "change",
    [
        {"GITHUB_WORKFLOW_REF": f"{REPO}/.github/workflows/ci.yml@refs/heads/main"},
        {"GITHUB_WORKFLOW_REF": f"{REPO}/{CAPTURE_WORKFLOW_PATH}@refs/heads/feature"},
        {
            "GITHUB_WORKFLOW_REF": f"other-owner/hio/{CAPTURE_WORKFLOW_PATH}@refs/heads/main"
        },  # another repository
        {"GITHUB_REF": "refs/heads/feature"},
        {"GITHUB_REF": "refs/pull/3/merge"},
        {"GITHUB_EVENT_NAME": "pull_request"},
        {"GITHUB_EVENT_NAME": "push"},
        {"GITHUB_EVENT_NAME": "workflow_call"},
        {"GITHUB_WORKFLOW_REF": None},
        {"GITHUB_REF": None},
        {"GITHUB_EVENT_NAME": None},
        {"GITHUB_REPOSITORY": None},
        {"GITHUB_REPOSITORY": ""},
        {"GITHUB_ACTIONS": "false"},
    ],
)
def test_any_other_run_is_other_and_keeps_the_raw_values(change):
    env = {k: v for k, v in (ENV | change).items() if v is not None}
    e = Execution.from_environ(env)
    assert e.platform == "other"
    if change.get("GITHUB_ACTIONS") != "false":
        assert e.run_id == "9" and e.sha == "b" * 40
        assert (e.workflow_ref, e.ref, e.event) == tuple(
            env.get(k) for k in ("GITHUB_WORKFLOW_REF", "GITHUB_REF", "GITHUB_EVENT_NAME")
        )


def test_the_unrelated_ci_job_counterexample_is_other():
    env = ENV | {
        "GITHUB_JOB": "unrelated_ci_job",
        "GITHUB_WORKFLOW_REF": f"{REPO}/.github/workflows/unrelated.yml@refs/heads/main",
        "GITHUB_EVENT_NAME": "push",
    }
    assert Execution.from_environ(env).platform == "other"


def test_no_github_environment_is_other():
    assert Execution.from_environ({}) == Execution("other")


def test_the_new_fields_are_recorded_when_present_and_omitted_when_absent():
    e = Execution.from_environ(ENV)
    assert json.loads(json.dumps(e.as_record())) == {
        "platform": "github_actions",
        "run_id": "9",
        "run_attempt": "2",
        "job": "capture",
        "sha": "b" * 40,
        "workflow_ref": CAPTURE_REF,
        "ref": "refs/heads/main",
        "event": "schedule",
    }
    assert set(Execution("github_actions", "1", "1", "j", "a" * 40).as_record()) == {
        "platform",
        "run_id",
        "run_attempt",
        "job",
        "sha",
    }
