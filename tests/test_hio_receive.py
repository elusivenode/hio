"""Tests for the scripted evidence receipt (harness-0.9 H6; operating model §6.2 step 5.0 to 5.11).

Each test builds throwaway git repositories in a temp directory: a bare repository as "origin", an
author repository that pushes a base, a reviewed head and a reviewer branch, and a scratch clone in
which the receipt runs. No network and no real remote. `main`'s own scope and assignment checks are
copied into the throwaway repository, so the tool is tested against the real checks.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parent.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolves string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


hio = load("hio_receive")

OD = "OD-0099"
SOURCE = "docs/history/owner-assign-t-1.md"

CHECK_REPO_STUB = """\
import subprocess
import sys
from pathlib import Path

if sys.argv[1:2] == ["trailers"]:
    span = f"{sys.argv[2]}..{sys.argv[3]}"
    shas = subprocess.run(
        ["git", "rev-list", "--no-merges", span], capture_output=True, text=True, check=True
    ).stdout.split()
    bad = 0
    for sha in shas:
        msg = subprocess.run(["git", "log", "-1", "--format=%B", sha], capture_output=True, text=True).stdout
        if "\\nHIO-Actor: " not in "\\n" + msg:
            print(f"{sha[:7]}: no HIO-Actor trailer")
            bad = 1
    sys.exit(bad)
for p in Path("reviews").rglob("*.md"):
    if "CHECK-REPO-FAIL" in p.read_text():
        print(f"FAIL: {p}")
        sys.exit(1)
"""

README_BASE = """\
---
id: HIO-REVIEWS
---
# index

## Assigned reviews

| Review | Repository | Base SHA | Head SHA | Task / scope | Assigned by (OD / source) | Status |
|---|---|---|---|---|---|---|
| OLD-1 | `r` | `1111111` | `2222222` | s | x | **received** |

## Reviewed revisions and review records

| Review | Subject | Base..head | Reviewer | Verdict | Record |
|---|---|---|---|---|---|
| OLD-1 | s | `1111111..2222222` | Codex | **READY** | [record](records/REVIEW-OLD-1.md) |

## Verification rounds

| Verification | Original review | Base..submission head | Fix commit | Reviewer outcome | Record |
|---|---|---|---|---|---|

## Findings register

| Finding | From review | Severity | State | Remediation claim | Verification | Waiver (owner OD) |
|---|---|---|---|---|---|---|
| F-OLD-1-1 | OLD-1 | high | **remediation_claimed** | remediation_claimed: fix `abc1234` | — | — |
| F-OLD-1-2 | OLD-1 | medium | **open** | — | — | — |

States: `open`, `remediation_claimed`, `verified_closed`, `waived`.
"""

GITCONFIG = """\
[user]
\tname = test
\temail = t@example.invalid
[commit]
\tgpgsign = false
[tag]
\tgpgsign = false
[init]
\tdefaultBranch = main
[protocol "file"]
\tallow = always
"""

PRE_RECEIVE = """\
#!/bin/sh
if [ -e "$GIT_DIR/deny-main" ]; then
  while read old new ref; do
    [ "$ref" = refs/heads/main ] && { echo "main is locked" >&2; exit 1; }
  done
fi
exit 0
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def add_row(text: str, header_prefix: str, row: str) -> str:
    """Append a row to the table whose header line starts with header_prefix."""
    lines = text.split("\n")
    i = next(n for n, line in enumerate(lines) if line.startswith(header_prefix))
    while lines[i + 1].startswith("|"):
        i += 1
    lines.insert(i + 1, row)
    return "\n".join(lines)


def replace_line(text: str, prefix: str, new: str) -> str:
    return "\n".join(new if line.startswith(prefix) else line for line in text.split("\n"))


H_ASSIGNED = "| Review | Repository"
H_REVIEWED = "| Review | Subject"
H_ROUNDS = "| Verification | Original review"
H_FINDINGS = "| Finding |"


class World:
    """origin (bare), author repository, scratch clone and the reviewer's branch."""

    def __init__(
        self,
        tmp: Path,
        monkeypatch,
        capsys,
        *,
        kind: str = "review",
        readme_fn=None,
        extra=None,
        unreported=None,
        record_head: str | None = None,
        record_extra: str = "",
    ) -> None:
        self.kind, self.capsys = kind, capsys
        cfg = tmp / "gitconfig"
        cfg.write_text(GITCONFIG)
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
        monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
        self.tmp = tmp
        self.origin = tmp / "origin.git"
        self.author = tmp / "author"
        self.recv = tmp / "recv"
        git(tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        hook = self.origin / "hooks" / "pre-receive"
        hook.write_text(PRE_RECEIVE)
        hook.chmod(0o755)
        a = self.author
        a.mkdir()
        git(a, "init", "-q", "-b", "main")
        git(a, "remote", "add", "origin", str(self.origin))
        (a / "tools").mkdir()
        for tool in ("check_review_branch.sh", "check_review_assignment.py"):
            shutil.copy(REPO / "tools" / tool, a / "tools" / tool)
        (a / "tools" / "check_repo.py").write_text(CHECK_REPO_STUB)
        self.write(a, "reviews/README.md", README_BASE)
        self.write(a, "reviews/records/REVIEW-OLD-1.md", "old\n")
        self.base = self.commit("base")
        self.write(a, "docs/mid.md", "mid\n")
        self.mid = self.commit("mid")
        self.write(a, "docs/work.md", "work under review\n")
        self.head = self.commit("head")
        git(a, "push", "-q", "origin", "main")
        git(a, "checkout", "-q", "-b", "other", self.base)
        self.write(a, "docs/side.md", "side\n")
        self.other = self.commit("side")
        git(a, "push", "-q", "origin", "other")
        git(a, "checkout", "-q", "main")

        if kind == "review":
            self.rec_id, self.branch = "REVIEW-T-1", "review/t-1-codex"
        else:
            self.rec_id, self.branch = "VERIFY-T-2", "review/t-2-verify-codex"
        self.rec_path = f"reviews/records/{self.rec_id}.md"
        self.handoff_path = "reviews/handoffs/2026-10-28-t-1-codex.md"
        self.source = SOURCE
        b7, h7 = self.base[:7], self.head[:7]
        body = (
            "### F-REVIEW-T-1-1 — high, open: a thing\n\ndetail\n"
            if kind == "review"
            else "| F-OLD-1-1 | **verified_closed.** the fix holds |\n"
        )
        record = (
            f"---\nid: {self.rec_id}\nreviewer: codex/reviewer\nreviewed_base: {self.base}\n"
            f"reviewed_head: {record_head or self.head}\nassignment: {SOURCE}\nreview_branch: {self.branch}\n"
            f"verdict: READY\n---\n# Record\n\n{body}{record_extra}"
        )
        readme = README_BASE
        readme = add_row(
            readme,
            H_ASSIGNED,
            f"| {self.rec_id} | `r` | `{self.base}` | `{self.head}` | scope | [{SOURCE}](../{SOURCE}) (owner "
            "assignment) | **received**; verdict READY |",
        )
        if kind == "review":
            readme = add_row(
                readme,
                H_REVIEWED,
                f"| {self.rec_id} | subject | `{b7}..{h7}` | Codex | **READY** | "
                f"[record](records/{self.rec_id}.md) |",
            )
            readme = add_row(
                readme, H_FINDINGS, f"| F-REVIEW-T-1-1 | {self.rec_id} | high | **open** | — | — | — |"
            )
        else:
            readme = add_row(
                readme,
                H_ROUNDS,
                f"| {self.rec_id} | OLD-1, finding 1 | `{b7}..{h7}` | `abc1234` | "
                f"**F-OLD-1-1 verified_closed**; READY | [record](records/{self.rec_id}.md) |",
            )
            readme = replace_line(
                readme,
                "| F-OLD-1-1 |",
                f"| F-OLD-1-1 | OLD-1 | high | **verified_closed** at `{h7}` | "
                f"remediation_claimed: fix `abc1234` | "
                f"[{self.rec_id}](records/{self.rec_id}.md) at `{h7}` | — |",
            )
        if readme_fn is not None:
            readme = readme_fn(readme, self)
        self.files = {self.rec_path: record, self.handoff_path: "handoff\n", **(extra or {})}
        git(a, "checkout", "-q", "-b", self.branch, self.head)
        for path, text in self.files.items():
            self.write(a, path, text)
        self.write(a, "reviews/README.md", readme)
        for path, text in (unreported or {}).items():
            self.write(a, path, text)
        self.tip = self.commit("reviewer evidence")
        git(a, "push", "-q", "origin", self.branch)
        git(a, "checkout", "-q", "main")
        self.report = {
            "branch_tip": self.tip,
            "files": {p: hashlib.sha256(t.encode()).hexdigest() for p, t in self.files.items()},
            "supplied_by": "Codex final message, relayed by the owner (test)",
        }
        self.report_path = tmp / "report.json"
        self.write_report()
        git(tmp, "clone", "-q", str(self.origin), str(self.recv))
        monkeypatch.chdir(self.recv)

    # --- builders ------------------------------------------------------------------------------

    @staticmethod
    def write(root: Path, path: str, text: str) -> None:
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self, msg: str) -> str:
        git(self.author, "add", "-A")
        git(self.author, "commit", "-q", "-m", msg)
        return git(self.author, "rev-parse", "HEAD")

    def write_report(self) -> None:
        self.report_path.write_text(json.dumps(self.report))

    def author_commit_on(self, branch: str, path: str, text: str) -> str:
        git(self.author, "checkout", "-q", branch)
        self.write(self.author, path, text)
        sha = self.commit(f"more on {branch}")
        git(self.author, "push", "-q", "origin", branch)
        git(self.author, "checkout", "-q", "main")
        return sha

    def origin_ref(self, ref: str) -> str | None:
        p = subprocess.run(
            ["git", "--git-dir", str(self.origin), "rev-parse", "-q", "--verify", ref],
            capture_output=True,
            text=True,
        )
        return p.stdout.strip() or None

    def origin_git(self, *args: str) -> str:
        return git(self.tmp, "--git-dir", str(self.origin), *args)

    def run(self, *, publish: bool = False, hooks=None, **over):
        vals = {
            "--review-id": self.rec_id,
            "--base": self.base,
            "--head": self.head,
            "--branch": self.branch,
            "--assignment-source": self.source,
            "--report": str(self.report_path),
            "--second-assignment-checked": "Assigned reviews table and the PR comments: no second assignment",
            "--od": OD,
        }
        vals.update({"--" + k.replace("_", "-"): v for k, v in over.items()})
        argv: list[str] = []
        for k, v in vals.items():
            if v is not None:
                argv += [k, *v] if isinstance(v, list) else [k, v]
        if publish:
            argv.append("--publish")
        code = hio.receive(argv, hooks=hooks)
        cap = self.capsys.readouterr()
        return SimpleNamespace(code=code, out=cap.out, err=cap.err)


@pytest.fixture
def make_world(tmp_path, monkeypatch, capsys):
    def make(**kw) -> World:
        return World(tmp_path, monkeypatch, capsys, **kw)

    return make


def received_main(w: World) -> str:
    return w.origin_ref("refs/heads/main") or ""


# --- 5.0 inputs ---------------------------------------------------------------------------------


def test_missing_5_0_inputs_stop(make_world):
    w = make_world()
    r = w.run(second_assignment_checked="  ")
    assert r.code == 1 and "5.0" in r.err and "second-assignment-checked" in r.err
    r = w.run(report=str(w.tmp / "nope.json"))
    assert r.code == 1 and "5.0.2" in r.err and "absent" in r.err
    r = w.run(assignment_source="")
    assert r.code == 1 and "assignment-source" in r.err
    r = w.run(publish=True, od=None)
    assert r.code == 1 and "--od" in r.err
    assert w.origin_ref(f"refs/tags/reviews/{w.rec_id}") is None


def test_report_must_not_come_from_the_repository(make_world):
    w = make_world()
    inside = w.recv / "report.json"
    shutil.copy(w.report_path, inside)
    r = w.run(report=str(inside))
    assert r.code == 1 and "inside the repository" in r.err


def test_report_shape_is_validated(make_world):
    w = make_world()
    w.report["files"][w.rec_path] = "nothex"
    w.write_report()
    r = w.run()
    assert r.code == 1 and "malformed sha256" in r.err
    w.report["files"][w.rec_path] = "0" * 64
    del w.report["supplied_by"]
    w.write_report()
    assert "supplied_by" in w.run().err


def test_receipt_runs_only_on_a_clean_main(make_world):
    w = make_world()
    git(w.recv, "checkout", "-q", "-b", "side")
    r = w.run()
    assert r.code == 1 and "clean `main`" in r.err
    git(w.recv, "checkout", "-q", "main")
    (w.recv / "stray.txt").write_text("x")
    r = w.run()
    assert r.code == 1 and "not clean" in r.err


# --- dry run and the full receipt ---------------------------------------------------------------


def test_dry_run_checks_everything_and_writes_nothing_remote(make_world):
    w = make_world()
    r = w.run()
    assert r.code == 0, r.err
    assert "checks passed (dry run" in r.out
    for needle in (
        "5.1 Tip",
        "5.2 Inventory",
        "expected:",
        "missing: none",
        "extra: none",
        "5.3 Checks",
        "5.6 Index-row semantics",
        "5.7 Verify",
        "Receipt-Checks: scope PASS; assignment PASS; index rows PASS; blob identity PASS; check_repo PASS",
        "Receipt sweep",
    ):
        assert needle in r.out, needle
    assert received_main(w) == w.head
    assert w.origin_ref(f"refs/tags/reviews/{w.rec_id}") is None
    assert w.origin_ref(f"refs/heads/receipt/{w.rec_id}") is None
    assert git(w.recv, "rev-parse", "main") == w.head
    assert git(w.recv, "status", "--porcelain") == ""
    assert git(w.recv, "worktree", "list").count("\n") == 0
    assert git(w.recv, "branch", "--list", f"receipt/{w.rec_id}") == ""


def test_dry_run_with_scope_terms(make_world):
    w = make_world()
    assert w.run(scope_terms=["Record", "detail"]).code == 0
    r = w.run(scope_terms=["absent-term"])
    assert r.code == 1 and "scope term" in r.err


def test_full_publish_receipt(make_world):
    w = make_world()
    r = w.run(publish=True, co_authored_by="Test Agent <agent@example.invalid>")
    assert r.code == 0, r.err
    assert "STATUS: received" in r.out and "receipt incomplete" not in r.out
    main = received_main(w)
    assert main != w.head
    assert git(w.recv, "rev-parse", "main") == main
    parents = w.origin_git("rev-list", "--parents", "-n1", main).split()
    assert len(parents) == 3 and parents[1] == w.head
    msg = w.origin_git("log", "-1", "--format=%B", main)
    assert msg.startswith(f"Merge receipt/{w.rec_id}: receive {w.rec_id} evidence (receipt only)")
    assert f"HIO-Actor: claude/implementation-agent (evidence receipt, {OD})" in msg
    imp = parents[2]
    body = w.origin_git("log", "-1", "--format=%B", imp)
    for line in (
        f"Review-Id: {w.rec_id}",
        f"Review-Branch: {w.branch}",
        f"Review-Commit: {w.tip}",
        f"Reviewed-Base: {w.base}",
        f"Reviewed-Head: {w.head}",
        f"Assignment-Source: {SOURCE}",
        "Reviewer-Report: Codex final message, relayed by the owner (test)",
        "Inventory: complete",
        "Receipt-Checks: scope PASS; assignment PASS; index rows PASS; blob identity PASS; check_repo PASS",
        f"HIO-Actor: claude/implementation-agent (evidence receipt, {OD})",
        "Co-Authored-By: Test Agent <agent@example.invalid>",
    ):
        assert line in body, line
    for path in (w.rec_path, w.handoff_path):
        blob = w.origin_git("rev-parse", f"{w.tip}:{path}")
        sha = hashlib.sha256(w.files[path].encode()).hexdigest()
        assert f"Record: {path} blob {blob} sha256 {sha}" in body
        assert w.origin_git("rev-parse", f"{main}:{path}") == blob
    assert set(w.origin_git("diff", "--name-only", imp + "^", imp).splitlines()) == {
        w.rec_path,
        w.handoff_path,
        "reviews/README.md",
    }
    assert f"| {w.rec_id} |" in w.origin_git("show", f"{main}:reviews/README.md")
    tag = f"refs/tags/reviews/{w.rec_id}"
    assert w.origin_git("cat-file", "-t", tag) == "tag"
    assert w.origin_git("rev-parse", f"{tag}^{{commit}}") == w.tip
    assert git(w.recv, "worktree", "list").count("\n") == 0


def test_publish_is_idempotent_after_completion(make_world):
    w = make_world()
    assert w.run(publish=True).code == 0
    before = received_main(w)
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert "already imported" in r.out and "STATUS: received" in r.out
    assert received_main(w) == before
    r = w.run()
    assert r.code == 0 and "already imported" in r.out


def test_verification_record_with_class_s_transition(make_world):
    w = make_world(kind="verify")
    r = w.run(publish=True)
    assert r.code == 0, r.err
    text = w.origin_git("show", f"{received_main(w)}:reviews/README.md")
    assert "| F-OLD-1-1 | OLD-1 | high | **verified_closed** at" in text
    assert "F-OLD-1-2 | OLD-1 | medium | **open**" in text


# --- design failure cases -----------------------------------------------------------------------


def test_moved_branch_tip_after_report(make_world):
    w = make_world()
    w.author_commit_on(w.branch, "reviews/reports/late.md", "late\n")
    r = w.run(publish=True)
    assert r.code == 1 and "differs from the reviewer's reported tip" in r.err
    assert "not started" in r.out
    assert received_main(w) == w.head
    assert w.origin_ref(f"refs/tags/reviews/{w.rec_id}") is None


def test_wrong_assignment_head_not_an_ancestor(make_world):
    w = make_world()
    r = w.run(head=w.other)
    assert r.code == 1 and "does not descend from the assigned head" in r.err


def test_wrong_assignment_head_is_an_earlier_commit(make_world):
    w = make_world()
    r = w.run(head=w.mid)
    assert r.code == 1 and "outside the allowed set" in r.err and "docs/work.md" in r.err


def test_record_names_a_different_head(make_world):
    w = make_world(record_head="f" * 40)
    r = w.run()
    assert r.code == 1 and "5.3" in r.err and "assignment FAIL" in r.err and "reviewed_head" in r.err


def test_record_assignment_field_is_never_the_expected_source(make_world):
    w = make_world()
    r = w.run(assignment_source="docs/history/some-other-source.md")
    assert r.code == 1 and "assignment FAIL" in r.err


def test_extra_file_not_in_the_report(make_world):
    w = make_world(unreported={"reviews/handoffs/extra.md": "extra\n"})
    r = w.run(publish=True)
    assert r.code == 1 and "extra ['reviews/handoffs/extra.md']" in r.err
    assert "extra: `reviews/handoffs/extra.md`" in r.out
    assert received_main(w) == w.head and w.origin_ref(f"refs/tags/reviews/{w.rec_id}") is None


def test_missing_file_named_in_the_report(make_world):
    w = make_world()
    w.report["files"]["reviews/handoffs/ghost.md"] = "a" * 64
    w.write_report()
    r = w.run(publish=True)
    assert r.code == 1 and "missing ['reviews/handoffs/ghost.md']" in r.err
    assert received_main(w) == w.head


def test_disallowed_path(make_world):
    w = make_world(extra={"src/evil.py": "x = 1\n"})
    w.report["files"]["src/evil.py"] = hashlib.sha256(b"x = 1\n").hexdigest()
    w.write_report()
    r = w.run(publish=True)
    assert r.code == 1 and "outside the allowed set" in r.err and "src/evil.py" in r.err
    assert received_main(w) == w.head


def test_hash_mismatch(make_world):
    w = make_world()
    w.report["files"][w.rec_path] = "0" * 64
    w.write_report()
    r = w.run(publish=True)
    assert r.code == 1 and "hash mismatch" in r.err
    assert received_main(w) == w.head


def test_existing_tag_at_another_commit_is_never_moved(make_world):
    w = make_world()
    tag = f"reviews/{w.rec_id}"
    git(w.author, "tag", "-a", tag, w.head, "-m", "wrong")
    git(w.author, "push", "-q", "origin", f"refs/tags/{tag}")
    r = w.run()
    assert r.code == 1 and "a mismatch for the owner" in r.err
    r = w.run(publish=True)
    assert r.code == 1 and "never moved or deleted" in r.err and "not started" in r.out
    assert w.origin_git("rev-parse", f"refs/tags/{tag}^{{commit}}") == w.head
    assert received_main(w) == w.head


def test_existing_tag_at_t_is_accepted(make_world):
    w = make_world()
    tag = f"reviews/{w.rec_id}"
    git(w.author, "tag", "-a", tag, w.tip, "-m", "earlier attempt")
    git(w.author, "push", "-q", "origin", f"refs/tags/{tag}")
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert w.origin_git("rev-parse", f"refs/tags/{tag}^{{commit}}") == w.tip


def test_unsupported_verified_closed_in_the_index(make_world):
    def flip(readme: str, _w: World) -> str:
        return replace_line(
            readme, "| F-OLD-1-2 |", "| F-OLD-1-2 | OLD-1 | medium | **verified_closed** | — | — | — |"
        )

    w = make_world(readme_fn=flip)
    r = w.run(publish=True)
    assert r.code == 1 and "5.6" in r.err and "no imported VERIFY record" in r.err
    assert received_main(w) == w.head
    assert "receipt incomplete" in r.out and "tag pushed, no import" in r.out
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip


def test_verify_record_cannot_close_another_finding(make_world):
    def flip(readme: str, w: World) -> str:
        return replace_line(
            readme,
            "| F-OLD-1-2 |",
            f"| F-OLD-1-2 | OLD-1 | medium | **verified_closed** at `{w.head[:7]}` | — | "
            f"[VERIFY-T-2](records/VERIFY-T-2.md) | — |",
        )

    w = make_world(kind="verify", readme_fn=flip)
    r = w.run()
    assert (
        r.code == 1 and "F-OLD-1-2" in r.err and "no imported VERIFY record states verified_closed" in r.err
    )


def test_waiver_is_never_created_by_the_receiver(make_world):
    def waive(readme: str, _w: World) -> str:
        return replace_line(
            readme, "| F-OLD-1-2 |", "| F-OLD-1-2 | OLD-1 | medium | **waived** (OD-0001) | — | — | — |"
        )

    r = make_world(readme_fn=waive).run()
    assert r.code == 1 and "waived" in r.err


def test_stale_target(make_world):
    w = make_world()
    w.author_commit_on("main", "docs/more.md", "more\n")
    r = w.run()
    assert r.code == 1 and "stale target" in r.err


def test_check_repo_failure_stops_before_any_import_commit(make_world):
    w = make_world(extra={"reviews/reports/bad.md": "CHECK-REPO-FAIL\n"})
    w.report["files"]["reviews/reports/bad.md"] = hashlib.sha256(b"CHECK-REPO-FAIL\n").hexdigest()
    w.write_report()
    r = w.run(publish=True)
    assert r.code == 1 and "check_repo.py failed" in r.err
    assert received_main(w) == w.head
    assert "STATUS: receipt incomplete" in r.out and "tag pushed, no import" in r.out


def test_main_push_rejected_leaves_a_reconcilable_state(make_world):
    w = make_world()
    (w.origin / "deny-main").write_text("")
    r = w.run(publish=True)
    assert r.code == 1
    assert "STATUS: receipt incomplete" in r.out and "merged locally, push of main failed" in r.out
    assert "push of main failed or was rejected" in r.err
    assert received_main(w) == w.head
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip
    local = git(w.recv, "rev-parse", "main")
    assert local != w.head and len(git(w.recv, "rev-list", "--parents", "-n1", local).split()) == 3
    # recovery (5.11): restart from 5.1; the merge is re-verified and only the push is retried
    (w.origin / "deny-main").unlink()
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert "STATUS: received" in r.out and "already holds the merge" in r.out
    assert received_main(w) == local
    assert git(w.recv, "rev-parse", "main") == local


def test_branch_moved_before_the_final_recheck(make_world):
    w = make_world()

    def move(_ctx) -> None:
        w.author_commit_on(w.branch, "reviews/reports/late.md", "late\n")

    r = w.run(publish=True, hooks={"before_recheck": move})
    assert r.code == 1 and "the branch moved" in r.err and "Do not merge" in r.err
    assert "STATUS: receipt incomplete" in r.out and "import committed, not merged" in r.out
    assert received_main(w) == w.head
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip
    assert git(w.recv, "rev-parse", "main") == w.head


def test_main_moved_before_merge_then_restart_rebuilds_the_import(make_world):
    w = make_world()

    def move(_ctx) -> None:
        w.author_commit_on("main", "docs/more.md", "more\n")

    r = w.run(publish=True, hooks={"before_recheck": move})
    assert r.code == 1 and "moved" in r.err and "rerun from 5.1" in r.err
    assert "import committed, not merged" in r.out
    git(w.recv, "pull", "-q", "--ff-only")
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert "discarded the disposable" in r.out
    assert "STATUS: received" in r.out


def test_tag_missing_after_main_pushed_is_recreated_and_noted(make_world):
    w = make_world()
    assert w.run(publish=True).code == 0
    git(w.tmp, "--git-dir", str(w.origin), "tag", "-d", f"reviews/{w.rec_id}")
    git(w.recv, "tag", "-d", f"reviews/{w.rec_id}")
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert "was missing after the import" in r.out
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip


def test_reviewer_branch_deleted_after_receipt_leaves_t_pinned(make_world):
    w = make_world()
    assert w.run(publish=True).code == 0
    git(w.tmp, "--git-dir", str(w.origin), "update-ref", "-d", f"refs/heads/{w.branch}")
    r = w.run(publish=True)
    assert r.code == 1 and "absent or was deleted" in r.err
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip


# --- 5.6 index semantics, unit level ------------------------------------------------------------


def record(rid: str, kind: str, body: str, **fm: str) -> object:
    front = {"id": rid, "reviewed_base": "a" * 40, "reviewed_head": "b" * 40, "verdict": "READY", **fm}
    text = "---\n" + "\n".join(f"{k}: {v}" for k, v in front.items()) + "\n---\n" + body
    return hio.Record(f"reviews/records/{rid}.md", rid, kind, front, text)


def test_check_index_accepts_class_n_and_s_and_refuses_the_rest():
    rec = record("VERIFY-X-1", "VERIFY", "| F-OLD-1-1 | **verified_closed.** ok |\n")
    s_new = (
        "| F-OLD-1-1 | OLD-1 | high | **verified_closed** at `bbbbbbb` | "
        "remediation_claimed: fix `abc1234` | [VERIFY-X-1](records/VERIFY-X-1.md) | — |"
    )
    good = replace_line(README_BASE, "| F-OLD-1-1 |", s_new)
    assert hio.check_index(README_BASE, good, [rec], SOURCE, OD) == []
    assert hio.check_index(README_BASE, README_BASE, [rec], SOURCE, OD) == []

    def refused(text: str, recs=None, needle: str = "") -> None:
        problems = hio.check_index(README_BASE, text, recs or [rec], SOURCE, OD)
        assert problems and any(needle in p for p in problems), problems

    refused(
        add_row(README_BASE, H_FINDINGS, "| F-OLD-1-1 | OLD-1 | high | **open** | — | — | — |"),
        needle="duplicate",
    )
    refused(
        add_row(README_BASE, H_FINDINGS, "| F-NEW-1 | NEW | high | **open** | — | — | — |"),
        needle="no imported REVIEW",
    )
    refused(README_BASE.replace("States:", "Extra prose.\nStates:"), needle="neither a Class N nor a Class S")
    refused(
        README_BASE.replace(
            "| OLD-1 | s | `1111111..2222222` | Codex | **READY** |",
            "| OLD-1 | s | `1111111..2222222` | Codex | **BLOCKED** |",
        ),
        needle="Class S",
    )
    changed_claim = s_new.replace("fix `abc1234`", "fix `ffffff1`")
    refused(replace_line(README_BASE, "| F-OLD-1-1 |", changed_claim), needle="claim cell changed")
    removed = "\n".join(line for line in README_BASE.split("\n") if not line.startswith("| F-OLD-1-2"))
    refused(removed, needle="no superseding Class S row")
    reordered = README_BASE.split("\n")
    reordered[-4], reordered[-5] = reordered[-5], reordered[-4]
    refused("\n".join(reordered), needle="reordered")
    accepted = replace_line(
        README_BASE, "| F-OLD-1-1 |", s_new.replace("**verified_closed**", "**accepted**")
    )
    refused(accepted, needle="accepted")
    wrong_cite = replace_line(
        README_BASE, "| F-OLD-1-1 |", s_new.replace("[VERIFY-X-1](records/VERIFY-X-1.md)", "none")
    )
    refused(wrong_cite, needle="does not cite")
    untraceable = replace_line(
        README_BASE, "| F-OLD-1-1 |", s_new.replace("at `bbbbbbb`", "at `bbbbbbb` (merge `1234567`)")
    )
    refused(untraceable, needle="1234567")
    review_only = record("REVIEW-X-1", "REVIEW", "### F-OLD-1-1 — high, open: x\n")
    refused(good, recs=[review_only], needle="no imported VERIFY record")


def test_check_index_class_n_rows_are_checked_against_the_record():
    rec = record("REVIEW-X-1", "REVIEW", "### F-X-1-1 — high, open: a\n", review_branch="review/x-codex")
    row = f"| REVIEW-X-1 | s | `{'a' * 7}..{'b' * 7}` | Codex | **READY** | [record](records/REVIEW-X-1.md) |"
    ok = add_row(README_BASE, H_REVIEWED, row)
    assert hio.check_index(README_BASE, ok, [rec], SOURCE, OD) == []
    for bad, needle in (
        (row.replace("**READY**", "**NOT READY**"), "verdict"),
        (row.replace("aaaaaaa", "ccccccc"), "base..head"),
        (row.replace("records/REVIEW-X-1.md", "records/REVIEW-Y-9.md"), "record cell"),
        (row.replace("| REVIEW-X-1 |", "| REVIEW-Z-1 |"), "matches no imported record"),
    ):
        problems = hio.check_index(README_BASE, add_row(README_BASE, H_REVIEWED, bad), [rec], SOURCE, OD)
        assert any(needle in p for p in problems), (needle, problems)
    finding = "| F-X-1-1 | REVIEW-X-1 | high | **open** | — | — | — |"
    assert hio.check_index(README_BASE, add_row(README_BASE, H_FINDINGS, finding), [rec], SOURCE, OD) == []
    for bad, needle in (
        (finding.replace("high", "low"), "severity"),
        (finding.replace("**open**", "**verified_closed**"), "state open"),
        (finding.replace("| — | — | — |", "| fix | — | — |"), "remediation"),
        (finding.replace("F-X-1-1", "F-X-1-9"), "no imported REVIEW"),
    ):
        problems = hio.check_index(README_BASE, add_row(README_BASE, H_FINDINGS, bad), [rec], SOURCE, OD)
        assert any(needle in p for p in problems), (needle, problems)
    assigned = f"| REVIEW-X-1 | `r` | `{'a' * 40}` | `{'b' * 40}` | scope | something else | **received** |"
    problems = hio.check_index(README_BASE, add_row(README_BASE, H_ASSIGNED, assigned), [rec], SOURCE, OD)
    assert any("assignment cell" in p for p in problems)
    good = assigned.replace("something else", f"[{SOURCE}](../{SOURCE})")
    assert hio.check_index(README_BASE, add_row(README_BASE, H_ASSIGNED, good), [rec], SOURCE, OD) == []


def test_real_index_has_no_duplicate_ids_and_every_table_is_recognised():
    lines = (REPO / "reviews" / "README.md").read_text().splitlines()
    assert hio.duplicate_problems(lines) == []
    kinds = {hio.table_kind(h) for h, _body in hio.parse_tables(lines)}
    assert {"assigned", "reviewed", "rounds", "findings"} <= kinds
