---
id: OD-0020
title: "Owner instruction: proceed with S1a implementation under OD-0017, with five implementation considerations"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-s1a-proceed.md (the owner's chat message, verbatim)
  sha256: 3584f1710977df2155a479bdc3cab52199f37a98244d2568653674d4c7cc27d4
  date: 2026-10-24
  quote: "Proceed with the already-authorised S1a implementation under OD-0017. No further architecture approval is required before coding."
applies_to:
  - path: /
    revision: 9370256bac6ba2193b09c342170bd11ca57b70a3
related: {adrs: [HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007, HIO-ADR-0010], tasks: [T-0005], findings: []}
---

# OD-0020: proceed with S1a implementation

## Owner action

The owner reviewed HIO at `9370256` and instructed Claude to proceed with S1a under OD-0017,
in this order:
1. harness CI;
2. Python/uv skeleton;
3. contracts and local object store;
4. observation/vintage/knowability model;
5. cash and FX constructions;
6. fixture-only rights and publication gates.

The work goes in small, testable commits. At completion, Claude submits a **fixed-head evidence
package** for a separately assigned Codex review.

## Implementation considerations (owner's, summarised; the verbatim text governs)

1. **Query modes:** all three knowledge query modes are deterministic. Tests cover:
   - same-time vintages;
   - revision sequences;
   - quarantine;
   - late capture;
   - evidence insufficiency;
   - schedule-only backfills.

   OBS-INV-007 is a mandatory regression fixture.
2. **Return accounting:** test it against every RA §3.2 and FX fixture, checking both numeric
   correctness and information availability.
3. **Synthetic rights fixtures:**
   - cover every required operation, every permission state, and refusal atomicity;
   - synthetic `owner_verified` metadata never changes the genuine
     `registers/sources.yaml`.
4. **Public-repository safeguards** against secrets, downloaded data, local databases and
   non-releasable artefacts. The network rules permit dependency installation and forbid
   source-data access.
5. **Keep migration provenance and approved historical documents intact.** No rewriting of
   approved content to tidy paths or stale wording.

## Exclusions (owner's)

- **Out of S1a:**
  - live sources, buckets, credentials, schedules;
  - SMSF integration;
  - equity returns, portfolio analytics;
  - vendor contact.
- **No self-certified acceptance.** An existing-chat review is not the §10 fresh-session test.
- **T-0002 and T-0003** continue only within their existing authorisations.
- **No T-0004 merge. No S1b.**

## What this record does NOT do

It does not accept S1a, authorise S1b, or change any approval.
