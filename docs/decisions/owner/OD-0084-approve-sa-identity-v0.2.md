---
id: OD-0084
title: "Owner approves solution-architect identity v0.2 (\"Independence of evidence\") as it reads at 72c0eaf; merged into main; only the status line changed afterwards"
decision: approve
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-approve-sa-identity-v0.2.md (typed by the owner, verbatim)
  sha256: f0c2586b1d6bb6e172359e640e6bd1ab101bda3d56c3cf2d2db3446ce4617bb0
  date: 2026-10-28
  quote: "yes approve v0.2"
applies_to:
  - path: docs/agents/solution-architect/identity.md
    revision: 72c0eaf0ead2   # approved text, blob 5592dbf2ca01; on main after the status-line edit, blob 25272b1adda5
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0081, OD-0082, OD-0083]}
---

# OD-0084: solution-architect identity v0.2 approved

## Owner action (verbatim in the source file)

"yes approve v0.2", answering Claude's question about identity v0.2 "as it reads at `72c0eaf`".

## What was done

1. **Merge.** `proposal/sa-identity-v0.2` at `72c0eaf` was merged into `main`. The identity blob after the merge
   is the approved `5592dbf2…`.
2. **One administrative edit.** The front-matter `status` line changed from "proposed … not approved" to
   "approved", citing this record. No other line changed (blob `25272b1a…`). The `sa` log records the identity
   blob of every call.
3. **Effect.** Every new architect session (`hiomux sa …`, reading `main`) now uses v0.2. An architect pane
   opened earlier keeps v0.1 until it is reopened.

## What this approval covers

- **Covers:** the identity text: the architect's role, authority limits, evidence discipline and its new
  independence principle, method, and dispositions.
- **Does not cover:** a harness change, authority for the architect (it stays advice only, OD-0081), the context
  manifest, the schema or the cases (still proposed), or harness-0.9.
- **Known limit:** v0.2's regression evidence includes the case it was tuned on (case 2). A held-out
  external-data case is still the outstanding test that the principle generalises (OD-0083).

## Corrections (append-only)

None.
