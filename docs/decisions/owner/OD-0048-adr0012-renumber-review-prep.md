---
id: OD-0048
title: "Owner instruction: renumber the staged-S1b proposal HIO-ADR-0012 (HIO-ADR-0011 retained for the equity TR decision); push the branch; open a documentation-only PR; authorise Codex's bounded design review REVIEW-2026-10-25-adr0012 once confirmed from Git"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-renumber-review-prep.md (pasted by the owner, verbatim)
  sha256: a25153614df0cd3ed16686cd674f56d6b3c7312bd55abe04bc38a16425b67124
  date: 2026-10-25
  quote: "I authorise Codex to undertake the bounded independent design review once the final PR head, base, scope and review branch are confirmed from Git."
applies_to:
  - path: docs/decisions/HIO-ADR-0012-staged-s1b.md
    revision: self   # the PR's Submission-Head: the commit that adds this record and the renamed ADR
  - path: /
    revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108   # the PR base (main)
related: {adrs: [HIO-ADR-0010, HIO-ADR-0012], tasks: [T-0002, T-0003, T-0005], findings: []}
---

# OD-0048: HIO-ADR-0012; PR; Codex design review authorised

## Owner action

1. **HIO-ADR-0012** is selected for the staged-S1b proposal.
   - HIO-ADR-0011 is **retained for the equity total-return source decision** under T-0003.
   - The immutable A01 review and the historical references are not modified or reinterpreted.
2. **On the proposal branch:**
   - rename the document, preserving its substance;
   - correct its status references, the candidate review assignment, the register entry and the
     new links;
   - set the review id `REVIEW-2026-10-25-adr0012` and the branch `review/adr0012-codex`;
   - verify the content and its Git identity;
   - commit and push;
   - open a documentation-only PR to `main` stating the fixed Submission-Head, and that the ADR
     is proposed, not approved;
   - prepare the owner-authored assignment details: the seven questions, with publication and
     revision timestamp semantics explicit.
3. **Codex is authorised** to undertake the bounded independent design review **once the final
   PR head, base, scope and review branch are confirmed from Git**:
   - in its isolated worktree;
   - with evidence under `reviews/` only;
   - assessing the proposal against HIO-ADR-0010 rev 3, the rights and observation standards,
     and the S1b acceptance obligations.

**Prohibited:**
- approving HIO-ADR-0012;
- verifying permissions;
- contacting publishers;
- implementing S1b;
- creating infrastructure;
- changing approved standards.

**Stop conditions:**
- the renumbering changes substance;
- the review scope differs materially;
- the submitted head differs from the assignment.

## Execution

**Renaming and branch.**
- `git mv` to `HIO-ADR-0012-staged-s1b.md` and `HIO-ADR-0012-review-assignment-draft.md`; the
  branch was renamed `docs/adr0012-staged-s1b-proposal`.
- The ADR changes are confined to:
  - the id;
  - the H1;
  - `drafted_under`;
  - the review-assignment link;
  - the removed numbering note and §8 item 4, which the owner's selection resolves;
  - one changelog line.

  The word diff against the `bd0b8fd` blob is reported in the handoff.
- **The assignment draft:** the review id, the branch, the subject path and the finding prefix
  were replaced. Question 5 is expanded to make the publication and revision timestamp semantics
  explicit (P, W, `knowable_at`, `captured_at`, late capture, `valid_time`, final-release
  cutoffs). This is a clarification the owner instructed, not a change of scope.
- **Links** in OD-0046 and OD-0047 were corrected, on the owner's instruction, each with an
  append-only correction entry.

**The PR and the head.**
- The Submission-Head is the commit that adds this record. It is stated in the PR description
  and in the owner-facing completion report, because a file cannot contain its own commit id.
- The assignment values that bind Codex are the ones the owner confirms from Git
  (operating model §6.2 step 1).
- `tools/check_review_assignment.py` is to be run at receipt.

## What this record does NOT do

- It does **not** approve HIO-ADR-0012, or supersede any HIO-ADR-0010 provision.
- It does **not** record a review, or receive one.
- It does **not** verify any right, or authorise S1b-1 or S1b-2.
- It does **not** merge the PR. A merge needs the owner's instruction after the review.

## Corrections (append-only)

None.
