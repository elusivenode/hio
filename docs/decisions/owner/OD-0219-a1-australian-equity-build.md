---
id: OD-0219
title: "Owner authorises package A1 of T-0024: a proposed spec and a local, exploratory AUD total-return build for the Australian equity fund in snapshot s2"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-a1-australian-equity.md (owner's message, verbatim, with Claude's question)
  sha256: 1c5f8ae5cc685904402053cef1148758c57a161115505ea1f03064794740c5d8
  date: 2026-11-22
  quote: "Y"
base_revision: 6d7535a290107a899436bfa912996c7644555abc
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0163, OD-0176, OD-0210, OD-0213, OD-0218]}
---

# OD-0219: package A1, Australian equity

## Owner action

**Authorised,** package A1 of T-0024 only:

1. **A proposed spec** for the AUD market-price total return of the ASX fund VAS, from snapshot `s2` (already held; `eodhd.personal_evaluation`).
2. **One local, exploratory build** with the existing tools, and Claude's check of it on the real data.
3. **Any small tool change** a worker needs to handle an ASX fund.
4. **A stub build record** in the repository. No value from the series enters the repository (OD-0210).

## What this record does NOT do

It authorises no new data, no fetch, and no other package of T-0024. T-0024 as a whole stays `proposed`. It accepts no series and adopts no spec.

## Corrections (append-only)
