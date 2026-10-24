---
id: OD-0032
title: "Owner remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-7 (35526b5); F7 correction on PR #2 within OD-0030/OD-0031"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-f7-verify-7-exception.md (pasted by the owner, verbatim)
  sha256: 175d6dbe692ef9db51c3cab734508a1191e44e40d518ced26879478797ecc88e
  date: 2026-10-24
  quote: "Under harness-0.7 §6.2, I authorise bounded remediation before receipt of this verification evidence."
applies_to:
  - path: /
    revision: f00db8c46a8462eab73a39117e866990160d5c57   # PR #2 head reviewed by VERIFY-2026-10-24-s1a-1-7
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-7
  commit: 35526b539186ca31b1c944dbb93b46ac7531360d
  record: reviews/records/VERIFY-2026-10-24-s1a-1-7.md
  record_blob: 3e1f282c89803a887e56328baef0d1dd7b72e5c5
  record_sha256: 5cfc9bc3e138afb4e60d7f205668c0abc9ea115448b888c538efadc60147e00c
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0032: exception for VERIFY-2026-10-24-s1a-1-7

## Checks performed before use (all passed)

| Check | Result |
|---|---|
| Reviewer commit | `35526b539186ca31b1c944dbb93b46ac7531360d`. Parent: `f00db8c` (the PR #2 head). Trailer: `HIO-Actor: codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-7.md` |
| Record SHA-256 (independent) | `5cfc9bc3e138afb4e60d7f205668c0abc9ea115448b888c538efadc60147e00c`, equal to the digest Codex reported in its handoff (`reviews/handoffs/2026-10-24-s1a-f4-f7-verify-7.md` at `4ebebd1`, line 8) |
| Reviewer-only scope | `sh tools/check_review_branch.sh f00db8c… review/s1a-1-verify-7-codex-local`: exit 0. The branch tip is `4ebebd1`: 2 commits, both `reviews/` only |
| Assigned review identity | `check_review_assignment.py` with id `VERIFY-2026-10-24-s1a-1-7`, base `191ac0f`, head `f00db8c`, branch `review/s1a-1-verify-7-codex-local`, and the record's assignment source: exit 0 |

## Owner action

1. **Exception** (harness-0.7 §6.2 step 6). The record is disposed of for technical remediation,
   **not** received into `main`.
2. **F7 correction** on PR #2, within the approved Q-002 contract and OD-0030/OD-0031. The fixture is
   Codex's three-receipt counterexample: 3.60, then 3.61, then 3.60, with the third receipt falsely
   labelled redundant. Required outcomes:
   - the forged state is refused by both the query and the resolution paths, also after reopening
     the store;
   - honest capture-order ingestion returns the final 3.60, with verified evidence and a
     reproducible result identity;
   - outcome verification applies the same capture-order rules as ingestion, including evidence
     strength and true reverts;
   - the F1–F6 regressions, the original F7 cases and the financial `data.csv` outputs all stay
     valid.
3. **If another defect is found** within the same F7 contract, give a direct, executable
   Claude–Codex handoff rather than asking for a new architecture decision.

## What this record does NOT do

- It does not change an approved standard, merge PR #2 or PR #3, close any finding, accept S1a,
  or start S1b.
