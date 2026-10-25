---
id: OD-0050
title: "Owner instruction: one-off byte-identical receipt of REVIEW-2026-10-25-adr0012 from PR #5 (no merge of PR #5 or its ADR-0012 ancestry); PR #5 closed unmerged; harness-0.7.1 prepared for independent review"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-pr5-receipt-harness-0.7.1.md (pasted by the owner, verbatim)
  sha256: eec82fcc7822ab663fc8a9398b8a355e401a92f60743f9584d5dbb844d1ef6e4
  date: 2026-10-25
  quote: "I authorise a specific, one-off byte-identical review-evidence receipt for `REVIEW-2026-10-25-adr0012` from PR #5, without merging PR #5 or its unapproved ADR-0012 ancestry."
applies_to:
  - path: reviews/records/REVIEW-2026-10-25-adr0012.md
    revision: 1a05d8e6e0dd453c91cc37aba16c921cd6c97238   # the reviewer's commit; blob f3f104da15295b3d6bfb3fe2cbb082cf481354bc
  - path: reviews/handoffs/2026-10-25-adr0012-codex.md
    revision: 1a05d8e6e0dd453c91cc37aba16c921cd6c97238   # blob 196de9c7dd411fe4336254d17d031fee504f7477
related: {adrs: [HIO-ADR-0010, HIO-ADR-0012, HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3]}
---

# OD-0050: receive REVIEW-2026-10-25-adr0012 by byte-identical import

## Owner action

1. **Authorise a one-off byte-identical receipt** of `REVIEW-2026-10-25-adr0012` from PR #5,
   **without merging PR #5 or its unapproved HIO-ADR-0012 ancestry**.
   - **Verify first:** the original assignment and its scope and reviewed head; reviewer commit
     `1a05d8e`; the record's sha256; reviewer-only scope; the assignment checks; and that the
     pushed review branch is still reachable. **Stop on any failure or assignment discrepancy.**
   - **If verified:**
     - import the record and handoff byte-identically, confirming blob ids;
     - incorporate only the reviewer's additive index entries, deleting no unrelated row;
     - record the exceptional receipt and its provenance here;
     - close PR #5 unmerged, keeping the review commit reachable and linked from the receipt;
     - keep the three findings open, with the ADR still proposed.
2. **Prepare harness-0.7.1 for independent review.** It must distinguish byte-identical record
   preservation from preserving reviewer commit ancestry, and delegate routine receipt to Claude
   after mechanical checks.
3. **After receipt, return the three findings and a bounded remediation plan.** Escalate only a
   required standards change, an assignment mismatch or an unapproved scope expansion.

**Prohibited:** approving harness-0.7.1 or HIO-ADR-0012; marking any source right verified;
implementing S1b; merging PR #4.

## Verification before receipt (all passed, 2026-10-25)

| Owner check | Result |
|---|---|
| 1. The original assignment: scope and reviewed head | **OD-0048** (history file sha256 `a2515361…7124`, re-checked) authorised the review and fixed the id `REVIEW-2026-10-25-adr0012`, branch `review/adr0012-codex`, the seven questions with timestamp semantics, and the fixed PR head. The draft assignment at the head (`HIO-ADR-0012-review-assignment-draft.md`) gives base `183523f…`, the seven questions, and the out-of-scope list. Head `1d68da3e90d879da6318082551bab943c60cf68b` equals PR #4's head (`gh pr view 4`). The record's seven answers follow the seven questions in order |
| 2. Reviewer commit and record hash | commit `1a05d8e6e0dd453c91cc37aba16c921cd6c97238`; one commit; parent `1d68da3…` (the assigned head); record blob `f3f104da15295b3d6bfb3fe2cbb082cf481354bc`, sha256 `3b12c9fee25b85b609f0195e777c308d55e57d70010b9bddd28691c2bbfe10f2`; handoff blob `196de9c7dd411fe4336254d17d031fee504f7477`, sha256 `5bfd10a95ef9d20c37a9f69d276e3bf004e1842eda3ca1851707451c0350fe2f` |
| 2. Reviewer-only scope | `tools/check_review_branch.sh 1d68da3… review/adr0012-codex`: PASS (`A` record, `A` handoff, `M reviews/README.md`) |
| 2. Assignment check | `tools/check_review_assignment.py` with id, base `183523f…`, head `1d68da3…`, branch, and the record's `assignment` string: PASS, with scope terms `HIO-ADR-0012`, `ADR-0010`, `timing`, `rights`, `revision` |
| 3. The original review branch is reachable | `git ls-remote origin refs/heads/review/adr0012-codex` = `1a05d8e6…`; PR #5 `OPEN`, head `1a05d8e6…`. The tip was re-fetched and unchanged immediately before the import |

**One residual discrepancy to be aware of (not a mismatch).** The record's `assignment` field
names "owner direct instruction to Codex, 2026-10-25 (image supplied in the review
conversation; OD-0048 authorises the bounded review)". **The image is not in the repository,
so the exact text the owner gave Codex cannot be compared byte for byte.** The mechanical
comparison used the record's own string, and the record's id, base, head, branch and scope all
agree with OD-0048 and the draft assignment. The owner's authorisation of this receipt, after
the checks above, is the confirmation that the assignment stands. If the image differed
materially from the draft assignment, this record should be corrected.

## Execution

- **Receipt branch:** `receipt/REVIEW-2026-10-25-adr0012`, cut from `main` at
  `183523fd6e2cc148abfe2619426bfc38c7cf2108`.
- **Import commit** (message trailers carry the provenance): `eadda1e5da5df2d5141d7951abed14df40f70782`.
  - Both files were taken with `git checkout 1a05d8e -- <path>`: the staged blob ids equal the
    reviewer's, `f3f104da…` and `196de9c7…`.
  - `reviews/README.md` was patched with `git diff 1d68da3 1a05d8e -- reviews/README.md | git
    apply`. The added lines equal the reviewer's added lines exactly, and **0 lines were
    removed**, so no unrelated row was touched.
  - Nothing outside `reviews/` was staged, and `tools/check_repo.py` passed.
- **Index status update:** a second commit, this record's, changes only the status cell of the
  reviewer's `Assigned reviews` row from "submitted for receipt" to "received". It follows the
  harness rule that the owner or Claude updates the index at receipt, and it is kept apart from
  the import commit so that the import stays byte-pure.
- **Provenance preserved:** the tag `reviews/REVIEW-2026-10-25-adr0012` points to
  `1a05d8e6e0dd453c91cc37aba16c921cd6c97238`. The review branch remains on the remote.
  The reviewer's commit is **not** an ancestor of `main`, by design, because its ancestry
  contains PR #4's proposed ADR-0012.
- **PR #5** was closed unmerged with a comment naming the receipt merge, the tag, and the
  record's blob id.

## Disposition

- **The ADR stays proposed** (PR #4 open, unmerged). The three findings stay **open**:

  | Finding | Severity | State |
  |---|---|---|
  | F-REVIEW-2026-10-25-adr0012-1: a first capture can be given `knowable_at` earlier than that vintage's actual publication | high | open |
  | F-REVIEW-2026-10-25-adr0012-2: a release can be labelled final before the post-window value is captured | high | open |
  | F-REVIEW-2026-10-25-adr0012-3: the SOFR Index has its own revision rule | medium | open |

- Remediation is a separate step, with a plan in the handoff for the owner's instruction.

## What this record does NOT do

- It does **not** approve HIO-ADR-0012 or harness-0.7.1, waive or close any finding, verify any
  source right, authorise S1b, or merge PR #4.
- It does **not** change harness-0.7. The one-off exception applies to this review only.

## Corrections (append-only)

None.
