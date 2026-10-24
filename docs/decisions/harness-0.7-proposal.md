---
id: HIO-HARNESS-0.7-PROPOSAL
title: "Decision package: harness-0.7 (integrated review flow), proposed"
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

## What changes

| Gap | Rule | Where |
|---|---|---|
| Assignment | An *Assigned reviews* row, an owner PR comment, or a direct owner instruction (indexed at receipt). The review record cites the source | operating model §2.2 and §6.2 step 1; `reviews/README.md`; `AGENTS.md` |
| Submission and receipt | The author PR pins `Submission-Head`. The reviewer pushes its branch and opens a PR pinning `Reviewed-Head`, with `reviews/` changes only. The owner's merge-commit merge is receipt, never acceptance. Remediation starts from a named receipt commit | §6.2 steps 0, 3, 5, 6 |
| Scope check in CI | `.github/workflows/review-scope.yml` runs the **base branch's** `check_review_branch.sh` against `Reviewed-Head` on every `review/*` PR | §6.2 step 4 |
| Evidence | Build claims cite the CI run id, attempt and SHA; independent reproduction is still required | §6.2 step 8 |
| Open decisions | `docs/decisions/open-decisions.md`: a navigation queue linking each question to its source and, later, its OD. It grants no authority; `pending-owner-decisions.md` stays as history | new §6.3 |
| Handoff | Every handoff and final message ends with a completion block: branch and SHA, pushed or not, received or not, the next actor, and a prompt with explicit prerequisites | §6.2 step 9; `templates/handoff.md`; `AGENTS.md`; PR template |
| Paths | §6.2 paths updated for the standalone repository (`reviews/`, `../hio-review-<id>`) | §6.2 steps 2–4 |

**Unchanged:**
- records stay authoritative;
- the reviewer still reproduces independently;
- merge is receipt only;
- acceptance, approval and waiver are separate owner actions;
- a PR is never an approval.

## Files in this proposal

- `docs/harness/operating-model.md` (front matter `status: proposed`, version
  `harness-0.7 (proposed)`, changelog, §2.2, §6.2, new §6.3);
- `AGENTS.md` (the reviewer bootstrap and the completion block). AGENTS.md is approved
  (OD-0008), so this needs the same approval;
- `reviews/README.md` (who writes what; the assignment heading);
- `templates/handoff.md` (completion block);
- `docs/decisions/open-decisions.md` (new);
- `.github/workflows/review-scope.yml` and `.github/pull_request_template.md` (new);
- `tools/check_repo.py` (exempts `.github/` from front matter).

The full diff: `git diff main proposal/harness-0.7`.

## Decision sought

Approve, revise or reject harness-0.7 **at the exact blobs of the commit you name** (the tip of
`proposal/harness-0.7`, resolved with `git rev-parse proposal/harness-0.7`). On approval, Claude
records an OD, sets the operating model's `status: approved`, `approved_by` and version, and
merges the branch with `--no-ff` on your instruction.

## Interaction with the current S1a round

None required. The receipt of REVIEW-2026-10-24-s1a-1 and the remediation of findings 1–3 and
5–6 proceed under harness-0.6. If harness-0.7 is approved first, the S1a verification round can
use PRs.
