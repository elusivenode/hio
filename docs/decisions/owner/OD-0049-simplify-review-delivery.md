---
id: OD-0049
title: "Owner instruction: prepare a narrowly scoped proposed harness amendment so that Codex pushes review branches without opening PRs, with evidence received by a controlled Git operation; PR #5 migration; harness-0.7 stays in force"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-simplify-review-delivery.md (typed and pasted by the owner, verbatim)
  sha256: 41bdec2cff13c4c3c2d6099a434569103b6bb283ad3a39b8fadad441444f8d55
  date: 2026-10-25
  quote: "Codex (the reviewer) keeps creating PRs and I don't want this workflow ... how can we fix it?"
applies_to:
  - path: docs/harness/operating-model.md
    revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108   # harness-0.7, unchanged; blob 920b1bb153bf7ffaf3a8356a7486b2fa86c5be3f
related: {adrs: [HIO-ADR-0008], tasks: [], findings: []}
---

# OD-0049: simplify review evidence delivery (proposal only)

## Owner action

Prepare a **narrowly scoped proposed amendment** that removes the reviewer-PR requirement while
preserving:
- independent verification;
- immutable records;
- exact-revision provenance;
- stop-on-mismatch.

Its seven points:
1. Claude PRs where appropriate.
2. Codex commits records on a short-lived review branch, in an isolated worktree.
3. Codex pushes the branch, with no PR.
4. Receipt by a controlled Git operation that cannot integrate unaccepted commits.
5. Receipt checks: the assignment, the head, record hashes, reviewer-only scope, provenance.
6. Findings immutable; Codex alone verifies closure.
7. The owner approves standards, scope changes, waivers, integration and acceptance, but not
   routine delivery.

The package must also:
- compare the receipt mechanisms, and recommend the simplest;
- address PR #5 without a new review, and without approving HIO-ADR-0012.

**Harness-0.7 stays in force** until an exact revision is independently checked and approved.

**Prohibited:** changing implementation code, accepted S1a content, approved standards, or the
existing review record.

## Execution

- **The package:**
  [`docs/decisions/harness-0.7.1-proposal.md`](../harness-0.7.1-proposal.md), `status:
  proposed`. It is named 0.7.1 because harness-0.8 is a stopped proposal (OD-0024, `b86f497`).
- **Read-only checks of PR #5:**
  - `tools/check_review_branch.sh` PASS;
  - `tools/check_review_assignment.py` PASS, in a scratch clone, with the record's own
    assignment string, which the owner must confirm.
- **A dry-run import** onto `main` in a scratch clone:
  - blob-identical;
  - only Codex's `README` rows;
  - `check_repo` PASS;
  - nothing committed.
- **Unchanged:** `docs/harness/operating-model.md`, `tools/`, `.github/`, PR #5 and its branch.

## What this record does NOT do

- It does **not** approve harness-0.7.1, or change harness-0.7.
- It does **not** receive, merge or close PR #5, or create any tag.
- It does **not** approve HIO-ADR-0012, or change any finding.

## Corrections (append-only)

None.
