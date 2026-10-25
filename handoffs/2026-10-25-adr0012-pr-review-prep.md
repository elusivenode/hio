---
id: HANDOFF-2026-10-25-adr0012-pr-review-prep
date: 2026-10-25
actor: claude/implementation-agent (Claude Opus 5.5)
work_status: in_review   # HIO-ADR-0012 proposed; a Codex design review is authorised (OD-0048); nothing approved
base_revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108
head_revision: self       # = the PR Submission-Head; resolve with: git log -n1 --format=%H -- handoffs/2026-10-25-adr0012-pr-review-prep.md
work_commits: [bd0b8fd56bf6b849fe67abf04493e9e1693eb296]
work_card: T-0005
---

# Handoff: HIO-ADR-0012 renumbering, PR and review preparation

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files (this commit, on `docs/adr0012-staged-s1b-proposal`)
- **Renamed:** `HIO-ADR-0011-staged-s1b.md` → `HIO-ADR-0012-staged-s1b.md`, and
  `HIO-ADR-0011-review-assignment-draft.md` → `HIO-ADR-0012-review-assignment-draft.md`.
- **Added:** the verbatim instruction (sha256 `a2515361…7124`); OD-0048; this handoff.
- **Edited:**
  - the decisions register row;
  - the owner and history indexes;
  - the candidate row in `reviews/README.md`;
  - `STATUS.md`;
  - links and corrections in OD-0046 and OD-0047.

## Done
- The renumbering was verified as non-substantive. `git diff --no-index --word-diff` against the
  `bd0b8fd` blob shows changes only to:
  - the id, H1 and `drafted_under`;
  - the assignment link;
  - the numbering note and §8 item 4 (removed: resolved by the owner);
  - one changelog line.
- In the assignment draft, the review id, branch, subject path and finding prefix were changed.
  Question 5 is expanded with explicit timestamp semantics.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| No substantive ADR change | the word diff above | identifiers and links only |
| No implementation, standard, approved-ADR, register or review-record change | `git diff --stat main -- src tests tools specs .github pyproject.toml uv.lock docs/standards docs/harness AGENTS.md docs/decisions/HIO-ADR-0010-first-slice-scope.md registers reviews/records` | empty |
| No link to the old paths | `grep` for `](…ADR-0011-staged…` and `](…ADR-0011-review…` | none |
| Repository checks | `check_repo`, `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- The Codex review has not run. The binding assignment values are the ones the owner confirms
  from Git.

## NOT approved by this session
- HIO-ADR-0012; any supersession of HIO-ADR-0010; any right; S1b-1, S1b-2; a PR merge.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/adr0012-staged-s1b-proposal` @ this commit (the Submission-Head) |
| Pushed? PR link | pushed; the PR to `main` is stated in the owner-facing completion report |
| Received into `main`? | no |
| Next actor | **owner**, to confirm the assignment; then **Codex**, for REVIEW-2026-10-25-adr0012 |
| Prompt for Codex | as in the owner's assignment: the review id, base `183523f…`, head = the Submission-Head, branch `review/adr0012-codex`, scope per `docs/decisions/HIO-ADR-0012-review-assignment-draft.md`. Prerequisite: the head equals the PR head (`gh pr view --json headRefOid`) |
