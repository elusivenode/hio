"""T-0010 W-2: the check_repo amendment (OD-0117 decision 4). The Azure SDK (`azure.*`) may be imported
only in src/hio/storage/azure_blob.py and src/hio/storage/azure_auth.py; the network allowance for
src/hio/sources/http_transport.py is unchanged, and azure_blob.py gains no network allowance.

Uses temporary trees under tmp_path; nothing is written to the repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BLOB = "src/hio/storage/azure_blob.py"
AUTH = "src/hio/storage/azure_auth.py"
TRANSPORT = "src/hio/sources/http_transport.py"
AZURE = ["azure", "azure.core", "azure.identity", "azure.storage.blob"]


@pytest.fixture
def check_repo(monkeypatch):
    spec = importlib.util.spec_from_file_location("check_repo", REPO / "tools" / "check_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "errors", [])
    return module


def _run(check_repo, tmp_path, monkeypatch, files: dict[str, str]) -> str:
    for path, text in files.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    check_repo.check_imports(list(files))
    return "\n".join(check_repo.errors)


@pytest.mark.parametrize("module", AZURE)
@pytest.mark.parametrize("path", [BLOB, AUTH])
def test_azure_import_is_accepted_in_the_two_authorised_storage_modules(
    check_repo, tmp_path, monkeypatch, module, path
):
    assert _run(check_repo, tmp_path, monkeypatch, {path: f"import {module}\n"}) == ""


@pytest.mark.parametrize("module", AZURE)
@pytest.mark.parametrize(
    "path",
    [
        "src/hio/storage/blobstore.py",
        "src/hio/storage/fakeblob.py",
        "src/hio/storage/objectstore.py",
        "src/hio/storage/azure_other.py",
        "src/hio/storage/azure_blob_extra.py",
        "src/hio/sources/azure_blob.py",  # the file name alone grants nothing
        "src/hio/marketdata/azure_auth.py",
        "src/hio/sources/run.py",
        "src/hio/sources/http_transport.py",
        "src/hio/jobs/s1b.py",
        "src/hio/azure_blob.py",
    ],
)
def test_azure_import_is_refused_anywhere_else_in_src(check_repo, tmp_path, monkeypatch, module, path):
    joined = _run(check_repo, tmp_path, monkeypatch, {path: f"import {module}\n"})
    assert f"forbidden import {module}" in joined


def test_from_import_form_is_refused_elsewhere_and_accepted_in_the_modules(check_repo, tmp_path, monkeypatch):
    joined = _run(
        check_repo,
        tmp_path,
        monkeypatch,
        {
            BLOB: "from azure.storage.blob import ContainerClient\n",
            AUTH: "from azure.identity import ClientAssertionCredential\n",
            "src/hio/sources/run.py": "from azure.storage.blob import ContainerClient\n",
            "src/hio/storage/blobstore.py": "from azure.core.exceptions import HttpResponseError\n",
        },
    )
    assert "src/hio/sources/run.py:1: forbidden import azure.storage.blob" in joined
    assert "src/hio/storage/blobstore.py:1: forbidden import azure.core.exceptions" in joined
    assert BLOB not in joined and AUTH not in joined


def test_azure_blob_gets_no_network_allowance(check_repo, tmp_path, monkeypatch):
    joined = _run(check_repo, tmp_path, monkeypatch, {BLOB: "import http.client\nimport socket\n"})
    assert "forbidden import http.client" in joined and "forbidden import socket" in joined


def test_azure_auth_may_use_the_network_for_the_github_token_request(check_repo, tmp_path, monkeypatch):
    assert _run(check_repo, tmp_path, monkeypatch, {AUTH: "import http.client\nimport urllib.parse\n"}) == ""


def test_the_http_transport_allowance_is_unchanged(check_repo, tmp_path, monkeypatch):
    assert TRANSPORT in check_repo.NETWORK_ALLOWED_IN
    assert _run(check_repo, tmp_path, monkeypatch, {TRANSPORT: "import http.client\nimport ssl\n"}) == ""


@pytest.mark.parametrize("module", ["macsmsf", "macsmsf.db", "ftplib", "smtplib"])
@pytest.mark.parametrize("path", [BLOB, AUTH])
def test_other_forbidden_modules_stay_forbidden_in_the_azure_modules(
    check_repo, tmp_path, monkeypatch, module, path
):
    assert f"forbidden import {module}" in _run(
        check_repo, tmp_path, monkeypatch, {path: f"import {module}\n"}
    )


def test_the_azure_modules_are_still_subject_to_the_architecture_import_rules(
    check_repo, tmp_path, monkeypatch
):
    joined = _run(
        check_repo, tmp_path, monkeypatch, {BLOB: "import azure.core\nfrom hio.sources import run\n"}
    )
    assert "hio.storage may not import hio.sources" in joined
    assert "forbidden import azure" not in joined


def test_the_repository_itself_passes_the_import_rule(check_repo):
    check_repo.check_imports(check_repo.tracked_files())
    assert check_repo.errors == []
