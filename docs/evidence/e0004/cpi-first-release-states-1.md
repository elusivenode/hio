---
id: HIO-EVIDENCE-E0004-CPI-FIRST-RELEASE-STATES-1
title: "E-0004 states recomputed from first-release CPI levels: identical to the states the run used"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0200
---

# First-release state comparison 1

> **A computed comparison, not a decision.** It shows that the run's states do not change when every CPI level is the one first published. It does not make the run's inputs first-release values, and it disposes of nothing: F-REVIEW-2026-11-22-e0004-1-1 stays open until the owner acts and Codex verifies. Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved 2026-11-21 and 2026-11-22. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

**Inputs.** The 245 releases of check 2, and 12 more dated 2005-05-18 to 2006-04-19 (12 requests, cap 15, OD-0200), which first published April 2005 to March 2006. The run's own `states.csv` from step 1 (233 periods, 2007-05-31 to 2026-10). No return series was read.

**Method** (`tools/e0004_first_release_states.py`, worker W2, checked `4bdf7db`). The first-release series takes each month's level from that month's own release, never from a later release's year-ago column. The states are recomputed with `tools/e0004_state.py`, unchanged, from the flat file and from the first-release series, under the primary rule and under the equality-as-accelerating sensitivity. The tool records every month the rule reads and does not find.

| Check | Result |
|---|---|
| First-release series | **257 months, 2005-04 to 2026-09**, one release each |
| Levels that differ from the flat file | **4**: May to August 2016 (check 2) |
| The 12 added months, April 2005 to March 2006 | all equal to the flat file |
| Flat-file states reproduce the run's `states.csv` | **yes**, all 233 periods |
| Periods whose state differs, primary rule | **0 of 233** |
| Periods whose state differs, equality sensitivity | **0 of 233** |
| Unavailable periods | 0 under either series |
| Months the rule reads and the first-release series lacks | **none** |
| Year-ago columns that differ from the month's own first release | 4: the 2017 releases print the corrected May to August 2016 levels, as expected |

**Reading: identical.** With the same states, returns, code and random settings, the estimation's inputs are the same, so repeating it would reproduce the result. That is computational equivalence only.

**Broken on purpose** (copies in a scratch directory): one first-release level raised by four points gave "differences found"; one release removed gave "incomplete" and named the month; one recorded state flipped gave "does not reproduce the run"; one release duplicated was refused.

## Local evidence (outside the repository)

| File | sha256 |
|---|---|
| `~/.hio-research/E-0004/releases/manifest.json` (245 files, each with its sha256) | `9f86987998f46f612cd56a50cc1b2b6cd3726984c871d017b84c96aedb90f8c6` |
| `~/.hio-research/E-0004/releases-2005/manifest.json` (12 files) | `412453b17479d7d73c7a30ea7d5e5ae21878187c7d12c8988bca3c211db1e1ef` |
| `~/.hio-research/E-0004/first-release-states/ledger.csv` (month, release, file sha256, printed level, flat level, equal) | `da19e3261bc02b7285a8444e854168e2cfb34e76ccd967b62c90b6ffd811ce01` |
| the run's `states.csv` | `2fc568ef88ee36026a73d46fe9f4a809c46df5f0d58655d9d28bba34c3c87c3b` |

A reviewer can rebuild the ledger and the comparison from the retained bytes with the committed tool.

## Limits

- The check covers the levels this run's states read. It says nothing about a different sample or rule.
- It finds a correction only through a month's own first release, and, from 2013, through a later release's year-ago column. A correction that BLS made and reversed between those two printings would not show.
- October 2025 was never published; no period of the run reads it.

## Not established

That F-1 is remediated or closed; that E-0004's result is accepted. The preregistration's promise of first-release values was not kept for four months, and stays as written.
