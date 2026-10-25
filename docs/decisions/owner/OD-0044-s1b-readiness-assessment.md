---
id: OD-0044
title: "Owner instruction: a bounded S1b readiness assessment (one report); no S1b implementation, real data, vendor contact, infrastructure or credentials"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-s1b-readiness-assessment.md (pasted by the owner, verbatim)
  sha256: 4853b017285b5d5e93c8b482af472f102e75acad4ecf2c2026b4e698326528d6
  date: 2026-10-25
  quote: "Begin a bounded S1b readiness assessment, without starting S1b implementation."
applies_to:
  - path: /
    revision: 1f5e5e29960ecb0bd07fa82f68e312b4cc80664b   # main when the instruction was received
related: {adrs: [HIO-ADR-0005, HIO-ADR-0010], tasks: [T-0002, T-0003, T-0005], findings: []}
---

# OD-0044: S1b readiness assessment

## Owner action

The owner instructed one concise S1b readiness report covering seven points:
- the rights evidence still needed;
- timing, calendars and the AUD cash-rate regime;
- network, credential, storage and capture controls;
- Q-010;
- the minimum first live-data output and its validation;
- the contribution to portfolio construction;
- authorised work versus new owner decisions.

The report ends with a recommendation, the unresolved blockers and the next owner decision.

**Prohibited by the instruction:**
- fetching real data;
- contacting vendors;
- creating infrastructure or credentials;
- modifying accepted S1a functionality;
- starting S1b implementation.

Any proposed change to approved standards, return mathematics or architectural boundaries is to
be escalated, not made.

## Output

[`docs/evidence/S1B-readiness-assessment.md`](../../evidence/S1B-readiness-assessment.md)
(`status: prepared_for_owner`). Its §8 lists the escalations: E1–E4.

## What this record does NOT do

- It does **not** authorise S1b, or any part of it.
- It does **not** lift OD-0013. Every source permission stays `unverified`.
- It does **not** approve any escalation in the report, amend HIO-ADR-0010 or any standard, or
  decide Q-004 or Q-010.
- It does **not** authorise the one-off manual samples or the sending of vendor questions.

## Corrections (append-only)

None.
