"""T-0014 P-3: rehearsing state restoration with DUMMY state in an isolated directory.

Nothing here runs an infrastructure command or applies anything: the rehearsal reads and writes one file."""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from hio.contracts.canonical import canonical_json, sha256_hex
from tests.test_t0014_recovery import REPO, restore_exercise


def backup(tmp_path: Path, state: dict | None = None) -> tuple[Path, str]:
    raw = canonical_json(state if state is not None else restore_exercise.dummy_state(serial=7))
    path = tmp_path / "backup.json"
    path.write_bytes(raw)
    return path, sha256_hex(raw)


def test_dummy_state_is_restored_into_an_isolated_directory(tmp_path):
    path, digest = backup(tmp_path)
    out = restore_exercise.rehearse_state_restore(path, digest, tmp_path / "isolated")
    assert out["ok"] and out["identical"] and out["serial"] == 7 and out["infrastructure_applied"] is False
    restored = tmp_path / "isolated" / restore_exercise.STATE_FILE
    assert restored.read_bytes() == path.read_bytes() and (restored.stat().st_mode & 0o777) == 0o600
    assert sorted(p.name for p in (tmp_path / "isolated").iterdir()) == [restore_exercise.STATE_FILE]


def test_state_without_the_dummy_marker_is_refused(tmp_path):
    real_looking = {**restore_exercise.dummy_state(), restore_exercise.DUMMY_MARKER: False}
    path, digest = backup(tmp_path, real_looking)
    with pytest.raises(restore_exercise.ExerciseError, match="only dummy state"):
        restore_exercise.rehearse_state_restore(path, digest, tmp_path / "isolated")
    assert not (tmp_path / "isolated").exists()
    unmarked = {k: v for k, v in restore_exercise.dummy_state().items() if k != restore_exercise.DUMMY_MARKER}
    path, digest = backup(tmp_path, unmarked)
    with pytest.raises(restore_exercise.ExerciseError, match="only dummy state"):
        restore_exercise.rehearse_state_restore(path, digest, tmp_path / "isolated")


def test_a_backup_that_does_not_match_its_recorded_hash_is_refused(tmp_path):
    path, _ = backup(tmp_path)
    with pytest.raises(restore_exercise.ExerciseError, match="recorded hash"):
        restore_exercise.rehearse_state_restore(path, "0" * 64, tmp_path / "isolated")
    assert not (tmp_path / "isolated").exists()


def test_a_directory_inside_the_repository_or_not_empty_is_refused(tmp_path):
    path, digest = backup(tmp_path)
    with pytest.raises(restore_exercise.ExerciseError, match="outside this repository"):
        restore_exercise.rehearse_state_restore(path, digest, REPO / "infra" / "rehearsal-should-not-exist")
    assert not (REPO / "infra" / "rehearsal-should-not-exist").exists()
    busy = tmp_path / "busy"
    busy.mkdir()
    (busy / "main.tf").write_text("# infrastructure code")
    with pytest.raises(restore_exercise.ExerciseError, match="must be empty"):
        restore_exercise.rehearse_state_restore(path, digest, busy)
    assert [p.name for p in busy.iterdir()] == ["main.tf"]


def test_a_second_rehearsal_into_the_same_directory_is_refused(tmp_path):
    path, digest = backup(tmp_path)
    restore_exercise.rehearse_state_restore(path, digest, tmp_path / "isolated")
    with pytest.raises(restore_exercise.ExerciseError, match="must be empty"):
        restore_exercise.rehearse_state_restore(path, digest, tmp_path / "isolated")


def test_the_rehearsal_runs_no_infrastructure_command():
    source = Path(restore_exercise.__file__).read_text()
    assert not re.search(r"\bsubprocess\b|os\.system|os\.exec|os\.spawn|\bPopen\b", source)
    body = inspect.getsource(restore_exercise.rehearse_state_restore)
    assert not re.search(r"\b(tofu|terraform)\s+(init|plan|apply)\b", body)


def test_the_command_line_rehearses_dummy_state(tmp_path, capsys):
    out = tmp_path / "dummy.json"
    assert restore_exercise.main(["dummy-state", "--out", str(out)]) == 0
    digest = json.loads(capsys.readouterr().out)["sha256"]
    assert sha256_hex(out.read_bytes()) == digest
    args = ["state", "--backup", str(out), "--sha256", digest, "--into", str(tmp_path / "isolated")]
    assert restore_exercise.main(args) == 0
    assert json.loads(capsys.readouterr().out)["infrastructure_applied"] is False
    assert restore_exercise.main(args) == 2  # the directory is no longer empty
