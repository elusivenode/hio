---
id: OD-0159
title: "Owner authorises Stage A of E-0002 (T-0021): reader and fixed-allocation calculations on synthetic data; amends OD-0139's order; adopts NumPy; allows a future trial before base camp, separately decided; vendor drafts extended"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-authorise-e0002-stage-a.md (owner's message, verbatim)
  sha256: 305403872bba7d4235e679e6d95f690b2154b6e2ac1576242b05b3e1166ffbef
  date: 2026-11-04
  quote: "yes, authorise Stage A of E-0002"
base_revision: cbab2a8c40257565236c47d7d7f7b0c048c60537
related: {adrs: [], tasks: [T-0020, T-0021, T-0003], findings: [], ods: [OD-0038, OD-0129, OD-0139, OD-0155, OD-0157, OD-0158]}
---

# OD-0159: Stage A of E-0002

The architect's advice (`20261104T130155-ask-4d38`, the seventeenth consultation) recommended synthetic Stage A only; it grants nothing.

## Authorised

1. **OD-0139's order, amended only so that** track 5 (the reader) no longer waits on track 4's result, and the part of track 6 in T-0021 starts with it. All other order, and every track's own authorisation, is unchanged. `docs/decisions/factor-first-sequencing-proposal.md` isn't edited; read it as amended here.
2. **NumPy as a new dependency,** a new stack decision (OD-0038 reserves other dependencies for their own decisions), hash-locked in `uv.lock`.
3. **Card T-0021:** the reader and calculations, on synthetic data only.
4. **A one-month data trial may come before base camp,** changing the preference in OD-0129. The vendor, purchase, rights and scope stay separately decided.
5. **The vendor drafts gain questions** on closing-price provenance, Treasury and bill ETF coverage, and issuer reference use. OD-0155 still governs sending, and the owner sends.

## The research question (E-0002, not yet pre-registered)

In USD, with equity fixed at 60% and rebalanced monthly, how do compounded wealth, volatility, drawdown, time under water and covariance differ if the other 40% is held in T-bills rather than intermediate Treasuries; how stable is that, and how uncertain? 40% and 80% equity are stability checks. E-0001's CMT is neither an input nor a reference.

## How Claude read it

- **Placement:** the reader is a tool in `tools/`, and calculations are in `src/hio/portfolio/`, importing only contracts and NumPy. No import rule changes.
- **ETF return construction:** the proposal's acceptance evidence named distribution and split cases, so T-0021 includes a small pure construction under RA §3.1 and §5, on invented numbers.
- **Decisions this replaces:** decisions 1, 2 and 4 of Claude's earlier list. H-0001 and H-0002 stay deferred.

## Not authorised

Data retrieval, any purchase or vendor choice, Stage C or pre-registering it, spec approval, a Codex review, AUD or FX, shrinkage, EWMA, risk contribution, optimisation, forecasting, Parquet or DuckDB in the reader, any change to capture code, workflows, infrastructure or T-0020's scope.

## Corrections (append-only)
