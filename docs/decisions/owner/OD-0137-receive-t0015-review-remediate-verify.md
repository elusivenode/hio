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

### Correction 1 (2026-11-03): receipt complete without the index diff; remediation submitted; verification assigned

**Receipt (§6.2 5.0–5.10, in a scratch clone).** The assignment source is the *Assigned reviews* row plus OD-0135. The reviewer's report
is the hiomux C1 result. A second owner-authored assignment was looked for in the *Assigned reviews* table, `docs/history/` and the
comments on PR #53; none was found.

| Receipt | T | Inventory | Index | Import, merge (PR) | 5.10 |
|---|---|---|---|---|---|
| REVIEW-2026-11-03-t0015-1 (NOT READY) | `312359993055409d5a954adc5e5faf8f9ec3b161` | 3 record files and the README reported; 3 imported, 0 missing, 0 extra, sha256 equal | README diff refused, omitted wholly (go-ahead in item 1) | `615359e`, `7b362ee` (#62) | PASS; tag peels to T; CI success on `615359e` |

**Refused lines, verbatim** (the reviewer's whole README diff):

```text
+| REVIEW-2026-11-03-t0015-1 | T-0015 B-2 follow-up, F-1 through F-3 | `a71f0ff..3d259d3` | Codex, assigned by OD-0135 | **NOT READY** | [record](records/REVIEW-2026-11-03-t0015-1.md) |
+| F-REVIEW-2026-11-03-t0015-1-1 | REVIEW-2026-11-03-t0015-1 | medium | **open** | — | — | — |
```

**§5.12 (this commit), navigation only.** Those two rows are added byte-identical (Class N, checked against the record: same id, base,
head and verdict; the finding `medium`, state `open`). The *Assigned reviews* row is set to received. **No finding changes state:**
F-REVIEW-2026-11-03-t0015-1-1 stays open.

**A slip in Claude's script, disclosed.** The first attempt piped the scope check to `head`, which killed it and gave a false failure
after it had printed PASS. Nothing had been tagged or pushed. It was re-run unpiped and passed.

**Remediation.** Fix `cf50736`; response at submission head `a05219a77ee9c21de56c1ea14dbd09f2dddeb327` on `feat/t0015`. Seven new
regression cases fail on the pre-fix code and pass after it; full suite 1007 passed; `ruff` clean. This is a claim, not a verification.

**Verification assigned (item 3):**

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-11-03-t0015-1-1` |
| Verifies | F-REVIEW-2026-11-03-t0015-1-1, per `reviews/responses/RESPONSE-REVIEW-2026-11-03-t0015-1.md` at the head |
| Base SHA | `3d259d34772f0876c8cb90c61bf73b1e80ece244` (the reviewed head) |
| Head SHA | `a05219a77ee9c21de56c1ea14dbd09f2dddeb327` (`feat/t0015`) |
| Scope | the remediation claim; no regression of REVIEW-2026-11-03-t0015-1's scope (F-1 to F-3); the full suite. No Azure access and no real data |
| Review branch | `review/t0015-1-verify-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0137-receive-t0015-review-remediate-verify.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |
