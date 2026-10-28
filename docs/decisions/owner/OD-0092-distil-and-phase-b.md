---
id: OD-0092
title: "Owner authorises the first findings distil (prepared for owner acceptance), a drafted architect-manifest fix, and bounded Phase B implementation work on H6 then H11 (activation still needs Codex review and approval at an exact revision)"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-approve-phase-a-and-phase-b.md (owner's message, verbatim, with the questions it answers)
  sha256: a1865264f200f95d96c75984611dde32085633921a709d7fcf4e4301201e624d
  date: 2026-10-28
  quote: "yes to all four"
base_revision: a949875
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0070, OD-0080, OD-0089, OD-0091]}
---

# OD-0092: the first distil, and Phase B (H6, H11)

## What is authorised

1. **The findings backlog and the first distil.**
   - Add the later candidate lessons to the Inbox of `knowledge/findings.md`: the five in
     `handoffs/2026-10-28-solution-architect-and-hiomux-layout.md`, and this session's (OD-0086 to OD-0092).
     Each is checked against its source.
   - Prepare the first distil: a proposed disposition for every Inbox line (keep and settle, merge, supersede,
     move or drop), each with its provenance.
   - **The owner accepts the Settled text separately, at an exact revision.** Preparing it settles nothing.
2. **The architect-manifest fix, drafted only:** make the solution architect read `MAP.md` and the findings
   index from its own checkout instead of `proposal/harness-0.9`. Applying it needs a further owner yes (OD-0089
   left the manifest unchanged).
3. **Phase B implementation work, bounded:** **H6** (scripted assignment and receipt) first, then **H11** (Codex
   continuity), as designed in the proposal (§6.1, §6.3).
   - The work happens on branches.
   - **Activation is not authorised:** each still needs the Codex review its design requires, including H6's
     deliberate-failure cases, and the owner's approval at an exact revision.
   - Codex's review protocol is not changed by this work until that approval.

## Not authorised

- H3, H7 and H8;
- branch protection;
- applying the manifest fix;
- settling any finding;
- any change to Codex's assignment path before approval;
- live operation.

## Corrections (append-only)
