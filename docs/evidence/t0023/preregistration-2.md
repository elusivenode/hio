---
id: HIO-EVIDENCE-T0023-PREREG-2
title: "T-0023 steps 6 and 7: the stress episodes and the decision rule, declared before any comparison"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0180
---

# T-0023 preregistration 2

> **Declared before this comparison ran. It isn't blind.** Claude hasn't read these episodes' values in the local reports, but the owner has, and the episodes are named because history already singled them out. **Retrospective description only:** three chosen episodes confirm nothing, and this isn't a regime model or a forecast.

## Episodes

The three windows E-0003 V1 already named. None is added, removed or moved after seeing a result.

| Episode | Month ends | Months |
|---|---|---|
| `2008` | 2007-12-31 to 2008-12-31 | 12 |
| `q1_2020` | 2019-12-31 to 2020-03-31 | 3 |
| `2022` | 2021-12-31 to 2022-12-31 | 12 |

## What's measured

On frozen panel `1aa29918…`, in AUD, monthly rebalanced, for each episode and the three allocations:

- compounded return and month-end maximum drawdown of each allocation;
- for each effect (`cash_rate_and_currency`, `treasury_duration`, `total`), the later allocation minus the earlier, on both measures;
- each sleeve's compounded return in AUD, the USD sleeves also in USD, and the FX return;
- the bills-against-cash split into rate gap, currency and cross.

No bootstrap: three months can't support one, and resampling can't add episodes.

## Robustness

Each effect in each episode, on each measure, is recomputed under sensitivities S1 to S9 of `preregistration-1.md`.

An effect is **robust** in an episode on a measure only if all of these hold:

1. it's at least 2 percentage points in size on the frozen panel, the size E-0003 already used;
2. it has the same sign under all nine sensitivities;
3. the sensitivities that can run did run. One not performed is listed, and that effect can't be called robust.

## Decision rule for step 7

Set before the result, on the two primary effects, `cash_rate_and_currency` and `treasury_duration`, on compounded return. Drawdown is reported beside it.

| Finding | Recommendation |
|---|---|
| An effect is robust with **opposite signs** in two episodes | One conditional-diversification experiment **may be warranted**: the contrast exists to be studied, and the recommendation must name what it needs |
| Every robust result for an effect has one sign | **Not warranted as conditional:** there's no contrast. Report the consistent direction, as three episodes only |
| No robust result | **Not warranted.** The evidence can't support it |

Whichever row applies, **the recommendation states the C1 to C5 failures and gaps it rests on,** and that a contrast across three hand-named episodes is a reason to design a test, not evidence of a relationship. The architect is consulted before it's put to the owner, and any difference is reported.

## Amendments
