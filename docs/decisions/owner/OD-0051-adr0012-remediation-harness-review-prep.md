---
id: OD-0051
title: "Owner instruction: remediate the three REVIEW-2026-10-25-adr0012 findings on PR #4 (ADR-0012 stays proposed); push harness-0.7.1 revision 2 at 9878dd0; prepare two fixed-head Codex assignment packages for owner confirmation"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-adr0012-remediation-harness-review-prep.md (pasted by the owner, verbatim)
  sha256: 449e7eb7c1e46e63425577293e7ac2de045ee6d7a8031f2254a6d1f2a22a7f59
  date: 2026-10-25
  quote: "Submit a new exact PR #4 head with a concise remediation response. Do not approve ADR-0012."
applies_to:
  - path: docs/decisions/HIO-ADR-0012-staged-s1b.md
    revision: bc939f778066d96ebafc2364640f9ebf0457d09e   # the fix commit; the submission head is the commit that adds the response
  - path: docs/decisions/harness-0.7.1-proposal.md
    revision: 9878dd0bad6fa61a0ef8519a6d47da7198b08526   # pushed, branch docs/harness-0.7.1-review-receipt
related: {adrs: [HIO-ADR-0012, HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-25-adr0012-1, F-REVIEW-2026-10-25-adr0012-2, F-REVIEW-2026-10-25-adr0012-3]}
---

# OD-0051: ADR-0012 remediation; harness-0.7.1 review preparation

## Owner action (summary; the verbatim text is in the history file)

**A. ADR-0012 remediation.**
- **F1:** distinguish evidenced per-vintage publication timestamps from approximate schedules;
  otherwise a conservative capture-time basis. Escalate any necessary change to approved
  observation semantics.
- **F2:** finality from verified successful post-window capture evidence, including unchanged
  content. An attempt alone cannot establish finality; failed or missing checks fail closed.
- **F3:** separate SOFR Index calculation corrections from SOFR-rate revisions, with independent
  Index checks.
- Preserve accepted S1a, the approved standards and all unverified rights. Submit a new exact
  PR #4 head with a concise remediation response. **Do not approve ADR-0012.**

**B. Harness-0.7.1 independent review.**
- Push revision 2 at `9878dd0` after verifying its identity and scope.
- Prepare a fixed-head assignment for Codex, with seven challenge areas.
- The owner **recommends** a push-only, no-reviewer-PR pilot exception to harness-0.7.
  **No harness amendment is approved by this instruction alone.**

**Prohibited:** implementing S1b; merging PR #4; approving ADR-0012; verifying rights; changing
the approved harness.

## Execution

**B first: the push.**
- Verified before pushing: the tip is the full id `9878dd0bad6fa61a0ef8519a6d47da7198b08526`;
  it descends from `main` (`6fbec1a`); it differs from `main` in documentation files only (the
  package, its draft assignment, OD-0049, one history file, a handoff and three indexes);
  `docs/harness/operating-model.md` is **identical** to `main`'s; no protected path differs;
  package blob `67683a37…`, sha256 `fd29f7a2…7316`.
- In a clean worktree at that exact commit: `check_repo` PASS, `ruff` clean, `pytest` 278 passed.
- Pushed as `docs/harness-0.7.1-review-receipt`. **No PR was opened**, because none was asked for
  (a deliberate departure from harness-0.7 step 0, which would have an author PR).

**A: the remediation.**
- `main` (receipt `6fbec1a`) was merged into PR #4's branch (`a3976bf`), so that the remediation
  descends from the receipt as §6.2 step 6 requires. The reviewed head `1d68da3` stays in
  ancestry. Conflicts were resolved by keeping both sides' index rows.
- Fix commit `bc939f778066d96ebafc2364640f9ebf0457d09e`: ADR-0012 revision 2, §4.3 rewritten.
  §4.1 and §4.4–§4.6 are byte-identical to the reviewed head.
- The submission head is the commit that adds
  [`RESPONSE-REVIEW-2026-10-25-adr0012-1`](../../../reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md)
  and this record. It is stated in the PR #4 comment and in the owner-facing report.

## Escalation raised: Q-013 (not decided)

The remediation of F1 needs a ruling on **approved observation semantics**. The approved standard
§3 defines `captured_on_schedule` by "the documented release time preceding that capture". Accepted
S1a code already uses the capture instant for a revised value (`knowability.py:51-52`), but not
for a first capture. Extending it is a clarification of the approved text plus an opt-in change to
accepted S1a placement behaviour. **The ADR does not depend on it:** the fail-closed `schedule_only`
fallback applies if it is declined. See [`open-decisions.md`](../open-decisions.md), Q-013.

## Assignment packages (for owner confirmation; neither is an assignment until the owner issues it)

### Package A: scoped verification of the ADR-0012 remediation

Draft: [`HIO-ADR-0012-verification-assignment-draft.md`](../HIO-ADR-0012-verification-assignment-draft.md).

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-10-25-adr0012-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` |
| Head SHA | **the PR #4 submission head** (stated in the report and the PR comment) |
| Previous reviewed head | `1d68da3e90d879da6318082551bab943c60cf68b` |
| Review branch | `review/adr0012-verify-1-codex` |
| Scope | verify F1–F3 independently; check section-by-section that nothing outside the response's closure map changed; check the escalations and the attempt-record design |

### Package B: independent review of harness-0.7.1 revision 2

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-10-25-harness-0.7.1` |
| Repository | `elusivenode/hio` |
| Base SHA | `6fbec1aa064551d7aa505cf3008a677acfd68e73` (`main`) |
| **Head SHA** | **`9878dd0bad6fa61a0ef8519a6d47da7198b08526`** (pushed; branch `docs/harness-0.7.1-review-receipt`). Fixed; never rebased or force-pushed during the review. **Stop if the branch tip differs** |
| Review branch | `review/harness-0.7.1-codex`, cut at the head, in an isolated worktree |
| Reviewer | Codex, independent reviewer; writes `.md` files under `reviews/` only |
| Delivery | **push-only pilot, no reviewer PR** — *requires the owner's explicit confirmation*; otherwise harness-0.7 step 3 applies |
| Assignment string for the record | `owner direct instruction to Codex, 2026-10-25, REVIEW-2026-10-25-harness-0.7.1, base 6fbec1aa064551d7aa505cf3008a677acfd68e73, head 9878dd0bad6fa61a0ef8519a6d47da7198b08526 (text recorded verbatim in docs/history at receipt; OD-0051)` |
| Subject (read-only) | `docs/decisions/harness-0.7.1-proposal.md` (§3 and §4 hold the replacement text) |
| Reference (approved) | `docs/harness/operating-model.md` §6.2 and §1.1; `tools/check_review_branch.sh`; `tools/check_review_assignment.py`; OD-0021; OD-0040; OD-0050 and its receipt commit `eadda1e`; the stopped `proposal/harness-0.8` at `b86f497`, §1–§3 |

**Challenge areas** (the owner's seven; answer each with file and line references, and build
counterexamples rather than only reading):

1. **Reviewer provenance and byte-identical import integrity.** Does the procedure prove that
   the record on `main` is the file the reviewer committed, and tie it to the reviewer's exact
   commit? What does it fail to prove?
2. **Assignment and reviewer-only scope enforcement.** Do the existing scope and assignment
   checks, as the package uses them, enforce the assigned head and a reviewers-only scope without
   a PR? Where does a PR-less flow lose a control the CI gate gave?
3. **Unapproved implementation ancestry never entering `main`.** Prove or break the claim that
   the import writes only `reviews/` files and that the reviewer's commit is never an ancestor of
   `main`, including a branch whose middle commit touches another path and is reverted.
4. **Author-as-receiver risks.** Where Claude receives a review of Claude's own work, can adverse
   evidence be **suppressed or altered** without detection? What do the blob-identity check, the
   reachable branch and tag, and the reviewer-stated tip and sha256 actually detect, and what
   residual risk is left?
5. **Adversarial cases:** deleted records; forged hashes; modified index entries; moving branch
   heads; conflicting assignments. For each, state whether the procedure stops, and how.
6. **Stop-on-mismatch and recovery.** Is every mismatch a stop? After a stop or a partial import,
   can the receiver recover without leaving unreviewed content in `main`?
7. **Harness-0.8 concerns.** For each concern in the stopped harness-0.8 proposal (stacked
   reviewer PRs; receipt becoming integration of unaccepted work; step 6 pushing towards a
   competing author PR; the descent checks in `tools/`; reviewer branches cut from `main`),
   state whether harness-0.7.1 **resolves** it, **partly** resolves it, or **leaves** it, and
   where 0.7.1 deliberately differs.

**Out of scope:** approving harness-0.7.1; changing `tools/` or `.github/`; ADR-0012 and its
findings; any rights value. The draft file `harness-0.7.1-review-assignment-draft.md` at the head
has a different, earlier question list. **Where it differs from this package, this package
governs**; the draft is not an owner-authored source.

**Output:** a verdict (`READY`, `READY WITH CONDITIONS` or `REQUEST CHANGES`); findings as
`F-REVIEW-2026-10-25-harness-0.7.1-N` with failure scenarios; and, in the final message, the
branch tip SHA and the sha256 of each added file.

**Receipt of Package B (if the pilot is confirmed).** Claude runs the harness-0.7.1 §4 procedure
as a second one-off exception: `check_review_branch.sh` from `main`, `check_review_assignment.py`
with the string above, the blob-identity and additive-`README` checks, a pure import commit,
the annotated tag, and no merge of the review branch.

## What this record does NOT do

- It does **not** approve ADR-0012 or harness-0.7.1, close or waive any finding, verify any
  right, authorise S1b, merge PR #4, or change harness-0.7.
- It does **not** authorise the push-only pilot. The owner's text only recommends it; Package B
  asks the owner to confirm.

## Corrections (append-only)

None.
