---
id: OD-0081
title: "Owner adopts the revised direction for a Codex CLI solution architect in hiomux (gpt-6.1-sol high; MACSMSF excluded; logged consultations; Codex review independent; existing knowledge records reused; read-only pilot with three regression cases); direction only, no implementation authorised"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-sa-direction.md (typed by the owner, verbatim)
  sha256: a02383f2be209972c1228c38a8b112b6d03097b8bd71546730cc5c1c8bbe2aa1
  date: 2026-10-28
  quote: "This approves the architectural direction only. It does not authorise implementation or approve harness-0.9 Phase A."
applies_to:
  - path: docs/decisions/sa-slice-1-proposal.md
    revision: self   # the proposal returned under this instruction; resolve with git log -n1 --format=%H -- docs/decisions/sa-slice-1-proposal.md
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], open_decisions: [Q-014], ods: [OD-0072, OD-0073, OD-0077, OD-0080]}
---

# OD-0081: solution-architect direction

## Owner action (verbatim in the source file)

The owner adopts Claude's revised direction for an automated solution architect, which replaces the
interactive ChatGPT architect. It does so within seven boundaries:
1. the existing Codex CLI and hiomux, with no separate Responses API service;
2. `gpt-6.1-sol` at High, subject to CLI availability and regression testing, with the reviewer configuration
   unchanged;
3. no MACSMSF content and no private financial data;
4. Claude may consult the architect directly, but consultations are logged and summarised to the owner, and its
   advice cannot widen Claude's scope, approve, waive or accept;
5. Codex's review stays independent, and the architect never directs Codex or influences its assignment or test
   plan;
6. existing knowledge records are reused, with no competing store;
7. a read-only, reversible pilot with three leak-free historical regression cases.

**Direction only.** No implementation is authorised, and harness-0.9 Phase A is not approved.

The ChatGPT-drafted specification that preceded this is collaborator advice (`AGENTS.md` rule 4). It is not
recorded verbatim and was adopted only as revised by these boundaries.

## The instruction carried out

"verify the current harness authority, model availability and hiomux security boundaries, then return a compact
first-slice proposal with prerequisites, acceptance criteria and stop conditions."

- Done by scratch probes only: a read-only `codex exec` with `gpt-6.1-sol`, and local `sandbox-exec` checks. The
  model never touched MACSMSF or credentials; canary files stood in for them.
- The proposal is `docs/decisions/sa-slice-1-proposal.md` (proposed). hiomux, the repository's code and the
  harness are unchanged.
- Main results:
  - an architect role needs no harness amendment;
  - `gpt-6.1-sol`/`high` is available and applied;
  - Codex's own read-only sandbox cannot exclude MACSMSF, so hiomux's profile must;
  - two gaps remain for slice 1: HTTPS stays open (G-a), and the home folder is readable, including the
    reviewer's transcripts (G-b).

## Not authorised

- Implementing slice 1.
- Any hiomux change.
- Any files under `docs/agents/`.
- Any architect run beyond the scratch probes.
- Harness-0.9 Phase A.

## Corrections (append-only)

None.
