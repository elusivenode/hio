---
id: OD-0170
title: "Owner authorises E-0003, an AUD cash comparator from 2011 on retained RBA data, after a separately verified E-0002 V3 correction"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-e0003-brief.md (the pasted brief, verbatim)
  sha256: 22b63017b32b1629339d9ef1d65df314ceaf4ac5776549b15f47f49bf63dde2f
  date: 2026-11-04
  quote: "I authorise pre-registration and a bounded local exploratory run of the AUD cash comparator, starting with the available rights-cleared RBA history from 2011."
base_revision: 1c05d470e02cd0408bec6557a41a53649627d7b7
related: {adrs: [], tasks: [T-0022], findings: [], ods: [OD-0116, OD-0118, OD-0162, OD-0166, OD-0167]}
---

# OD-0170: E-0003, and the V3 correction first

The brief is the record. Its Codex verification of V3 is `VERIFY-2026-11-04-e0002-v3`, assigned by this OD; its head is named in a correction below, before launch. Work sits on `feat/e0003-aud-cash`, stacked on `feat/t0022-eodhd`, because it needs that code, and it changes nothing in PR #97.

## How Claude read it

- **Retained RBA data is read, not newly fetched:** the evidence store's existing F1 receipts, with the owner's reader identity, read-only, as in T-0018. Nothing is written to the store, and the soak isn't touched.
- **Rights:** `rba.cash_rate_tri` is `owner_verified` (OD-0116, OD-0118), and the gate allows local build and store, on its attribution conditions. `quotation_in_documents` is `unknown`, so no value is committed.

## Not authorised

As the brief lists. Accepting T-0022, E-0002 or E-0003; any AUD cash before 2011; any consumer use.

## Corrections (append-only)

1. **2026-11-04: the verification is assigned.** `VERIFY-2026-11-04-e0002-v3`'s assigned head is the commit that adds this correction: `git log -n1 --format=%H -- docs/decisions/owner/OD-0170-e0003-aud-cash.md`. Scope: the V3 correction only, in `src/hio/portfolio/fixed_allocation.py` (`period_ends`, `period_returns`), `tools/eodhd_eval.py` (`describe`, `dependence`, `WINDOWS`, `compare`), `tools/e0002_aud.py` (`reconcile_reports`) and their tests. Codex receives no licensed bytes or values, and the workspace is unreadable for the run. It writes only under `reviews/`.
