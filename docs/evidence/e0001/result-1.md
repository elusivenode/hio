---
id: HIO-EVIDENCE-E0001-RESULT-1
title: "E-0001 result: implementation bars pass; approximation bars B6 and B7 fail"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0157
---

# E-0001 result 1

> **Pre-registered verdict: "approximation not adequate for this purpose".** Under the decision rule, the flat-yield approximation failed two of its three bars. Nothing is validated, and no reference exists, so this wouldn't have validated the factor even if it had passed. The bars weren't changed. **No value is recorded here:** `quotation_in_documents` is `unknown`, so values stay in `~/.hio-research/E-0001/`.

## Run

Code `49e1b4d`; spec `rates.us.cmt_10y.total_return` 0.1.3; bars from the pre-registration merged at `de834d8`. One one-off download of 37 yearly files on 2026-11-04, under `c3a730e`. Manifest sha256 `1ac5b696a4bca5e138408ee17e1358e52f8f2f1c03b1019051687d7009965db8`; summary sha256 `74539e80f954aa8640405bfcc7546e4d6963dff8b7d65bfeb03f9471e5577dd7`. Release `rel-05e05e482265376e8e33c19fcb868a2be69e782eb037a4b1fed196666a904376`, exploratory, local store only. Data sha256 `436d6948fcc4ca6ee8ccd89603c2f34620f4019a7a783e89b60da7327493e988`.

## Bars

| Bar | Test | Result |
|---|---|---|
| B1 | RA-INV-013, CMT-INV-1 to 6, ZC-INV-1 to 3 on the code that ran | **pass** (full suite at `49e1b4d`, invented inputs) |
| B2 | No CMT-INV-5 breach on real data | **pass** |
| B3 | ZC-INV-1 holds, and no D_n <= 0, on every covered date | **pass** |
| B4 | Two runs byte-identical | **pass**; same run, same machine |
| B5 | Every parsed row accounted for; bytes match the manifest | **pass** |
| B6 | \|d_t\| at most 1 bp in at least 99% of covered periods | **FAIL** |
| B7 | max \|d_t\| at most 5 bp | **FAIL** |
| B8 | \|compounded annualised difference\| at most 10 bp a year: full, before, after | **pass** |
| B9 | The sensitivity covers at least 95% of periods | **pass**: every period |

## Counts

9,217 rows parsed; 9,216 dates included, from 1990-01-02 to 2026-11-03; 1 date excluded for a missing tenor; 0 duplicates; 9,215 periods, all covered; 7,987 before the method change, 1,227 after, 1 crossing. 0 gaps over 5 days; 0 periods refused; 1 move over 50 bp; 0 zero-curve failures. The start date matches the expected 1990-01-02. The Treasury page confirms 2021-12-06 as the method change.

## What the failure is (post-hoc, not part of the bars)

**It looks like economics, not a coding error.** A separate float calculation of one mechanism reproduced the difference closely: when the 10-year par yield moves, the bond's coupon differs from par, and that difference is priced on a flat-yield annuity in one series and a zero-curve annuity in the other. On a sloped curve the two annuities differ, so the gap scales with the size of the move and the slope of the curve, and largely cancels as yields go up and down. That fits B8 passing while B6 and B7 fail.

**This doesn't say which series is right.** Both are models from one source. The bars were judgement set before any data, and the result doesn't justify moving them. The figures are in `post-hoc-1.txt` beside the results.

## Not established

Agreement with traded returns, costs, historical availability, diversification, and interpolation sensitivity. No independent reference exists. No Codex review has happened. B4's identity covers one machine.
