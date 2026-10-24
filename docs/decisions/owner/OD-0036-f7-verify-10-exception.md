---
id: OD-0036
title: "Owner remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-10 (586b35e); loaded quality-event clock validation on PR #2"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-f7-verify-10-exception.md (pasted by the owner, verbatim)
  sha256: 0b001817457e4a6162a1de6a68d3ab228bb97f7aae32f1ea70b5a6f578ff9924
  date: 2026-10-25
  quote: "I authorise a specific harness-0.7 remediation-before-receipt exception for `VERIFY-2026-10-24-s1a-1-10`, followed by the bounded technical correction identified in that record."
applies_to:
  - path: /
    revision: 21e4a0777f2f6bcece0b2dd691a552b6a7020e39   # PR #2 head reviewed by VERIFY-2026-10-24-s1a-1-10
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-10
  commit: 586b35e6dfe1226b8b139a5deee13a211faa84ba
  record: reviews/records/VERIFY-2026-10-24-s1a-1-10.md
  record_sha256: 35685f04a2368616258032bba044093b45a7ddb7c9c4b28d76d653a925a1ca4b
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0036: exception for VERIFY-2026-10-24-s1a-1-10

## Checks performed before use (all passed)

| Check | Result |
|---|---|
| Record and commit | `586b35e` resolves to `586b35e6dfe1226b8b139a5deee13a211faa84ba`. Parent: `21e4a07`. Trailer: `codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-10.md` |
| Record SHA-256 (independent) | `35685f04a2368616258032bba044093b45a7ddb7c9c4b28d76d653a925a1ca4b`, equal to Codex's handoff (`reviews/handoffs/2026-10-25-s1a-f7-verify-10.md` at `4654c6d`, line 8) |
| Reviewer-only scope | `check_review_branch.sh 21e4a07… review/s1a-1-verify-10-codex-local`: exit 0 (2 commits, both `reviews/` only) |
| Assignment | `check_review_assignment.py` (base `0e900e8`, head `21e4a07`, branch `review/s1a-1-verify-10-codex-local`, and the record's assignment source): exit 0 |
| PR #2 reviewed head | `21e4a0777f2f6bcece0b2dd691a552b6a7020e39`, as expected |

## Owner action

1. **Exception** (harness-0.7 §6.2 step 6). The record is disposed of for technical remediation,
   **not** received into `main`.
2. **Correction on PR #2:** loaded quality events are validated with the Q-001 decision-clock rule.
   - `recorded_at > decided_at` is refused.
   - `decided_at` at or before the vintage's capture is refused.
   - Invalid events cannot reach views, digests, pin verification or releases.
   - Faithful copies with valid, differing `recorded_at` keep identical quality digests.
3. The approved Q-001, Q-002 and Q-002-R1 contracts are preserved. Escalate only for a contract
   change or a material expansion of scope.

## What this record does NOT do

- It does not merge PR #2 or PR #3, accept S1a, approve observations v0.3, or start S1b.
