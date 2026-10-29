---
id: OD-0132
title: "Owner authorises Claude to work to close the gap to base camp (docs/base-camp.md, proposed): B-2 per its plan, a Codex review of T-0013, and the non-live build and drafting work for criteria 3-6 and 9, consulting the architect or Fable on details and blockers; approvals, acceptances, rights verification, go-live and purchases stay separate owner acts"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-close-basecamp-gap.md (owner's message 6, verbatim, with the decisions Claude had just put)
  sha256: 64a5cb7aeed3076e2a468d426c25d8b51e0490f6bd2e7980fa087e581d8cdfef
  date: 2026-10-29
  quote: "you are authorised to try to close the gap to base camp.  consult that architect or fable with any details you want clarified or blockers you hit."
applies_to:
  - path: main
    revision: 2765811
related: {adrs: [HIO-ADR-0012], tasks: [T-0012, T-0013], findings: [], ods: [OD-0089, OD-0090, OD-0130, OD-0131]}
---

# OD-0132: close the gap to base camp

The owner answered decisions A and B with a broader instruction. Claude's reading is recorded here, and the owner can
correct it at any time ("we can make any adjustments going forward", OD-0131).

## What Claude reads as authorised

1. **B-2 (decision A):** steps 1–8 of `docs/evidence/S1B1-B2-probe-plan.md` at `b825551`, without 7b. The plan's own
   checkpoints stay: each Azure write, GitHub change and dispatch happens after the owner's "go" on what is shown.
2. **Codex review of T-0013 (decision B):** `REVIEW-2026-10-29-t0013-1`, as put above. Receipt and acceptance are
   separate.
3. **Non-live work toward base-camp criteria 3–6 and 9:** a completion task card (cash rebuild and comparison
   dispositions, cash specifications, finality recorded alongside releases, restore exercise, the CI consumer contract
   test), its build by hiomux workers, and a data-need statement drafted as `proposed`.
4. **Consultation** of the solution architect (OD-0089) or Fable (OD-0090) on details and blockers, each summarised to
   the owner.

## What stays a separate owner act

Under AGENTS.md rule 3, each of these is tied to an exact revision: adopting `docs/base-camp.md`; accepting T-0013 or
any later task; receipt of a review; any rights verification (V1–V5, criterion 8); a change to the S2/S3-after-G2
ordering (criterion 7); a C5 amendment; **B-3 go-live** (the five URLs, `LIVE_AUTHORISATION`, enabling the alert,
removing the reviewer rule); any purchase or vendor contact.

## Corrections (append-only)
