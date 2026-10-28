"""Tests for the scripted assignment tool (harness-0.9 H6; operating model §6.2 step 1).

README content is synthetic; ancestry checks use throwaway git repositories.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assign = load("hio_assign")

A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40

HEADER = "| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |"
ROW_1 = (
    f"| REVIEW-X-1 | `elusivenode/hio` | `{A}` | `{B}` | Review: first scope. "
    "Review branch `review/REVIEW-X-1-codex`. Reviewer: codex | OD-0001 | **received** at `abc` |"
)
ROW_2 = (
    f"| REVIEW-X-2 | `elusivenode/hio` | `{A}` | `{C}` | Review: old scope. "
    "Review branch `review/REVIEW-X-2-codex`. Reviewer: codex | OD-0002 | "
    "**not received; superseded** by X-3 |"
)
README = f"""# HIO review index

## Assigned reviews (owner-assigned)

{HEADER}
|---|---|---|---|---|---|---|
{ROW_1}
{ROW_2}

## Candidate review targets (NOT assigned)

| Candidate | Repository |
|---|---|
| none | none |

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| REVIEW-OLD-9 | something | `aaa..bbb` | Codex | **READY** | [record](records/x.md) |
"""


@pytest.fixture
def readme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "reviews" / "README.md"
    path.parent.mkdir()
    path.write_text(README)
    return path


def run(readme, *extra, review_id="REVIEW-N-1", base=A, head=D, scope=("the scope",)):
    argv = ["--review-id", review_id, "--repo", "elusivenode/hio", "--base", base, "--head", head]
    for s in scope:
        argv += ["--scope", s]
    return assign.main([*argv, "--readme", str(readme), *extra])


EXPECTED_ROW = (
    f"| REVIEW-N-1 | `elusivenode/hio` | `{A}` | `{D}` | Review: the scope; second scope. "
    "Review branch `review/REVIEW-N-1-codex`. Reviewer: codex | "
    "OD-0099 (owner instruction, transcribed) | assigned |"
)

EXPECTED_MESSAGE = f"""\
Review assignment: REVIEW-N-1 (review)

Repository: elusivenode/hio
Base: {A}
Head: {D}
Scope:
- the scope
- second scope
Review branch: review/REVIEW-N-1-codex
Reviewer: codex

Delivery rules (operating model §6.2 steps 1 to 3):
- Work in your own worktree, on the review branch cut at the head above:
  git worktree add ../hio-REVIEW-N-1 {D} -b review/REVIEW-N-1-codex
- Write only .md files under reviews/. Never edit the work under review, STATUS.md or handoffs/.
  No merge commits.
- Push the review branch review/REVIEW-N-1-codex. Open no pull request: an unpushed branch has not been
  submitted.
- Your final message is your independent report. State the pushed branch, the branch tip SHA,
  the reviewed head ({D}) and the sha256 of every file you added. The receiver reconciles
  against it.
- If this assignment conflicts with another owner-authored source, stop before reviewing and
  report the conflict.
"""

HAPPY = ("--od", "OD-0099")
SCOPES = ("the scope", "second scope")


def test_happy_path_prints_exact_row_and_message_and_writes_nothing(readme, capsys):
    assert run(readme, *HAPPY, scope=SCOPES) == 0
    out = capsys.readouterr().out
    assert EXPECTED_ROW + "\n" in out
    assert EXPECTED_MESSAGE in out
    assert readme.read_text() == README


def test_row_has_the_column_count_of_the_table(readme, capsys):
    run(readme, *HAPPY, scope=SCOPES)
    out = capsys.readouterr().out
    assert len(assign.cells(EXPECTED_ROW)) == len(assign.cells(README.splitlines()[4])) == 7
    assert EXPECTED_ROW in out


def test_od_link_when_the_record_exists(readme):
    owner = readme.parent.parent / "docs" / "decisions" / "owner"
    owner.mkdir(parents=True)
    (owner / "OD-0099-something.md").write_text("x")
    row = assign.build_row(
        assign.argparse.Namespace(
            review_id="R", repo="r", base=A, head=D, scope=["s"], branch="b",
            reviewer="codex", kind="verify", od="OD-0099",
        ),
        owner,
    )
    assert "[OD-0099](../docs/decisions/owner/OD-0099-something.md)" in row
    assert "Verification: s. Review branch `b`. Reviewer: codex" in row


def test_verify_kind_changes_message_heading(readme, capsys):
    assert run(readme, "--kind", "verify", "--reviewer", "codex") == 0
    assert "Review assignment: REVIEW-N-1 (verification)" in capsys.readouterr().out


def test_apply_inserts_after_last_assigned_row_only(readme, capsys):
    assert run(readme, *HAPPY, "--apply", scope=SCOPES) == 0
    lines = readme.read_text().splitlines()
    original = README.splitlines()
    idx = lines.index(EXPECTED_ROW)
    assert lines[idx - 1] == original[idx - 1]
    assert lines[idx + 1] == ""
    assert lines[:idx] + lines[idx + 1 :] == original
    assert "APPLIED" in capsys.readouterr().err


def test_apply_twice_is_refused_and_leaves_one_row(readme, capsys):
    assert run(readme, *HAPPY, "--apply", scope=SCOPES) == 0
    after_first = readme.read_text()
    assert run(readme, *HAPPY, "--apply", scope=SCOPES) == 1
    assert readme.read_text() == after_first
    assert after_first.count("| REVIEW-N-1 |") == 1
    assert "already assigned or recorded" in capsys.readouterr().err


@pytest.mark.parametrize("existing", ["REVIEW-X-1", "REVIEW-OLD-9"])
def test_duplicate_id_in_either_table_is_refused(readme, capsys, existing):
    assert run(readme, "--apply", review_id=existing) == 1
    assert "already assigned or recorded" in capsys.readouterr().err
    assert readme.read_text() == README


def test_duplicate_id_with_a_record_file_is_refused(readme, capsys):
    (readme.parent / "records").mkdir()
    (readme.parent / "records" / "REVIEW-N-1.md").write_text("x")
    assert run(readme) == 1
    assert "already has a record" in capsys.readouterr().err


def test_same_head_different_scope_is_refused(readme, capsys):
    assert run(readme, "--apply", head=B, scope=("another scope",)) == 1
    err = capsys.readouterr().err
    assert "conflicting channels" in err and "REVIEW-X-1" in err
    assert readme.read_text() == README


def test_same_head_same_scope_is_not_a_conflict(readme):
    assert run(readme, head=B, scope=("first scope",)) == 0


def test_superseded_assignment_does_not_block_its_head(readme):
    assert run(readme, head=C, scope=("a different scope",)) == 0


@pytest.mark.parametrize("bad", ["abc1234", "A" * 40, "g" * 40, "a" * 41, ""])
@pytest.mark.parametrize("field", ["base", "head"])
def test_malformed_sha_is_refused(readme, capsys, field, bad):
    kwargs = {field: bad}
    assert run(readme, "--apply", **kwargs) == 1
    assert "40-character" in capsys.readouterr().err
    assert readme.read_text() == README


def test_pipe_in_scope_is_refused(readme, capsys):
    assert run(readme, scope=("a | b",)) == 1
    assert "table cell" in capsys.readouterr().err


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


def make_repo(root):
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "test")
    git(root, "config", "commit.gpgsign", "false")

    def commit(name):
        (root / name).write_text(name)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", name)
        return git(root, "rev-parse", "HEAD")

    return commit


def test_head_descending_from_base_in_a_real_repo_is_accepted(readme, tmp_path, monkeypatch, capsys):
    root = tmp_path / "repo"
    root.mkdir()
    commit = make_repo(root)
    base = commit("one")
    head = commit("two")
    monkeypatch.chdir(root)
    assert run(readme, base=base, head=head) == 0
    assert "ancestry not checked" not in capsys.readouterr().err


def test_head_not_descending_from_base_is_refused(readme, tmp_path, monkeypatch, capsys):
    root = tmp_path / "repo"
    root.mkdir()
    commit = make_repo(root)
    root_commit = commit("one")
    base = commit("two")
    git(root, "checkout", "-q", "-b", "side", root_commit)
    head = commit("side")
    monkeypatch.chdir(root)
    assert run(readme, "--apply", base=base, head=head) == 1
    assert "not a descendant" in capsys.readouterr().err
    assert readme.read_text() == README


def test_real_index_parses_and_its_existing_ids_are_refused(tmp_path, monkeypatch, capsys):
    """Read-only: the committed index parses and ids it already holds are duplicates."""
    monkeypatch.chdir(tmp_path)
    real = REPO / "reviews" / "README.md"
    assert run(real, review_id="REVIEW-2026-10-18-a01") == 1
    assert "already assigned or recorded" in capsys.readouterr().err
    assert run(real, review_id="VERIFY-2026-10-28-t0009-1-3") == 1
    assert run(real, review_id="REVIEW-NEW-NOT-IN-INDEX") == 0


def test_commits_absent_from_the_repository_are_noted_not_refused(readme, capsys):
    assert run(readme) == 0
    assert "ancestry not checked" in capsys.readouterr().err
