---
id: HANDOFF-2026-10-25-adr0011-staged-s1b-proposal
date: 2026-10-25
actor: claude/implementation-agent (Claude Opus 5.5)
work_status: proposed   # HIO-ADR-0011 awaits review and the owner; nothing approved or assigned
base_revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-25-adr0011-staged-s1b-proposal.md
work_commits: []
work_card: T-0005
---

# Handoff: HIO-ADR-0011 (staged S1b) proposed

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files (one commit on `docs/adr0011-staged-s1b-proposal`)
- **New:**
  - HIO-ADR-0011 (`proposed`) and its draft review assignment;
  - the T-0002 verification matrix;
  - OD-0046 and OD-0047, with their verbatim instructions;
  - this handoff, and the superseded OD-0046 handoff.
- **Edited:**
  - the decisions register (HIO-ADR-0011 row);
  - the owner, history and research indexes;
  - one candidate row in `reviews/README.md`;
  - `STATUS.md`;
  - an append-only correction in the 2026-10-25 evidence note.
- **Not touched:** `HIO-ADR-0010-first-slice-scope.md`, every approved standard, `src/`,
  `tests/`, `specs/`, `registers/`.

## Done
- `main` verified and pushed (`a37d81f..183523f`).
- HIO-ADR-0011 drafted:
  - §2, revision 3's provisions by id: only S10-B2 and S10-B5 superseded, plus the conditional
    wording of S10-B8(ii);
  - §3, the invariants;
  - §4.1, the funding benchmarks (no reclassification);
  - §4.3, the publication and revision windows;
  - §4.6, unavailable versus denied;
  - §4.7, Q-010;
  - §5, the complete obligation mapping.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| No implementation, standard or approved-ADR change | `git diff --stat main -- src tests tools specs .github pyproject.toml uv.lock docs/standards docs/harness AGENTS.md docs/decisions/HIO-ADR-0010-first-slice-scope.md registers` | empty |
| Repository checks (all files staged) | `check_repo`, `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- The §2 revision 3 quotations were machine-checked: all 12 are substrings of the approved blob
  `8ade196` (`hio` `5ea6287`), after removing bold and normalising whitespace.
- The §4.4 "no label shift" claim rests on the methodology wording. No data comparison was made,
  by instruction.

## Conflicts found between documents
- **"HIO-ADR-0011"** also names the future equity ADR in planning documents and an immutable
  review record. Left unedited and flagged (OD-0047).

## NOT approved by this session
- HIO-ADR-0011; any supersession of HIO-ADR-0010; a review assignment; any right; S1b-1, S1b-2;
  the FX source; Q-004, Q-010; the equity ADR number.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/adr0011-staged-s1b-proposal` @ this commit |
| Pushed? PR link | branch **not pushed**; `main` pushed at `183523f` |
| Received into `main`? | no. It is a review head, and is merged only on the owner's instruction after review |
| Next actor | **owner** |
| Prompt for the owner | "Issue (or amend) the draft assignment for REVIEW-2026-10-25-adr0011 at this head; answer U1 and U4 in the verification matrix; choose a new number for the equity ADR. Prerequisite: the head SHA from the completion report." |
