---
id: HIO-HARNESS-0.7-PROPOSAL
title: "Decision package: harness-0.7 (integrated review flow), proposed, revision 3"
status: proposed
owner: owner (decides); drafted by claude/documentation-agent
last_reviewed: 2026-10-24
source: "collaborator advice pasted by the owner on 2026-10-24 (stage 2: 'draft a small amendment'), plus the gaps Claude reported after REVIEW-2026-10-24-s1a-1"
---

# Decision package: harness-0.7

> **No effect until the owner approves an exact revision.** The approved operating model is
> harness-0.6 (OD-0012, `f2275e2`, blob `e3114bd188ad`). This proposal lives on branch
> `proposal/harness-0.7` and is not merged.

## Why

REVIEW-2026-10-24-s1a-1 was done correctly, but the round exposed five gaps:
1. the review branch stayed local, and a prompt assumed receipt had happened;
2. assignments are valid from three places, but the review index called its table "the only
   source";
3. the author and the reviewer each had build evidence the other could not see;
4. policy questions (findings 4 and 7) had no standing place to wait for a decision;
5. no message said whose turn it was, or what had to be true before acting.

## What changes (revision 2, after the owner's review of `decf55c`)

| Gap | Rule | Where |
|---|---|---|
| Assignment | An *Assigned reviews* row, an owner PR comment, or a direct owner instruction (indexed at receipt). The review record cites its source | operating model §2.2 and §6.2 step 1; `reviews/README.md`; `AGENTS.md` |
| **Conflicting channels** (rev 2) | If channels disagree on id, base, head, scope or branch, the reviewer and the author stop and report. The owner reconciles in one statement, which becomes the cited source. No channel takes priority silently | §6.2 step 1 |
| Submission and receipt | The author PR pins `Submission-Head`. The reviewer pushes its branch and opens a PR pinning `Reviewed-Head`, with `reviews/` changes only. The owner's merge-commit merge is receipt, never acceptance | §6.2 steps 0, 3, 5 |
| **Scope check, trusted base** (rev 2) | `review-scope.yml` runs under `pull_request_target`, so it is the base branch's workflow. It reads `tools/review_gate.py` and `tools/check_review_branch.sh` with `git show` from `github.event.pull_request.base.sha`. It fetches PR commits as data and never executes them. One, and only one, full-SHA `Reviewed-Head` line is required | §6.2 step 4 |
| **Assignment verification** (rev 2; rev 3 compares the source) | New step 4a, before receipt. A scope-check pass is not assignment verification. `tools/check_review_assignment.py` compares the record's id, base, head, branch and **assignment source against an owner-supplied expected source** (required; exact after collapsing whitespace), plus descent from the head, using values **from the assignment**; the owner reads the scope | §6.2 step 4a |
| Remediation start | **Receipt before remediation is the default.** **Exception (rev 2):** only by an owner instruction recorded in an OD, naming the review id, the record's commit and each record file's sha256, where immutable evidence exists but normal receipt is blocked. Claude reads by `git show` and checks the hashes; receipt or an owner disposition is still required before verification is assigned | §6.2 step 6 |
| Evidence | Build claims cite the CI run id, attempt and SHA; independent reproduction is still required | §6.2 step 8 |
| **Open decisions** (rev 2) | `open-decisions.md` is a pointer list only: question, source, who decides, what it blocks, and the deciding OD. Options and recommendations live in the source documents. Exploratory internal use (Q-005a) is split from distribution-class approval (Q-005b) | §6.3 |
| Handoff | Every handoff and final message ends with a completion block. An unmet prerequisite means stop and report, never assume | §6.2 step 9; `templates/handoff.md`; `AGENTS.md`; PR template |
| Paths | §6.2 paths for the standalone repository | §6.2 steps 2–4 |

## Test evidence (rev 2)

`tests/test_review_gate.py` (23 tests, throwaway git repositories, no network):
- **Adversarial reviewer PRs:** source edits; non-`.md` files; executables; symlinks;
  modified submitted records; deletions; workflow edits; a merge commit. A PR that replaces
  `check_review_branch.sh` with `exit 0` and `review_gate.py` with a no-op still fails, because
  the policy comes from the base commit.
- **Mismatched heads:** a `Reviewed-Head` naming an earlier commit pulls the author's changes
  into the range and fails. A head the branch does not descend from fails. Missing, short,
  non-hex or conflicting `Reviewed-Head` lines stop the gate.
- **Assignment source (rev 3):** a record with the correct id, base, head and branch but the
  **wrong assignment source fails**. A matching source passes, whitespace differences included.
  An empty expected source fails, as do a record with no `assignment` field and a CLI call
  without `--assignment-source`.
- **Assignment verification:** passes on a matching record. A branch that **passes the scope
  gate while naming the wrong head fails assignment verification**. A wrong id, head, branch,
  base or scope term fails.
- **On the real data:** `check_review_assignment.py` passes on Codex's
  REVIEW-2026-10-24-s1a-1 (`review/s1a-1-codex` @ `b4025dd`).

**Not tested here:** the workflow file itself on GitHub. `pull_request_target` runs only from the
default branch, so it cannot run until harness-0.7 is merged. Its logic is in the two tested
scripts.

## Files in this proposal

- `docs/harness/operating-model.md` (front matter `status: proposed`, version
  `harness-0.7 (proposed)`, changelog, §2.2, §6.2, new §6.3);
- `AGENTS.md` (the reviewer bootstrap and the completion block). AGENTS.md is approved
  (OD-0008), so this needs the same approval;
- `reviews/README.md` (who writes what; the assignment heading);
- `templates/handoff.md` (completion block);
- `docs/decisions/open-decisions.md` (new);
- `.github/workflows/review-scope.yml` and `.github/pull_request_template.md` (new);
- `tools/review_gate.py` and `tools/check_review_assignment.py` (new; standard library only);
- `tests/test_review_gate.py` (new);
- `tools/check_repo.py` (exempts `.github/` from front matter).

The full diff: `git diff main proposal/harness-0.7`.

## Adoption condition (owner, 2026-10-24)

After adoption, the **first reviewer PR validates the GitHub workflow itself**: it must show that
the workflow runs under `pull_request_target` from the base commit, and that it fails a
deliberately non-conforming change. Until then, a passing workflow is not treated as an
established automated control. The owner still runs step 4 locally.

## Decision sought

Approve, revise or reject harness-0.7 **at the exact blobs of the commit you name** (the tip of
`proposal/harness-0.7`, resolved with `git rev-parse proposal/harness-0.7`; revision 1 was
`decf55c`, which the owner did not approve; revision 2 was `fcabd7f`, supported subject to the
assignment-source correction made in revision 3). On approval, Claude
records an OD, sets the operating model's `status: approved`, `approved_by` and version, and
merges the branch with `--no-ff` on your instruction.

## Interaction with the current S1a round

None required. The receipt of REVIEW-2026-10-24-s1a-1 and the remediation of findings 1–3 and
5–6 proceed under harness-0.6. If harness-0.7 is approved first, the S1a verification round can
use PRs.
