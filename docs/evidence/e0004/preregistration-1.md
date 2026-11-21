---
id: HIO-EVIDENCE-E0004-PREREG-1
title: "E-0004: does duration reduce downside losses differently when inflation is accelerating? Preregistration, proposed"
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0187
---

# E-0004 preregistration 1 (proposed)

> **A proposed design, written before any of its data exists in HIO.** Nothing here is authorised to run, and the CPI source is unverified. **It isn't blind:** the author and owner know how 2008, Q1 2020 and 2022 went, and the state was chosen knowing that (T-0023 recommendation 1). It can support a forward research record, not validate a policy. Revised once after the architect's review (`sa` `20261122T083318-ask-b4ca`); every change follows its advice.

## The question

In otherwise identical USD portfolios, rebalanced monthly, does holding US Treasuries instead of USD bills reduce **monthly downside losses** by a different amount when US inflation is **accelerating** than when it isn't? This is a portfolio consequence, not a causal claim about inflation, and not a forecast.

## Portfolios

| Item | Declared |
|---|---|
| Treasury portfolio `T` | 60% SPY, 40% IEF |
| Bills portfolio `B` | 60% SPY, 40% BIL |
| Currency | USD throughout. Translation can't change the sign of a USD difference (T-0023, `tools/t0023_episodes.py`) |
| Returns | market-price total return under RA 3.1 and 5, from close to close with distributions reinvested on the ex-date, built by `tools/e0002_*` from E-0002 snapshot s2. Fund expenses are in the fund returns; **no additional trading costs or tax** |
| Rebalancing | to target at each month's last trading close; fractional holdings |
| Pinned at adoption | the snapshot's manifest hashes for SPY, BIL and IEF and the code revision, written into this file in the adopting commit. A later snapshot is a new preregistration |

## Primary outcome

For a monthly portfolio return `R`, the downside loss is `L(R) = max(0, -R)`.

- **Duration benefit in a month:** `b = L(R_B) - L(R_T)`. Positive means Treasuries lost less.
- **Per state:** `D_s` is the mean of `b` over the months in state `s`, **including months where neither portfolio lost** (`b = 0`). This is average monthly downside benefit, not crisis protection alone.
- **The contrast:** `Δ = D_accelerating - D_not`, the one primary number. Its sign isn't predicted; nothing here tests why.

## The state

**Accelerating for month `m+1`:** at the rebalance instant ending month `m`, the latest published year-on-year CPI-U rate is greater than the latest one published as of the same instant twelve months earlier.

| Rule | Declared |
|---|---|
| Series | CPI-U, US city average, all items, not seasonally adjusted (`CUUR0000SA0`), BLS |
| Year-on-year rate | the ratio of the two index levels as first published (three decimals), minus one, **unrounded**. Not the published rounded percentage |
| Values | first-release values only, with each release's bytes retained. A later correction is recorded beside it and never changes a past state |
| Information cutoff | the rebalance instant: month `m`'s last trading close, 16:00 ET. A release at 08:30 ET on or before that day counts |
| Carry-forward | the latest published rate holds until the next release. **The unpublished October 2025 CPI needs no special case:** September's rate stays latest until November's is published, as it did then. (`docs/research/cpi-source-1.md` is corrected to match) |
| Equality | not accelerating |
| Missing publication evidence | that month is **unavailable**: excluded, counted, and treated as a break (below) |

## Sample

Every month `m+1` whose three fund returns and state are all available, from BIL's first full month to the last complete month in snapshot s2. **Not trimmed after any result.** An unavailable month **breaks** runs, stress clusters and bootstrap blocks: nothing spans it. E-0001's duration construction is a sensitivity only.

## Step 1: the information count, before any outcome

It reads the state and SPY's monthly returns only. It computes no `b`, no `D` and no `Δ`.

| Count, per state | Definition |
|---|---|
| Months | available months in the state |
| Runs | maximal spells of consecutive available months in one state |
| Stress months | SPY's monthly total return at or below −5% |
| Stress clusters | stress months, in time order, joined when fewer than three months lie between them and no break intervenes. A cluster **counts for a state** when at least one of its stress months is in that state |
| Concentration | for each state, the largest share of that state's **stress months** that any one cluster holds |

**Minimum screen. All must hold in both states, or E-0004 stops and reports only these counts:** at least 48 months, at least 4 runs, at least 3 stress clusters, and concentration of at most one half. These are screens, not evidence of enough precision; step 1b decides that.

## Step 1b: the precision check, still before any outcome

It estimates how wide the primary interval would be with no true state difference, without computing `Δ` on the real alignment.

- Circularly shift the state sequence against the return sequence by `k` months, for every `k` from 13 to `n − 13` (so no shift is within a year of the real alignment). Breaks move with the state.
- For each shift, the half-width of the step 2 bootstrap interval for `Δ` (12-month blocks, 1,000 replications, seed `20260004`).
- **Pass:** the median half-width is at most **0.20 percentage points**. Otherwise E-0004 stops and reports the counts and the median half-width.
- Only the median half-width is recorded; no shifted `Δ` is reported.

## Step 2: estimation, only if steps 1 and 1b pass and the owner says go

| Item | Declared |
|---|---|
| Point estimate | `Δ` on the full sample |
| Bootstrap | circular moving-block over the available segments (blocks never cross a break or wrap across one); returns and state resampled together; 12-month blocks; the last block truncated to the sample length; 10,000 replications; NumPy `default_rng(20260004)` (PCG64); `numpy.quantile` with `method="linear"` at 2.5% and 97.5% |
| A replication with no month in one state | dropped and counted. If more than 1% are dropped, reported as a limitation |
| Block sensitivities | 6 and 24 months, same settings. Disagreement with the 12-month reading is disclosed, and the 12-month result stays primary |
| Fragility | `Δ` recomputed with each stress cluster's months left out in turn; every value reported |
| Relevance threshold | `|Δ|` beyond **0.20 percentage points** of monthly downside benefit. **An owner-chosen practical threshold, not an empirical boundary.** Not annualised. The owner confirms it at adoption |

## Decision rule

| Finding (12-month interval) | Reading |
|---|---|
| The whole interval lies beyond +0.20 or beyond −0.20 points, and no left-out cluster makes `Δ` zero or flips its sign | **a relevant state-dependent difference in this sample**: retrospective, a reason for a forward record |
| The interval excludes zero but not ±0.20, or a left-out cluster makes `Δ` zero or flips its sign | **a nonzero difference of uncertain relevance** |
| The interval includes zero | **not distinguished** |

## Sensitivities (reported, never substituted)

1. Equality counted as accelerating.
2. IEF replaced by E-0001's 10-year construction, where it overlaps.
3. A three-month persistence filter: the state changes only after three consecutive months in the new state.
4. The month containing 2008-09-30 excluded (T-0023 C1, BIL's open discrepancy).

## Data conditions, fixed before any result

- **IEF's NAV corroboration must pass** (C1 and C2 against the issuer's NAV file, at the T-0023 bars) before step 2, or step 2 doesn't run. No substitute.
- **BIL's 2008-09-30 discrepancy** is bounded by sensitivity 4. If sensitivity 4 changes the reading's row, that's reported as the result's limit, not resolved.
- No other substitution or bound may be added after step 1.

## Don't run step 2 if

- step 1 or 1b fails;
- the CPI rights or release dates can't be established;
- IEF's NAV corroboration fails or is missing;
- the state, threshold, sample or bootstrap would need changing to separate the known episodes.

## What it needs before step 1

1. The owner's rights reading of the BLS CPI source, then a separate yes for one bounded download (`docs/research/cpi-source-1.md`).
2. The owner's adoption of this preregistration at an exact revision, with the pinned hashes filled in and the 0.20-point threshold confirmed.
3. A task card and a register entry for E-0004.
