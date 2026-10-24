---
id: OD-0024
title: "Owner authorisation: F6 remediation on remediation/s1a-1 (PR #2) under the harness-0.7 remediation-before-receipt exception; harness-0.8 work stopped"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-f6-remediation-before-receipt.md (the owner's chat message, verbatim)
  sha256: 3a3a2a419fd54472f3bae67e4d9e630ffc92d2f50e36eec62951466a2d70e29d
  date: 2026-10-24
  quote: "I authorise a bounded continuation of F6 remediation on the existing `remediation/s1a-1` branch and PR #2, using the approved harness-0.7 remediation-before-receipt exception."
applies_to:
  - path: /
    revision: 18c80f27a64c8cbba653f347a3bc3401f536d0aa   # PR #2's submission head when this work began
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-1
  commit: 0255cb2a3966f87a6c41af6020d0fd621a4fc2f1
  record: reviews/records/VERIFY-2026-10-24-s1a-1-1.md
  record_sha256: 03dbf7197f9a0ee99902698aa265b86ad8ef4ba24f44a06dcc9fdff13fc55e5e   # checked before use: match
related: {adrs: [HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-6]}
---

# OD-0024: F6 remediation before receipt

## Owner action

1. **Exception invoked** (operating model §6.2 step 6, *remediation before receipt*, harness-0.7,
   OD-0021). Evidence:
   - review `VERIFY-2026-10-24-s1a-1-1`;
   - commit `0255cb2a3966f87a6c41af6020d0fd621a4fc2f1`;
   - record `reviews/records/VERIFY-2026-10-24-s1a-1-1.md`, sha256 `03dbf719…5e5e`.

   The owner names the committed record as the complete evidence source; Codex's chat response
   is not needed.
   - **Check performed before use:** the commit resolves, and `git show 0255cb2:<record> | shasum
     -a 256` equals the expected value.
   - The record is read only with `git show`.
2. **Scope:** F-REVIEW-2026-10-24-s1a-1-6 only, on `remediation/s1a-1` (PR #2), with no
   competing PR:
   - reproduce Codex's failure-injection counterexample as a regression test;
   - correct the atomic-write behaviour;
   - preserve the four corrections the record verified closed (F1, F2, F3, F5) and the existing
     financial output.

   Then submit a new fixed implementation head and a handoff.
3. **Verification:** Codex may verify that head independently, in its isolated worktree.
4. **harness-0.8 work stopped.** The proposal stays unchanged and unapproved, at `b86f497`.
5. **Separately**, prepare a minimal local-first workflow proposal (shared Git evidence, standing
   reviewer assignments, reduced owner intervention). It is a proposal only: no harness machinery
   without approval.

## Reading

- Under §6.2 step 6, the record must still be received, or its disposition recorded by the
  owner, before verification of this remediation is assigned. The owner's statement "Codex may
  independently verify that head" is read as permission for that verification.
- That statement is not read as receipt of PR #3. PR #3 stays open and unmerged.
- If the owner intends the statement to also record the record's disposition, a short
  confirmation closes the point.

## What this record does NOT do

- It does not merge or close PR #2 or PR #3.
- It does not receive VERIFY-2026-10-24-s1a-1-1, or change its verdict or any finding state.
- It does not accept S1a or change the approved temporal standards.
- It does not implement Q-001 or Q-002 (findings 4 and 7 stay open).
- It does not approve harness-0.8 or any workflow proposal, and does not authorise S1b.
