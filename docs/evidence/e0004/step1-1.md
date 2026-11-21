---
id: HIO-EVIDENCE-E0004-STEP1-1
title: "E-0004 step 1: the information count passes the screen in both states"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0190
---

# E-0004 step 1, run 1

> **Counts only: no portfolio outcome was computed.** Run `20261121T230030Z-6745c1fd` at code `6745c1f` (tools `e0004_state.py` by worker W10 with Claude's year-earlier fix, `e0004_info.py` by W11), on the pinned inputs: snapshot s2 via frozen panel `1aa29918…` and the OD-0189 CPI download. counts.json sha256 `65a909f3f176e8bd588a9a6285411db1ac63c2cb8769d609b5953cd9e9dec879`; states.csv `2fc568ef88ee36026a73d46fe9f4a809c46df5f0d58655d9d28bba34c3c87c3b` (local, `~/.hio-research/E-0004/runs/`). CPI is from the U.S. Bureau of Labor Statistics (CPI-U, CUUR0000SA0), retrieved 2026-11-21. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

| Per state | Accelerating | Not accelerating | Bar |
|---|---|---|---|
| Months | 114 | 119 | ≥ 48 |
| Runs | 12 | 12 | ≥ 4 |
| Stress months (SPY ≤ −5%) | 18 | 6 | — |
| Stress clusters | 7 | 5 | ≥ 3 |
| Concentration (largest cluster's share) | 0.28 | 0.33 | ≤ 0.5 |

233 periods, 2007-05-31 to 2026-10-30, none unavailable. **The screen passes in both states.**

**Spot checks against known history** (Claude's, from states.csv): accelerating through 2008 until its last month, then not; accelerating into early 2020, not from May 2020; accelerating through 2021 and 2022; not through 2023.

**Worth noting before step 1b.** Three times as many stress months fall in the accelerating state (18 against 6), and late 2008 is classified accelerating alongside 2022. The architect warned of this, and the rule stands. Only 6 stress months in the other state means its downside estimates will be noisy; step 1b measures how noisy.

**One deviation, fixed before the run:** Claude's brief had the year-earlier comparison use a panel month end, which would have made the first twelve months unavailable. The adopted rule compares with the rate published as of the same instant a year earlier; the fix uses that month's last calendar day (CPI is released mid-month). Recorded in commit `6745c1f`.
