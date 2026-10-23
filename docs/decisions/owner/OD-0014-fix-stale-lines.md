---
id: OD-0014
title: "Owner instruction: fix the stale lines (STATUS authority row, T-0002/T-0003 front matter, T-0007 line 60)"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-24-owner-stale-line-fixes.md (the owner's chat message, verbatim, with the list it refers to)
  sha256: 4e2378845831de59e0005daaaec3efd719f310c196e1eee70a0992b65e4eae8c
  date: 2026-10-24
  quote: "fix the stale lines, including T-0007 line 60"
applies_to:
  - path: hio/
    revision: 4a994d3bc3214bfcc54ce3ac1961da299b114ac5
related: {adrs: [], tasks: [T-0002, T-0003, T-0007], findings: []}
---

# OD-0014: fix the stale lines

## Owner action

Fix the stale lines listed in Claude's 2026-10-24 bootstrap report, including T-0007 line 60.

## Scope and exclusions

- `STATUS.md`: the *Owner decision records* row.
- T-0002 and T-0003: the "execution not yet started" front-matter comment.
- T-0007 line 60 (criteria 1–2), recorded as a later edit in a *Later edits* section. The
  accepted version stays at `b48f83c`.
- Bookkeeping: this record, the OD index, the history index, `STATUS.md` and a handoff.
- **Excluded:** any other text, including other stale lines found while doing this work. Those
  are reported in the handoff for a separate instruction.

## What this record does NOT do

- It does not re-accept T-0007, or change its acceptance (OD-0004 at `b48f83c`).
- It does not change any approval, verification or task status.
- It does not authorise S1a, live data operations or vendor contact.
