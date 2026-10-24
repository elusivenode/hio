"""Negative tests for the reviewer-PR gate and assignment verification (harness-0.7 proposed).

Each test builds a throwaway git repository: a base commit holding the checking policy, an
author's reviewed head, and a reviewer branch. Adversarial branches must fail; a mismatched
Reviewed-Head or assignment must fail; the policy is always read from the trusted base commit.
"""

import importlib.util
import os
import shutil
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


gate = load("review_gate")
assignment = load("check_review_assignment")

RECORD = """---
id: REVIEW-T-1
reviewed_base: {base}
reviewed_head: {head}
assignment: owner direct assignment (test)
review_branch: review/t-1-codex
verdict: READY
---
# Review of T-0099 scope
"""


class Repo:
    base: str
    head: str

    def __init__(self, root: Path) -> None:
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "test")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, check=True
        ).stdout.strip()

    def write(self, path: str, text: str, mode: int | None = None) -> None:
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if mode is not None:
            os.chmod(p, mode)

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    r = Repo(tmp_path)
    (tmp_path / "tools").mkdir()
    for tool in ("check_review_branch.sh", "review_gate.py"):
        shutil.copy(REPO / "tools" / tool, tmp_path / "tools" / tool)
    r.write("reviews/README.md", "# index\n")
    r.write("reviews/records/REVIEW-OLD.md", "old\n")
    r.write("src/app.py", "x = 1\n")
    r.base = r.commit("base: policy")
    r.write("src/app.py", "x = 2\n")
    r.head = r.commit("author: reviewed head")
    r.git("checkout", "-q", "-b", "review/t-1-codex")
    return r


def add_record(r, base=None, head=None):
    r.write("reviews/records/REVIEW-T-1.md", RECORD.format(base=base or r.base, head=head or r.head))
    return r.commit("reviewer: record")


def run_gate(r, pr_head, body):
    return gate.run(r.base, pr_head, body, r.root)


def body(sha):
    return f"Kind: reviewer evidence\r\nReviewed-Head: {sha}\r\n"


# --- the gate: content scope with policy from the base commit -----------------------------------


def test_a_clean_reviewer_branch_passes(repo):
    tip = add_record(repo)
    code, out = run_gate(repo, tip, body(repo.head))
    assert code == 0, out


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda r: r.write("src/app.py", "x = 3\n"), "path outside reviews/"),
        (lambda r: r.write("reviews/records/notes.txt", "x\n"), "not a .md file"),
        (lambda r: r.write("reviews/records/run.md", "x\n", 0o755), "mode 100755"),
        (lambda r: r.write("reviews/records/REVIEW-OLD.md", "rewritten\n"), "submitted record modified"),
        (lambda r: (r.root / "reviews/README.md").unlink(), "status D not allowed"),
        (lambda r: r.write(".github/workflows/x.yml", "on: push\n"), "path outside reviews/"),
    ],
)
def test_inappropriate_file_changes_fail(repo, change, expected):
    add_record(repo)
    change(repo)
    tip = repo.commit("reviewer: adversarial change")
    code, out = run_gate(repo, tip, body(repo.head))
    assert code != 0 and expected in out, out


def test_a_symlink_fails(repo):
    add_record(repo)
    (repo.root / "reviews/records/link.md").symlink_to("../README.md")
    tip = repo.commit("reviewer: symlink")
    code, out = run_gate(repo, tip, body(repo.head))
    assert code != 0 and "mode 120000" in out, out


def test_weakening_the_policy_in_the_pr_does_not_weaken_the_gate(repo):
    """The PR replaces the scope script with `exit 0` and edits src/; the gate still reads the
    base commit's script, so the change fails."""
    add_record(repo)
    repo.write("tools/check_review_branch.sh", "#!/bin/sh\nexit 0\n")
    repo.write("tools/review_gate.py", "raise SystemExit(0)\n")
    tip = repo.commit("reviewer: try to weaken the checks")
    code, out = run_gate(repo, tip, body(repo.head))
    assert code != 0 and "path outside reviews/: tools/check_review_branch.sh" in out, out


def test_a_merge_commit_on_the_review_branch_fails(repo):
    add_record(repo)
    repo.git("checkout", "-q", "-b", "side", repo.head)
    repo.write("reviews/records/REVIEW-SIDE.md", "side\n")
    repo.commit("side")
    repo.git("checkout", "-q", "review/t-1-codex")
    repo.git("merge", "-q", "--no-ff", "-m", "merge", "side")
    code, out = run_gate(repo, repo.git("rev-parse", "HEAD"), body(repo.head))
    assert code != 0 and "merge commits" in out, out


# --- mismatched or malformed Reviewed-Head ---------------------------------------------------------


def test_a_reviewed_head_naming_an_earlier_commit_pulls_author_changes_into_scope_and_fails(repo):
    tip = add_record(repo)
    code, out = run_gate(repo, tip, body(repo.base))  # the author's src change is now in the range
    assert code != 0 and "path outside reviews/: src/app.py" in out, out


def test_a_reviewed_head_the_branch_does_not_descend_from_fails(repo):
    tip = add_record(repo)
    repo.git("checkout", "-q", "-b", "elsewhere", repo.base)
    repo.write("src/other.py", "y = 1\n")
    unrelated = repo.commit("unrelated")
    code, out = run_gate(repo, tip, body(unrelated))
    assert code != 0 and "does not descend from the assigned head" in out, out


@pytest.mark.parametrize(
    "text",
    [
        "no head line here",
        "Reviewed-Head: abc123",
        "Reviewed-Head: " + "g" * 40,
        "Reviewed-Head: {a}\nReviewed-Head: {b}",
    ],
)
def test_missing_short_invalid_or_conflicting_reviewed_heads_stop(repo, text):
    tip = add_record(repo)
    with pytest.raises(gate.GateError):
        run_gate(repo, tip, text.format(a=repo.head, b=repo.base))


# --- assignment verification (separate from the scope check) ----------------------------------------


def verify(repo, **over):
    args = {
        "review_id": "REVIEW-T-1",
        "base": repo.base,
        "head": repo.head,
        "branch": "review/t-1-codex",
        "scope_terms": ["T-0099"],
    } | over
    cwd = os.getcwd()
    os.chdir(repo.root)
    try:
        return assignment.verify(**args)
    finally:
        os.chdir(cwd)


def test_assignment_verification_passes_when_the_record_matches(repo):
    add_record(repo)
    assert verify(repo) == []


def test_a_scope_clean_branch_reviewing_the_wrong_head_fails_assignment_verification(repo):
    """Scope check and assignment verification are different: this branch passes the gate (the
    record sits under reviews/) but its record names a head the owner did not assign."""
    tip = add_record(repo, head=repo.base)
    assert run_gate(repo, tip, body(repo.head))[0] == 0
    problems = verify(repo)
    assert any("reviewed_head" in p for p in problems), problems


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"review_id": "REVIEW-T-2"}, "exactly one added record"),
        ({"head": "f" * 40}, "does not resolve"),
        ({"branch": "review/other"}, "does not resolve"),
        ({"base": "e" * 40}, "reviewed_base"),
        ({"scope_terms": ["T-0100"]}, "scope term"),
    ],
)
def test_assignment_mismatches_fail(repo, override, fragment):
    add_record(repo)
    assert any(fragment in p for p in verify(repo, **override))
