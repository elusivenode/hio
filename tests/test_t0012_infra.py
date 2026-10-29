"""T-0012 P-1 (OD-0127): the B-2 probe's OpenTofu root module (infra/tofu/probe/) is separate from the
evidence store, short-lived, create-only and local-state. Nothing is planned or applied here: the tests
read the .tf files as text and run `tofu fmt -check` (offline) if OpenTofu is installed."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROBE = REPO / "infra" / "tofu" / "probe"
EVIDENCE = REPO / "infra" / "tofu"

GUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _code(source: str) -> str:
    """The definitions without comments: a comment may name what is excluded, a resource may not."""
    return "\n".join(re.sub(r"\s*#.*$", "", line) for line in source.splitlines())


def text(name: str) -> str:
    return _code((PROBE / name).read_text())


def all_tf() -> str:
    return "\n".join(_code(p.read_text()) for p in sorted(PROBE.glob("*.tf")))


def _resource(kind: str, name: str, source: str) -> str:
    return re.search(rf'resource "{kind}" "{name}" \{{.*?\n\}}(?:\n|$)', text(source), re.S).group(0)


def _variable(name: str) -> str:
    return re.search(rf'variable "{name}" \{{.*?\n\}}(?:\n|$)', text("variables.tf"), re.S).group(0)


def test_the_probe_is_a_separate_root_module_with_the_same_provider_constraint():
    assert (PROBE / "versions.tf").exists() and PROBE != EVIDENCE
    probe, evidence = text("versions.tf"), _code((EVIDENCE / "versions.tf").read_text())
    for line in ('required_version = ">= 1.8.0"', 'version = "~> 4.0"'):
        assert re.sub(r"\s+", " ", line) in re.sub(r"\s+", " ", probe), line
        assert re.sub(r"\s+", " ", line) in re.sub(r"\s+", " ", evidence), line
    assert re.search(r"^\s*subscription_id\s+= var\.subscription_id$", probe, re.M)
    assert re.search(r"^\s*storage_use_azuread\s+= true$", probe, re.M)


def test_there_is_no_backend_block_so_state_stays_local_and_outside_the_repository():
    assert not re.search(r"\bbackend\b", all_tf())
    assert not list(PROBE.glob("*.tfstate*")) and not list(PROBE.glob("*.tfvars*"))
    readme = (PROBE / "README.md").read_text()
    assert "~/.hio-state/probe.tfstate" in readme and "-state" in readme


def test_the_account_has_the_evidence_settings_and_a_one_day_unlocked_immutability_period():
    main = text("main.tf")
    for key, value in (
        ("account_kind", '"StorageV2"'),
        ("account_replication_type", '"ZRS"'),
        ("is_hns_enabled", "false"),
        ("shared_access_key_enabled", "false"),
        ("default_to_oauth_authentication", "true"),
        ("allow_nested_items_to_be_public", "false"),
        ("min_tls_version", '"TLS1_2"'),
        ("https_traffic_only_enabled", "true"),
        ("versioning_enabled", "true"),
        ("default_action", '"Allow"'),
        ("container_access_type", '"private"'),
    ):
        assert re.search(rf"^\s*{key}\s+= {value}$", main, re.M), key
    policy = re.search(r"immutability_policy \{[^}]*\}", main, re.S).group(0)
    assert re.search(r'state\s+= "Unlocked"', policy)
    assert re.search(r"period_since_creation_in_days\s+= 1$", policy, re.M)
    assert '"Locked"' not in main
    assert "var.storage_account_name" in main


def test_no_soft_delete_retention_so_destroy_works_after_the_period():
    main = text("main.tf")
    assert "delete_retention_policy" not in main  # also covers container_delete_retention_policy
    assert "restore_policy" not in main


def test_the_resource_group_container_and_identity_are_the_probe_names():
    assert re.search(
        r'^\s*name\s+= "rg-hio-probe"$', _resource("azurerm_resource_group", "probe", "main.tf"), re.M
    )
    container = _resource("azurerm_storage_container", "probe", "main.tf")
    assert re.search(r'^\s*name\s+= "probe"$', container, re.M)
    assert "azurerm_storage_account.probe.id" in container
    identity = _resource("azurerm_user_assigned_identity", "probe", "identity.tf")
    assert re.search(r'^\s*name\s+= "id-hio-probe"$', identity, re.M)
    assert "azurerm_resource_group.probe.name" in identity


def test_the_federated_credential_uses_github_oidc_with_a_subject_variable():
    credential = _resource("azurerm_federated_identity_credential", "probe", "identity.tf")
    assert re.search(r'^\s*issuer\s+= "https://token\.actions\.githubusercontent\.com"$', credential, re.M)
    assert re.search(r'^\s*audience\s+= \["api://AzureADTokenExchange"\]$', credential, re.M)
    assert re.search(r"^\s*subject\s+= var\.github_oidc_subject$", credential, re.M)
    assert not re.search(r'subject\s+= "', all_tf())


def test_the_writer_role_can_create_and_read_but_not_write_or_delete():
    role = _resource("azurerm_role_definition", "probe_writer", "identity.tf")
    assert re.search(r'^\s*name\s+= "HIO probe writer \(create-only\)"$', role, re.M)
    actions = re.findall(r'"(Microsoft\.[^"]+)"', role)
    assert actions == [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action",
    ]
    assert not re.search(r"/(write|delete|move/action|runAsSuperUser/action)\b", role)
    assert "actions = []" in role  # no control-plane actions
    assert re.search(r"assignable_scopes\s+= \[azurerm_storage_account\.probe\.id\]", role)
    assert re.search(r"^\s*scope\s+= azurerm_storage_account\.probe\.id$", role, re.M)


def test_the_role_is_assigned_to_the_probe_identity_on_the_probe_container_only():
    identity = text("identity.tf")
    assignments = re.findall(r'resource "azurerm_role_assignment" "(\w+)"', identity)
    assert assignments == ["probe_writer"]
    assignment = _resource("azurerm_role_assignment", "probe_writer", "identity.tf")
    assert re.search(r"^\s*scope\s+= azurerm_storage_container\.probe\.id$", assignment, re.M)
    assert "azurerm_role_definition.probe_writer.role_definition_resource_id" in assignment
    assert "azurerm_user_assigned_identity.probe.principal_id" in assignment
    scopes = re.findall(r"^\s*scope\s+= (\S+)$", identity, re.M)
    assert set(scopes) <= {"azurerm_storage_account.probe.id", "azurerm_storage_container.probe.id"}


def test_owner_inputs_have_no_default():
    for name in ("subscription_id", "storage_account_name", "github_oidc_subject"):
        assert not re.search(r"^\s*default\s*=", _variable(name), re.M), name


def test_outputs_are_identifiers_only():
    outputs = text("outputs.tf")
    assert re.findall(r'output "(\w+)"', outputs) == [
        "storage_account_name",
        "container_name",
        "probe_identity_client_id",
    ]
    tf = all_tf()
    for forbidden in ("primary_access_key", "secondary_access_key", "connection_string", "sas_token"):
        assert forbidden not in tf, forbidden
    assert "sensitive" not in outputs and "key" not in outputs.lower().replace("client_id", "")


def test_nothing_is_shared_with_the_evidence_store_or_other_systems():
    tf = all_tf()
    assert "rg-hio-evidence" not in tf and "id-hio-capture" not in tf
    assert re.search(r"hnf|hedgehog|macsmsf|tigris", tf, re.I) is None
    names = re.findall(r'(?:name\s+=\s+)"([^"]+)"', tf)
    assert names and all("hio" in n.lower() or n in {"github-probe", "probe"} for n in names), names


def test_no_email_guid_or_github_numeric_id_is_committed_in_the_probe():
    for path in PROBE.iterdir():
        content = path.read_text()
        assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", content), path
        assert not re.search(GUID, content, re.I), path
        assert not re.search(r"@[0-9]{3,}", content), path  # <owner>@<id> in an immutable subject


def test_the_readme_describes_a_short_lived_module_applied_and_destroyed_only_under_b2():
    readme = (PROBE / "README.md").read_text()
    front = readme.split("---")[1]
    assert "id: HIO-INFRA-TOFU-PROBE" in front and "status: proposed" in front and "owner:" in front
    flat = " ".join(readme.split())
    assert "Short-lived" in flat
    assert "Authorisation B stage B-2" in flat
    assert "~/.hio-state/probe.tfstate" in flat
    assert "deletable one day after creation" in flat
    assert "Destroy afterwards" in flat


@pytest.mark.skipif(shutil.which("tofu") is None, reason="OpenTofu is not installed")
def test_the_probe_definitions_are_formatted():
    result = subprocess.run(
        ["tofu", "fmt", "-check", "-diff", str(PROBE)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
