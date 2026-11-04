---
id: OD-0172
title: "Owner decides the rights for the RBA's historical overnight cash series, pages read, and allows one one-off download; E-0003 isn't extended"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-rba-history-rights.md (owner's messages, verbatim, with the question each answered)
  sha256: b7ddab6bc87427cfce4c1cccd743c1c430b6ba8ef716a241ee1bee29c63f3569
  date: 2026-11-04
  quote: "yes, pages read"
base_revision: 0a816f59493b21f7571013f852073b1860ca5993
related: {adrs: [], tasks: [T-0002], findings: [], ods: [OD-0116, OD-0118, OD-0170, OD-0171]}
---

# OD-0172: RBA historical overnight cash

The owner read the live pages and answered yes to all four questions in `docs/research/T-0002-rba-history-reading-pack.md`:

1. **File:** the daily historical F1 table, 1976 to 31 December 2010, with monthly F1.1 as the fallback.
2. **Third-party columns:** the whole file is a sealed receipt. Only the RBA-sourced overnight series is used. **If that series' own source isn't the RBA, its use stops, and it comes back to the owner.**
3. **Download:** one modest, one-off request, with a declared User-Agent. No retries.
4. **Operations:** raw retention "indefinite, for audit and rebuild"; calculate, store derived, rebuild, external processing, `hio_internal` and agent context; on RBA attribution and no implied endorsement.

`rba.f1_historical` is `owner_verified` for these. The conditions are recorded as met, because the tool's manifest carries the attribution and each later use will.

## Not authorised

Extending E-0003, which needs its own yes and pre-registration; third-party columns; quotation in documents, including this repository; any consumer release; scheduled capture; other RBA tables.

## Corrections (append-only)
