---
id: OD-0104
title: "Owner approves the H6 option B amendment at d26c2fa, and starts the fix of F-VERIFY-2026-10-28-h6-1-3-1 and response 4 on phase-b/h6; application of the amendment to the operating model, H6 activation and verification 4 not authorised"
decision: approve
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-option-b-and-h6-fix.md (owner's message, verbatim, with the decisions it answers)
  sha256: 32a54f7dc5524394f7e8345a9da80c39c8cf0f03f1c7119cb65e84580f7f77e8
  date: 2026-10-29
  quote: "continue with H6 work.  approved option b"
approves:
  - path: docs/decisions/h6-option-b-amendment.md
    revision: "d26c2faca78fc40dc409ff53c872cb172e918d7e (proposal/h6-option-b), blob 202f8d9219fcf1ab352d7809d51db81d1a63476a"
base_revision: 5d3259cb26cd0d17354d0d5c80795c867f0b4e2f
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [F-REVIEW-2026-10-28-h6-1-2, F-VERIFY-2026-10-28-h6-1-3-1], ods: [OD-0092, OD-0100, OD-0103]}
---

# OD-0104: option B approved; the H6 fix started

## What is approved

The amendment `docs/decisions/h6-option-b-amendment.md` at `d26c2fa` (blob `202f8d92…`), the revision Claude named
when putting the decision. `proposal/h6-option-b` was still at `d26c2fa` when this was recorded.

**Consequence for the index:** F-REVIEW-2026-10-28-h6-1-2 was reconciled to `verified_closed` against the *draft*
option B, final only on approval (OD-0103). With this approval, that condition is met. The row is unchanged.

## What is authorised (work)

"continue with H6 work" answers decision 1 as put. Under OD-0092 and OD-0100:
- one Sonnet worker fixes F-VERIFY-2026-10-28-h6-1-3-1 on `phase-b/h6` (head `cd87bc0`), limited to
  `tools/hio_receive.py` and `tests/test_hio_receive.py`, with a test that fails before the fix and CI's exact lint
  commands;
- Claude checks it, integrates exactly the checked commit, and proves the test catches the defect;
- response 4.

## Not authorised

- **Applying the amendment** to `docs/harness/operating-model.md` and the H6 design wording (harness-0.9b). The
  owner approved the text; the edit to `main` waits for an explicit instruction, as OD-0091 gave for harness-0.9a.
- Pushing any branch.
- Assigning or launching verification 4.
- H6 approval or activation; H11.
- `hiomux cleanup 20261028T081310Z-d55d` (decision 2, unanswered).

## Corrections (append-only)
