---
id: OD-0213
title: "Owner redirects the work to factors and analytics, and authorises building the SPY, IEF and BIL market total-return series from EODHD snapshot s3, locally, with workers"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-factor-series.md (owner's messages, verbatim, with Claude's question)
  sha256: fa0032fbdd7dba020fe668ec282afcbc78a404115409f27c157e4909351cfaf7
  date: 2026-11-22
  quote: "Y"
base_revision: a63cb354328d66390b48ade5bf83a9c8798691f6
related: {adrs: [], tasks: [T-0003], findings: [], ods: [OD-0139, OD-0162, OD-0176, OD-0194, OD-0199, OD-0210]}
---

# OD-0213: back to factors

**The owner's direction:** too many cycles went on things that do not advance the core goal, which is to develop investment factors and portfolio construction and analytics capabilities. From here:

- **No further verification or redaction rounds on E-0004.** The verification already running (OD-0211) is received when it lands and put to the owner once: leave open and parked, or waive.
- **A finding on parked or exploratory work gets one remediation and one verification.** After a NOT READY, Claude stops and asks.

**Authorised:**

1. **Build the three market total-return series** for the proposed specs `equity.us.spy`, `rates.us.ief` and `cash.us.bil` (`.market_total_return`, version 0.1.0) from EODHD snapshot `s3`, pinned by its manifest hash, with `src/hio/library/vehicle_return.py`. Each build writes its series and a build record (spec hash, snapshot hash, input hashes, code commit, invariant results) to a local factor store under `~/.hio-research/`. Workers write the tools on invented data; Claude runs them on the real snapshot.
2. **Portfolio analytics on those series,** as the next capability: return, volatility, drawdown, correlation and sleeve contribution for a fixed-weight, monthly-rebalanced portfolio, with `src/hio/portfolio/fixed_allocation.py`.

**Bounds.** Local data only; no download. Exploratory: no series is accepted, no spec is adopted, T-0003 is not decided, and nothing goes to a consumer or the SMSF. No value from the series enters the repository (OD-0210): records state what was built, its hashes and whether its invariants passed.

## Not authorised

Any download or vendor contact; accepting a series or adopting a spec; publication; any SMSF use.

## Corrections (append-only)
