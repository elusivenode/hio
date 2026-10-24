---
id: OD-0025
title: "Owner disposition of VERIFY-2026-10-24-s1a-1-1 and -2 (preserved, not received) and authorisation of the F6 correction cycle on PR #2"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-f6-round3-authorisation.md (the owner's chat message, verbatim)
  sha256: 54c2a35a4e4bf9f8520e7a3959f9588a9349bf335bc596d3b482cd0a59a050ec
  date: 2026-10-24
  quote: "I authorise continuation of the bounded F6 remediation on the existing `remediation/s1a-1` branch and PR #2."
owner_correction:
  source: docs/history/2026-10-24-owner-f6-round3-hash-correction.md (the owner's chat message, verbatim)
  sha256: de34650232ec6dc2746773e87752d71ef8b3189037b62f6566003b8828a46050
  date: 2026-10-24
  quote: "The previous hash was incorrectly transcribed. All other parts of my F6 round-3 authorisation remain unchanged."
applies_to:
  - path: /
    revision: 759ddf7df599c20675395982e97e7fbd6a6fd3af   # PR #2's submission head when this cycle began
evidence:
  - review_id: VERIFY-2026-10-24-s1a-1-1
    commit: 0255cb2a3966f87a6c41af6020d0fd621a4fc2f1
    record_sha256: 03dbf7197f9a0ee99902698aa265b86ad8ef4ba24f44a06dcc9fdff13fc55e5e   # checked: match
  - review_id: VERIFY-2026-10-24-s1a-1-2
    commit: 9a94c3a8a68d9627b205c954065a9210db4c6aa3
    record_sha256: 3fda0fd349bac50afc64a3663910aa3d186daeefad17b4bb1f5db1f774882c53   # the corrected value; checked: match
related: {adrs: [HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-6]}
---

# OD-0025: F6 correction cycle (round 3 onward)

## Provenance

- **The original instruction** gave a 62-character value for VERIFY-2026-10-24-s1a-1-2's SHA-256,
  and it did not match the record.
  - Claude stopped, changed nothing, and reported the mismatch.
  - The owner then corrected the value and confirmed that the rest of the instruction stands.
- Both messages are kept verbatim. The corrected value was checked against
  `git show 9a94c3a:reviews/records/VERIFY-2026-10-24-s1a-1-2.md`, and it matches.

## Owner action

1. **Disposition** (harness-0.7 §6.2 step 6):
   - VERIFY-2026-10-24-s1a-1-1 (`0255cb2`) stays preserved, immutable evidence, not received into
     `main`.
   - VERIFY-2026-10-24-s1a-1-2 (`9a94c3a`) is authorised as evidence for this correction, not
     received into `main`.
   - For this F6 correction cycle, both are owner-disposed evidence. The dispositions need not be
     repeated for each technical iteration within the same scope.
2. **Scope.** Continue F6 on `remediation/s1a-1` (PR #2), appending commits only:
   - reproduce the failed-rollback visibility counterexample;
   - investigate the concurrent-writer ownership counterexample independently.

   The correction must give these properties:
   1. no uncommitted object is observable through the supported interface while its
      transaction is unresolved;
   2. rollback and recovery never delete another writer's object;
   3. a failed rollback leaves durable journal evidence for recovery;
   4. the single-writer assumption is kept, with no general concurrent-writer transactions;
   5. financial outputs, immutable receipts and the F1, F2, F3 and F5 behaviour are unchanged.

   Required tests are adversarial: visibility before and after reopening, rollback failures,
   journal recovery and ownership.
   **If object identity cannot give these guarantees under the existing storage contract, stop and
   escalate. Do not weaken the tests.**
3. **Collaboration.** Codex may verify successive F6 corrections under the existing bounded review
   assignment. Neither agent may approve S1a, waive findings or change approved standards.

## What this record does NOT do

- It does not merge or close PR #2 or PR #3.
- It does not receive either record into `main`.
- It does not close any finding.
- It does not approve harness-0.8, accept S1a, authorise S1b, or resolve Q-001 or Q-002.
