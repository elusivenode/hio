"""T-0009 A-4 and OD-0065: the OpenTofu definitions are HIO-only and encode the storage controls.
Nothing is planned or applied here. The tests read the .tf files as text, run `tofu fmt -check`
(offline) if OpenTofu is installed, and check that infrastructure state can never be committed."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TF = REPO / "infra" / "tofu"


def _code(source: str) -> str:
    """The definitions without comments: a comment may name what is excluded, a resource may not."""
    return "\n".join(re.sub(r"\s*#.*$", "", line) for line in source.splitlines())


def text(name: str) -> str:
    return _code((TF / name).read_text())


def all_tf() -> str:
    return "\n".join(_code(p.read_text()) for p in sorted(TF.glob("*.tf")))


def test_the_storage_account_encodes_the_required_controls():
    main = text("main.tf")
    for key, value in (
        ("is_hns_enabled", "false"),
        ("shared_access_key_enabled", "false"),
        ("default_to_oauth_authentication", "true"),
        ("allow_nested_items_to_be_public", "false"),
        ("min_tls_version", '"TLS1_2"'),
        ("versioning_enabled", "true"),
        ("container_access_type", '"private"'),
    ):
        assert re.search(rf"^\s*{key}\s+= {value}$", main, re.M), key
    assert re.search(r'immutability_policy \{[^}]*state\s+= "Unlocked"', main, re.S)
    assert '"Locked"' not in main  # locking is irreversible: a deliberate owner action, never a default


def test_the_writer_can_create_but_not_overwrite_or_delete():
    identity = text("identity.tf")
    role = re.search(
        r'resource "azurerm_role_definition" "capture_writer" \{.*?\n\}\n', identity, re.S
    ).group(0)
    actions = re.findall(r'"(Microsoft\.[^"]+)"', role)
    assert actions == [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action",
    ]
    assert not re.search(r"/(write|delete|move/action|runAsSuperUser/action)\b", role)
    assert "actions = []" in role  # no control-plane actions


def test_access_is_identity_only_with_no_static_credential():
    tf = all_tf()
    assert "azurerm_federated_identity_credential" in tf and "token.actions.githubusercontent.com" in tf
    assert re.search(r"^\s*subject\s+= var\.github_oidc_subject$", tf, re.M)
    for forbidden in (
        "primary_access_key",
        "secondary_access_key",
        "connection_string",
        "sas_token",
        "access_key =",
    ):
        assert forbidden not in tf, forbidden
    outputs = text("outputs.tf")
    assert "key" not in outputs.lower().replace("client_id", "")  # identifiers only


def test_resources_are_hio_only_and_no_subscription_is_committed():
    tf = all_tf()
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", tf
    )  # no GUID at all
    assert re.search(r"hnf|hedgehog|macsmsf|tigris", tf, re.I) is None
    names = re.findall(r'(?:name\s+=\s+)"([^"]+)"', tf)
    assert names and all(
        "hio" in n.lower() or n in {"github-capture", "Storage Blob Data Reader"} for n in names
    ), names
    variables = text("variables.tf")
    sub = re.search(r'variable "subscription_id" \{.*?\n\}\n', variables, re.S).group(0)
    assert not re.search(r"^\s*default\s*=", sub, re.M)  # chosen at apply time, never committed
    reader = re.search(r'variable "reader_principal_object_id" \{.*?\n\}\n', variables, re.S).group(0)
    assert not re.search(r"^\s*default\s*=", reader, re.M)


def test_every_scope_is_the_hio_account_or_container():
    identity = text("identity.tf")
    scopes = re.findall(r"^\s*scope\s+= (\S+)$", identity, re.M)
    assert scopes and set(scopes) <= {
        "azurerm_storage_account.evidence.id",
        "azurerm_storage_container.evidence.id",
    }


def _variable(name: str) -> str:
    return re.search(rf'variable "{name}" \{{.*?\n\}}(?:\n|$)', text("variables.tf"), re.S).group(0)


def _resource(kind: str, name: str, source: str) -> str:
    return re.search(rf'resource "{kind}" "{name}" \{{.*?\n\}}(?:\n|$)', text(source), re.S).group(0)


def test_the_oidc_subject_is_a_variable_with_no_default_and_no_github_repository():
    tf = all_tf()
    subject = _variable("github_oidc_subject")
    assert not re.search(r"^\s*default\s*=", subject, re.M)
    assert "immutable" in (TF / "variables.tf").read_text()  # the description names the format
    assert "var.github_repository" not in tf and "var.github_environment" not in tf
    assert not re.search(r'subject\s+= "', tf)  # never a literal subject
    assert "github_repository" not in tf


def test_no_deprecated_resource_manager_id():
    assert "resource_manager_id" not in all_tf()


def test_the_reader_stays_separate_from_the_writer():
    identity = text("identity.tf")
    reader = _resource("azurerm_role_assignment", "owner_reader", "identity.tf")
    writer = _resource("azurerm_role_assignment", "capture_writer", "identity.tf")
    assert 'role_definition_name = "Storage Blob Data Reader"' in reader
    assert "var.reader_principal_object_id" in reader and "azurerm_user_assigned_identity" not in reader
    assert "azurerm_user_assigned_identity.capture.principal_id" in writer
    assert "var.reader_principal_object_id" not in writer
    assert identity.count("azurerm_role_assignment") == 2


def test_storage_decisions_are_variables_with_defaults_and_validation():
    main = text("main.tf")
    for argument, variable in (
        ("period_since_creation_in_days", "immutability_period_days"),
        ("account_replication_type", "account_replication_type"),
        ("default_action", "network_default_action"),
    ):
        assert re.search(rf"{argument}\s+= var\.{variable}$", main, re.M), argument
        block = _variable(variable)
        assert re.search(r"^\s*default\s*=", block, re.M), variable
        assert "validation {" in block, variable
    assert re.search(r"default\s+= 3650$", _variable("immutability_period_days"), re.M)
    replication = _variable("account_replication_type")
    assert '["ZRS", "GZRS"]' in replication and 'default     = "ZRS"' in replication
    network = _variable("network_default_action")
    assert '["Allow", "Deny"]' in network and 'default     = "Allow"' in network


def test_blob_audit_logs_go_to_a_workspace_in_the_hio_resource_group():
    workspace = _resource("azurerm_log_analytics_workspace", "hio", "monitoring.tf")
    assert "azurerm_resource_group.hio.name" in workspace
    assert "retention_in_days   = var.log_retention_days" in workspace
    assert re.search(r"default\s+= 90$", _variable("log_retention_days"), re.M)
    diag = _resource("azurerm_monitor_diagnostic_setting", "evidence_blob", "monitoring.tf")
    assert '"${azurerm_storage_account.evidence.id}/blobServices/default"' in diag
    assert "log_analytics_workspace_id = azurerm_log_analytics_workspace.hio.id" in diag
    # Dedicated: logs land in the resource-specific StorageBlobLogs table the soak alert queries.
    assert re.search(r'^\s*log_analytics_destination_type\s+= "Dedicated"$', diag, re.M)
    assert re.findall(r'enabled_log \{\s*category = "(\w+)"', diag) == [
        "StorageRead",
        "StorageWrite",
        "StorageDelete",
    ]
    assert re.findall(r'enabled_metric \{\s*category = "(\w+)"', diag) == ["Transaction"]


def test_the_soak_alert_watches_the_attempts_prefix_and_emails_the_owner():
    monitoring = text("monitoring.tf")
    group = _resource("azurerm_monitor_action_group", "owner", "monitoring.tf")
    assert "email_address           = var.owner_email" in group
    alert = _resource("azurerm_monitor_scheduled_query_rules_alert_v2", "no_attempt_write", "monitoring.tf")
    assert "azurerm_monitor_action_group.owner.id" in alert
    assert "azurerm_resource_group.hio.name" in alert
    assert 'operator                = "LessThan"' in alert and "threshold               = 1" in alert
    query = re.search(r"<<-QUERY\n(.*?)\n\s*QUERY", monitoring, re.S).group(1)
    assert query.lstrip().startswith("StorageBlobLogs")  # named directly: a missing table must error
    assert "isfuzzy" not in monitoring and "datatable" not in monitoring and "union" not in query
    assert 'Category == "StorageWrite"' in query and 'OperationName == "PutBlob"' in query
    assert 'StatusText == "Success"' in query
    assert 'ObjectKey contains "/catalogue/attempts/"' in query
    assert "ago(${var.missing_write_window_hours}h)" in query
    assert "summarize WriteCount = count()" in query
    assert re.search(r"default\s+= 26$", _variable("missing_write_window_hours"), re.M)


def test_the_readme_specifies_the_github_failure_notification_and_its_verification():
    readme = " ".join((TF / "README.md").read_text().split())
    assert (
        "Settings > Notifications > System > Actions* (the dropdown), choose **Email**, "
        "tick **Only notify for failed workflows**, and **Save**"
    ) in readme
    assert "Send notifications for failed workflows only" not in readme
    assert "managing-github-actions-notifications" in readme
    assert "notifications-for-workflow-runs" in readme
    assert "**created or last modified the cron schedule**" in readme
    assert "**re-enabled a disabled workflow**" in readme
    assert "The owner's account must therefore be that user" in readme
    assert "requires the verification below to be repeated" in readme
    assert "deliberate-failure test" in readme and "S1-A13" in readme
    assert "must make a **scheduled** run fail on purpose" in readme
    assert "workflow_dispatch" in readme and "never sufficient" in readme
    assert "scheduled-or-dispatched" not in readme
    assert "the soak does not count" in readme
    assert "Dedicated" in readme and "StorageBlobLogs" in readme


def test_the_budget_covers_the_hio_resource_group_and_notifies_the_owner_at_80_and_100():
    budget = _resource("azurerm_consumption_budget_resource_group", "hio", "budget.tf")
    assert "resource_group_id = azurerm_resource_group.hio.id" in budget
    assert "amount            = var.budget_amount" in budget
    assert re.search(r"default\s+= 20$", _variable("budget_amount"), re.M)
    assert re.findall(r"threshold\s+= (\d+)$", budget, re.M) == ["80", "100"]
    assert budget.count("contact_emails = [var.owner_email]") == 2


def test_owner_inputs_have_no_default():
    for name in ("owner_email", "budget_start_date", "github_oidc_subject"):
        assert not re.search(r"^\s*default\s*=", _variable(name), re.M), name


def test_no_email_guid_or_github_numeric_id_is_committed_in_infra():
    sources = [*TF.glob("*.tf"), TF / "README.md", *(REPO / "infra" / "workflows").glob("*")]
    for path in sources:
        content = path.read_text()
        assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", content), path
        assert not re.search(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", content, re.I
        ), path
        assert not re.search(r"@[0-9]{3,}", content), path  # <owner>@<id> in an immutable subject


@pytest.mark.skipif(shutil.which("tofu") is None, reason="OpenTofu is not installed")
def test_the_definitions_are_formatted():
    result = subprocess.run(
        ["tofu", "fmt", "-check", "-diff", str(TF)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_infrastructure_state_and_variables_cannot_be_committed(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_repo", REPO / "tools" / "check_repo.py")
    check_repo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_repo)
    monkeypatch.setattr(check_repo, "errors", [])
    bad = [
        "infra/tofu/terraform.tfstate",
        "infra/tofu/prod.tfvars",
        "infra/tofu/.terraform/x",
        "infra/tofu/plan.tfplan",
    ]
    for path in bad:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("{}")
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    check_repo.check_public(bad)
    joined = "\n".join(check_repo.errors)
    assert joined.count("infrastructure state, plan or variables") == len(bad)
    assert not any("infra/tofu/variables.tf" in e for e in check_repo.errors)
