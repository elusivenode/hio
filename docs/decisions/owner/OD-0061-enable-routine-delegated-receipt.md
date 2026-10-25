---
id: OD-0061
title: "Owner enables routine delegated receipt of review and verification evidence under the OD-0060 conditions; the harness-0.7.1 adoption condition (OD-0056) is recorded as met"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-enable-routine-delegated-receipt.md (typed by the owner, verbatim)
  sha256: 14077c8856da1f9d9c6e56cc6d4d93b51757628c64a5abed4dac806b83cbbfae
  date: 2026-10-25
  quote: "Enable routine delegated receipt under the OD-0060 conditions"
applies_to:
  - path: docs/decisions/owner/OD-0060-b2-receipt-and-local-exchange.md
    revision: bdc971a8ee16b3f70266263898e851077078ee4b   # on main since this merge
related: {adrs: [], tasks: [], findings: []}
---

# OD-0061: enable routine delegated receipt

## Owner action

Enable routine delegated receipt, under the conditions in OD-0060 ("Recommendation"). Recorded by Claude as a
transcription of that one instruction; no operating-model text, tool, workflow or hook is changed (the owner
asked for no further harness work).

## What is enabled, and only this

Claude (or another agent the owner names) may perform a **receipt** (operating model §6.2 step 5, the corrected
text) of a `VERIFY-*` or `REVIEW-*` record **without a per-receipt go-ahead before the push to `main`**, provided **all**:

1. an **owner-authored assignment source** exists for that exact review id, base, head and branch (§6.2 5.0.1);
2. the reviewer's **independent report** (5.0.2) is held: Codex's own final message relayed by the owner, **or** Codex's
   report published by Codex itself in `~/.local/share/hio/agent-exchange/codex/` and checked against Git with
   `hio-exchange check`. *Claude's reading of the owner's intent (the exchange was authorised to remove routine relay);
   the owner may narrow this to relayed messages only by a later OD.* The record's own claims and Git-computed
   hashes never substitute for it;
3. the import needs **no `reviews/README.md` change, or only Class N rows** (5.6).

All of §6.2 5.0 to 5.11 still runs in full, including the second-assignment search, the tag first, blob checks,
`check_repo.py trailers` on the unpublished import commit, the 5.9 recheck, the 5.10 verification and the
`HIO-Actor` trailer on every commit.

## What still needs the owner's go-ahead (stop and report)

A Class S transition; an index conflict or any hunk failing 5.6; a missing or withheld 5.0 input; any stop
condition in §6.2; a review whose assignment source is not owner-authored; a tip or tag mismatch. Also unchanged: a
receipt is evidence only. Acceptance, approval, waiver and closure remain separate owner actions.

## Mandatory with every delegated receipt

- The **receipt sweep** (`git ls-remote origin 'refs/heads/review/*'`) at the start and end, listing every branch not recorded
  as received or dispositioned.
- Adverse verdicts and open findings reported first, with the record path.
- **CI reported as a separate result** (run id and head SHA per pushed commit), never merged with integrity.
- The receipt recorded in an OD (and the import commit kept pure).

## Accepted weaknesses (restated from OD-0059/OD-0060)

The 5.6 semantic check is manual; the assignment checker's expected string comes from the receiver's text citing the
owner file; an author-receiver is not independent (where the owner wants independence, the owner or a different
agent receives); the exchange is not authenticated (same host user).

## Adoption condition

OD-0056's condition (a supervised first receipt, recorded, before routine receipt) is recorded as **met** by OD-0058 (A2),
OD-0059 (correction) and OD-0060 (B2 clean under the corrected text), on the owner's decision here. The operating
model's changelog still states the condition as text; this OD is the record that it is satisfied, and the text is not
edited (approved standard).

## What this record does NOT do

Accept, approve or waive anything; close findings or update index rows; alter any standard, tool, workflow or
hook; change source-rights states; authorise S1b; grant review assignments; start a harness revision or review cycle.

## Corrections (append-only)

None.
