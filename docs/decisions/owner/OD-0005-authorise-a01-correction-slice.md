---
id: OD-0005
title: Owner instruction to proceed with the A01 correction slice (T-0008)
decision: authorise_work
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: >-
    Claude Code chat, 2026-10-18. The owner pasted a Codex recommendation ("directing Claude's A01
    correction slice next, with a separate remediation response for the eight open findings and
    a fixed submission head for Codex verification. Leave T-0006 acceptance as its own
    decision.") followed by the owner's own words.
  sha256: null   # chat message, not a file
  date: 2026-10-18
  quote: "proceed with the correction slice"
applies_to:
  - path: hio/
    revision: e99fae104908c79fc800222b9c2eb1c82fec388d
related: {adrs: [HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007], tasks: [T-0008], findings: [F-REVIEW-2026-10-18-a01-1, F-REVIEW-2026-10-18-a01-2, F-REVIEW-2026-10-18-a01-3, F-REVIEW-2026-10-18-a01-4, F-REVIEW-2026-10-18-a01-5, F-REVIEW-2026-10-18-a01-6, F-REVIEW-2026-10-18-a01-7, F-REVIEW-2026-10-18-a01-8]}
---

# OD-0005: proceed with the A01 correction slice

## Owner action

The owner instructed Claude to proceed with the correction slice for the eight open A01 findings
(`REVIEW-2026-10-18-a01`), starting from `e99fae1`. The owner adopted the forwarded Codex
recommendation on its form:
- fixes first;
- then one remediation response for the eight findings;
- with a fixed submission head for Codex verification.

## Scope and exclusions

**Scope:** documentation, standards, spec and plan corrections inside `hio/` that address the
eight findings, with numeric synthetic fixtures; the remediation response; the *Remediation
claim* cells.

**Excluded:**
- any ADR `status:` change;
- accepting T-0006;
- closing or waiving findings (Codex verifies; only the owner waives);
- editing the review record;
- HIO code, infrastructure, live capture or vendor contact;
- `macsmsf`;
- HIO-001;
- S1 implementation.

## What this record does NOT do

It does not approve HIO-ADR-0004/0005/0006/0007 or any standard. It does not authorise S1. It
does not assign the verification review; the owner assigns that at the submission head.
