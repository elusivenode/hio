---
id: OD-0169
title: "Owner waives further independent verification of F-REVIEW-2026-11-04-t0022-1-4 and accepts the fix at 75c67a4"
decision: waive
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-waive-f4.md (owner's message, verbatim)
  sha256: 6cc0447f8ae57dc29d8d393c5e9efb4921283db6aa2829a5357b0f3a8edd74e2
  date: 2026-11-04
  quote: "yes to all"
base_revision: 5cfb9f6e95db2a8bd6f12e76a162f4df7f717330
related: {adrs: [], tasks: [T-0022], findings: [F-REVIEW-2026-11-04-t0022-1-4], ods: [OD-0162, OD-0167, OD-0168]}
---

# OD-0169: waiver for F-4

**Waived, by the owner:** further independent verification of F-REVIEW-2026-11-04-t0022-1-4. The fix at `75c67a4` (`tools/eodhd_eval.py`, `private_write`) is accepted. **Stated basis:** exploiting it needs someone able to plant links inside the owner's private folder, on a single-user Mac. **Stated against it:** Codex found something real on all three passes, so the fix is unproven by anyone but its author.

**This waives verification of one finding only.** It doesn't verify the fix, accept T-0022, or apply to any other tool or workspace. VERIFY-2026-11-04-t0022-1-2's own record stays NOT READY as written.

## How Claude read it

"All" had one question behind it. Claude's other items asked the owner to do things, and nothing is read as done: the reports read, #96 merged, issuer files supplied, or a renewal date given.

## Not authorised

Accepting T-0022; finding-state reconciliation in `reviews/README.md` (§6.2 step 5.12), which Claude has asked for with acceptance.

## Corrections (append-only)
