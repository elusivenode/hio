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
    assert re.search(
        r'subject\s+= "repo:\$\{var\.github_repository\}:environment:\$\{var\.github_environment\}"', tf
    )
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
        "azurerm_storage_container.evidence.resource_manager_id",
    }


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
