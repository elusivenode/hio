---
id: OD-0222
title: "Owner authorises one EODHD fetch of VGB, IGB and AGVT into a new pinned local snapshot, with three proposed specs and three local exploratory builds (T-0024 package B3)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-b3-fetch.md (owner's message, verbatim, with Claude's question)
  sha256: cdaf514193d9a39a4f27a8d216ef3cf108e7a7ff8aada35dc2d81ca0dadb9384
  date: 2026-11-22
  quote: "Y"
base_revision: 6ae728817251c2b785f7c58c0966fd9ca1e904d1
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0163, OD-0164, OD-0176, OD-0210, OD-0221]}
---

# OD-0222: Australian duration, the fetch and the builds

## Owner action

**Authorised:**

1. **One fetch** of VGB, IGB and AGVT (closes, distributions and splits, with the ASX symbol list the build needs) from EODHD under `eodhd.personal_evaluation`, on the owner's Mac with the owner's key from the key vault, into a new pinned local snapshot.
2. **Three proposed specs and three local, exploratory builds,** with Claude's checks on the real data.
3. **A stub build record.** No value from the series enters the repository (OD-0210).

**Read as included:** the small change `tools/eodhd_eval.py` needs before it will fetch these three symbols, since its fund list is fixed. It is made by a worker on invented data and changes no default behaviour.

## What this record does NOT do

It authorises no other symbol (VAS is not refreshed), no new source, no comparison report (package B4) and no acceptance.

## Corrections (append-only)
