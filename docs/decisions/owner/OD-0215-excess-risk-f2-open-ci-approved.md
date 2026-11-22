---
id: OD-0215
title: "Owner authorises excess-return series over BIL and a simple risk model; leaves F-2 open with the work parked; approves the CI trigger change (PR #139) at c2ca8fd"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-to-all-three.md (owner's message, verbatim, with Claude's three items)
  sha256: bfd65e573fc2dea110cc4ef42a5872fc0405e32808347c8e631df9d0ca41791b
  date: 2026-11-22
  quote: "Y to all. Proceed"
approved_revisions:
  - path: .github/workflows/ci.yml (PR #139)
    revision: c2ca8fdc7d8a9add4fa46395cc979332c2cc25ed
base_revision: f460d23bbe1a71d1bf39b5959f776ed13ca8c7e9
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0184, OD-0207, OD-0210, OD-0212, OD-0213, OD-0214]}
---

# OD-0215: three yeses

## 1. Excess returns and a risk model (authorised)

- **Two excess-return series over BIL,** per RA §3.3 (`X_t = R_t − r^c_t`, arithmetic, same currency and period, cash leg recorded): a US equity premium (SPY over BIL) and a US duration premium (IEF over BIL), each with a **proposed** spec and its invariants (RA-INV-004, RA-INV-005).
- **A simple risk model** on built series: rolling volatility and correlation, the covariance matrix, and each sleeve's contribution to portfolio risk.
- Workers write the tools on invented data; Claude runs them on the local `s3` builds. Local only; no value enters the repository (OD-0210). Nothing is accepted; no spec is adopted.

## 2. F-2 stays open (decided)

**F-REVIEW-2026-11-22-e0004-1-2 stays open, with the E-0002, T-0023 and E-0004 work parked,** as F-1 was (OD-0207). Not a waiver. VERIFY-2026-11-22-e0004-1-4's inventory (received, OD-0214) is the list to act on if the owner later wants the public files cleaned further. No further remediation or verification round is authorised.

## 3. The CI trigger change (approved at an exact head)

The owner approved PR #139 at `c2ca8fdc7d8a9add4fa46395cc979332c2cc25ed`. Its checks were green at that head, and Claude merged it there as `f460d23bbe1a71d1bf39b5959f776ed13ca8c7e9`. This is the owner's approval that OD-0184 C requires for a workflow change.

## Not authorised

Accepting any series or adopting any spec; publication or SMSF use; waiving or closing F-2; any other workflow change.

## Corrections (append-only)
