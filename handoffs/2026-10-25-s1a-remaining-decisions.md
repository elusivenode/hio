---
id: HANDOFF-2026-10-25-s1a-remaining-decisions
date: 2026-10-25
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code session)
work_status: done (decisions recorded); S1a acceptance pending (owner)
base_revision: 3fd129e946498e180b9f78a13d3f745afb46c638   # main
head_revision: self       # resolve: git log -n1 --format=%H -- handoffs/2026-10-25-s1a-remaining-decisions.md
work_card: T-0005 (S1a), OD-0038
---

# Handoff: the remaining S1a owner decisions

> A dated snapshot. **Not a decision; S1a is not accepted.** The authority is
> [OD-0038](../docs/decisions/owner/OD-0038-s1a-remaining-decisions.md).

## Done (OD-0038)

- **Verified first**, as the owner made the decisions conditional on it:
  - the implementation is identical to the reviewed head `084154c`;
  - the approved standards, harness, ADRs, `AGENTS.md` and contract blobs are unchanged;
  - `check_repo` passes, and two clean runs reproduce the four `data.csv` hashes.
  - Detail is in OD-0038.
- **Recorded:** the owner's instruction verbatim (`docs/history/`, sha256 `46e013c1…`), and
  OD-0038 itself:
  - Q-007 ratified, as used;
  - Q-008 accepted for S1a only, as a known limitation, with S1b needing a network and
    credential-control decision first;
  - Q-005a confirmed;
  - the capture-clock archive question deferred to S1b design, behaviour unchanged.
- **Registers:**
  - `open-decisions.md`: Q-005a, Q-007 and Q-008 now point to OD-0038; **Q-010** added (the
    archive question, blocking S1b design);
  - both indexes, STATUS and T-0005 updated.
- **§10 preparation:** the commands, the verbatim prompts and an owner-only grading key were
  prepared **outside the repository**. A copy in the repository would be readable by the fresh
  agents. Revision X is `3fd129e`.

## Flagged for the owner (no change made)

- **The §10 Codex baseline.** At X, `reviews/README.md` *Assigned reviews* still lists
  REVIEW-2026-10-18-t0004 as **assigned** (OD-0010). The readiness document's expected Q2 answer
  ("No review target has been assigned.") may therefore be incomplete. The owner fixes the
  grading baseline before grading.
- **The §10 prompt path.** The prompts say `hio/AGENTS.md`, which is the path from before the
  migration. The operating model is approved, so the text was not changed.
- **No dedicated test** exercises the archive-receipt case of Q-010. The fail-closed suppression
  it relies on is tested generally (`tests/test_f4_f7_acceptance.py`,
  `tests/test_query_properties.py`).

## Not done

- S1a is not accepted. Observations v0.3 is not approved. S1b is not authorised.
- The §10 test has not been run.
- Nothing is pushed or merged.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/s1a-owner-decisions-od0038` @ this commit (local) |
| Pushed? PR link | **no**: awaiting the owner's instruction to push and merge `--no-ff` |
| Received into `main`? | no |
| Next actor | **owner** |
| Prompt for the owner | "Run the §10 sessions using the owner kit at revision X = `3fd129e`, first fixing the Codex Q2 baseline. Then give Claude the grades and transcripts to record. Decide observations v0.3 separately, then S1a acceptance. Prerequisite: `main` still contains `3fd129e`, and OD-0038 is merged or explicitly left unmerged." |
