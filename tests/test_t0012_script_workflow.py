"""T-0012 P-3: text-level checks of `.github/workflows/storage-probe.yml`. Nothing is run or dispatched.

Dispatch only, no schedule, no stored secret, the `capture` environment, an OIDC-only token permission,
pinned actions and probe variables from `vars.*`."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / ".github" / "workflows" / "storage-probe.yml"
CAPTURE = REPO / "infra" / "workflows" / "s1b1-capture.yml"

SHA_PIN = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
# The upload-artifact commit SHA could not be verified offline, so it is a marked placeholder for the
# orchestrator to replace (see the TODO in the workflow). No other action may be unpinned.
UPLOAD_PLACEHOLDER = "actions/upload-artifact@TODO-PIN-V4-FULL-COMMIT-SHA"


def code(source: str) -> str:
    """The workflow without comments: a comment may name what is excluded, the workflow may not use it."""
    return "\n".join(re.sub(r"(^|\s)#.*$", "", line) for line in source.splitlines())


def parsed() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def steps() -> list[dict]:
    return parsed()["jobs"]["probe"]["steps"]


def test_the_trigger_is_workflow_dispatch_only_with_a_repeats_input_defaulting_to_20():
    triggers = parsed()[True]  # PyYAML reads the bare key `on` as the boolean True
    assert list(triggers) == ["workflow_dispatch"]
    repeats = triggers["workflow_dispatch"]["inputs"]["repeats"]
    assert repeats["default"] == 20 and repeats["type"] == "number"
    text = code(WORKFLOW.read_text())
    assert not re.search(r"^\s*(schedule|push|pull_request\w*|workflow_run|workflow_call):", text, re.M)
    assert "cron" not in text


def test_no_secrets_context_is_used():
    assert "secrets." not in code(WORKFLOW.read_text())
    assert "secrets" not in parsed()["jobs"]["probe"]


def test_the_job_runs_in_the_capture_environment_with_oidc_and_read_only_contents():
    assert parsed()["permissions"] == {"contents": "read", "id-token": "write"}
    assert parsed()["jobs"]["probe"]["environment"] == "capture"
    assert "permissions" not in parsed()["jobs"]["probe"]  # nothing widens the workflow-level grant


def test_actions_are_pinned_by_commit_sha_like_the_capture_definition():
    uses = [s["uses"] for s in steps() if "uses" in s]
    assert uses[:2] == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "astral-sh/setup-uv@07a047e608db84b3d8c06cd9a7c7dcc9c355c18e",
    ]
    capture = CAPTURE.read_text()
    for pin in uses[:2]:  # the very same pins, with the same version comments
        assert pin in capture
    for pin in uses:
        assert SHA_PIN.match(pin) or pin == UPLOAD_PLACEHOLDER, pin
    assert uses[2].startswith("actions/upload-artifact@")


def test_the_pinned_versions_match_the_capture_definition_comments():
    text = WORKFLOW.read_text()
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1" in text
    assert "astral-sh/setup-uv@07a047e608db84b3d8c06cd9a7c7dcc9c355c18e  # v10.3.2" in text
    setup = next(s for s in steps() if s.get("uses", "").startswith("astral-sh/setup-uv@"))
    assert setup["with"] == {"version": "0.11.19", "enable-cache": False}
    checkout = next(s for s in steps() if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"] == {"persist-credentials": False}


def test_the_probe_step_runs_the_script_frozen_with_the_repeats_input_and_vars_only():
    step = next(s for s in steps() if "storage_probe.py" in s.get("run", ""))
    assert step["run"].startswith("uv run --frozen python tools/storage_probe.py --repeats ")
    assert "--report-file storage-probe-report.json" in step["run"]
    assert step["env"] == {
        "PROBE_REPEATS": "${{ inputs.repeats }}",
        "HIO_PROBE_ACCOUNT_URL": "${{ vars.HIO_PROBE_ACCOUNT_URL }}",
        "HIO_PROBE_CONTAINER": "${{ vars.HIO_PROBE_CONTAINER }}",
        "AZURE_TENANT_ID": "${{ vars.AZURE_TENANT_ID }}",
        "AZURE_PROBE_CLIENT_ID": "${{ vars.AZURE_PROBE_CLIENT_ID }}",
    }
    assert "${{" not in step["run"]  # the input reaches the shell as a variable, never interpolated


def test_the_report_is_uploaded_even_when_the_probe_fails():
    upload = steps()[-1]
    assert upload["uses"].startswith("actions/upload-artifact@")
    assert upload["if"] == "always()"
    assert upload["with"]["path"] == "storage-probe-report.json"
    assert upload["with"]["name"] == "storage-probe-report"


def test_no_literal_identifier_or_account_is_committed_in_the_workflow():
    text = WORKFLOW.read_text()
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text, re.I)
    assert "blob.core.windows.net" not in text
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", text)
    assert "evidence" not in code(text).lower()  # the evidence store is never named as a target
    assert "HIO_STORAGE_" not in text and "AZURE_CLIENT_ID" not in text.replace("AZURE_PROBE_CLIENT_ID", "")
