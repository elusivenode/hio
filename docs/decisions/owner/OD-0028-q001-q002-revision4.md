---
id: OD-0028
title: "Owner instruction: Q-001/Q-002 drafts revision 4 (header fix; Q-002 processing order vs acquisition history); architectural direction approved, exact text not yet"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-q001-q002-revision4.md (pasted by the owner, verbatim)
  sha256: 54a8a43b9c949f6d6008679246b17345927b835d9c751123429a23be9d7b59cc
  date: 2026-10-24
  quote: "I approve the architectural direction of both amendments, but not yet their exact revisions as governing standards."
applies_to:
  - path: docs/standards/drafts/
    revision: 6f013a70996e0fef15bb6cb1425dd0e569e932c9   # revision 3, reviewed by the owner
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0028: drafts revision 4

## Owner action

- **Approved:** the architectural direction of OBS-AMEND-Q001 and OBS-AMEND-Q002.
- **Not yet approved:** their exact revisions as governing standards.
- **Documentation corrections only:**
  - Q-001: remove the duplicated query-mode table header;
  - Q-002: resolve the OBS-INV-011 / OBS-INV-015 inconsistency. This distinguishes fixed
    capture-time evidence processed in different orders, genuinely different acquisition
    histories, and final conflict state versus historical event history. The invariants and
    acceptance tests then require only guarantees the model can deliver.
- **Preserved:**
  - deterministic final conflict identity;
  - append-only provenance;
  - point-in-time stability;
  - owner-only resolution;
  - complete diagnostics.
- If the event representation must change, present the narrowest alternative before
  implementation.

## What this record does NOT do

- It does not change source code, tests, the approved standard or review records.
- It does not approve a governing standard or authorise F4/F7 implementation.
- It does not merge any PR, accept S1a, or start S1b.
