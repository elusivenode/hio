---
id: OD-0234
title: "Owner authorises a covariance and risk mart, and asks for the session to be distilled"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-risk-mart-and-distil.md (owner's two messages, verbatim, with Claude's question)
  sha256: c6fe174849ddec8f601052ab4bed70ea81bd81245698c48ad5f62ecc8a7d03cd
  date: 2026-11-22
  quote: "Y"
base_revision: 619d7c87776266730463a5eddfb25b7b49415a15
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0093, OD-0135, OD-0199, OD-0233]}
---

# OD-0234: a covariance and risk mart; a draft of distil 3

## Owner action

**1. Authorised ("Y"): a covariance and risk mart** on the gold-mart pattern: an addition to the contract (`docs/decisions/gold-marts-contract.md`, proposed) for covariance estimates over a panel and risk contributions for a portfolio, in floating point with the library versions in each build's identity; worker-built code on invented data; Claude's comparison with today's `tools/risk_model.py` outputs; an evidence note.

**Comparison declared before the build:** for the blend already built (`aud-eq60-dur40`), the full-sample covariance, correlation and volatilities, the portfolio volatility, each sleeve's risk contributions, and the trailing 36-month volatilities, correlations and portfolio volatility are compared with `risk.json` and `rolling.csv` of today's run for the same blend. Agreement means a relative difference below 1e-9 in every figure. Anything examined afterwards is labelled post hoc.

**2. Authorised ("Look for an opportunity to distill the session"): a draft of distil 3.** Claude prepares a disposition for every line in the findings Inbox, on a proposal branch, as distils 1 and 2 were prepared (OD-0092, OD-0134).

## What this record does NOT do

It replaces no existing tool, changes no existing bundle's identity, and accepts nothing. **It does not accept distil 3:** Settled lines take their rank only when the owner accepts the proposal at an exact revision (OD-0093, OD-0135).

## Corrections (append-only)

None.
