---
id: OD-0031
title: "Owner remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-6 (3cb3dd0); F4/F7 correction continues on PR #2 within OD-0030"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-f4-f7-verify-6-exception.md (pasted by the owner, verbatim)
  sha256: 277ecaaecd70a9c566110ebf8f25408800a723b5de38263934f47d8c28f679bf
  date: 2026-10-24
  quote: "Under harness-0.7 §6.2, I authorise a bounded remediation-before-receipt exception for this verification record."
applies_to:
  - path: /
    revision: 191ac0f0461b59c61c8b11c60befd6f7f04da6b6   # PR #2 head reviewed by VERIFY-2026-10-24-s1a-1-6
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-6
  commit: 3cb3dd073f832f2cb9d49a1d2690a131b14e7f37
  record: reviews/records/VERIFY-2026-10-24-s1a-1-6.md
  record_blob: 4fc2d807173811e555c88d2109b9b240b25c0604
  record_sha256: 87ff2b82c8779cb73015468bb59447022a2af838f272df656786c16c33bab9d1
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0031: exception for VERIFY-2026-10-24-s1a-1-6

## Checks performed before use (all passed)

| Check | Result |
|---|---|
| Reviewer commit | `3cb3dd073f832f2cb9d49a1d2690a131b14e7f37`. Parent: `191ac0f` (the PR #2 head). Trailer: `HIO-Actor: codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-6.md` |
| Record SHA-256 (independent) | `87ff2b82c8779cb73015468bb59447022a2af838f272df656786c16c33bab9d1`, equal to the digest Codex reported in its handoff (`reviews/handoffs/2026-10-24-s1a-f4-f7-verify-6.md` at `1c989a8`, line 8) |
| Reviewer-only scope | `sh tools/check_review_branch.sh 191ac0f… review/s1a-1-verify-6-codex-local`: exit 0. The branch tip is `1c989a8`: 2 commits, both `reviews/` only (the record and Codex's handoff) |
| Assigned review identity | `check_review_assignment.py` with id `VERIFY-2026-10-24-s1a-1-6`, base `b4c398d`, head `191ac0f`, branch `review/s1a-1-verify-6-codex-local`, and the record's assignment source ("OD-0030 section 4 and owner-forwarded 2026-10-24 F4/F7 completion block"): exit 0 |

## Owner action

1. **Exception** (harness-0.7 §6.2 step 6). The record above is disposed of for technical
   remediation.
   - It is **not** received into `main`.
   - It does not accept S1a, and does not permit changes to approved standards.
2. **Remediation** continues on PR #2 within OD-0030, for the two demonstrated defects only:
   1. **Processing completeness.** Every captured receipt is accounted for, including a
      same-value receipt with stronger timing evidence. Capture evidence, capture mode and
      processing outcome stay distinct. Incomplete processing refuses queries and resolutions.
      Codex's counterexample becomes a regression.
   2. **Predictive admissibility** is enforced at the point-in-time release-building boundary. A
      Q > T market result is refused before publication, with no partial output. There is no
      override and no invented descriptive-publication exception.
3. Codex may verify the corrected head within the existing bounded F4/F7 assignment.

## What this record does NOT do

- It does not close or waive any finding, merge PR #2 or PR #3, accept S1a, or authorise S1b.
- It does not change the approved Q-001 or Q-002 contracts.
