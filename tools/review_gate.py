"""Reviewer-PR gate (harness-0.7, OD-0021; operating model §6.2 step 4).

Checks the CONTENT SCOPE of a reviewer PR, using policy taken only from the trusted event base
commit:
1. The PR description must contain exactly one line `Reviewed-Head: <40-hex sha>`.
2. `tools/check_review_branch.sh` is read from the base commit (git show <base>:<path>) and run
   against <Reviewed-Head> and the PR head. A PR that edits the script, or this gate, cannot
   weaken its own check: those edits are outside reviews/ and fail it.

A pass is a content-scope constraint only. It does NOT verify that the reviewed head, review id
or scope match the owner's assignment: that is tools/check_review_assignment.py, an owner step
before receipt. Standard library only. PR commits are read as git data and never executed.

Usage: python review_gate.py --base-sha <sha> --pr-head <sha> --body-file <path>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
LINE = re.compile(r"^Reviewed-Head:\s*(\S*)\s*$", re.M)
SCRIPT = "tools/check_review_branch.sh"


class GateError(Exception):
    pass


def parse_reviewed_head(body: str) -> str:
    values = LINE.findall(body.replace("\r", ""))
    if not values:
        raise GateError("the PR description has no 'Reviewed-Head: <40-hex sha>' line")
    if len(set(values)) > 1 or len(values) > 1:
        raise GateError(f"the PR description names more than one Reviewed-Head: {values}; stop and reconcile")
    if not SHA.match(values[0]):
        raise GateError(f"Reviewed-Head must be a full 40-hex sha: {values[0]!r}")
    return values[0]


def run(base_sha: str, pr_head: str, body: str, repo: Path) -> tuple[int, str]:
    for name, value in (("base", base_sha), ("PR head", pr_head)):
        if not SHA.match(value):
            raise GateError(f"{name} must be a full 40-hex sha: {value!r}")
    reviewed = parse_reviewed_head(body)
    script = subprocess.run(
        ["git", "show", f"{base_sha}:{SCRIPT}"], cwd=repo, capture_output=True, check=True
    ).stdout
    with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as fh:
        fh.write(script)
    out = subprocess.run(["sh", fh.name, reviewed, pr_head], cwd=repo, capture_output=True, text=True)
    Path(fh.name).unlink()
    return out.returncode, out.stdout + out.stderr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--pr-head", required=True)
    ap.add_argument("--body-file", required=True)
    args = ap.parse_args(argv)
    try:
        code, output = run(args.base_sha, args.pr_head, Path(args.body_file).read_text(), Path.cwd())
    except GateError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(output, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
