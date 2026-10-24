---
id: OD-0026
title: "Owner instruction: refine the Q-001 and Q-002 draft amendments (drafting only); F6 verification acknowledged"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-q001-q002-drafting.md (pasted by the owner, verbatim)
  sha256: 70bbdb22c30759992204e97aad2d98aec579db1747bf8b2356523359d846db84
  date: 2026-10-24
  quote: "This instruction authorises drafting only. Do not change implementation code or the approved observation standard yet."
applies_to:
  - path: docs/standards/drafts/
    revision: d9fa2766126aa38bb9cfbce83f37818a0d65fe4a   # PR #2 head verified by VERIFY-2026-10-24-s1a-1-5
evidence:
  - review_id: VERIFY-2026-10-24-s1a-1-5
    commit: 6d8b60d4498f2cd911f84980b17946b27d555a52
    record_sha256: 2e851b84b7f7db3635b6a4dcd7d2037da33b183ef27b1962081d946009c171ae   # verdict READY; preserved, not received
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0026: refine the Q-001 and Q-002 drafts

## Owner action

1. **Acknowledged:** Codex's verification of F6 at `d9fa276` (VERIFY-2026-10-24-s1a-1-5, READY,
   "verified_closed" within the S1a local single-writer storage contract).
   - The record is preserved at `6d8b60d`; it is not received into `main`.
   - The review index's F6 row is the reviewer's to update at receipt, so this record changes
     no index state.
2. **Drafting authorised.** Refine OBS-AMEND-Q001 and OBS-AMEND-Q002 to cover:
   - Option A as refined by the quoted solution-architecture advice;
   - the information clocks;
   - mode-specific behaviour;
   - conflict adjudication;
   - executable regression invariants.

## Reading

- The pasted text combines solution-architecture advice ("for owner adoption") with an
  instruction in the owner's voice. The advice is treated as the brief for the drafts.
- Option A is **not adopted** by this record. Adoption, and approval of any standard change,
  are separate owner actions at an exact revision.

## What this record does NOT do

- It does not change implementation code or the approved observation standard (v0.2).
- It does not merge PR #2 or PR #3, or receive any review record.
- It does not close findings 4, 6 or 7, accept S1a, start S1b, or change the harness.
