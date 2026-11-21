---
id: OD-0186
title: "T-0023 review received (NOT READY, two medium findings) and remediation started, under the standing delegation (OD-0184 A3, A8)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (A3 receipt under OD-0061's conditions; A8 remediation; A2 for the verification)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
base_revision: 68c32d526d67b07891e90e98b1977f897155975c
related: {adrs: [], tasks: [T-0023], findings: [F-REVIEW-2026-11-22-t0023-1-1, F-REVIEW-2026-11-22-t0023-1-2], ods: [OD-0061, OD-0182, OD-0184]}
---

# OD-0186: T-0023 review received; remediation

1. **Receipt of `REVIEW-2026-11-22-t0023-1`** (NOT READY; reviewer tip `65c5606`, hiomux C11 report), by §6.2 step 5, under OD-0061's conditions. Two findings enter as `open`.
2. **Remediation** of both findings on Claude's own work, with a response to each (A8).
3. **One Codex verification** at the remediated head, assigned under A2 and recorded here by correction once that head exists.

**Receipt record (§6.2 5.0–5.7).** Assignment source: the *Assigned reviews* row and OD-0182, under OD-0184 A2. Second assignment: looked for in the *Assigned reviews* table, `docs/history/` and the comments on PR #104; none found. Reviewer's report: the hiomux runner result for C11 (run `20261103T065037Z-3d12`, `attempt-1/result.json`).

| T | Inventory | Checks | Index |
|---|---|---|---|
| `65c56062938c7dc40b4581fd5de49b88f3f12bb9` | 3 record files reported, 3 imported, 0 missing, 0 extra; sha256 equal to the report | `check_review_branch.sh` PASS; `check_review_assignment.py` PASS; tag `reviews/REVIEW-2026-11-22-t0023-1` peels to `T`; branch pushed | Claude added the Class N rows (the reviewer wrote none): one review row and two finding rows, state `open`, equal to the record |

**What the review found, in short.** The code computes what the evidence files describe, and the recommendation follows the rule *if* the reported duration signs hold. It could not reproduce any licensed-input result (the assignment excluded those inputs). It traced the six audited fund-years to the public SEC filings. Two weaknesses: C5 can pass with a fiscal year missing (F-1), and downstream tools trust a run's claimed panel id without recomputing it (F-2).

## Not authorised

Accepting T-0023; closing either finding before verification; any waiver.

## Corrections (append-only)

### Correction 1 (2026-11-22): receipt merged; the verification's head

**Receipt complete.** PR #109 merged as `054f58a` (OD-0184 A1). The three blobs equal `T`'s, and the tag peels to `T`. Both findings stay `open` until verification; the author's claim is in the response.

**Remediation submitted:** `fix/t0023-review-1`, fixes at `0288120`, response at `602be49d296316313ea479fb6b7b364555e253e5` (PR #110). Assigned under OD-0184 A2:

| Field | Value |
|---|---|
| Review id | `VERIFY-2026-11-22-t0023-1-1` |
| Target | F-REVIEW-2026-11-22-t0023-1-1 and -2, per `reviews/responses/RESPONSE-REVIEW-2026-11-22-t0023-1.md` at the head; no regression in the T-0023 tools and tests |
| Base SHA | `4b6472e54aa7a1d989ee78ee49f83d6967a27536` |
| Head SHA | `602be49d296316313ea479fb6b7b364555e253e5` (`fix/t0023-review-1`, PR #110) |
| Scope | whether each claim is true at the head, on the code and tests; the merges of `main` brought only records. No licensed data (no EODHD bytes or values, nothing under `~/.hio-research/`), no Azure, no vendor URL; public reads only. The author's real-input reruns are author-reported |
| Review branch | `review/t0023-1-verify-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0186-receive-t0023-review-remediate.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |
