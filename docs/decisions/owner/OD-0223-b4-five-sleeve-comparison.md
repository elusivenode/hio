---
id: OD-0223
title: "Owner authorises package B4 of T-0024: a five-sleeve AUD comparison with a 60/40 sensitivity, on the series already built"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-b4-comparison.md (owner's message, verbatim, with Claude's question)
  sha256: da1285d43c520284e383b086707b8e240cd168d803e5c9a90c64e1f0c74dadb9
  date: 2026-11-22
  quote: "Y"
base_revision: dd9a307589587d4b19962331fc5d380d7781dbd2
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0210, OD-0220, OD-0222]}
---

# OD-0223: package B4, the five-sleeve comparison

## Owner action

**Authorised:** a comparison in AUD of VAS, SPY (unhedged), VGB, IEF (unhedged) and AUD cash on their common complete months, with a 60/40 sensitivity, using the existing comparison, portfolio and risk tools. The note goes in the local store and a stub in the repository. No value from the series enters the repository (OD-0210).

It runs without packages B1 (a proper USD cash leg) and B2 (a hedge from rates lockable at inception). Hedged figures appear only as labelled diagnostics.

## What this record does NOT do

It authorises no new data and no other package. It accepts no series, adopts no spec, and recommends no allocation or hedge ratio.

## Corrections (append-only)
