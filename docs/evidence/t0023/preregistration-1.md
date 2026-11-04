---
id: HIO-EVIDENCE-T0023-PREREG-1
title: "T-0023 steps 3 to 5: checks and bars, declared before any comparison"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0178
---

# T-0023 preregistration 1

> **Declared before any of these comparisons ran.** Claude has seen only the files' structure and date spans. A failed bar is reported and narrows the claim; bars aren't moved afterwards. Any later change is a dated amendment below, with its reason.

**Reference period** for "2008" is 2007-12-31 to 2008-12-31. **Full** is the frozen panel, 233 months. All checks use panel `1aa29918…`.

## Independence of each reference

| Reference | Independent of EODHD? | Limit |
|---|---|---|
| State Street NAV history, SPY from 2003, BIL from May 2007 | yes | the fund's value, not its traded close; holds no distributions |
| Treasury par curve, 1-month and 10-year (OD-0156) | yes | a different instrument from either fund |
| RBA cash rate target page | of the overnight file's rows, yes | the same institution |
| Audited fund reports on SEC EDGAR; IEF's iShares NAV file | yes | **not obtained yet:** each check below is reported "not performed" until it is |

## Step 3: the three sleeves

| Id | Check | Bar |
|---|---|---|
| C1 | Close against NAV at month ends: `close/NAV - 1` | within 1.00% for SPY and IEF, 0.25% for BIL, in at least 99% of month ends and in every month of 2008 |
| C2 | HIO's market return against a NAV return, monthly. The NAV return uses EODHD's distributions, so this doesn't test income | within 1.00 point for SPY and IEF, 0.25 for BIL, in at least 95% of months; 2008 compounded within 1.00 point; full sample within 0.10 points a year |
| C3 | BIL against the 1-month par yield, accrued simple ACT/365 on each published date | 2008 compounded within 1.00 point; full sample within 0.50 points a year |
| C4 | IEF against the 10-year construction (E-0001 variant V1 `r`, itself unreferenced). Consistency only: 7 to 10 years isn't 10 years | monthly correlation at least 0.90, in full and over 2008-2009; 2008 compounded within 4.00 points |
| C5 | Distributions per share and total return for each fund's fiscal years covering 2008, from its audited report, against EODHD's records and HIO's return | per share within 0.01; total return within 0.25 points. NAV within 0.01 of the issuer's NAV file |

## Step 4: the cash seam

| Id | Check | Bar |
|---|---|---|
| M1 | Method: accrual against the TRI, monthly, from 2011 (recorded) | at least 95% of months within 1 bp |
| M2 | Method: cumulative drift of the accrual against the TRI to the panel's last month | within 0.10% |
| R1 | Rates: pre-2011 `FIRMMCRID` against the RBA's target page, each published day, reported per calendar year | within 5 bp on at least 95% of days, each year |
| R2 | Rates: pre-2011 accrual on the target against the accrual on `FIRMMCRID`, monthly | at least 95% of months within 1 bp |
| R3 | The page's parser: its target against F1's `FIRMMCRTD` from 2011 | every published day equal |

M1 and M2 test the method only. R1 and R2 test consistency with the RBA's own target, not the rates' accuracy against a third party. A benchmark accrual isn't an investable deposit return, and nothing here changes that.

## Step 5: what remains

| Id | Check | Bar |
|---|---|---|
| X1 | H.10 against EODHD's AUD/USD at month ends | counted within 0.5%, 1% and 2%; no bar, because neither is a reference for the other |
| G1 | The SPY gap: reinvesting on the payment date rather than the ex-date, against the issuer's returns | the guess is supported only if every SPY gap at least halves, and BIL and IEF stay within 0.10 points a year; otherwise it stays unexplained |

## Sensitivities

Each reruns the same comparison, seed and block lengths with one thing changed. **The bar for each is no change of class in any effect and metric pair.** A change is reported and narrows the claim.

| Id | Change |
|---|---|
| S1 | SPY on its NAV return |
| S2 | BIL on its NAV return |
| S3 | BIL on the 1-month accrual |
| S4 | IEF on the 10-year construction |
| S5 | S1 and S2 together |
| S6 | pre-2011 AUD cash on the target's accrual |
| S7 | AUD cash on the `FIRMMCRID` accrual throughout, no TRI |
| S8 | FX on EODHD's AUD/USD |
| S9 | FX on H.10 the next published day, the timing shift |

## Amendments

1. **2026-11-04, S9.** H.10 has no published date after the panel's last month end, so that one month keeps its own rate. Found when the run stopped, before any S9 result. No bar changes.
2. **2026-11-04, independence table.** The audited reports were obtained under OD-0179, after this table was written. IEF's NAV file still wasn't. No bar changes.
