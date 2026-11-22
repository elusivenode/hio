---
id: OD-0224
title: "Owner approves package A2 of T-0024, extended to the Australian funds: VAS and VGB distributions and returns checked against the issuer's published figures"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-approved-a2-issuer-check.md (owner's messages, verbatim, with Claude's proposal)
  sha256: db5be910fa3636987bd86864919e4c23c7a2e0d6522a65a4c4a4751d7a3a7896
  date: 2026-11-22
  quote: "Approved to proceed"
base_revision: 6e0f0f572c941408d51e4c4d23a6aafeef2dec59
related: {adrs: [], tasks: [T-0024, T-0023, T-0003], findings: [], ods: [OD-0178, OD-0179, OD-0210, OD-0215, OD-0218]}
---

# OD-0224: package A2, the issuer check of the Australian funds

## Owner action

The owner approved Claude's proposal: "package A2 extended to the Australian funds: checking VAS and VGB distributions and returns against the issuers' published figures, as was done for the US funds".

**Claude's reading, stated so the owner can correct it:**

1. **It answers the A2 proposal,** the last thing put, not the separate open question on package A3.
2. **It extends the parked T-0023 line of work** to this one check (OD-0215 had parked it). T-0023 itself stays parked and unaccepted.
3. **It allows one read of the issuer's public pages or documents for VAS and VGB,** as OD-0178 and OD-0179 allowed for the US funds. The figures stay local; no issuer file is committed; the issuer rights row stays `unverified`. No automated or repeated retrieval.
4. **For the US funds it allows no new read:** the record names what T-0023 and E-0002 already checked and what remains.

## Bars, declared before any issuer figure is read

| Check | Bar |
|---|---|
| D1 distributions | every issuer distribution found (amount per unit, by ex-date) has a vendor record with the same ex-date and the same amount once the issuer's figure is rounded to the vendor's decimals |
| D2 completeness | within the span the issuer's list covers, the vendor holds no distribution the issuer lacks, and lacks none the issuer holds |
| R1 returns, market-price basis | HIO's compounded return to the issuer's as-of date is within 0.10 points a year of the issuer's figure, for each period the issuer publishes |
| R1 returns, NAV basis (if that is all the issuer publishes) | within 0.25 points a year, labelled NAV basis: a market-price return need not equal a NAV return |

A fail stands. Any diagnostic chosen after a result is labelled post hoc. Franking is not tested. If the HIO series ends before the issuer's as-of date, that period is not performed rather than approximated.

## What this record does NOT do

It authorises no vendor fetch, no new data source for building, and no other package. It verifies no rights row, accepts no series and reopens nothing else in T-0023.

## Corrections (append-only)
