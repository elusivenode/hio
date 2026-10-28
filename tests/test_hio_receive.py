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

    def run(self, *, publish: bool = False, without_index: bool = False, hooks=None, **over):
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
        if without_index:
            argv.append("--without-index")
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


def test_verification_record_with_class_s_transition_is_refused(make_world):
    # option B (OD-0100): receipt never changes a finding's state, so the former Class S receipt is refused
    w = make_world(kind="verify")
    r = w.run(publish=True)
    assert r.code == 1 and "5.6" in r.err and "removed or changed line" in r.err, r.err
    assert "never sets a finding's state" in r.err
    assert received_main(w) == w.head


# --- option B: --without-index and index reconciliation pending -----------------------------------


def test_without_index_dry_run_leaves_the_refused_diff_out_and_reports_it(make_world):
    w = make_world(kind="verify")  # its README diff rewrites F-OLD-1-1's state: refused
    r = w.run()
    assert r.code == 1 and "--without-index" in r.err  # without the flag a refused diff is a STOP
    r = w.run(without_index=True)
    assert r.code == 0, r.err
    assert "checks passed (dry run" in r.out and "PARTIAL" in r.out
    assert "INDEX DIFF REFUSED" in r.out and "index rows REFUSED" in r.out
    # the refused lines are listed verbatim
    assert (
        "-| F-OLD-1-1 | OLD-1 | high | **remediation_claimed** | remediation_claimed: fix `abc1234` |"
        in r.out
    )
    assert f"+| {w.rec_id} | `r` | `{w.base}` | `{w.head}` | scope |" in r.out
    assert "+| F-OLD-1-1 | OLD-1 | high | **verified_closed** at" in r.out
    assert received_main(w) == w.head and git(w.recv, "worktree", "list").count("\n") == 0
    # 5.12: the VERIFY record's outcome is reported as pending reconciliation, and nothing else changes
    assert "index reconciliation pending: F-OLD-1-1: VERIFY-T-2 states verified_closed" in r.out
    assert "the index on main shows 'remediation_claimed'" in r.out


def test_without_index_publish_receives_the_records_but_not_the_index(make_world):
    w = make_world(kind="verify")
    before = w.origin_git("show", "main:reviews/README.md")
    assert w.run(publish=True).code == 1 and received_main(w) == w.head  # no flag: a STOP, nothing merged
    r = w.run(publish=True, without_index=True)
    assert r.code == 0, r.err
    assert "STATUS: received" in r.out and "PARTIAL" in r.out
    main = received_main(w)
    assert main != w.head
    assert w.origin_git("show", f"{main}:reviews/README.md") == before  # README untouched
    assert w.origin_git("show", f"{main}:{w.rec_path}") == w.files[w.rec_path].rstrip("\n")
    parents = w.origin_git("rev-list", "--parents", "-n1", main).split()
    imp = parents[2]
    body = w.origin_git("log", "-1", "--format=%B", imp)
    trailer = next(x for x in body.splitlines() if x.startswith("Index-Diff: refused ("))
    assert trailer.endswith(")") and "\n" not in trailer
    assert "Receipt-Checks: scope PASS; assignment PASS; index rows REFUSED; blob identity PASS" in body
    assert set(w.origin_git("diff", "--name-only", imp + "^", imp).splitlines()) == {
        w.rec_path,
        w.handoff_path,
    }
    assert f"Record: {w.rec_path} blob " in body
    assert "index reconciliation pending: F-OLD-1-1: VERIFY-T-2 states verified_closed" in r.out
    assert w.origin_git("rev-parse", f"refs/tags/reviews/{w.rec_id}^{{commit}}") == w.tip
    # a rerun after completion is idempotent
    r = w.run(publish=True, without_index=True)
    assert r.code == 0 and "already imported" in r.out and received_main(w) == main


REFUSED_LINES = (
    "-| F-OLD-1-1 | OLD-1 | high | **remediation_claimed** | remediation_claimed: fix `abc1234` |",
    "+| F-OLD-1-1 | OLD-1 | high | **verified_closed** at",
)


def assert_partial_disclosure(w: World, out: str) -> None:
    """What a receipt OD may be built from: PARTIAL, the reasons and the refused lines, verbatim."""
    assert "PARTIAL" in out and "INDEX DIFF REFUSED" in out and "index rows REFUSED" in out
    assert "refused lines, verbatim" in out
    assert all(x in out for x in REFUSED_LINES)
    assert f"+| {w.rec_id} | `r` | `{w.base}` | `{w.head}` | scope |" in out
    assert "a removed or changed line" in out  # the reasons, recomputed on the restart


def test_restart_after_a_failed_main_push_still_discloses_the_refused_index(make_world):
    w = make_world(kind="verify")  # its README diff rewrites F-OLD-1-1's state: refused
    before = w.origin_git("show", "main:reviews/README.md")
    (w.origin / "deny-main").write_text("")
    r = w.run(publish=True, without_index=True)
    assert r.code == 1 and "STATUS: receipt incomplete" in r.out
    assert "refused lines, verbatim" in r.out and received_main(w) == w.head
    (w.origin / "deny-main").unlink()
    # attempt 2 publishes the import and merge made by attempt 1; its summary is the receipt's source
    r = w.run(publish=True, without_index=True)
    assert r.code == 0, r.err
    assert "STATUS: received" in r.out
    assert_partial_disclosure(w, r.out)
    main = received_main(w)
    assert main != w.head and w.origin_git("show", f"{main}:reviews/README.md") == before
    imp = w.origin_git("rev-list", "--parents", "-n1", main).split()[2]
    assert "Index-Diff: refused (" in w.origin_git("log", "-1", "--format=%B", imp)
    # a later idempotent run discloses the same
    r = w.run(publish=True, without_index=True)
    assert r.code == 0, r.err
    assert "already imported" in r.out and "STATUS: received" in r.out
    assert_partial_disclosure(w, r.out)
    assert received_main(w) == main and w.origin_git("show", f"{main}:reviews/README.md") == before
    assert git(w.recv, "worktree", "list").count("\n") == 0


def test_dry_run_after_the_import_exists_discloses_the_refused_index(make_world):
    w = make_world(kind="verify")
    assert w.run(publish=True, without_index=True).code == 0
    r = w.run(without_index=True)
    assert r.code == 0, r.err
    assert "checks passed (dry run" in r.out
    assert_partial_disclosure(w, r.out)
    assert git(w.recv, "worktree", "list").count("\n") == 0


def test_restart_without_the_go_ahead_stops_after_a_refused_index_import(make_world):
    w = make_world(kind="verify")
    (w.origin / "deny-main").write_text("")
    assert w.run(publish=True, without_index=True).code == 1
    (w.origin / "deny-main").unlink()
    for publish in (True, False):
        r = w.run(publish=publish)
        assert r.code == 1 and "restart with --without-index" in r.err
        assert "STATUS: received" not in r.out
    assert received_main(w) == w.head  # nothing was published without the flag


def test_without_index_is_ignored_when_the_index_diff_is_acceptable(make_world):
    w = make_world()  # a Class N review receipt
    r = w.run(publish=True, without_index=True)
    assert r.code == 0, r.err
    assert "PARTIAL" not in r.out and "INDEX DIFF REFUSED" not in r.out and "index rows PASS" in r.out
    main = received_main(w)
    imp = w.origin_git("rev-list", "--parents", "-n1", main).split()[2]
    assert "Index-Diff" not in w.origin_git("log", "-1", "--format=%B", imp)
    assert f"| {w.rec_id} |" in w.origin_git("show", f"{main}:reviews/README.md")


def test_without_index_does_not_apply_the_acceptable_part_of_a_refused_diff(make_world):
    def waive(readme: str, _w: World) -> str:
        return replace_line(
            readme, "| F-OLD-1-2 |", "| F-OLD-1-2 | OLD-1 | medium | **waived** (OD-0001) | — | — | — |"
        )

    w = make_world(readme_fn=waive)  # its Class N rows are fine; the waived row refuses the whole diff
    before = w.origin_git("show", "main:reviews/README.md")
    r = w.run(publish=True, without_index=True)
    assert r.code == 0, r.err
    assert w.origin_git("show", f"{received_main(w)}:reviews/README.md") == before
    assert "+| F-OLD-1-2 | OLD-1 | medium | **waived** (OD-0001)" in r.out


def test_class_n_verify_receipt_passes_and_reports_the_pending_outcome(make_world):
    def navigation_only(readme: str, _w: World) -> str:
        # keep the assigned and rounds rows; leave the finding row exactly as on main
        return replace_line(
            readme,
            "| F-OLD-1-1 |",
            "| F-OLD-1-1 | OLD-1 | high | **remediation_claimed** | remediation_claimed: fix `abc1234` "
            "| — | — |",
        )

    w = make_world(kind="verify", readme_fn=navigation_only)
    r = w.run(publish=True)
    assert r.code == 0, r.err
    assert "PARTIAL" not in r.out and "index rows PASS" in r.out
    # the index on main still shows remediation_claimed, so the record's outcome is pending (5.12)
    assert "index reconciliation pending: F-OLD-1-1: VERIFY-T-2 states verified_closed" in r.out
    text = w.origin_git("show", f"{received_main(w)}:reviews/README.md")
    assert "| F-OLD-1-1 | OLD-1 | high | **remediation_claimed** |" in text and f"| {w.rec_id} |" in text


def test_review_receipt_reports_no_pending_reconciliation(make_world):
    r = make_world().run()  # a REVIEW record states no outcomes
    assert r.code == 0, r.err
    assert "none: every outcome an imported VERIFY record states is shown" in r.out


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
    assert r.code == 1 and "5.6" in r.err and "never sets a finding's state" in r.err  # was: no VERIFY record
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
    # option B: the VERIFY record states nothing for F-OLD-1-2, and no record could make this row receivable
    assert r.code == 1 and "F-OLD-1-2" in r.err and "removed or changed line" in r.err


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


def test_check_index_accepts_class_n_and_refuses_class_s_and_the_rest():
    rec = record("VERIFY-X-1", "VERIFY", "| F-OLD-1-1 | **verified_closed.** ok |\n")
    s_new = (
        "| F-OLD-1-1 | OLD-1 | high | **verified_closed** at `bbbbbbb` | "
        "remediation_claimed: fix `abc1234` | [VERIFY-X-1](records/VERIFY-X-1.md) | — |"
    )
    good = replace_line(README_BASE, "| F-OLD-1-1 |", s_new)
    # option B: even a Class S row the old receiver accepted (affirmative, cited, exact head) is refused
    problems = hio.check_index(README_BASE, good, [rec], SOURCE, OD)
    assert any("removed or changed line" in p for p in problems), problems
    assert any("verified_closed in the state cell" in p for p in problems), problems
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
    refused(README_BASE.replace("States:", "Extra prose.\nStates:"), needle="not a Class N row")
    refused(
        README_BASE.replace(
            "| OLD-1 | s | `1111111..2222222` | Codex | **READY** |",
            "| OLD-1 | s | `1111111..2222222` | Codex | **BLOCKED** |",
        ),
        needle="removed or changed line",
    )
    changed_claim = s_new.replace("fix `abc1234`", "fix `ffffff1`")
    refused(replace_line(README_BASE, "| F-OLD-1-1 |", changed_claim), needle="removed or changed line")
    removed = "\n".join(line for line in README_BASE.split("\n") if not line.startswith("| F-OLD-1-2"))
    refused(removed, needle="removed or changed line")
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
    refused(wrong_cite, needle="removed or changed line")
    untraceable = replace_line(
        README_BASE, "| F-OLD-1-1 |", s_new.replace("at `bbbbbbb`", "at `bbbbbbb` (merge `1234567`)")
    )
    refused(untraceable, needle="removed or changed line")
    review_only = record("REVIEW-X-1", "REVIEW", "### F-OLD-1-1 — high, open: x\n")
    refused(good, recs=[review_only], needle="removed or changed line")


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


# --- remediation of REVIEW-2026-10-28-h6-1 (F-1, F-2, F-4) ----------------------------------------


NEGATED = "Nothing was accepted or approved. The owner has not waived anything.\n"
S_NEW = (
    "| F-OLD-1-1 | OLD-1 | high | **verified_closed** at `bbbbbbb` | "
    "remediation_claimed: fix `abc1234` | [VERIFY-X-1](records/VERIFY-X-1.md) at `bbbbbbb` | — |"
)


def problems_for(staged: str, recs: list, main: str = README_BASE) -> list[str]:
    return hio.check_index(main, staged, recs, SOURCE, OD)


def test_check_index_refuses_accepted_waived_approved_rows_whatever_the_record_says():
    rec = record("REVIEW-X-1", "REVIEW", f"### F-X-1-1 — high, open: a\n\n{NEGATED}")
    row = (
        f"| REVIEW-X-1 | `r` | `{'a' * 40}` | `{'b' * 40}` | unrelated scope | "
        f"[{SOURCE}](../{SOURCE}) | **received** |"
    )
    assert problems_for(add_row(README_BASE, H_ASSIGNED, row), [rec]) == []
    for word in ("accepted", "waived", "approved"):
        for status in (
            f"**{word}**",
            f"**received**; {word}",
            f"**received**; verdict READY; not {word.upper()}",
        ):
            bad = row.replace("**received**", status)
            problems = problems_for(add_row(README_BASE, H_ASSIGNED, bad), [rec])
            assert any(word in p and "owner OD" in p for p in problems), (status, problems)
    reviewed = (
        f"| REVIEW-X-1 | s | `{'a' * 7}..{'b' * 7}` | Codex | **READY** | [record](records/REVIEW-X-1.md) |"
    )
    assert problems_for(add_row(README_BASE, H_REVIEWED, reviewed), [rec]) == []
    for word in ("accepted", "approved"):
        bad = reviewed.replace("**READY**", f"**{word}**")
        problems = problems_for(add_row(README_BASE, H_REVIEWED, bad), [rec])
        assert any(word in p for p in problems) and any("verdict" in p for p in problems), problems


def test_check_index_assigned_row_status_is_bound_to_the_record():
    rec = record("REVIEW-X-1", "REVIEW", "### F-X-1-1 — high, open: a\n", verdict="NOT READY")
    row = (
        f"| REVIEW-X-1 | `r` | `{'a' * 40}` | `{'b' * 40}` | scope | [{SOURCE}](../{SOURCE}) | "
        "**received**; verdict NOT READY; seven findings open |"
    )
    assert problems_for(add_row(README_BASE, H_ASSIGNED, row), [rec]) == []
    wrong_verdict = row.replace("verdict NOT READY", "verdict READY")
    problems = problems_for(add_row(README_BASE, H_ASSIGNED, wrong_verdict), [rec])
    assert any("status cell verdict" in p for p in problems), problems
    not_received = row.replace("**received**", "**assigned**")
    problems = problems_for(add_row(README_BASE, H_ASSIGNED, not_received), [rec])
    assert any("begin with received" in p for p in problems), problems
    wrong_head = row.replace("b" * 40, "c" * 40)
    assert any("head sha" in p for p in problems_for(add_row(README_BASE, H_ASSIGNED, wrong_head), [rec]))


def test_check_index_verdict_in_a_rounds_row_is_the_outcome_not_a_substring():
    rec = record("VERIFY-X-1", "VERIFY", "| F-OLD-1-1 | **verified_closed.** ok |\n", verdict="READY")
    row = (
        f"| VERIFY-X-1 | OLD-1, finding 1 | `{'a' * 7}..{'b' * 7}` | `abc1234` | "
        "**F-OLD-1-1 verified_closed**; READY | [record](records/VERIFY-X-1.md) |"
    )
    # option B: the rounds row is a Class N row on its own; the finding row is not rewritten with it
    assert problems_for(add_row(README_BASE, H_ROUNDS, row), [rec]) == []
    not_ready = row.replace("; READY", "; NOT READY")
    assert any("outcome cell" in p for p in problems_for(add_row(README_BASE, H_ROUNDS, not_ready), [rec]))
    buried = row.replace("; READY", "; ready is not claimed here; BLOCKED")
    assert any("outcome cell" in p for p in problems_for(add_row(README_BASE, H_ROUNDS, buried), [rec]))


def test_receive_publish_refuses_an_unsupported_accepted_assigned_row(make_world):
    def accept(readme: str, w: World) -> str:
        return replace_line(
            readme,
            f"| {w.rec_id} | `r`",
            f"| {w.rec_id} | `r` | `{w.base}` | `{w.head}` | an unrelated scope | [{SOURCE}](../{SOURCE}) "
            "(owner assignment) | **accepted** |",
        )

    w = make_world(readme_fn=accept, record_extra=NEGATED)
    r = w.run(publish=True)
    assert r.code == 1 and "5.6" in r.err and "accepted" in r.err and "owner OD" in r.err
    assert received_main(w) == w.head
    assert "receipt incomplete" in r.out


def outcome_record(body: str, rid: str = "VERIFY-X-1") -> object:
    return record(rid, "VERIFY", body)


def test_class_s_rewrites_are_refused_whatever_the_record_states():
    # option B: the receiver never changes a finding's state, however affirmative the record's outcome row is
    good = outcome_record("| F-OLD-1-1 | **verified_closed.** the fix holds |\n")
    recs = [
        good,
        outcome_record("| `F-OLD-1-1` | **verified_closed** |\n"),
        outcome_record("F-OLD-1-1 remains open; do not mark verified_closed.\n"),
        outcome_record("| F-OLD-1-1 | verified_closed was NOT reached; the finding remains open. |\n"),
        outcome_record("| F-OLD-1-1 | **open.** not fixed |\n"),
        outcome_record("| F-OLD-1-1 | **remediation_rejected.** x |\n"),
    ]
    for state in ("verified_closed", "open", "remediation_rejected", "waived", "accepted"):
        staged = replace_line(README_BASE, "| F-OLD-1-1 |", S_NEW.replace("verified_closed", state))
        for rec in recs:
            problems = problems_for(staged, [rec])
            assert any("removed or changed line" in p for p in problems), (state, rec.text, problems)
    # a new row cannot carry such a state either, whether or not a record states it
    for state in ("verified_closed", "remediation_rejected", "waived", "accepted", "approved"):
        row = f"| F-OLD-1-9 | OLD-1 | high | **{state}** | — | — | — |"
        problems = problems_for(add_row(README_BASE, H_FINDINGS, row), [good])
        assert any(f"{state} in the state cell of an added row" in p for p in problems), (state, problems)


def test_codexs_contradictory_state_cell_is_refused():
    cell = "**verified_closed.** was NOT reached; the finding remains open."
    rec = record("REVIEW-X-1", "REVIEW", "### F-X-1-1 — high, open: a\n")
    row = f"| F-X-1-1 | REVIEW-X-1 | high | {cell} | — | — | — |"
    problems = problems_for(add_row(README_BASE, H_FINDINGS, row), [rec])
    assert any("verified_closed in the state cell of an added row" in p for p in problems), problems
    # the same text as a rewrite of an existing finding's state cell
    rewrite = replace_line(
        README_BASE, "| F-OLD-1-2 |", f"| F-OLD-1-2 | OLD-1 | medium | {cell} | — | — | — |"
    )
    outcome = outcome_record("| F-OLD-1-2 | verified_closed was NOT reached; the finding remains open. |\n")
    problems = problems_for(rewrite, [outcome])
    assert any("removed or changed line" in p for p in problems) and any(
        "verified_closed" in p for p in problems
    )
    # a plain new `open` finding row for a finding the REVIEW record defines is still Class N
    ok = "| F-X-1-1 | REVIEW-X-1 | high | **open** | — | — | — |"
    assert problems_for(add_row(README_BASE, H_FINDINGS, ok), [rec]) == []


def test_pending_reconciliation_lists_outcomes_the_index_does_not_show():
    rec = outcome_record(
        "| F-OLD-1-1 | **verified_closed.** the fix holds |\n"
        "| F-OLD-1-2 | **open.** not fixed |\n"
        "| F-GONE-1 | **remediation_rejected.** x |\n"
        "| F-OLD-1-3 | verified_closed was NOT reached; the finding remains open. |\n"
        "| F-OLD-1-4 | **open.** a |\n| F-OLD-1-4 | **verified_closed.** b |\n"
        "F-OLD-1-1 remains open; do not mark verified_closed.\n"
    )
    pending = hio.pending_reconciliation(README_BASE, [rec])
    assert all(p.startswith("index reconciliation pending: ") for p in pending)
    joined = "\n".join(pending)
    assert "F-OLD-1-1: VERIFY-X-1 states verified_closed; the index on main shows" in joined
    assert "F-GONE-1: VERIFY-X-1 states remediation_rejected; the index on main has no row" in joined
    assert "F-OLD-1-4: VERIFY-X-1 has conflicting outcome rows" in joined
    assert "F-OLD-1-2" not in joined  # the index already shows open
    assert "F-OLD-1-3" not in joined  # a negated cell states nothing
    assert len(pending) == 3
    # a REVIEW record states no outcomes
    assert (
        hio.pending_reconciliation(
            README_BASE, [record("REVIEW-X-1", "REVIEW", "| F-OLD-1-1 | **verified_closed.** |\n")]
        )
        == []
    )


def with_blank_in_findings(text: str) -> str:
    """The shape of main's real index: a blank line inside the findings register."""
    return text.replace("| F-OLD-1-2 |", "\n| F-OLD-1-2 |", 1)


def test_findings_table_continues_across_a_blank_separator_line():
    main = with_blank_in_findings(README_BASE)
    lines = main.splitlines()
    kinds = {
        line.split("|")[1].strip(): hio.row_index(lines)[line][0] for line in lines if "| F-OLD-1-" in line
    }
    assert kinds == {"F-OLD-1-1": "findings", "F-OLD-1-2": "findings"}
    after = (
        "| F-OLD-1-2 | OLD-1 | medium | **verified_closed** at `bbbbbbb` | — | "
        "[VERIFY-X-1](records/VERIFY-X-1.md) at `bbbbbbb` | — |"
    )
    staged = replace_line(main, "| F-OLD-1-2 |", after)
    rec = outcome_record("| F-OLD-1-2 | **verified_closed.** ok |\n")
    # option B: the later row is recognised as a finding row, and rewriting its state is refused
    problems = problems_for(staged, [rec], main=main)
    assert any("removed or changed line" in p for p in problems), problems
    assert any("verified_closed in the state cell" in p for p in problems), problems
    # a new `open` finding row after the blank line is still Class N
    review = record("REVIEW-X-1", "REVIEW", "### F-X-1-1 — high, open: a\n")
    new_row = "| F-X-1-1 | REVIEW-X-1 | high | **open** | — | — | — |"
    last = "| F-OLD-1-2 | OLD-1 | medium | **open** | — | — | — |"
    assert problems_for(main.replace(last, last + "\n" + new_row, 1), [review], main=main) == []
    assert hio.duplicate_problems(staged.splitlines()) == []


def test_blank_separated_table_with_its_own_header_stays_a_separate_table():
    def shape(text: str) -> list[tuple[list[str], list[str]]]:
        return [(h, [cells[0] for _line, cells in b]) for h, b in hio.parse_tables(text.splitlines())]

    text = (
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n| Finding | X |\n|---|---|\n| F-1 | y |\n\n| 3 | 4 |\n\n"
        "prose\n\n| 5 | 6 |\n"
    )
    # a header makes a new table; a header-less run continues it; prose ends the table
    assert shape(text) == [(["a", "b"], ["1"]), (["finding", "x"], ["F-1", "3"]), (["5", "6"], [])]
    # a row with another cell count is not folded in
    odd = "| A | B |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 | 5 |\n| 6 | 7 |\n"
    assert shape(odd) == [(["a", "b"], ["1", "6"]), (["3", "4", "5"], [])]


def test_real_index_shape_refuses_a_class_s_transition_after_its_blank_line():
    main = (REPO / "reviews" / "README.md").read_text()
    lines = main.splitlines()
    index = hio.row_index(lines)
    start = next(i for i, line in enumerate(lines) if line.startswith("| Finding |"))
    blank = next(i for i in range(start, len(lines)) if not lines[i].strip())
    later = [
        line for line in lines[blank + 1 :] if line.startswith("| F-") and len(hio.split_row(line) or []) == 7
    ]
    assert later, "main's findings register has no seven-cell finding row after its blank line"
    assert all(index[line][0] == "findings" for line in later)
    old = later[0]
    cells = hio.split_row(old)
    assert cells is not None
    cells[3] = "**open**"
    cells[5] = "[VERIFY-X-1](records/VERIFY-X-1.md) at `bbbbbbb`"
    new = "| " + " | ".join(cells) + " |"
    staged = main.replace(old, new, 1)
    fid = hio.norm_cell(cells[0])
    rec = outcome_record(f"| {fid} | **open.** not fixed at the reviewed head |\n")
    # option B: even this affirmative, cited, same-state-word rewrite of an existing row is refused
    assert any("removed or changed line" in p for p in problems_for(staged, [rec], main=main))
    unsupported = outcome_record(f"{fid} is verified_closed in prose only\n")
    assert any("removed or changed line" in p for p in problems_for(staged, [unsupported], main=main))


def test_real_index_has_no_duplicate_ids_and_every_table_is_recognised():
    lines = (REPO / "reviews" / "README.md").read_text().splitlines()
    assert hio.duplicate_problems(lines) == []
    kinds = {hio.table_kind(h) for h, _body in hio.parse_tables(lines)}
    assert {"assigned", "reviewed", "rounds", "findings"} <= kinds


# --- round 3: VERIFY-2026-10-28-h6-1-1 (F-2, F-4 and the F-1-fix regression) ----------------------


def test_outcome_cell_counts_only_with_the_exact_bold_state_token():
    def stated(cell: str) -> str | None:
        return hio.record_outcome(outcome_record(f"| F-OLD-1-1 | {cell} |\n"), "F-OLD-1-1")

    for cell, state in (
        ("**verified_closed.** the fix holds", "verified_closed"),
        ("**verified_closed**", "verified_closed"),
        ("**verified_closed.**", "verified_closed"),
        ("**verified_closed** at `bbbbbbb`", "verified_closed"),
        ("**remediation_rejected.** x", "remediation_rejected"),
        ("**open.** not fixed", "open"),
    ):
        assert stated(cell) == state, cell
    for cell in (
        "verified_closed was NOT reached; the finding remains open.",  # the verifier's exact case
        "verified_closed",
        "open",
        "**verified_closed was NOT reached**",
        "**not verified_closed**",
        "*verified_closed.* ok",
        "**verified_closed.**x",
        "**verified_closed**; later",
        "**verified_closed.**. later",
        "the **verified_closed.** claim is rejected",
        "",
    ):
        assert stated(cell) is None, cell
    to_closed = replace_line(README_BASE, "| F-OLD-1-1 |", S_NEW)
    verifier_case = outcome_record(
        "| F-OLD-1-1 | verified_closed was NOT reached; the finding remains open. |\n"
    )
    problems = problems_for(to_closed, [verifier_case])  # option B: refused, whatever the record says
    assert any("removed or changed line" in p for p in problems), problems


FINDING_6 = (
    "| F-OLD-1-3 | OLD-1 | high | **remediation_claimed** (still open): late | "
    "remediation_claimed (round 1): fix `abc1234` | — |"
)
FINDING_7 = "| F-OLD-1-4 | OLD-1 | low | **open** | — | — | — |"
FINDING_6_DONE = (
    "| F-OLD-1-3 | OLD-1 | high | **verified_closed** at `bbbbbbb` ([VERIFY-X-1](records/VERIFY-X-1.md)) | "
    "remediation_claimed (round 1): fix `abc1234` | — |"
)


def with_six_cell_rows(text: str) -> str:
    """The shape of main's real index: after a blank line, six-cell rows (no verification cell) then seven."""
    return text.replace("| F-OLD-1-2 |", f"\n{FINDING_6}\n{FINDING_7}\n| F-OLD-1-2 |", 1)


def test_header_less_run_after_blank_lines_continues_the_findings_table_with_six_cell_rows():
    main = with_six_cell_rows(README_BASE)
    lines = main.splitlines()
    rows = hio.row_index(lines)
    for line in (FINDING_6, FINDING_7, "| F-OLD-1-2 | OLD-1 | medium | **open** | — | — | — |"):
        assert rows[line][0] == "findings", line
    # a row with any other cell count is still not folded in
    odd = main.replace(FINDING_7, "| F-OLD-1-4 | OLD-1 | low | **open** |", 1)
    assert "| F-OLD-1-4 | OLD-1 | low | **open** |" not in hio.row_index(odd.splitlines())
    staged = main.replace(FINDING_6, FINDING_6_DONE, 1)
    rec = outcome_record("| F-OLD-1-3 | **verified_closed.** the fix holds |\n")
    assert hio.duplicate_problems(staged.splitlines()) == []

    def refused(new_row: str, recs: list, needle: str) -> None:
        problems = problems_for(main.replace(FINDING_6, new_row, 1), recs, main=main)
        assert any(needle in p for p in problems), (new_row, problems)

    # option B: every rewrite of the six-cell row is refused as a changed line, the record notwithstanding
    for new_row in (
        FINDING_6_DONE,
        FINDING_6_DONE.replace("VERIFY-X-1", "none"),
        FINDING_6_DONE.replace("fix `abc1234`", "fix `ffffff1`"),
        FINDING_6_DONE + " — |",
    ):
        for recs in (
            [rec],
            [outcome_record("F-OLD-1-3 stays open; do not mark verified_closed.\n")],
            [outcome_record("| F-OLD-1-3 | verified_closed was NOT reached |\n")],
        ):
            refused(new_row, recs, "removed or changed line")
    # a new six-cell row is not a Class N row
    new_rows = main.replace(FINDING_7, FINDING_7 + "\n" + FINDING_6.replace("F-OLD-1-3", "F-OLD-1-5"), 1)
    problems = problems_for(new_rows, [rec], main=main)
    assert any("F-OLD-1-5" in p and "cells" in p for p in problems), problems


def test_real_index_adr0012_six_cell_row_refuses_a_class_s_transition():
    main = (REPO / "reviews" / "README.md").read_text()
    old = next(line for line in main.splitlines() if line.startswith("| F-REVIEW-2026-10-25-adr0012-1 |"))
    cells = hio.split_row(old)
    assert cells is not None and len(cells) == 6
    assert hio.row_index(main.splitlines())[old][0] == "findings"
    cells[3] = "**verified_closed** at `bbbbbbb` ([VERIFY-X-1](records/VERIFY-X-1.md))"
    new = "| " + " | ".join(cells) + " |"
    staged = main.replace(old, new, 1)
    fid = hio.norm_cell(cells[0])
    rec = outcome_record(f"| {fid} | **verified_closed.** closed at the reviewed head |\n")
    problems = problems_for(staged, [rec], main=main)  # option B: refused, however affirmative the record
    assert any("removed or changed line" in p for p in problems), problems
    unsupported = outcome_record(f"| {fid} | verified_closed was NOT reached; still open |\n")
    problems = problems_for(staged, [unsupported], main=main)
    assert any("removed or changed line" in p for p in problems), problems
    altered = staged.replace("| high |", "| low |", 1)
    assert problems_for(altered, [rec], main=main) != []


def test_forbidden_state_guard_reads_state_cells_never_scope_or_prose():
    prose = "Review whether the work was accepted by the owner"
    rec = record("REVIEW-X-1", "REVIEW", "### F-X-1-1 — high, open: a\n", verdict="NOT READY")
    row = (
        f"| REVIEW-X-1 | `r` | `{'a' * 40}` | `{'b' * 40}` | {prose} | [{SOURCE}](../{SOURCE}) | "
        "**received**; verdict NOT READY |"
    )
    assert problems_for(add_row(README_BASE, H_ASSIGNED, row), [rec]) == []
    for word in ("accepted", "waived", "approved"):
        bad = row.replace("**received**; verdict NOT READY", f"**{word}**")
        problems = problems_for(add_row(README_BASE, H_ASSIGNED, bad), [rec])
        assert any(word in p and "owner OD" in p for p in problems), (word, problems)
    # option B: a rewrite is refused as a changed line; the guard still names an `accepted` state cell
    claim = "remediation_claimed: the design was approved by the owner; fix `abc1234`"
    main = README_BASE.replace("remediation_claimed: fix `abc1234`", claim)
    s_new = S_NEW.replace("remediation_claimed: fix `abc1234`", claim)
    good = outcome_record("| F-OLD-1-1 | **verified_closed.** ok |\n")
    problems = problems_for(replace_line(main, "| F-OLD-1-1 |", s_new), [good], main=main)
    assert any("removed or changed line" in p for p in problems), problems
    assert not any("approved in the state cell" in p for p in problems), problems  # prose in a claim cell
    accepted = s_new.replace("**verified_closed**", "**accepted**")
    problems = problems_for(replace_line(main, "| F-OLD-1-1 |", accepted), [good], main=main)
    assert any("accepted" in p and "owner OD" in p for p in problems), problems
