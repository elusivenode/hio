"""Independence and boundaries (S1-A1, S1-A2, OBS-INV-005 lint).

The checks themselves live in tools/check_repo.py and run in CI; these tests prove that they
pass on the repository and that deliberate violations fail.
"""

import importlib.util
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def check_repo(monkeypatch):
    spec = importlib.util.spec_from_file_location("check_repo", REPO / "tools" / "check_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "errors", [])
    return module


def test_repository_passes_the_import_and_valid_time_rules(check_repo):
    files = check_repo.tracked_files()
    check_repo.check_imports(files)
    check_repo.check_valid_time(files)
    assert check_repo.errors == []


def test_deliberate_violations_fail(check_repo, tmp_path, monkeypatch):
    bad = {
        "src/hio/library/leak.py": "from hio.storage.objectstore import LocalObjectStore\n",
        "src/hio/marketdata/net.py": "import urllib.request\n",
        "src/hio/models/smsf.py": "import macsmsf\n",
        "src/hio/marketdata/when.py": "def f(t):\n    return t.astimezone().date()\n",
        "src/hio/newpkg/x.py": "x = 1\n",
    }
    for path, text in bad.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text)
    monkeypatch.setattr(check_repo, "ROOT", tmp_path)
    check_repo.check_imports(list(bad))
    check_repo.check_valid_time(list(bad))
    joined = "\n".join(check_repo.errors)
    assert "hio.library may not import hio.storage" in joined
    assert "forbidden import urllib.request" in joined
    assert "forbidden import macsmsf" in joined
    assert ".date() on an instant" in joined
    assert "hio.newpkg has no declared import rule" in joined


def test_no_macsmsf_dependency_in_the_lockfile_or_project():
    lock = tomllib.loads((REPO / "uv.lock").read_text())
    names = {p["name"] for p in lock["package"]}
    assert not any("macsmsf" in n for n in names)
    project = tomllib.loads((REPO / "pyproject.toml").read_text())
    assert not any("macsmsf" in d for d in project["project"]["dependencies"])
