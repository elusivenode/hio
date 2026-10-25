---
id: HANDOFF-2026-10-25-adr0010-rev4-proposal
date: 2026-10-25
actor: claude/implementation-agent (Claude Opus 5.5)
work_status: proposed   # HIO-ADR-0010 rev 4 and the verification matrix await the owner; nothing approved
base_revision: 183523fd6e2cc148abfe2619426bfc38c7cf2108
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-25-adr0010-rev4-proposal.md
work_commits: [b35c75c, 183523f]
work_card: T-0005
---

# Handoff: HIO-ADR-0010 revision 4 proposal; T-0002 verification matrix

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files (this branch, `docs/adr0010-rev4-proposal`)
- added:
  - the verbatim instruction (sha256 `170ab13b…06c7`);
  - OD-0046;
  - `docs/decisions/HIO-ADR-0010-rev4-proposed.md`;
  - `docs/research/T-0002-owner-verification-matrix.md`;
  - this handoff.
- edited:
  - four index READMEs (one row each);
  - `STATUS.md`;
  - an append-only correction in the 2026-10-25 evidence note.

## Done
- `main` re-verified and pushed (`a37d81f`); the T-0002 evidence committed (`b35c75c`) and
  merged `--no-ff` (`183523f`, **not pushed**).
- Revision 4 is drafted as **proposed**:
  - its invariants section;
  - the stage table and gates;
  - every revision 3 S1b obligation re-mapped, none deleted, with S1-A10's three triangulations
    still owed at G2 unless explicitly superseded;
  - the index triangulations;
  - capture schedules;
  - per-dataset source ids;
  - Q-010 and Q-004.
- The verification matrix: D1–D9 × nine operations, with clause keys and U1–U7.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| No implementation, standard or approved-ADR change | `git diff --stat main -- src tests tools specs .github pyproject.toml uv.lock docs/standards docs/harness AGENTS.md docs/decisions/HIO-ADR-0010-first-slice-scope.md` | empty |
| Rights unchanged | `registers/sources.yaml` not in the diff | confirmed |
| Repository checks | `check_repo` (with the new files staged), `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- The TRI and SOFR Index accrual conventions are read from the methodology wording, not from a
  computed comparison (no further data was fetched).
- The SIFMA and the RBA bank-holiday pages are still unread.

## Conflicts found between documents
- The owner asked for "revision 4". The decisions README process step 5 forbids substantive
  edits to an approved ADR. Resolved as a separate proposed file that supersedes revision 3 only
  on approval. The owner may prefer a new ADR number instead.
- The evidence note's "one-day label shift" claim (§3, §5) is wrong. An append-only correction
  was added.

## NOT approved by this session
- Revision 4; any right (U1–U7); OD-0013's lift; S1b-1, S1b-2; the FX source; Q-004, Q-010.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/adr0010-rev4-proposal`, never committed under OD-0046. **Superseded** by `handoffs/2026-10-25-adr0011-staged-s1b-proposal.md` (OD-0047): the branch was renamed, and the file became HIO-ADR-0011 |
| Pushed? PR link | no. `main` at `183523f` is local and unpushed; `origin/main` = `a37d81f` |
| Received into `main`? | no |
| Next actor | **owner** |
| Prompt for the owner | "Answer U1–U7 in the verification matrix; decide whether revision 4 goes to an independent review (and whether it stays a revision or becomes a new ADR number). Prerequisite: the proposal branch is committed, or read in the working tree." |
