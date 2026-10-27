---
id: OD-0070
title: "Adopt the solution architect's harness-0.9 disposition (ADOPT WITH CHANGES), qualified by Claude's response and the owner's adjudication; authorise drafting revision 3 only"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-adopt-harness-0.9-disposition.md
  sha256: 06470061791b0650e8b8fbab5bc923eaf6dc8ffea5728417d77bf37b47a46f0c
  date: 2026-10-28
  quote: "I authorise you to prepare **revision 3 of the harness-0.9 decision package**. This is a bounded drafting authorisation only; it does not approve or authorise implementation, integration or activation of the proposed harness amendments."
adopted_advice:   # collaborator material the owner adopted (AGENTS.md rule 4), each verbatim
  - source: docs/history/2026-10-28-solution-architect-harness-0.9-assessment.md
    sha256: 0a3419cecffed702dff8726131cff903efaef04e5da457fbc372da847462812b
  - source: docs/history/2026-10-28-claude-response-to-solution-architect-harness-0.9.md
    sha256: f9a5ef546f1175f1bd0dc5330d9277d7b796f1c386059794ba09c7bd71515e57
applies_to:
  - path: docs/decisions/harness-0.9-proposal.md
    revision: f5ce1b8beaaaed59fbcbccf586892ac9ae1cf261   # revision 2, the base for revision 3
related: {adrs: [HIO-ADR-0008], tasks: [T-0009], findings: []}
---

# OD-0070: adopt the harness-0.9 disposition; draft revision 3

## Owner action

The owner "adopt[s] the solution architect's **ADOPT WITH CHANGES** disposition for harness-0.9,
qualified by your response dated 28 October 2026 and the final architectural adjudication below",
and authorises a bounded **drafting** of revision 3.

The adjudication fixes the design direction for revision 3:
- ten adopted points;
- an H7 qualification separating source consistency, owner authority and publication permission;
- the authority and sequencing rules;
- seven deliverables.

The verbatim text is the source file. This record does not restate it as policy.

## Scope and exclusions

**Authorised:** revising `docs/decisions/harness-0.9-proposal.md` and its proposed seed files
(`MAP.md`, `knowledge/findings.md`) on `proposal/harness-0.9`. Recording the adoption (this OD and
the three transcripts). Pushing that branch.

**Not authorised** (the owner's stop conditions):
- any merge;
- activation of an approved document (`AGENTS.md`, the operating model, templates, the skill);
- any reviewer-protocol change;
- any new standing delegation;
- any CI enforcement change;
- any expansion of T-0009's scope.

T-0009 remediation under OD-0067 remains the immediate implementation priority, and no harness
change enters its branches.

## What this record does NOT do

- It approves no part of harness-0.9: not Phase A, Phase B, H7 or any seed file.
- Adopting the disposition directs the drafting. It is not approval of the resulting text, which
  needs a separate owner approval at an exact revision (`AGENTS.md` rule 3).
- The solution architect's assessment and Claude's response remain advice, except where the owner's
  adjudication adopts them.

## Corrections (append-only)

None.
