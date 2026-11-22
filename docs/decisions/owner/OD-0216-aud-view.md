---
id: OD-0216
title: "Owner authorises the AUD investor's view: AUD-translated series (unhedged and hedged) from local data, and the analytics and risk model rerun on them"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-aud-view.md (owner's message, verbatim, with Claude's question)
  sha256: 58e145b9bed1d71d64497f425d927edec259fa76f0368f3f267c1878d4282270
  date: 2026-11-22
  quote: "Y"
base_revision: 857a549d85ef195aadbc5b10abc18918e968de59
related: {adrs: [], tasks: [], findings: [], ods: [OD-0166, OD-0172, OD-0199, OD-0210, OD-0213, OD-0215]}
---

# OD-0216: the AUD view

**Authorised, on local data only** (the `s3` builds, the H.10 AUD/USD archive of OD-0166 and the RBA cash history of OD-0172, all already on disk):

1. **Unhedged AUD series** for SPY, IEF and BIL: `1 + R^h = (1 + R^f)(1 + s)` with `s = q_(t−1)/q_t − 1` on H.10's USD-per-AUD rate (RA §4.1, RA-INV-006, RA-INV-007), with the cross term reported.
2. **An AUD cash series** from the RBA history, as E-0003 assembled it, in the build format.
3. **Hedged AUD series** for SPY and IEF per RA §4.3 at hedge ratio one, with a **CIP-implied** forward from the AUD cash series and a USD bill proxy. This is `replicable_with_basis`: no market forward points are used.
4. **AUD excess returns over AUD cash,** and the analytics and risk model rerun in AUD.

Proposed specs accompany each series. Workers write the tools on invented data; Claude runs them on the local data. No download. Nothing is accepted, no spec is adopted, no value enters the repository (OD-0210), and nothing goes to a consumer or the SMSF.

## Not authorised

Any download; accepting a series or adopting a spec; publication; any SMSF use.

## Corrections (append-only)
