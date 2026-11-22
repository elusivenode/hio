---
id: OD-0220
title: "Owner authorises package A4 of T-0024: a research note comparing Australian and US equity against AUD cash, with the currency effect separated"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-a4-equity-comparison.md (owner's message, verbatim, with Claude's question)
  sha256: ae91d365cf7afb215da02bbe46386c2d8b880b821bd420eafa1cbbaf4ed12a68
  date: 2026-11-22
  quote: "Y"
base_revision: ffd7ff415faa0d36b0e078822316ae3c0aa7981d
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0199, OD-0210, OD-0216, OD-0218, OD-0219]}
---

# OD-0220: package A4, the equity comparison

## Owner action

**Authorised,** package A4 of T-0024 only:

1. **The analysis,** on the local series already built: Australian equity (VAS) and US equity (SPY, unhedged in AUD) against AUD cash, on their common complete months, with the currency effect separated and uncertainty stated.
2. **A small worker-built tool** where the existing analytics do not cover it, written on invented data; and an AUD excess series for VAS over AUD cash with the existing excess tool.
3. **The note in the local store,** and a stub in the repository. No value from the series enters the repository (OD-0210).

Hedged figures appear only as labelled diagnostics.

## What this record does NOT do

It authorises no new data, no fetch and no other package of T-0024. It accepts no series, adopts no spec and recommends nothing.

## Corrections (append-only)
