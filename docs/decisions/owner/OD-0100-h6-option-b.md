---
id: OD-0100
title: "Owner authorises drafting option B for H6 (receipt imports evidence with Class N index changes only; finding-state changes become a separate owner-authorised reconciliation) and the matching receiver change on phase-b/h6; nothing approved or activated"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-h6-option-b.md (owner's message, verbatim, with Claude's question)
  sha256: 1dddd38628691c950c7f2ddd4a6656545debfe4c9621f9cc70e9f52675f3e32e
  date: 2026-10-28
  quote: "yes"
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [F-REVIEW-2026-10-28-h6-1-2], ods: [OD-0061, OD-0089, OD-0092, OD-0099]}
---

# OD-0100: H6 option B (drafting and implementation work)

## Basis

**F-REVIEW-2026-10-28-h6-1-2** survived two rounds of fixes. A free-text outcome cell can always contradict its
token, and the second verification showed a published false closure.

**The architect's advice** (consultation `20261028T211545-ask-2e83`, summarised to the owner; advice only):
- choose B now;
- A or C would fix only how outcomes are written, not reviewers lacking `main`'s finding rows;
- revisit automated Class S handling only if separate reconciliation proves costly.

## What is authorised

1. **Drafting, on a proposal branch:**
   - the exact amendment to operating model §6.2:
     - step 5.6 allows Class N changes only;
     - a defined way to receive a record when its reviewer's index change is refused, never silently dropping
       part of it;
     - a separate, owner-authorised administrative step that reconciles finding rows against named, received
       verification records, transcribing their technical outcome and accepting nothing;
   - the matching H6 design wording.
2. **The receiver change on `phase-b/h6`:** `hio_receive.py` refuses any change to an existing finding row, and reports
   "index reconciliation pending" when a received record states outcomes the index does not show.

## Not authorised

- Approval of the amendment, which needs the owner at an exact revision.
- Activation of H6.
- Any change to existing records.

## Corrections (append-only)
