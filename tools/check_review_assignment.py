"""Assignment verification before receipt (harness-0.7 proposed; operating model §6.2 step 4a).

The owner supplies the values from the AUTHORITATIVE assignment (an Assigned reviews row, an
owner PR comment, or the owner's direct instruction). This compares them with the review or
verification record that the review branch adds. It is separate from the scope check: a
branch can pass the scope check while reviewing the wrong head, under the wrong id or scope.

Checks: exactly one record with the assigned id is added on the branch; its front matter names
the assigned base, head and review branch, and states its assignment source; the branch
descends from the assigned head. Scope wording is compared by the owner reading the record;
--scope-terms adds a mechanical check that each named term appears in the record.

Usage:
  python tools/check_review_assignment.py --review-id ID --base SHA --head SHA \
      --branch review/<id>-codex [--scope-terms "T-0005,S1a"]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

KEYS = ("id", "reviewed_base", "reviewed_head", "review_branch", "assignment")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([a-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if km:
            out[km.group(1)] = km.group(2).strip("\"'")
    return out


def verify(review_id: str, base: str, head: str, branch: str, scope_terms: list[str]) -> list[str]:
    problems = []
    for name, ref in (("assigned head", head), ("review branch", branch)):
        if subprocess.run(
            ["git", "rev-parse", "--verify", "-q", f"{ref}^{{commit}}"], capture_output=True
        ).returncode:
            return [f"{name} {ref!r} does not resolve to a commit"]
    tip = git("rev-parse", "--verify", f"{branch}^{{commit}}").strip()
    if git("merge-base", head, tip).strip() != head:
        problems.append(f"{branch} does not descend from the assigned head {head}")
    added = [
        p
        for p in git("diff", "--name-only", "--diff-filter=A", head, tip).split()
        if re.match(r"^(hio/)?reviews/records/(REVIEW|VERIFY)-[^/]+\.md$", p)
    ]
    records = [(p, git("show", f"{tip}:{p}")) for p in added]
    matching = [(p, t) for p, t in records if front_matter(t).get("id") == review_id]
    if len(matching) != 1:
        problems.append(
            f"expected exactly one added record with id {review_id}; found {len(matching)} "
            f"(records added: {added})"
        )
        return problems
    path, text = matching[0]
    fm = front_matter(text)
    for key in KEYS:
        if not fm.get(key):
            problems.append(f"{path}: front matter lacks {key}")
    expected = {"reviewed_base": base, "reviewed_head": head, "review_branch": branch}
    for key, value in expected.items():
        if fm.get(key) and fm[key] != value:
            problems.append(f"{path}: {key} is {fm[key]!r}; the assignment says {value!r}")
    for term in scope_terms:
        if term not in text:
            problems.append(f"{path}: scope term {term!r} does not appear in the record")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--review-id", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--scope-terms", default="")
    a = ap.parse_args(argv)
    terms = [t.strip() for t in a.scope_terms.split(",") if t.strip()]
    problems = verify(a.review_id, a.base, a.head, a.branch, terms)
    for p in problems:
        print(f"FAIL: {p}")
    print(
        "PASS: the record matches the assignment values supplied"
        if not problems
        else f"FAIL: {len(problems)}"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
