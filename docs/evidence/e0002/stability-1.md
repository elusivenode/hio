---
id: HIO-EVIDENCE-E0002-STABILITY-1
title: "EODHD stability: s2 (2026-11-03) against s3, for SPY, IEF and BIL. Rules declared before s3 is taken"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0194
---

# EODHD stability 1

> **Rules first.** Everything above "Result" was committed before `s3` existed. Stability means EODHD reproduces its own history; it says nothing about accuracy (the architect, `20261122T093338-ask-993d`). No EODHD value is recorded here.

## What's compared, per fund (SPY.US, IEF.US, BIL.US)

Over the **common history**: every date present in `s2`, compared with the same date in `s3`. Dates after `s2`'s last date are new data, counted, not compared.

| Item | Counted |
|---|---|
| Raw closes (`close`) | changed, removed (in `s2`, absent from `s3`), added inside the common span (absent from `s2`, present in `s3`) |
| Distributions (`unadjustedValue`, keyed by ex-date) | amount changed, removed, added; and, for each change, whether the payment date changed |
| Splits | changed, removed, added |
| Missing weekdays | weekdays within the common span absent from each snapshot (counted, not judged: no holiday calendar) |
| Adjusted closes | not compared; expected to move with new distributions |

## How a revision is explained

- **Return impact:** HIO's market-price total return (RA §3.1 and §5, `tools/eodhd_eval.py`'s construction) over the common span, from each snapshot. The **difference in compounded return** over the span, and the largest single-period difference.
- **Each changed or added row** is listed locally with both values; the record states only counts and whether the change has a stated cause (for example a distribution later restated by the issuer).

## Reading (fixed now)

| Finding | Reading |
|---|---|
| No closes, distributions or splits changed, removed or added in the common span | **stable** |
| Changes exist, each with a stated cause, and the compounded-return difference is under 0.01 points | **stable with explained revisions** |
| Any unexplained change, or a compounded-return difference of 0.01 points or more | **revisions not explained**; T-0003 can't rest on these series until they are |

## What this record may state (added before s3, after F-REVIEW-2026-11-22-e0004-1-2)

Only the reading, and for each fund and category whether anything changed (yes or no) and whether each change has a stated cause. **No counts, dates, values or return impacts**: those are derived from EODHD data and stay in the local report (OD-0176).

## Result

_Not yet run._
