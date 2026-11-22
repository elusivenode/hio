---
id: OD-0217
title: "Owner authorises the session handoff and STATUS update for an orchestrator session roll, and a hedge-ratio sweep on the local AUD series"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-handoff-and-sweep.md (owner's message, verbatim, with Claude's question)
  sha256: d10b3e363042be1fa3d348c78875bdf994dcb17b1b27a6849f2e4414fd14d600
  date: 2026-11-22
  quote: "Yes. Distill the session and prepare for orchestration session roll"
base_revision: e9efdf6ca792a1087e726cb892da7b5fafca0eb4
related: {adrs: [], tasks: [], findings: [], ods: [OD-0199, OD-0210, OD-0213, OD-0215, OD-0216]}
---

# OD-0217: session roll, and the hedge-ratio sweep

**Authorised:**

1. **The session handoff,** its findings Inbox lines and the `STATUS.md` update, written so a fresh orchestrator session can continue the factor work.
2. **A hedge-ratio sweep** on the local series: for hedge ratios from 0 to 1 on the US equity leg (RA §4.3, `R = (1 + R_f)(1 + s) − 1 − h (s − f)`, the forward CIP-implied as in OD-0216), the return, volatility and drawdown at each ratio on one common span, for the asset alone and inside a fixed-weight portfolio. Descriptive only: it reports the sample and recommends no hedge ratio.

"Distill" is read as distilling this session into the handoff and the Inbox. It is **not** distil 3 of the findings index, which stays a separate owner action.

Local data only; nothing is accepted; no value enters the repository (OD-0210).

## Not authorised

Distil 3; any download; accepting a series or adopting a spec; any recommendation of a hedge ratio to a consumer or the SMSF.

## Corrections (append-only)
