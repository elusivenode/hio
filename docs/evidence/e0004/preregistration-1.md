---
id: HIO-EVIDENCE-E0004-PREREG-1
title: "E-0004: does duration reduce downside losses differently when inflation is accelerating? Preregistration, proposed"
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0187
---

# E-0004 preregistration 1 (proposed)

> **A proposed design, written before any of its data exists in HIO.** Nothing here is authorised to run. The CPI source is unverified, so the state can't be built yet. **It isn't blind:** the author and owner know how 2008, Q1 2020 and 2022 went, and the state was chosen knowing that (T-0023 recommendation 1). Older history added later is still retrospective, not an untouched sample.

## The question

In otherwise identical USD portfolios, rebalanced monthly, does holding US Treasuries instead of USD bills reduce **monthly downside losses** by a different amount when US inflation is **accelerating** than when it isn't?

This is a portfolio consequence, not a causal claim about inflation, and not a forecast.

## Portfolios

| Item | Declared |
|---|---|
| Treasury portfolio `T` | 60% SPY, 40% IEF |
| Bills portfolio `B` | 60% SPY, 40% BIL |
| Currency | USD throughout, with no FX. Translation can't change the sign of a USD difference (T-0023, `tools/t0023_episodes.py`) |
| Returns | market-price total return under RA 3.1 and 5, from E-0002's snapshot s2, as in E-0003; simple returns; no costs or tax |
| Rebalancing | to target at every month end; fractional holdings |

## Primary outcome

For a monthly portfolio return `R`, the downside loss is `L(R) = max(0, -R)`.

- **The duration benefit in a month:** `b = L(R_B) - L(R_T)`. Positive means Treasuries lost less that month.
- **Per state:** `D_s` is the mean of `b` over the months in state `s`.
- **The contrast:** `Δ = D_accelerating - D_not`.

`Δ` is the one primary number. Its sign isn't predicted: the economic story (Treasuries hedge less when inflation is rising) points negative, but nothing here tests that story.

## The state

**Accelerating at month end `t`:** the latest year-on-year CPI-U rate published on or before `t` is greater than the latest rate published on or before the same day twelve months earlier.

| Rule | Declared |
|---|---|
| Series | CPI-U, US city average, all items, not seasonally adjusted (`CUUR0000SA0`), BLS |
| Year-on-year rate | the index for the reference month over the index twelve reference months before, as published in that release |
| Published | the release's date, from BLS's own schedule records. A release on day `t` counts as known at month end `t` (08:30 ET precedes the close) |
| Applied to | the month **after** `t`: the state at month end `t` labels the return from `t` to `t+1` |
| Equality | not accelerating |
| Missing publication evidence | the month is **unavailable**, excluded and counted. The unpublished October 2025 CPI needs no special case: "latest published" then means September's, as it did at the time |
| Values | original release values only. If NSA CPI-U proves to be revised beyond flagged corrections, values come from the archived news releases instead |

## Sample

Every month whose three fund returns and state are all available: expected from mid-2007 (BIL's first full month) to the last complete month in snapshot s2. **The sample isn't trimmed after seeing a result.** E-0001's duration construction is a sensitivity only, never the primary Treasury sleeve, since it has no independent reference.

## Step 1: the information count, before any outcome

Run first, and alone. It reads the state and SPY's returns only; it computes no `b`, no `D` and no `Δ`.

| Count, per state | Definition |
|---|---|
| Months | available months in the state |
| Runs | maximal spells of consecutive months in one state |
| Stress clusters | SPY months at or below −5%, grouped when separated by fewer than three non-stress months; a cluster belongs to the state of most of its months |

**Feasibility bar. All must hold in both states, or E-0004 stops and reports only these counts:**

- at least 48 months;
- at least 4 runs;
- at least 3 stress clusters;
- no single stress cluster holding more than half of that state's stress months.

## Step 2: estimation, only if step 1 passes and the owner says go

| Item | Declared |
|---|---|
| Point estimate | `Δ` on the full sample |
| Uncertainty | moving-block bootstrap of whole months (returns and state together): 12-month blocks, 10,000 replications, seed `20260004`; 2.5th to 97.5th percentiles. 6- and 24-month blocks reported beside it |
| Fragility | `Δ` recomputed with each stress cluster left out in turn |
| Economic relevance | `|Δ|` of at least **0.20 percentage points** of monthly downside loss |

## Decision rule

| Finding | Reading |
|---|---|
| `|Δ|` ≥ 0.20 points, the 12-month interval excludes zero, and no single left-out cluster flips the sign | **a state-dependent difference in the sample.** Still retrospective; a reason for a forward record, not a policy |
| The interval excludes zero but `|Δ|` < 0.20 points, or one left-out cluster flips the sign | **not economically or robustly distinguished**; reported as such |
| The interval includes zero | **not distinguished** |

## Sensitivities (reported, never substituted for the primary)

1. Equality counted as accelerating.
2. IEF replaced by E-0001's 10-year construction, where it overlaps.
3. A three-month persistence filter: the state changes only after three consecutive months in the new state.

## Don't run step 2 if

- step 1's bar fails;
- the CPI rights or release dates can't be established;
- an unresolved return discrepancy could decide the result: **C1 for BIL (2008-09-30) and IEF's missing NAV corroboration must be resolved, or bounded by a declared sensitivity, first**;
- the state, threshold or sample would need changing to separate the known episodes;
- step 1's counts imply an interval too wide to see 0.20 points.

## What it needs before step 1

1. The owner's rights reading of the BLS CPI source, then a separate yes for one bounded download (`docs/research/cpi-source-1.md`).
2. The owner's adoption of this preregistration, at an exact revision.
3. A task card and register entry for E-0004.
