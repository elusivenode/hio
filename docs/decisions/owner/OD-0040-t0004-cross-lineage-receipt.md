---
id: OD-0040
title: "Owner approval: Q-011 byte-identical cross-lineage receipt of REVIEW-2026-10-18-t0004 (macsmsf@db305a3); S1-A16 two-revision basis; documentation-only integration into main; not T-0004 or S1a acceptance"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  - source: docs/history/2026-10-25-owner-approve-q011-s1a16-basis.md (pasted by the owner, verbatim)
    sha256: 1e8bead99f70cd43884982f110b10a559a6e73d443f4d7458b72a2556dd2020f
    quote: "Approve a byte-identical cross-repository receipt of the completed T-0004 review evidence from the private MACSMSF repository into HIO, as a specific exception to harness-0.7 §6.2 step 5."
  - source: docs/history/2026-10-25-owner-t0004-cross-lineage-receipt.md (pasted by the owner, verbatim)
    sha256: 635b6124cecebe97a07c00ee090079fac7e62ad0aed4293ddf4abab9bb821a24
    quote: "I confirm that the ordinary assignment check requiring `review/t0004-codex` to descend from the reviewed target `macsmsf@fe3fdc7` is inapplicable to this specific review."
applies_to:
  - path: reviews/records/REVIEW-2026-10-18-t0004.md
    revision: macsmsf@db305a3cbfe0b149b25d0cde30a3bb890e70dc39   # source of the bytes; not merged
  - path: reviews/handoffs/2026-10-24-t0004-codex.md
    revision: macsmsf@db305a3cbfe0b149b25d0cde30a3bb890e70dc39
related: {adrs: [HIO-ADR-0003, HIO-ADR-0008], tasks: [T-0004, T-0005], findings: []}
---

# OD-0040: receive the T-0004 review across lineages; fix the S1-A16 basis

## Owner action

1. **Q-011 approved.** REVIEW-2026-10-18-t0004 is received by a **byte-identical
   cross-repository copy** from the private `macsmsf` repository. This is a **specific exception
   to harness-0.7 §6.2 step 5**, whose receipt is a `--no-ff` merge keeping the reviewer's
   commit ids.
   - Only the review record and the reviewer handoff are copied. **No `macsmsf` history is
     merged into this public repository.**
   - The reviewer's commit id is kept by citation, and by `macsmsf`'s own branch
     `review/t0004-codex` on its private remote, which the owner pushed.
2. **The ordinary assignment check is inapplicable to this review, and to this review only.**
   - `tools/check_review_assignment.py` requires the review branch to descend from the reviewed
     head `macsmsf@fe3fdc7`.
   - OD-0010 required this branch to descend from the staging commit `macsmsf@760f73e`
     instead, and OD-0018 confirmed those mechanics.
   - The check is **not modified, not bypassed globally, and not reported as passing**. Its
     failure is preserved below.
3. **S1-A16 two-revision basis approved:** the original fresh Claude session at `3fd129e`
   (run 1), plus a fresh Codex-only retest at a later fixed revision Y after this receipt (run 2).
4. **Documentation-only integration authorised:** OD-0038, the run-1 record and this receipt,
   each into `main` with a controlled `--no-ff` merge.

## Verification (all required checks passed)

| Owner requirement | Result |
|---|---|
| Review commit | `db305a3cbfe0b149b25d0cde30a3bb890e70dc39`: local and `origin/review/t0004-codex` equal; trailer `HIO-Actor: codex/reviewer` |
| Alternative ancestry (requirement 2) | `760f73e` is the merge base and an ancestor (`is-ancestor` exit 0). The range `760f73e..db305a3` is exactly one commit, whose parent is `760f73e`; 0 merges |
| Reviewer-only scope (requirements 2 and 4) | the staging `hio/tools/check_review_branch.sh` from `macsmsf@760f73e` exits 0. The diff is `M hio/reviews/README.md`, `A …/handoffs/2026-10-24-t0004-codex.md` and `A …/records/REVIEW-2026-10-18-t0004.md` |
| Record identity (requirement 3) | `reviewed_base` `1502ab8…` and `reviewed_head` `fe3fdc78cb2d2b9f147122528cc5cf97db976397`, equal to the *Assigned reviews* row and the tip of `docs/hio-001-boundary-c1`; `1502ab8` is an ancestor of `fe3fdc7`; `review_branch` `review/t0004-codex` and `review_branch_base` `760f73e…`, as OD-0010 set; `assignment` cites the index row (OD-0010) and OD-0018. Verdict **READY**; no finding opened |
| Record integrity (requirement 4) | record sha256 `e70bd93de991d087929e82144cabdb40af29088aea28e2f01dc9e0bc9e5e0a2a`, equal to the value cited in HARNESS-2026-10-25-s1a16-1 and OD-0039; handoff sha256 `5be7a6740bcd116f05eebcbc2871cb88fab431f703d45520850aa92d24760a87` |
| Bytes preserved (requirement 6) | the copies have the same git blob ids as the originals: record `339425004e68…`, handoff `be340e499e57…` |
| Ordinary assignment check (requirement 1) | **exit 1, one problem: the inapplicable descent check.** Every other comparison it makes raised nothing |

**One correction, stated plainly.** The first run of the ordinary check passed the
remote-tracking name `origin/review/t0004-codex` as `--branch`. That run reported a second,
invocation-caused failure: the record's branch name is not the string supplied. The re-run with
the assigned name `review/t0004-codex` (the same commit) reports only the descent failure. Both
outputs are preserved below.

### Check log (verbatim; local file sha256 `0ed36e8165c0fb86e7ca7467a4219c58620bebba4b4f6fe9dcb671134db0397c`)

```text
# T-0004 receipt checks, 2026-10-24T23:37:22Z, macsmsf repo
## 1. ordinary assignment check (expected structural failure)
FAIL: origin/review/t0004-codex does not descend from the assigned head fe3fdc78cb2d2b9f147122528cc5cf97db976397
FAIL: hio/reviews/records/REVIEW-2026-10-18-t0004.md: review_branch is 'review/t0004-codex'; the assignment says 'origin/review/t0004-codex'
FAIL: 2
exit 1
## 2. alternative ancestry: branch descends from macsmsf@760f73e
db305a3cbfe0b149b25d0cde30a3bb890e70dc39
db305a3cbfe0b149b25d0cde30a3bb890e70dc39
760f73e3aabf025150f88776da0ca7d7fc792369
is-ancestor exit 0
db305a3cbfe0b149b25d0cde30a3bb890e70dc39 760f73e3aabf025150f88776da0ca7d7fc792369
merges in range: 0
## 3. staging scope check (hio/tools/check_review_branch.sh at 760f73e)
PASS: origin/review/t0004-codex (1 commit(s)) changes only permitted review records relative to 760f73e3aabf025150f88776da0ca7d7fc792369
M	hio/reviews/README.md
A	hio/reviews/handoffs/2026-10-24-t0004-codex.md
A	hio/reviews/records/REVIEW-2026-10-18-t0004.md
exit 0
M	hio/reviews/README.md
A	hio/reviews/handoffs/2026-10-24-t0004-codex.md
A	hio/reviews/records/REVIEW-2026-10-18-t0004.md
## 4. record front matter and identity
---
id: REVIEW-2026-10-18-t0004
subject: T-0004 SMSF documentation amendment for HIO-001 boundary option C1
reviewer: codex/reviewer
reviewed_base: 1502ab8804c5968a8bf91fa36275c44e6e84f575
reviewed_head: fe3fdc78cb2d2b9f147122528cc5cf97db976397
assignment: owner assignment in hio/reviews/README.md (OD-0010); cross-lineage mechanics confirmed by OD-0018
review_branch: review/t0004-codex
review_branch_base: 760f73e3aabf025150f88776da0ca7d7fc792369
created_at: 2026-10-24
updated_at: 2026-10-24
verdict: READY
---

target commit: fe3fdc78cb2d2b9f147122528cc5cf97db976397 on docs/hio-001-boundary-c1 = fe3fdc78cb2d2b9f147122528cc5cf97db976397
1502ab8 is ancestor of fe3fdc7
## 5. digests at db305a3
e70bd93de991d087929e82144cabdb40af29088aea28e2f01dc9e0bc9e5e0a2a  -
5be7a6740bcd116f05eebcbc2871cb88fab431f703d45520850aa92d24760a87  -
+| REVIEW-2026-10-18-t0004 | T-0004 SMSF documentation amendment for HIO-001 boundary option C1 | `1502ab8..fe3fdc7` | Codex, under OD-0010 and OD-0018 | **READY** | [record](records/REVIEW-2026-10-18-t0004.md) |
commit db305a3cbfe0b149b25d0cde30a3bb890e70dc39
author elusivenode Sat Oct 24 10:26:34 2026 +1000
trailer: codex/reviewer


## 1b. ordinary assignment check re-run with the assigned branch name (1 used the remote-tracking name by mistake; same commit)
FAIL: review/t0004-codex does not descend from the assigned head fe3fdc78cb2d2b9f147122528cc5cf97db976397
FAIL: 1
exit 1
```

## What this record does NOT do

- It does **not** accept T-0004, merge the amendment `fe3fdc7` into `macsmsf` `main`, or change
  any `macsmsf` file or application functionality.
- It does **not** accept S1a, pass S1-A16, approve observations v0.3 or authorise S1b.
- It does **not** change `tools/check_review_assignment.py`, harness semantics, any approved
  standard, or the implementation. The exception covers this receipt only.
- It does **not** touch Codex's branches or worktrees.

## Corrections (append-only)

None.
