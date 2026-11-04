---
id: OD-0152
title: "Owner authorises receipt of REVIEW-2026-11-04-t0019-1 (NOT READY), remediation of its three findings, and one Codex verification"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-receive-t0019-fix.md (owner's message, verbatim, with Claude's question put)
  sha256: 9b5f81788e7a6353322f72ade57647422da8d4283b88c6d30d66078a7fd9e658
  date: 2026-11-04
  quote: "yes, receive it and fix the findings"
applies_to:
  - path: review/t0019-1-codex
    revision: 7a555a784dbeb6174d75555880f3b41eabdeb6d3
base_revision: 6e2e60da1679029fae40f94faea60f0b605e412b
related: {adrs: [], tasks: [T-0019], findings: [F-REVIEW-2026-11-04-t0019-1-1, F-REVIEW-2026-11-04-t0019-1-2, F-REVIEW-2026-11-04-t0019-1-3], ods: [OD-0150, OD-0151]}
---

# OD-0152: T-0019 review received; remediation

1. **Receipt of `REVIEW-2026-11-04-t0019-1`** (NOT READY; reviewer tip `7a555a7`, hiomux C3 report), by §6.2 step 5. Three findings enter as `open`.
2. **Remediation** on `feat/t0019`, as put, with a response to each finding.
3. **One Codex verification** at the new head. Its head is recorded here by correction once it exists.

**Receipt record (§6.2 5.0–5.7).** Assignment source: the *Assigned reviews* row and OD-0151. Second assignment: looked for in the *Assigned reviews* table, `docs/history/` and the comments on PR #83; none found.

| T | Inventory | Index |
|---|---|---|
| `7a555a784dbeb6174d75555880f3b41eabdeb6d3` | 3 record files and the README reported; 3 imported, 0 missing, 0 extra, sha256 equal | the reviewer's diff applied: a review row and three finding rows, all Class N, state `open`, equal to the record |

## Not authorised

Accepting T-0019; adopting the spec; closing a finding before verification; any waiver; any real data.

## Corrections (append-only)

### Correction 1 (2026-11-04): receipt complete; the verification's head

**§5.9 and 5.10.** PR #85 merged as `ba9946d` by the owner. Tip and tag were rechecked before it; the three blobs equal `T`'s and the tag peels to `T` after it. **CI, reported separately:** green on the receipt PR. The Assigned reviews row is set to received. All three findings stay `open`.

**Remediation submitted:** `feat/t0019`, fixes at `83dae6a`, main merged at `fa6370d`. Response: `reviews/responses/RESPONSE-REVIEW-2026-11-04-t0019-1.md`. The owner's yes covers one verification; this fills in its head.

| Field | Value |
|---|---|
| Review id | `VERIFY-2026-11-04-t0019-1-1` |
| Target | F-REVIEW-2026-11-04-t0019-1-1, -2 and -3, per the response at the head; no regression of C-1 to C-3 |
| Base SHA | `b4929f721d9772f64d5904685ccc741a5ae10224` |
| Head SHA | `fa6370dc3f55c4d9e6537d502ab4a4727ca85fbd` (`feat/t0019`, PR #83) |
| Scope | whether each claim is true at the head; the merge of `main` brought only the index rows and earlier records. No Azure access; no request to any data URL; no real yields; publishers' documentation pages may be read |
| Review branch | `review/t0019-1-verify-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0152-receive-t0019-review-remediate.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |
