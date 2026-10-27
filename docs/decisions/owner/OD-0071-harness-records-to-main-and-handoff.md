---
id: OD-0071
title: "Bring the harness-0.9 authority records (OD-0068, OD-0070 and their transcripts) to main, update STATUS.md and add the session handoff; documentation only, nothing approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-documentation-merge-and-handoff.md
  sha256: 2262c3d49443812109d193e3b45c09c3e4e60fd028db2e40045b73eb2e57e4a1
  date: 2026-10-28
  quote: "yes, do the documentation merge and handoff"
applies_to:
  - path: STATUS.md
    revision: 16ea0c6f472b61a28a9741c75635255bf173ffa6   # base: origin/main
  - path: (records listed below)
    revision: 50e72293df23f3bead56e359436d1a1b40411500   # source: proposal/harness-0.9
related: {adrs: [HIO-ADR-0008], tasks: [T-0009], findings: []}
---

# OD-0071: harness-0.9 authority records to `main`, STATUS, handoff

## Owner action

"yes, do the documentation merge and handoff", answering Claude's proposal (quoted in the source
file) to keep the authority for the harness-0.9 work on `main`, as OD-0069 did for T-0009.

## What was done

On `docs/od0071-harness-records-and-handoff`, cut from `origin/main` at `16ea0c6`:

1. **Byte-identical import** from `50e7229` of six files:
   - OD-0068 and OD-0070;
   - the transcripts of the owner's instruction (`2026-10-28-owner-harness-0.9-instruction.md`)
     and adoption (`2026-10-28-owner-adopt-harness-0.9-disposition.md`);
   - the solution architect's assessment and Claude's response.

   Each blob equals the source.
2. **Index rows** for those records, taken verbatim from the source branch. The open-decisions
   queue's Q-014 entry is updated, with the proposal named by branch and commit rather than linked,
   since the proposal is not on `main`.
3. **`STATUS.md`** updated: the proposal is pushed at `50e7229`, its direction adopted (OD-0070),
   and its open owner decisions listed.
4. **The session handoff** `handoffs/2026-10-28-harness-0.9-and-od0069.md`.

## Scope and exclusions

The harness-0.9 proposal, `MAP.md`, `knowledge/findings.md` and the dry-run report stay on
`proposal/harness-0.9`. Putting them on `main` would be integration, which awaits the owner's
approval of Phase A. No approved document (`AGENTS.md`, the operating model, templates, skills)
changes.

## What this record does NOT do

It approves no part of harness-0.9, activates nothing, and changes neither the review protocol
nor T-0009's scope.

## Corrections (append-only)

None.
