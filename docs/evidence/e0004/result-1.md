---
id: HIO-EVIDENCE-E0004-RESULT-1
title: "E-0004 step 2: not distinguished. No state-dependent difference in duration's downside benefit is shown"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0191
---

# E-0004 result 1

> **Exploratory, retrospective and unaccepted.** One run, `20261121T232243Z-23424eae`, at code `23424ea` (`tools/e0004_estimate.py` by worker W14), on the pinned inputs, under the preregistration adopted at `067bd7b` (OD-0190) and the two readings recorded before the run (OD-0191 and its correction 1). **No EODHD-derived value is recorded here:** the numbers are in the local result.json (sha256 `e03a3e0f38892ac1543e4280bbc54d79537998e1a8dd4c5308b743ac56de0193`) and were reported to the owner. CPI is from the U.S. Bureau of Labor Statistics (CPI-U, CUUR0000SA0), retrieved 2026-11-21. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

## The reading

**Not distinguished.** The primary 95% interval for Δ (accelerating minus not, in Treasuries' monthly downside benefit over bills) includes zero.

| Check | Reading | Sign of the point estimate |
|---|---|---|
| Primary, 12-month blocks | not distinguished | positive |
| 6- and 24-month blocks | not distinguished, both | positive |
| Block disagreement | none | — |
| Fragility (each of 11 stress clusters left out) | no cluster changes the sign | all positive |
| S1 equality counted as accelerating | not distinguished | positive (no month changes state) |
| S2 IEF replaced by E-0001's 10-year construction (overlap: the full panel) | not distinguished | positive |
| S3 three-month persistence filter | not distinguished | positive, much smaller |
| S4 the period ending 2008-09-30 excluded | not distinguished | positive |

## What it means, and what it doesn't

- **The sample doesn't show that Treasuries' downside protection depends on accelerating inflation**, at the 95% level, under any block length or sensitivity.
- **The point estimate's sign runs against the usual story.** Treasuries reduced downside losses slightly *more* in accelerating months, not less. The interval includes zero, so this is not evidence either way. Stress months cluster in the accelerating state (step 1: 18 against 6), which includes late 2008.
- **Not "no effect".** Step 1b showed the design resolves about ±0.17 points; a smaller real difference wouldn't be seen.
- **The 2022 cluster moves the estimate the most** when left out, and in the positive direction.
- **Retrospective.** The state was chosen knowing 2008, 2020 and 2022 (T-0023 recommendation 1). This can't be validated on the same history.

## Limits

One author, one machine, one run; no Codex review yet. October 2008's return also starts from BIL's disputed 2008-09-30 close, which S4 doesn't remove (OD-0191). The fund returns rest on EODHD's records, corroborated in T-0023 with failures C1 BIL, C4 IEF and C5 SPY (and IEF's audited NAV row) still standing.
