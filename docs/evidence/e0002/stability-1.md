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
- **Each changed or added row** is listed locally with both values; the record states only readings and whether the change has a stated cause (for example a distribution later restated by the issuer).

## Reading (fixed now)

| Finding | Reading |
|---|---|
| No closes, distributions or splits changed, removed or added in the common span | **stable** |
| Changes exist, each with a stated cause, and the compounded-return difference is under 0.01 points | **stable with explained revisions** |
| Any unexplained change, or a compounded-return difference of 0.01 points or more | **revisions not explained**; T-0003 can't rest on these series until they are |

## What this record may state (added before s3, after F-REVIEW-2026-11-22-e0004-1-2)

Only the reading, and for each fund and category whether anything changed (yes or no) and whether each change has a stated cause. **No counts, dates, values or return impacts**: those are derived from EODHD data and stay in the local report (OD-0176).

## Result

Snapshot `s3` taken 2026-11-22 at code `27553ba` (10 requests, no stop; manifest sha256 `ce6b17c9f2590c26adabf37856d79e607597027a1701e7833bf386a9fe4757cc`). Comparison run `stability-20261121T234318Z` (`tools/eodhd_stability.py` by worker W1); stability.json sha256 `7612ce1ec819f96b27c1fe2aa56b2ae8508ec6b54ac90730b76e75de75f4567f`, local with the change list.

**Reading: revisions not explained.** EODHD revised its own history between 2026-11-03 and 2026-11-22.

| Fund | Closes changed | Distributions changed | Splits changed | Stated cause (Claude's reading of the local change list) |
|---|---|---|---|---|
| SPY | no | **yes**: a historical distribution ex-date moved; amount unchanged | no | apparently a correction: the new date is the fund's usual quarterly ex-date weekday. Its return impact over the common span is at or above the 0.01-point bar, so the declared rule reads it as not explained |
| IEF | **yes**, many | no | no | mostly re-rounding of stored closes to two decimals; a few changes are larger than rounding and have no stated cause. Return impact over the span is below the bar |
| BIL | no | **yes**: payment dates filled in where `s2` had none; amounts and ex-dates unchanged | no | metadata completion; no return impact |

**What it means.** EODHD's history is not frozen: closes and distribution records can change between pulls, without notice. So every HIO series built from EODHD must pin the snapshot it was built from (as E-0003 and T-0023 already do by hash), and a rebuild from a later pull is a new version, not the same series. It says nothing about accuracy.

**For T-0003.** Under the declared rule, the source can't rest on these series as "stable". A narrow T-0003 decision can still name EODHD as a provisional, snapshot-pinned source for exploratory research, with this revision behaviour stated as a property.
