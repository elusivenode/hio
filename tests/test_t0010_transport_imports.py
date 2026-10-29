"""T-0010 W-1: the check_repo amendment (OD-0115). Network modules are allowed only in
src/hio/sources/http_transport.py; `macsmsf` and every other module rule are unchanged.

Uses temporary trees under tmp_path; nothing is written to the repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ALLOWED = "src/hio/sources/http_transport.py"
NETWORK = ["socket", "ssl", "http.client", "urllib.request", "urllib3", "requests", "httpx", "aiohttp"]


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


@pytest.mark.parametrize("module", NETWORK)
def test_network_import_is_accepted_only_in_http_transport(check_repo, tmp_path, monkeypatch, module):
    ok = _run(check_repo, tmp_path, monkeypatch, {ALLOWED: f"import {module}\n"})
    assert ok == ""


@pytest.mark.parametrize("module", NETWORK)
@pytest.mark.parametrize(
    "path",
    [
        "src/hio/sources/run.py",
        "src/hio/sources/other_transport.py",
        "src/hio/marketdata/http_transport.py",  # the file name alone does not grant anything
        "src/hio/jobs/s1b.py",
        "src/hio/http_transport.py",
    ],
)
def test_network_import_is_refused_in_any_other_src_module(check_repo, tmp_path, monkeypatch, module, path):
    joined = _run(check_repo, tmp_path, monkeypatch, {path: f"import {module}\n"})
    assert f"forbidden import {module}" in joined


def test_from_import_form_is_also_refused_elsewhere_and_accepted_in_the_transport(
    check_repo, tmp_path, monkeypatch
):
    joined = _run(
        check_repo,
        tmp_path,
        monkeypatch,
        {
            ALLOWED: "from urllib.parse import urljoin\nfrom http.client import HTTPSConnection\n",
            "src/hio/sources/run.py": "from urllib.parse import urljoin\n",
        },
    )
    assert "src/hio/sources/run.py:1: forbidden import urllib.parse" in joined
    assert ALLOWED not in joined


@pytest.mark.parametrize("module", ["macsmsf", "macsmsf.db", "ftplib", "smtplib"])
def test_other_forbidden_modules_stay_forbidden_even_in_http_transport(
    check_repo, tmp_path, monkeypatch, module
):
    joined = _run(check_repo, tmp_path, monkeypatch, {ALLOWED: f"import {module}\n"})
    assert f"forbidden import {module}" in joined


def test_http_transport_is_still_subject_to_the_architecture_import_rules(check_repo, tmp_path, monkeypatch):
    joined = _run(check_repo, tmp_path, monkeypatch, {ALLOWED: "import socket\nfrom hio.jobs import s1a\n"})
    assert "hio.sources may not import hio.jobs" in joined
    assert "forbidden import socket" not in joined


def test_the_repository_itself_passes_the_import_rule(check_repo):
    check_repo.check_imports(check_repo.tracked_files())
    assert check_repo.errors == []
