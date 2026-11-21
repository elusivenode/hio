---
id: HIO-EVIDENCE-E0004-STEP1B-1
title: "E-0004 step 1b: the precision check passes (median half-width 0.17 points against 0.20)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0190
---

# E-0004 step 1b, run 1

> **No delta was computed on the real alignment, and none on any shift was recorded.** Run `20261121T230331Z-cc1ee2c7` at code `cc1ee2c` (`tools/e0004_precision.py` by worker W12), on the same pinned inputs as step 1. precision.json sha256 `a7c3fefb5e15972d1888fa25e912ca731a800df66b2b62701516b9ceb9cbb3c6` (local). CPI is from the U.S. Bureau of Labor Statistics (CPI-U, CUUR0000SA0), retrieved 2026-11-21. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

| Item | Result |
|---|---|
| Shifts | 208 (k = 13 to n − 13; n = 233) |
| Bootstrap per shift | 12-month circular blocks, 1,000 replications, seed 20260004 |
| Replications dropped | 0 |
| **Median half-width** | **0.167 percentage points** |
| Bar | ≤ 0.20 points: **pass** |

**Reading.** With no true state difference, the 95% interval for Δ would typically span about ±0.17 points. That is just inside the 0.20-point relevance threshold, so step 2 can in principle show a relevant difference, but **only one clearly larger than the threshold would clear it**: under the adopted rule, the whole interval must lie beyond ±0.20.

**Before step 2 (preregistration "Data conditions"):** IEF's NAV corroboration must pass first; it needs the owner's browser download. Step 2 also needs its own owner yes (OD-0190).
