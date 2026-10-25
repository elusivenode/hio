---
id: OD-0046
title: "Owner instruction: push main; integrate the T-0002 RBA/NY Fed evidence (--no-ff, permissions unverified); draft HIO-ADR-0010 revision 4 (staged S1b) as a proposed amendment; prepare the owner-verification matrix"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-integrate-t0002-draft-adr0010-rev4.md (pasted by the owner, verbatim)
  sha256: 170ab13b235e19cdfb925726d54f2f5238fac0496d3fed6605ac08b558b206c7
  date: 2026-10-25
  quote: "Prepare **HIO-ADR-0010 revision 4 as a proposed amendment**, not approved policy."
applies_to:
  - path: /
    revision: a37d81f3cd4fa7fb61b912c64d82e7ed7077db72   # main re-verified, then pushed
  - path: docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md
    revision: b35c75c   # committed; integrated by merge 183523f
related: {adrs: [HIO-ADR-0010, HIO-ADR-0005], tasks: [T-0002, T-0005], findings: []}
---

# OD-0046: push, integrate T-0002 evidence, draft ADR-0010 rev 4

## Owner action

1. **Confirm the readiness-assessment merge is unchanged, then push `main`.**
2. **Commit the T-0002 evidence** on its branch, every permission kept unverified.
3. **Check** that no source data, unauthorised third-party material, credentials or
   implementation changes are included.
4. **Integrate it `--no-ff`**, after the diff and the repository checks.
5. **Preserve** the URLs, access dates, quotations and uncertainties.
6. **Draft HIO-ADR-0010 revision 4 as a proposed amendment**, with the preferred design:
   - S1b-1, the cash legs and publisher indices;
   - S1b-2, FX on a separately authorised source;
   - further triangulations, independently gated.

   It must preserve:
   - S1a;
   - the point-in-time invariants;
   - the immutable evidence model;
   - independent releases;
   - the boundary.

   It must address:
   - the acceptance criteria, without silently deleting any;
   - the index triangulations;
   - capture schedules;
   - per-source permissions;
   - Q-010.
7. **Prepare the T-0002 owner-verification matrix**, per dataset and per operation.

**Prohibited:**
- marking any right owner-verified;
- fetching more real data;
- contacting publishers;
- implementing adapters;
- creating infrastructure;
- scheduling capture.

The owner said to stop if a design needs a change to the return mathematics or weakens
evidence integrity.

## Execution

**Steps 1–2.**
- `main` = `a37d81f`, with parents `1f5e5e2` and `569753a` and tree `2f4ceec…`, equal to
  `569753a`. `origin/main` (`1f5e5e2`) was an ancestor.
- A clean worktree at `main` ran `check_repo` PASS and `pytest` 278 passed.
- Pushed: `1f5e5e2..a37d81f`.
- The T-0002 evidence was committed as `b35c75c`.

**Step 3, scan of the staged diff.**
- no `.csv`, `.json`, `.xlsx` or `.parquet` file;
- the only decimals added were `1.00000000` (the documented SOFR Index base) and `4.00`
  ("4.00 pm");
- no secret-like strings;
- protected paths unchanged;
- every genuine rights record loads as `unverified` with every permission `unknown`.

**Step 4.** Merged `--no-ff` as `183523f`, tree equal to the branch's; the branch was deleted.
`main` was **not pushed again** after this merge, because the instruction's push was step 1.

**Steps 6–7.**
- `docs/decisions/HIO-ADR-0010-rev4-proposed.md` (since renamed; see Corrections), with
  `status: proposed`.
- [`docs/research/T-0002-owner-verification-matrix.md`](../../research/T-0002-owner-verification-matrix.md).
- **A conflict was flagged:** the decisions README (process step 5) says an approved ADR "is
  never edited in substance". So revision 4 is a **separate file**, and the approved rev 3 file
  is untouched.
- **A correction of the author's own error:** the 2026-10-25 evidence note's "one-day label
  shift" for the index triangulations was wrong. An append-only correction was added, and no
  earlier text was rewritten.
- **No stop condition was reached:** the proposal changes no approved standard, return
  mathematics or evidence-integrity guarantee.

## What this record does NOT do

- It does **not** approve revision 4, or supersede revision 3.
- It does **not** verify any right, lift OD-0013, or authorise S1b-1 or S1b-2.
- It does **not** decide Q-004 or Q-010, or the FX source.

## Corrections (append-only)

- 2026-10-25 (OD-0047): before this record was committed, the owner directed that the proposal
  become a new ADR. The file was renamed to
  `docs/decisions/HIO-ADR-0011-staged-s1b.md` and revised under OD-0047. The text above describes
  the state under OD-0046.
- 2026-10-25 (OD-0048): the owner renumbered the proposal **HIO-ADR-0012**, now
  [`docs/decisions/HIO-ADR-0012-staged-s1b.md`](../HIO-ADR-0012-staged-s1b.md). HIO-ADR-0011
  stays reserved for the equity total-return decision. The link in the entry above was corrected
  on the owner's instruction ("any new links introduced by this proposal").
