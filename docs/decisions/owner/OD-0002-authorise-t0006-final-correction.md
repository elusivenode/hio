---
id: OD-0002
title: Owner instruction to execute the T-0006 final harness correction
decision: authorise_work
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-18-directive-t0006-final-correction.md
  sha256: 99b0ddad6bdf0fa989f9572b94aa4d7d0c345ddf450af0861d63f2c4a9d160a8
  date: 2026-10-18
  quote: >-
    "From: HIO owner, with ChatGPT acting as strategic architecture collaborator …
    Authorisation: The owner's explicit instruction to execute this directive authorises the
    bounded documentation work described below. It does not approve the resulting documents,
    HIO-ADR-0008, other A01 ADRs, HIO-S1, deployment, or changes to macsmsf."
    The owner supplied the directive in the Claude Code chat by file path.
applies_to:
  - path: hio/
    revision: 23ad27f3d25763d829b5846815b0568000d6648f
related: {adrs: [HIO-ADR-0008], tasks: [T-0006], findings: []}
---

# OD-0002: the T-0006 final correction instruction

## Owner action

The owner explicitly authorised six bounded documentation corrections to the staged harness,
starting from `23ad27f`:
1. authorisation versus approval;
2. advice and adoption;
3. trailer provenance;
4. the provisional bootstrap;
5. the state-aware reviewer test;
6. low-risk deduplication.

The directive was co-drafted with ChatGPT. The authority is the owner's own statement in it.

## Scope and exclusions

Per the directive's "Hard boundaries":
- documentation only;
- no ADR status change;
- no acceptance of T-0006;
- no waiving or closing of findings;
- no substantive roadmap or architecture rewrite;
- no `macsmsf` or HIO-S1 work.

## What this record does NOT do

It does not accept T-0006, approve HIO-ADR-0008 or any A01 ADR, or assign a Codex review.
