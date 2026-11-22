"""Local results store: archive, verify and list, on a temporary git repository with invented data."""

import importlib.util
import json
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("results_store", REPO / "tools" / "results_store.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

NOW = datetime(2026, 11, 22, 3, 0, tzinfo=UTC)
FIRST = b"alpha,1\nbeta,2\n"
SECOND = b"alpha,1\nbeta,3\ngamma,4\n"
PATH = "results/invented.csv"


def git(repo, *args):
    cmd = ["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@example.invalid"]
    cmd += ["-c", "commit.gpgsign=false", *args]
    return subprocess.run(cmd, check=True, capture_output=True).stdout.decode().strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "results").mkdir(parents=True)
    git(root, "init", "-q")
    (root / PATH).write_bytes(FIRST)
    git(root, "add", PATH)
    git(root, "commit", "-q", "-m", "one")
    (root / PATH).write_bytes(SECOND)
    git(root, "commit", "-q", "-am", "two")
    return root


@pytest.fixture
def revs(repo):
    return git(repo, "rev-parse", "HEAD~1"), git(repo, "rev-parse", "HEAD")


@pytest.fixture
def store(tmp_path):
    return tmp_path / "store"


@pytest.fixture
def filled(repo, revs, store):
    tool.archive(store, "rec-1", [f"{PATH}@{revs[0]}", f"{PATH}@{revs[1]}"], repo=repo, now=NOW)
    return store


def test_archive_stores_both_revisions_byte_exactly(repo, revs, store):
    out = tool.archive(store, "rec-1", [f"{PATH}@{revs[0]}", f"{PATH}@HEAD"], note="n", repo=repo, now=NOW)
    assert [e["status"] for e in out] == ["stored", "stored"]
    assert (store / "records" / "rec-1" / revs[0][:12] / "invented.csv").read_bytes() == FIRST
    assert (store / "records" / "rec-1" / revs[1][:12] / "invented.csv").read_bytes() == SECOND
    entries = json.loads((store / "manifest.json").read_text())["entries"]
    assert {e["revision"] for e in entries} == set(revs)
    assert all(e["note"] == "n" and e["archived_at"].startswith("2026-11-22T03:00:00") for e in entries)
    assert all(len(e["blob"]) == 40 for e in entries)


def test_manifest_and_catalogue_agree(filled):
    entries = json.loads((filled / "manifest.json").read_text())["entries"]
    con = duckdb.connect(str(filled / "catalogue.duckdb"), read_only=True)
    rows = con.execute(f"SELECT {', '.join(tool.COLUMNS)} FROM records").fetchall()
    con.close()
    assert sorted(rows) == sorted(tuple(e[c] for c in tool.COLUMNS) for e in entries)
    assert entries == sorted(entries, key=lambda e: (e["record_id"], e["path"], e["revision"]))


def test_second_archive_changes_nothing(repo, revs, filled):
    before = (filled / "manifest.json").read_bytes()
    later = datetime(2027, 1, 1, tzinfo=UTC)
    out = tool.archive(filled, "rec-1", [f"{PATH}@{revs[0]}", f"{PATH}@{revs[1]}"], repo=repo, now=later)
    assert [e["status"] for e in out] == ["held", "held"]
    assert (filled / "manifest.json").read_bytes() == before
    assert len(tool.listing(filled)) == 2
    assert tool.verify(filled)["problems"] == []


def test_verify_passes(filled):
    result = tool.verify(filled)
    assert result == {"entries": 2, "files": 2, "problems": []}


def stored_file(store):
    return next((store / "records").rglob("invented.csv"))


def test_verify_detects_altered_file(filled):
    stored_file(filled).write_bytes(b"tampered")
    assert any("sha256" in p for p in tool.verify(filled)["problems"])


def test_verify_detects_deleted_file(filled):
    stored_file(filled).unlink()
    assert any("missing" in p for p in tool.verify(filled)["problems"])


def test_verify_detects_extra_file(filled):
    (filled / "records" / "rec-1" / "planted.txt").write_bytes(b"x")
    assert any("not listed" in p for p in tool.verify(filled)["problems"])


def test_verify_detects_wrong_manifest_sha(filled):
    path = filled / "manifest.json"
    data = json.loads(path.read_text())
    data["entries"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    assert tool.verify(filled)["problems"]


def test_verify_detects_catalogue_deleted_or_different(filled):
    cat = filled / "catalogue.duckdb"
    con = duckdb.connect(str(cat))
    con.execute("UPDATE records SET note = 'changed' WHERE revision = (SELECT min(revision) FROM records)")
    con.close()
    assert any("differ" in p for p in tool.verify(filled)["problems"])
    cat.unlink()
    assert any("missing" in p for p in tool.verify(filled)["problems"])


def test_store_inside_repository_refused(repo, revs):
    with pytest.raises(ValueError, match="outside"):
        tool.archive(repo / "store", "r", [f"{PATH}@{revs[0]}"], repo=repo)
    with pytest.raises(ValueError, match="outside"):
        tool.archive(repo, "r", [f"{PATH}@{revs[0]}"], repo=repo)


@pytest.mark.parametrize("record_id", ["", "-x", ".x", "a/b", "a b", "../x"])
def test_bad_record_id_refused(repo, revs, store, record_id):
    with pytest.raises(ValueError, match="record id"):
        tool.archive(store, record_id, [f"{PATH}@{revs[0]}"], repo=repo)


@pytest.mark.parametrize("path", ["../x", "a/../x", "/etc/passwd", "missing.csv", "results"])
def test_bad_path_refused(repo, revs, store, path):
    with pytest.raises(ValueError):
        tool.archive(store, "r", [f"{path}@{revs[0]}"], repo=repo)
    assert not store.exists()


def test_unknown_revision_refused(repo, store):
    with pytest.raises(ValueError, match="does not resolve"):
        tool.archive(store, "r", [f"{PATH}@nosuchrev"], repo=repo)
    with pytest.raises(ValueError, match="bad revision"):
        tool.archive(store, "r", [f"{PATH}@--all"], repo=repo)


def test_source_given_twice_refused(repo, revs, store):
    with pytest.raises(ValueError, match="twice"):
        tool.archive(store, "r", [f"{PATH}@{revs[1]}", f"{PATH}@HEAD"], repo=repo)
    assert not store.exists()


def test_same_key_with_different_stored_bytes_refused(repo, revs, filled):
    stored_file(filled).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="does not match"):
        tool.archive(filled, "rec-1", [f"{PATH}@{revs[0]}", f"{PATH}@{revs[1]}"], repo=repo)
    assert stored_file(filled).read_bytes() == b"tampered"


def test_same_key_with_different_manifest_sha_refused(repo, revs, filled):
    path = filled / "manifest.json"
    data = json.loads(path.read_text())
    for entry in data["entries"]:
        entry["sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="different bytes"):
        tool.archive(filled, "rec-1", [f"{PATH}@{revs[0]}"], repo=repo)


def test_file_exists_outside_manifest_refused(repo, revs, store):
    target = store / "records" / "r" / revs[0][:12]
    target.mkdir(parents=True)
    (target / "invented.csv").write_bytes(b"x")
    with pytest.raises(ValueError, match="outside the manifest"):
        tool.archive(store, "r", [f"{PATH}@{revs[0]}"], repo=repo)
    assert (target / "invented.csv").read_bytes() == b"x"


def test_modes(filled):
    for path in [filled / "manifest.json", filled / "catalogue.duckdb", *filled.rglob("invented.csv")]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, path
    for path in [filled, filled / "records", *(p for p in (filled / "records").rglob("*") if p.is_dir())]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o700, path


def test_cli_exit_codes_and_list_prints_no_content(repo, revs, store, capsys):
    args = ["archive", "--store", str(store), "--record-id", "r", "--source", f"{PATH}@{revs[0]}"]
    args += ["--repo", str(repo)]
    assert tool.main([*args, "--note", "n"]) == 0
    assert "stored r" in capsys.readouterr().out
    assert tool.main(["verify", "--store", str(store)]) == 0
    assert tool.main(["list", "--store", str(store)]) == 0
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.startswith("r ")]
    assert len(lines) == 1
    fields = lines[0].split()
    assert fields[:3] == ["r", PATH, revs[0][:12]] and len(fields[3]) == 64
    assert "alpha" not in out and "beta" not in out
    bad = ["archive", "--store", str(store), "--record-id", "!bad", "--source", f"{PATH}@{revs[0]}"]
    bad += ["--repo", str(repo)]
    assert tool.main(bad) == 2
    stored_file(store).write_bytes(b"tampered")
    assert tool.main(["verify", "--store", str(store)]) == 2
    assert "sha256" in capsys.readouterr().err
