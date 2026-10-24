---
id: OD-0033
title: "Owner remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-8 (db1722c); F7 quarantine-related completeness correction on PR #2"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-f7-verify-8-exception.md (pasted by the owner, verbatim)
  sha256: 17e9b404fba8def14ab6084f0112b8c3c0f82e531969593d1e1df9a4807ad9a8
  date: 2026-10-24
  quote: "Under harness-0.7, I authorise bounded remediation before receipt of this specific verification record, subject to independent verification of its commit, hash, reviewer-only scope and assignment."
applies_to:
  - path: /
    revision: 6720a6cbeac5aa45e51fa8bcd2433f8b9bbe2968   # PR #2 head reviewed by VERIFY-2026-10-24-s1a-1-8
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-8
  commit: db1722c35fe2136461b6b936a8d6d9d0044e656b
  record: reviews/records/VERIFY-2026-10-24-s1a-1-8.md
  record_blob: 4af8a1295a46a6f5f1b41df007aebfb00cc3c0e8
  record_sha256: 6776d92b47225f5e408824a084ec1162a752bd64c1829e76fe4ee1532ae673d4
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0033: exception for VERIFY-2026-10-24-s1a-1-8

## Checks performed before use (all passed)

| Check | Result |
|---|---|
| Reviewer commit | `db1722c35fe2136461b6b936a8d6d9d0044e656b`. Parent: `6720a6c` (the PR #2 head). Trailer: `HIO-Actor: codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-8.md` |
| Record SHA-256 (independent) | `6776d92b47225f5e408824a084ec1162a752bd64c1829e76fe4ee1532ae673d4`, equal to the owner's statement and to Codex's handoff (`reviews/handoffs/2026-10-24-s1a-f7-verify-8.md` at `c9840ba`, line 8) |
| Reviewer-only scope | `sh tools/check_review_branch.sh 6720a6c… review/s1a-1-verify-8-codex-local`: exit 0. The branch tip is `c9840ba`: 2 commits, both `reviews/` only |
| Assigned review identity | `check_review_assignment.py` with id `VERIFY-2026-10-24-s1a-1-8`, base `f00db8c`, head `6720a6c`, branch `review/s1a-1-verify-8-codex-local`, and the record's assignment source: exit 0 |

## Owner action

1. **Exception** (harness-0.7 §6.2 step 6). The record is disposed of for technical remediation,
   **not** received into `main`.
2. **Correct F7's quarantine-related completeness failures** within the approved Q-002 contract:
   - reproduce both counterexamples first;
   - assess the completeness mechanism as a whole, especially its trust boundaries.

   Required outcomes:
   1. every captured receipt's raw bytes are verified before it counts, quarantined receipts
      included;
   2. a quarantine marker does not by itself establish that processing is complete; the evidence
      must warrant quarantine under the ingest rules;
   3. missing or corrupt data, forged outcomes and forged markers cause refusal;
   4. valid quarantine behaviour is preserved, including malformed receipts;
   5. fixed-(T, Q) results and evidence pins cannot silently change as processing state changes.
3. **Stop condition.** If the mechanism cannot satisfy the contract without a structural change,
   stop and present the smallest design decision needed.
4. **Collaboration.** Records and counterexamples are exchanged through the shared repository.
   Each review leaves an actionable handoff and names any mandatory owner prerequisite.

## What this record does NOT do

- It does not merge PR #2 or PR #3, approve observations v0.3, close any finding, accept S1a, or
  start S1b.
