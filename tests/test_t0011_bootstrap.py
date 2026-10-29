"""T-0011 I-2 (OD-0118): the OpenTofu state bootstrap is a separate root module with its own resource
group, and it encodes the state-store controls. Nothing is planned or applied here. The tests read the
.tf files as text and run `tofu fmt -check` (offline) if OpenTofu is installed."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TOFU = REPO / "infra" / "tofu"
BOOT = TOFU / "bootstrap"
GUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _code(source: str) -> str:
    """The definitions without comments: a comment may name what is excluded, a resource may not."""
    return "\n".join(re.sub(r"\s*#.*$", "", line) for line in source.splitlines())


def text(name: str) -> str:
    return _code((BOOT / name).read_text())


def all_tf() -> str:
    return "\n".join(_code(p.read_text()) for p in sorted(BOOT.glob("*.tf")))


def block(source: str, header: str) -> str:
    return re.search(rf"{re.escape(header)} \{{.*?\n\}}(?:\n|\Z)", source, re.S).group(0)


def test_the_state_account_encodes_the_required_controls():
    main = text("main.tf")
    for key, value in (
        ("account_kind", '"StorageV2"'),
        ("is_hns_enabled", "false"),
        ("shared_access_key_enabled", "false"),
        ("default_to_oauth_authentication", "true"),
        ("allow_nested_items_to_be_public", "false"),
        ("min_tls_version", '"TLS1_2"'),
        ("https_traffic_only_enabled", "true"),
        ("versioning_enabled", "true"),
        ("container_access_type", '"private"'),
    ):
        assert re.search(rf"^\s*{key}\s+= {value}$", main, re.M), key
    assert "shared_access_key_enabled       = true" not in main


def test_blob_and_container_soft_delete_are_30_days():
    main = text("main.tf")
    for header in ("delete_retention_policy", "container_delete_retention_policy"):
        assert re.search(rf"^\s*{header} \{{\s*days\s+= 30\s*\}}", main, re.M), header


def test_the_replication_default_is_zrs_and_the_namespace_is_flat():
    variables = text("variables.tf")
    repl = block(variables, 'variable "account_replication_type"')
    assert re.search(r'^\s*default\s+= "ZRS"$', repl, re.M)
    assert "account_replication_type = var.account_replication_type" in text("main.tf")


def test_the_state_container_is_private_and_named_tfstate():
    container = block(text("main.tf"), 'resource "azurerm_storage_container" "tfstate"')
    assert re.search(r'^\s*name\s+= "tfstate"$', container, re.M)
    assert re.search(r'^\s*container_access_type\s+= "private"$', container, re.M)
    assert "blob" not in re.sub(r"container_access_type.*|azurerm_storage_container", "", container)


def test_the_role_is_scoped_to_the_container_only():
    main = text("main.tf")
    assignments = re.findall(r'resource "azurerm_role_assignment" "(\w+)"', main)
    assert assignments == ["state_admin"]
    role = block(main, 'resource "azurerm_role_assignment" "state_admin"')
    assert re.search(r"^\s*scope\s+= azurerm_storage_container\.tfstate\.id$", role, re.M)
    assert re.search(r'^\s*role_definition_name\s+= "Storage Blob Data Contributor"$', role, re.M)
    assert re.search(r"^\s*principal_id\s+= var\.state_admin_principal_object_id$", role, re.M)
    scopes = re.findall(r"^\s*scope\s+= (\S+)$", all_tf(), re.M)
    assert scopes == ["azurerm_storage_container.tfstate.id"]


def test_the_bootstrap_has_its_own_resource_group_apart_from_the_evidence_store():
    boot_main = text("main.tf")
    evidence_main = _code((TOFU / "main.tf").read_text())
    boot_rg = re.findall(r'resource "azurerm_resource_group" "\w+" \{\s*name\s+= "([^"]+)"', boot_main)
    evidence_rg = re.findall(
        r'resource "azurerm_resource_group" "\w+" \{\s*name\s+= "([^"]+)"', evidence_main
    )
    assert boot_rg == ["rg-hio-tfstate"]
    assert evidence_rg == ["rg-hio-evidence"]
    assert set(boot_rg).isdisjoint(evidence_rg)
    assert "rg-hio-evidence" not in all_tf()
    assert "azurerm_storage_account.evidence" not in all_tf()
    # A separate root module: it declares its own provider rather than sharing infra/tofu's.
    assert 'provider "azurerm"' in text("versions.tf")


def test_versions_match_the_main_module_and_there_is_no_backend_block():
    boot, main = text("versions.tf"), _code((TOFU / "versions.tf").read_text())
    assert 'required_version = ">= 1.8.0"' in boot
    assert 'version = "~> 4.0"' in boot and 'source  = "hashicorp/azurerm"' in boot
    assert re.search(r"^\s*storage_use_azuread\s+= true$", boot, re.M)
    assert re.search(r"^\s*subscription_id\s+= var\.subscription_id$", boot, re.M)
    for fragment in ('required_version = ">= 1.8.0"', 'version = "~> 4.0"'):
        assert fragment in main
    backend_block = r'^\s*backend\s+"'
    assert not re.search(backend_block, all_tf(), re.M)  # local state, kept outside the repository
    assert not re.search(backend_block, main, re.M)  # the main module is out of this contract


def test_no_identifier_or_guid_is_committed_and_required_inputs_have_no_default():
    for path in sorted(BOOT.iterdir()):
        content = path.read_text()
        assert not re.search(GUID, content, re.I), path.name
        if path.suffix == ".tf":
            assert not re.search(r"hnf|hedgehog|macsmsf|tigris", _code(content), re.I), path.name
    variables = text("variables.tf")
    for name in ("subscription_id", "state_admin_principal_object_id", "storage_account_name"):
        body = block(variables, f'variable "{name}"')
        assert not re.search(r"^\s*default\s*=", body, re.M), name
    assert not re.search(r"tenant_id|client_id|client_secret", all_tf())


def test_no_static_credential_and_outputs_carry_only_backend_names():
    tf = all_tf()
    for forbidden in (
        "primary_access_key",
        "secondary_access_key",
        "connection_string",
        "sas_token",
        "access_key =",
    ):
        assert forbidden not in tf, forbidden
    outputs = text("outputs.tf")
    assert re.findall(r'output "(\w+)"', outputs) == [
        "resource_group_name",
        "storage_account_name",
        "container_name",
    ]
    assert "key" not in outputs.lower() and "sensitive" not in outputs
    assert "principal" not in outputs and "subscription" not in outputs


def test_no_state_plan_variables_or_lock_file_in_the_bootstrap_directory():
    bad = [
        p.name
        for p in BOOT.rglob("*")
        if re.search(r"\.tfstate|\.tfplan|\.tfvars|\.terraform", str(p.relative_to(BOOT)))
    ]
    assert bad == []
    # The provider lock file is generated by the orchestrator, not authored here.
    names = {p.name for p in BOOT.iterdir() if p.is_file()} - {".terraform.lock.hcl"}
    assert names == {"README.md", "main.tf", "outputs.tf", "variables.tf", "versions.tf"}


def test_the_readme_declares_its_front_matter_and_the_runbook():
    readme = (BOOT / "README.md").read_text()
    front = readme.split("---")[1]
    assert re.search(r"^id: HIO-INFRA-TOFU-BOOTSTRAP$", front, re.M)
    assert re.search(r"^status: proposed$", front, re.M)
    assert re.search(r"^owner: \S", front, re.M)
    for needle in (
        "Authorisation B",
        "outside the repository",
        "-backend-config",
        "use_azuread_auth = true",
        "-migrate-state",
        "never committed",
        "evidence store",
    ):
        assert needle in readme, needle


@pytest.mark.skipif(shutil.which("tofu") is None, reason="OpenTofu is not installed")
def test_the_bootstrap_is_formatted():
    result = subprocess.run(
        ["tofu", "fmt", "-check", "-diff", str(BOOT)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
