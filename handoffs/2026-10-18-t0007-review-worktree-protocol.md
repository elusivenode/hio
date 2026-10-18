---
id: HANDOFF-2026-10-18-t0007-review-worktree-protocol
date: 2026-10-18
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0003) → submitted_for_review; NOT accepted
base_revision: bada9526342d62fc2776e8f71aedf26097ab65ac
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-18-t0007-review-worktree-protocol.md
work_commits: []
work_card: T-0007
---

# Handoff: review branch and worktree protocol (harness-0.4)

> A dated snapshot. Not a decision.

## Done

- **Operating model:**
  - new §6.2: assignment fields, worktree and branch, allowed writes, scope check, merge as
    receipt, remediation, verification, index-as-summary, the transition note on `bada952`, the
    hosted evolution path;
  - §2.2: the reviewer takes its review branch from the assignment;
  - §3: immutable findings, plus separate response and verification records, with the
    directive's suggested states mapped onto ours.
- **Review index:** "Who writes what" rewritten. Codex's review and finding rows are
  **untouched**.
- **`AGENTS.md`:** a one-line reviewer pointer.
- **Templates:**
  - review record: `review_branch`; verdicts `READY | READY WITH CONDITIONS | NOT READY`;
    verification moved out to separate records;
  - new `verification-record.md` and `remediation-response.md`.
- **New `hio/tools/check_review_branch.sh`.** It sits outside `hio/reviews/`, so a review
  branch cannot alter it without failing its own check.
- OD-0003; T-0007; the directive archived verbatim; index, STATUS and history entries.

## Tests and evidence

Synthetic branches were created from `35c9821` in a scratch worktree, then removed.

| Case | Expected | Result |
|---|---|---|
| new record + index row only | PASS | PASS (exit 0) |
| `hio/STATUS.md` changed | FAIL | FAIL: path outside `hio/reviews/` |
| symlink under `reviews/records/` | FAIL | FAIL: mode 120000 |
| an existing record modified; a `.json`; an executable `.md` | FAIL ×3 | all three reported |
| a record deleted | FAIL | FAIL: status D |
| a merge commit in the range | FAIL | FAIL: merge commits |
| the real `bada952` against `35c9821` | FAIL (pre-protocol) | FAIL: `hio/STATUS.md`, `hio/handoffs/…` |

The first draft of the script had two defects, both found by these tests and fixed before
commit:
- `grep -q` truncated reporting;
- a `case` syntax error inside a command substitution.

Documentation checks (YAML, front matter, links and anchors, STATUS length): see the commit
message.

## Not verified

- **Codex has not yet used the protocol.** No fresh Codex cold-start session has been run
  against harness-0.4.
- A wrong assigned SHA that is an *ancestor* of the true head is caught only indirectly, when
  the extra commits touch non-review paths. The check is relative to the SHA the owner passes.

## Observations (not acted on)

- `bada952` predates the protocol. It wrote `hio/STATUS.md` and `hio/handoffs/`, which reviewers
  may no longer do. Recorded in §6.2 as history, not a precedent.
- The eight A01 findings are **open and untouched**. Remediation needs an owner instruction.

## NOT approved by this session

- T-0006 and T-0007 are not accepted.
- HIO-ADR-0008 and all A01 ADRs remain proposed.
- No finding was closed, waived or remediated.
- No review is assigned.

## Next permissible action

The owner:
1. advises Codex of §6.2;
2. decides whether to instruct a correction slice for the A01 findings;
3. accepts or returns T-0006 and T-0007.
