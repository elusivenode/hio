"""Scripted review assignment (harness-0.9 H6; operating model §6.2 step 1).

From the owner's values this prints (1) the *Assigned reviews* row for reviews/README.md and
(2) the exchange message for the reviewer. It writes nothing unless --apply is given; then it
inserts the row into the table in the working tree only (no commit). The owner still commits
the row: the tool transcribes an assignment, it does not make one.

It refuses a second assignment for the same target (step 1, "conflicting channels"):
  - the review id is already assigned or recorded (index tables or reviews/records/);
  - another active assignment exists for the same repository and head, whatever its scope or id
    (active: the status cell does not mark it received, withdrawn or superseded);
  - a SHA is not 40 lowercase hex characters;
  - inside a repository holding both commits, the head is not a descendant of the base.

Usage:
  python tools/hio_assign.py --review-id ID --repo REPO --base SHA --head SHA \
      --scope "..." [--scope "..."] [--branch review/ID-codex] [--reviewer codex] \
      [--kind review|verify] [--od OD-0099] [--apply]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
ROLE = re.compile(r"[a-z][a-z0-9_-]*")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
HEADING = "## Assigned reviews"
RECORDED_HEADING = "## Reviewed revisions and review records"
SCOPE_END = ". Review branch `"
INITIAL_STATUS = "assigned"
INACTIVE = re.compile(r"received|withdrawn|superseded", re.IGNORECASE)


class Refusal(Exception):
    """The assignment is refused; the message says why."""


def cells(line: str) -> list[str]:
    return [c.strip() for c in CELL_SPLIT.split(line.strip().strip("|"))]


def plain(cell: str) -> str:
    return cell.replace("`", "").replace("*", "").strip()


def norm(text: str) -> str:
    return " ".join(text.split())


def table_after(lines: list[str], heading: str) -> tuple[int, list[int]]:
    """Return (index of the separator line, indexes of the data rows of the table under the heading)."""
    start = next((i for i, ln in enumerate(lines) if ln.startswith(heading)), None)
    if start is None:
        raise Refusal(f"reviews/README.md has no {heading!r} section")
    rows: list[int] = []
    in_table = False
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("|"):
            in_table = True
            rows.append(i)
        elif in_table or lines[i].startswith("## "):
            break
    if len(rows) < 2:
        raise Refusal(f"the table under {heading!r} has no header and separator")
    return rows[1], rows[2:]


def scope_cell(scopes: list[str], branch: str, reviewer: str, kind: str) -> str:
    label = "Verification" if kind == "verify" else "Review"
    return f"{label}: {'; '.join(scopes)}{SCOPE_END}{branch}`. Reviewer: {reviewer}"


def scope_part(cell: str) -> str:
    """The scope wording of a Task / scope cell, without the branch and reviewer suffix."""
    return norm(cell.split(SCOPE_END)[0])


def assigned_by(od: str | None, owner_dir: Path) -> str:
    if not od:
        return "owner instruction (OD record to follow)"
    for p in sorted(owner_dir.glob(f"{od}-*.md")):
        return f"[{od}](../docs/decisions/owner/{p.name}) (owner instruction, transcribed)"
    return f"{od} (owner instruction, transcribed)"


def build_row(a: argparse.Namespace, owner_dir: Path) -> str:
    fields = [
        a.review_id,
        f"`{a.repo}`",
        f"`{a.base}`",
        f"`{a.head}`",
        scope_cell(a.scope, a.branch, a.reviewer, a.kind),
        assigned_by(a.od, owner_dir),
        INITIAL_STATUS,
    ]
    return "| " + " | ".join(fields) + " |"


def build_message(a: argparse.Namespace) -> str:
    what = "verification" if a.kind == "verify" else "review"
    scope = "\n".join(f"- {s}" for s in a.scope)
    return f"""\
Review assignment: {a.review_id} ({what})

Repository: {a.repo}
Base: {a.base}
Head: {a.head}
Scope:
{scope}
Review branch: {a.branch}
Reviewer: {a.reviewer}

Delivery rules (operating model §6.2 steps 1 to 3):
- Work in your own worktree, on the review branch cut at the head above:
  git worktree add ../hio-{a.review_id} {a.head} -b {a.branch}
- Write only .md files under reviews/. Never edit the work under review, STATUS.md or handoffs/.
  No merge commits.
- Push the review branch {a.branch}. Open no pull request: an unpushed branch has not been
  submitted.
- Your final message is your independent report. State the pushed branch, the branch tip SHA,
  the reviewed head ({a.head}) and the sha256 of every file you added. The receiver reconciles
  against it.
- If this assignment conflicts with another owner-authored source, stop before reviewing and
  report the conflict.
"""


def check_values(a: argparse.Namespace) -> None:
    if not ID.fullmatch(a.review_id):
        raise Refusal(f"malformed review id {a.review_id!r}")
    if not BRANCH.fullmatch(a.branch) or ".." in a.branch or a.branch.endswith(("/", ".lock")):
        raise Refusal(f"malformed review branch {a.branch!r}")
    if not ROLE.fullmatch(a.reviewer):
        raise Refusal(f"reviewer {a.reviewer!r} is not a declared role name (lowercase letters, digits, - _)")
    for name, value in (("base", a.base), ("head", a.head)):
        if not SHA.fullmatch(value):
            raise Refusal(f"{name} {value!r} is not a full 40-character lowercase hex SHA")
    if a.base == a.head:
        raise Refusal("base and head are the same commit")
    if not a.repo.strip():
        raise Refusal("repository is empty")
    for text in [a.repo, a.od or "", *a.scope]:
        if "|" in text or "\n" in text or "\r" in text:
            raise Refusal(f"{text!r} contains '|' or a line break, which cannot sit in a table cell")
    if any(not s.strip() for s in a.scope):
        raise Refusal("an empty --scope")


def commit_exists(sha: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True
        ).returncode
        == 0
    )


def check_ancestry(base: str, head: str) -> str | None:
    """Refuse a head that does not descend from the base, where git can tell. Return a note if not."""
    have_base, have_head = commit_exists(base), commit_exists(head)
    if have_base and have_head:
        rc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, head], capture_output=True
        ).returncode
        if rc == 1:
            raise Refusal(f"head {head} is not a descendant of base {base}")
        if rc:
            raise Refusal("git could not compare base and head")
        return None
    if have_base or have_head:
        which = "base" if have_base else "head"
        return f"note: only the {which} commit is present in this repository; ancestry not checked"
    return "note: neither commit is present in this repository; ancestry not checked"


def check_conflicts(a: argparse.Namespace, lines: list[str], readme: Path) -> None:
    _, assigned = table_after(lines, HEADING)
    recorded = []
    if any(ln.startswith(RECORDED_HEADING) for ln in lines):
        recorded = table_after(lines, RECORDED_HEADING)[1]
    for i in assigned + recorded:
        row = cells(lines[i])
        if row and plain(row[0]) == a.review_id:
            raise Refusal(f"review id {a.review_id} is already assigned or recorded (README line {i + 1})")
    records = readme.parent / "records"
    if records.is_dir() and any(records.glob(f"{a.review_id}.md")):
        raise Refusal(f"review id {a.review_id} already has a record in {records}")
    for i in assigned:
        row = cells(lines[i])
        if len(row) < 7 or plain(row[3]) != a.head or plain(row[1]) != a.repo.strip():
            continue
        if INACTIVE.search(row[6]):
            continue
        raise Refusal(
            f"second assignment for the same target (operating model §6.2 step 1): "
            f"{plain(row[0])} is already active for {a.repo} head {a.head} (README line {i + 1}), "
            "whatever the scope wording. Do not pick one: the owner reconciles it in one "
            "statement that names the assignment that stands, and marks the other "
            "received, withdrawn or superseded"
        )


def apply_row(readme: Path, lines: list[str], row: str, newline: str) -> None:
    separator, assigned = table_after(lines, HEADING)
    lines.insert((assigned[-1] if assigned else separator) + 1, row)
    readme.write_text(newline.join(lines) + newline)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--review-id", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True, help="full 40-hex SHA")
    ap.add_argument("--head", required=True, help="full 40-hex SHA")
    ap.add_argument("--scope", action="append", required=True, help="repeatable")
    ap.add_argument("--branch", help="default: review/<review-id>-codex")
    ap.add_argument("--reviewer", default="codex", help="a declared role (default: codex)")
    ap.add_argument("--kind", choices=("review", "verify"), default="review")
    ap.add_argument("--od", help="OD record id for provenance, e.g. OD-0099")
    ap.add_argument("--readme", default="reviews/README.md", help="the index to check and update")
    ap.add_argument("--apply", action="store_true", help="insert the row into the README (no commit)")
    a = ap.parse_args(argv)
    a.branch = a.branch or f"review/{a.review_id}-codex"
    readme = Path(a.readme)
    try:
        check_values(a)
        note = check_ancestry(a.base, a.head)
        if not readme.is_file():
            raise Refusal(f"{readme} not found")
        text = readme.read_text()
        newline = "\r\n" if "\r\n" in text else "\n"
        lines = text.splitlines()
        check_conflicts(a, lines, readme)
        row = build_row(a, readme.parent.parent / "docs" / "decisions" / "owner")
        if a.apply:
            apply_row(readme, lines, row, newline)
    except Refusal as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    if note:
        print(note, file=sys.stderr)
    print("Row for reviews/README.md, Assigned reviews:\n")
    print(row)
    print("\nMessage to the reviewer:\n")
    print(build_message(a))
    if a.apply:
        print(f"APPLIED: row inserted into {readme} (working tree only; not committed)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
