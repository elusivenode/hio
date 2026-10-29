---
id: OD-0106
title: "Owner authorises applying the approved option B amendment (d26c2fa) verbatim as harness-0.9b, and hiomux cleanup of run 20261028T081310Z-d55d; nothing pushed by this record"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-push-assign-h6-verify-4.md (owner's message, verbatim, with Claude's decisions 3 and 4)
  sha256: 7e734b207676828f382cf858149d441fa2b7babd3dd0faee9b18fc3a37877d31
  date: 2026-10-29
  quote: "yes"
applies_to:
  - path: docs/decisions/h6-option-b-amendment.md
    revision: "d26c2faca78fc40dc409ff53c872cb172e918d7e, blob 202f8d9219fcf1ab352d7809d51db81d1a63476a (approved, OD-0104)"
base_revision: 8662d62aea9d335fe43d53d01ccbe68092863856
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0091, OD-0100, OD-0104, OD-0105]}
---

# OD-0106: harness-0.9b applied; the closed run cleaned up

## Decision 3: apply option B

Applied verbatim, as OD-0091 applied harness-0.9a:
- **`docs/harness/operating-model.md`** (this OD's commit):
  - §6.2 step 5.6 replaced, from `**5.6 Index-row semantics.**` up to `**5.7 Verify.**`, by part A's block;
  - step 5.12 (part B's block) inserted after the 5.11 table, before `**Accountability, not mechanism.**`;
  - `version: harness-0.9b`, `approved_by: OD-0104`, and part E's changelog line with the date, OD and commit
    filled in.
  
  Each anchor matched exactly once; the inserted text is byte-identical to the amendment's code blocks. No other
  canonical file mentions Class S.
- **Part D (the H6 design wording)** lives in `docs/decisions/harness-0.9-proposal.md` on `proposal/harness-0.9`,
  not on `main`. It is applied there in commit `f4d4b28d4c8230edb8556aa6bca93e8d350a88bc` (local).
- **Part C:** no text change, as the amendment says.

**Unchanged:** §2.2, every other §6.2 step, tools, CI and hooks. H6 remains unactivated. Existing index rows are
unchanged.

## Decision 4: cleanup

`hiomux cleanup 20261028T081310Z-d55d` ran: the run's clones are gone (`wt/` empty) and no
`refs/hiomux/20261028T081310Z-d55d/*` remain. Its review branches and ledgers stay.

## Not authorised

- **Pushing** this commit (harness-0.9b on `main`) or `proposal/harness-0.9` at `f4d4b28d4c8230edb8556aa6bca93e8d350a88bc`. Decision 2's push covered
  only OD-0105 and its row.
- H6 approval or activation; receipt of VERIFY-2026-10-28-h6-1-4.

## Corrections (append-only)
