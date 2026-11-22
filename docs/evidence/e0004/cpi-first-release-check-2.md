---
id: HIO-EVIDENCE-E0004-CPI-FIRST-RELEASE-2
title: "First-release CPI levels against the flat file E-0004 used: all 245 archived releases, 2006-05 to 2026-10"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0197
---

# CPI first-release check 2

> **A comparison, not a decision.** It answers F-REVIEW-2026-11-22-e0004-1-1's question for the months it can reach, and finds four differences. OD-0197 says that on any difference Claude stops and the owner chooses. Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved 2026-11-21 and 2026-11-22. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

**Method.** `tools/bls_cpi_releases.py fetch` downloaded every archived CPI news release dated 2006-05-01 to 2026-10-31 once: **245 requests, 245 files** (224 HTML, 21 PDF), at tool commit `e8d43a0`, kept outside the repository under a manifest. `compare` read Table 1's "All items" unadjusted index from each release (the reference month, and the same month a year earlier where the release prints it) and set it against `cu.data.1.AllItems`, the file E-0004's run used. Comparison is exact, on decimals.

| Result | Count |
|---|---|
| Releases parsed | **245 of 245**; reference months 2006-04 to 2026-09, each once |
| Printed levels equal to the flat file | **415** |
| Printed levels that differ | **4** |
| Levels the release does not print | 71 |

**The four differences** are consecutive reference months. BLS's release of 2016-10-18 announced corrections to the prescription drug indexes for May to August 2016, which changed the All items index. The flat file holds the corrected values.

| Reference month | First release | Flat file (used by the run) |
|---|---|---|
| 2016-05 | 240.236 | 240.229 |
| 2016-06 | 241.038 | 241.018 |
| 2016-07 | 240.647 | 240.628 |
| 2016-08 | 240.853 | 240.849 |

**Reading.** E-0004's run did not use first-release values for those four months; for every other reference month from 2006-04 to 2026-09 the first-published level equals the level used. Whether any month's state changes with the four first-release levels has **not** been computed: that is outside OD-0197.

## What this check cannot show

- **Year-ago levels before 2013.** The PDF and `<PRE>` releases (to 2012) print the previous and the reference month only. Their year-ago levels make up most of the 71 "not printed". A later correction to a month's level would show here only if BLS made it before that month served as a year-ago base and the release printed it.
- **April 2005 to March 2006.** These base levels were first published in releases before 2006-05, which OD-0197 does not cover.
- **October 2025** was never published; the 2026-11-10 release shows "-" for it.
- **Corrections to a month other than through its own first release** are found only where a later release prints that month again (as its year-ago level, 2013 on).

## Not established

That F-1 is remediated; that E-0004's state or result stands or changes. Nothing here is accepted or approved.
