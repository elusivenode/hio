---
id: T-0007
title: Add the review branch and worktree protocol to the harness (documentation + one check script)
status: accepted
owner: owner
assignee_role: documentation agent (Claude)
created_at: 2026-10-18
updated_at: 2026-10-18
authorised_by: OD-0003
base_revision: bada9526342d62fc2776e8f71aedf26097ab65ac
accepted_by: OD-0004    # accepted at b48f83cdca6f272d76730346372f6b939855e092
review_required: owner; optionally Codex, as part of a later harness or A01 verification
links: {adrs_governing_approved: [], adrs_context_proposed: [HIO-ADR-0008], specs: [], standards: [], findings: [], depends_on: [], blocks: [the next assigned Codex review]}
---

# T-0007: review branch and worktree protocol

## State history (append-only)

| Date | State | Revision | Basis |
|---|---|---|---|
| 2026-10-18 | authorised → in_progress | from `bada952` | OD-0003 |
| 2026-10-18 | submitted_for_review | `46ea6a5` | harness-0.4 |
| 2026-10-18 | changes required, then in_progress | from `46ea6a5` | a Codex assessment, pasted by the owner without words (`docs/history/2026-10-18-codex-assessment-t0007.md`). Its three points are defects in T-0007's own deliverables, so they are remediated within OD-0003's scope. It is not a review record, and no findings were registered |
| 2026-10-18 | submitted_for_review | `b48f83c` | harness-0.5: per-commit check, required record, reviewer handoff exception, two-SHA remediation |
| 2026-10-18 | reviewed | `46ea6a5..b48f83c` | REVIEW-2026-10-18-t0007-pilot (Codex): READY, no findings; received by merge `385389d` |
| 2026-10-18 | **accepted** | `b48f83c` | OD-0004: the owner's statement "I accept T-0007 at b48f83c" |

**Accepted at `b48f83c` only.** HIO-ADR-0008 remains proposed, and the protocol stays provisional. Any later change to these files is new work.

## Purpose and rationale

Give independent reviews a fixed revision, an isolated checkout, and a write scope that can be
checked mechanically. This keeps reviewer evidence separable from the work under review, and
makes "merge" mean *receipt*, not approval.

Brief: [`../../docs/history/2026-10-18-directive-review-worktree-protocol.md`](../../docs/history/2026-10-18-directive-review-worktree-protocol.md).

## Owner-instructed scope (OD-0003)

- operating model §2.2, §3 and §6.2;
- the review index's "Who writes what";
- an `AGENTS.md` pointer;
- the review, verification and remediation-response templates;
- `hio/tools/check_review_branch.sh`.

## Exclusions

- ADR statuses;
- Codex's review record and findings;
- remediating any A01 finding;
- code beyond the check script;
- `macsmsf`;
- HIO-S1.

## Acceptance evidence (directive §10)

| # | Criterion | Where / evidence |
|---|---|---|
| 1–2 | A fresh Codex session finds an assignment, or reports that there is none | AGENTS.md; operating model §2.2; the review index *Assigned reviews*. A **fresh-session test is pending** |
| 3 | separate worktree; review-only commit | §6.2 steps 2–3. Not yet exercised by Codex |
| 4 | a repeatable check fails on non-review paths and unexpected file types, **in any commit**, and fails on empty branches | `hio/tools/check_review_branch.sh`; synthetic-branch results in the T-0007 handoffs |
| 5 | merge documented as receipt | §6.2 step 5 |
| 6 | original findings immutable; separate response and verification records with SHAs | §3; templates |
| 7 | waivers and acceptance remain explicit owner actions tied to revisions | §1.1 (unchanged) |
| 8 | no new heavyweight ritual or duplicate authority | §6.2 is one section; the index is a summary; records are the source of truth |
