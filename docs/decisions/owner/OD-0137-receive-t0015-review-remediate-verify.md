---
id: OD-0137
title: "Owner authorises receipt of REVIEW-2026-11-03-t0015-1 (without the index diff if it does not apply), remediation of F-REVIEW-2026-11-03-t0015-1-1, and a Codex verification at the new head"
decision: authorise_work
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-t0015-receive-remediate.md (owner's message, verbatim, with Claude's decisions put)
  sha256: 27c5d905f595af83c7dff73c035986285f0aa630e6ed9a820478cf98a779460e
  date: 2026-11-03
  quote: "yes to both"
applies_to:
  - path: review/t0015-1-codex
    revision: 312359993055409d5a954adc5e5faf8f9ec3b161
  - path: feat/t0015
    revision: 3d259d34772f0876c8cb90c61bf73b1e80ece244
base_revision: 7c36e4a641bf1e996804259bd12fa8e341948eff
related: {adrs: [HIO-ADR-0012], tasks: [T-0015], findings: [F-REVIEW-2026-11-03-t0015-1-1], ods: [OD-0134, OD-0135, OD-0136]}
---

# OD-0137: T-0015 review received, finding remediated, verification assigned

The same message also answered the publication question: OD-0136's record merged and PR #60 opened, unmerged, adopting nothing.

1. **Push and receipt.** `review/t0015-1-codex` pushed at `3123599`. `REVIEW-2026-11-03-t0015-1` (NOT READY; hiomux C1 report) is
   received by §6.2 step 5. The go-ahead to receive without the index diff is given in advance, should it not apply.
2. **Remediation of F-REVIEW-2026-11-03-t0015-1-1 (medium) on `feat/t0015`, only:** `_key_exists` requires a real properties result
   for that key, with a regression test for the inconclusive case.
3. **Verification.** Codex verifies at the new head. The assignment (id, base, head, branch) is recorded in a correction to this OD
   before launch, because the head doesn't exist yet.

## Not authorised

Accepting or merging T-0015; the re-run, 7b or the destroy; any C5 amendment; adopting PR #60; closing the finding before its
verification is received.

## Corrections (append-only)
