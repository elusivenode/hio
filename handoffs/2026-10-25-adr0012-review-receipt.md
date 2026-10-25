---
id: HANDOFF-2026-10-25-adr0012-review-receipt
date: 2026-10-25
actor: claude/implementation-agent (Claude Sonnet 5.5)
work_status: authorised   # OD-0050: receipt done; ADR-0012 proposed; findings open; nothing approved
base_revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-25-adr0012-review-receipt.md
work_commits: [eadda1e5da5df2d5141d7951abed14df40f70782]
work_card: T-0005
---

# Handoff: REVIEW-2026-10-25-adr0012 received; remediation plan

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Done
- Receipt by one-off byte-identical import (OD-0050), commit `eadda1e`: the record and handoff
  have the reviewer's blob ids; the `README` change adds exactly Codex's lines, removes none; the
  reviewer's commit `1a05d8e` is kept by the tag `reviews/REVIEW-2026-10-25-adr0012` and the
  remote branch. PR #5 is closed unmerged. PR #4 is untouched.
- A second commit: OD-0050, the verbatim instruction, the index status cell, STATUS and this
  handoff.

## The three findings (all open; immutable in the record)
| Finding | Severity | Summary |
|---|---|---|
| F-REVIEW-2026-10-25-adr0012-1 | high | §4.3 gives a first capture `knowable_at` = the documented publication time P. The RBA allows deferred publication and the NY Fed publishes the index "shortly after" 08:00 ET, so P can be earlier than this vintage's actual publication |
| F-REVIEW-2026-10-25-adr0012-2 | high | §4.3 calls a release final when its `knowledge_cutoff` is after the window close W, even if the post-window capture has not happened (revision at 15:50, final capture 16:30, build at 16:10) |
| F-REVIEW-2026-10-25-adr0012-3 | medium | the SOFR Index can be revised at about 14:30 ET for an index-calculation error without a SOFR rate revision; §4.3 groups both under the 1 bp rule |

## Bounded remediation plan (for the owner's instruction; nothing started)
**Scope:** edit HIO-ADR-0012 §4.3, §4.2 gates and §5 mapping only, on PR #4's branch, producing
a new fixed `Submission-Head`. No standard, return mathematics, S1a code or rights value changes.

1. **F1: stop inferring publication from the schedule.**
   - Split P into the documented schedule (an upper-bound expectation, never evidence) and an
     **observed** per-vintage instant.
   - Where a capture carries the publisher's own timestamp, such as an HTTP `Last-Modified`
     header, record it in the receipt metadata and use it (`publisher_timestamp`; observations
     §3 explicitly allows headers).
   - Otherwise set `knowable_at` to no earlier than the first capture that contains the value,
     and state which `knowable_basis` it carries. **Open design point:** the approved
     definition of `captured_on_schedule` ("the documented release time preceding that
     capture") may not fit a capture-time bound. If no existing basis fits, that is **a
     required standards clarification, and I will escalate it rather than decide it.**
   - Add to the S1b-1 gate: header and payload timestamp semantics evidenced per source. For
     the NY Fed API, no header evidence has been examined, and further manual inspection needs
     your approval.
2. **F2: define finality by evidence.**
   - A release is final for an input only if a **post-window capture exists with `captured_at`
     ≥ W and ≤ `knowledge_cutoff`**.
   - **Constraint found in the accepted S1a code:** `capture()` returns early and writes
     nothing for an identical consecutive re-fetch, so an unchanged final capture leaves no
     durable record. The fix is an **additive** S1b capture-attempt record, specified in the
     ADR, with `capture()` unchanged. That is not an S1a change, but it must be stated
     explicitly.
   - Specify failed, delayed and unchanged final captures. Otherwise the release is provisional.
3. **F3: separate SOFR and SOFR Index rules.** Index-only corrections get their own trigger,
   and the post-window Index check runs even when the SOFR rate and `revisionIndicator` are
   unchanged. No standards effect.
4. **Verify:** Codex re-verifies the three findings at the new head, by a verification record
   (`VERIFY-…`), delivered under the harness-0.7.1 procedure as a second one-off exception, or
   under harness-0.7 if you prefer.
5. **Escalate only if:** F1 needs a standards clarification (above); the assignment or scope
   changes; or a rights value would need to be verified.

## Not done / not approved
- HIO-ADR-0012, harness-0.7.1, any finding closure or waiver, any source right, S1b, PR #4's merge.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `receipt/REVIEW-2026-10-25-adr0012`; import commit `eadda1e5da5df2d5141d7951abed14df40f70782`; this handoff in the next commit |
| Pushed? PR link | `main` and the tag are pushed after the merge; no PR (PR #5 closed unmerged) |
| Received into `main`? | yes, by the receipt merge (stated in the report) |
| Next actor | **owner** |
| Prompt for the owner | "Instruct the F1–F3 remediation on PR #4's branch (and decide the F1 basis question if it needs a standards clarification). Prerequisite: the receipt merge is in `main`." |
