---
id: HANDOFF-2026-10-18-g1-decisions-recorded
date: 2026-10-18
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0006…0009 record the owner's decisions and instructions)
base_revision: f7a9ec90bb2f0cbd58272c5bd0f0da07948a4ecb
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-18-g1-decisions-recorded.md
work_commits: [fe3fdc78cb2d2b9f147122528cc5cf97db976397]   # T-0004, on branch docs/hio-001-boundary-c1 (from main), not merged
work_card: T-0001 (G1), T-0004
---

# Handoff: G1 decisions recorded; ADR-0010 revised; T-0004 prepared

> A dated snapshot. Not a decision.

## Done

- **The owner's message archived** verbatim at `docs/history/2026-10-18-owner-g1-decisions.md`.
- **Owner decision records:**

  | Record | What it records |
  |---|---|
  | OD-0006 | T-0008 accepted at `0c74686` |
  | OD-0007 | T-0006 accepted at `35c9821` |
  | OD-0008 | G1: items 1–11 and 13–20 approved **per file at `a82aa0d`**, with blob hashes; C1 chosen; projection fund-level; item 12 returned |
  | OD-0009 | `reports/` path; T-0002 and T-0003 authorised; prepare T-0004; S1a limits |

- **Status-only edits recording OD-0008**, on the 19 approved files:
  - `status: approved` and `approved_by`;
  - the ADR *Approval* sections;
  - "provisional" wording in `AGENTS.md` rule 5 and operating model §1.1, §6.2 and the
    precedence table.
- **Content change on owner instruction (OD-0009):** operating model §6.2 step 3 adds
  `reviews/reports/` (harness-0.6, logged against the approved blob `7172659cf4ba`), with a
  matching line in the review index.
- **HIO-ADR-0010 revision 2:** S1a synthetic-fixture-only, then S1b live data, with separate
  entry gates. Status `proposed`.
- **T-0004:** amendment prepared on branch `docs/hio-001-boundary-c1` from `main`, commit
  `fe3fdc7` (two documentation files, +19 lines). **Not merged.** Its temporary worktree was
  removed; the branch remains for review.
- **Cards:** T-0002/T-0003 `authorised`; T-0004 `submitted_for_review`; T-0006/T-0008
  `accepted`. Also updated: the ADR register, the OD index, STATUS, the history index.

## Not done (by instruction or because not yet requested)

- T-0002 and T-0003 are authorised, **not started**.
- No S1a work.
- No live data operation.
- The T-0004 branch is not merged.
- The implementation plan is not updated to the S1a/S1b split (it is a recommendation; it
  follows ADR-0010 approval).

## Verification

- `git diff a82aa0d HEAD -- <each approved file>` shows only `status:`, `approved_by:` and
  *Approval* lines, plus the listed provisional-wording, changelog and §6.2 `reports/` lines.
- No file outside `hio/` changed on the staging branch.
- The `macsmsf` change is isolated on `docs/hio-001-boundary-c1`.

## NOT approved by this session

- HIO-ADR-0010 revision 2.
- The harness-0.6 text.
- The factor specs, the roadmap and the plan.
- The T-0004 merge.
- G1 is **open**.

## Next permissible action

The owner decides HIO-ADR-0010 revision 2, which would complete G1, and reviews T-0004.
