---
id: HIO-EVIDENCE-E0004-CPI-FIRST-RELEASE-1
title: "Are today's NSA CPI-U index levels the first-published ones? A sample check of the retained BLS releases"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0189
---

# CPI first-release check 1

> **A sample check, not proof.** It supports the preregistration's use of today's NSA values as first-release values. Source: U.S. Bureau of Labor Statistics, CPI-U (CUUR0000SA0), retrieved 2026-11-21. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.

**Method.** For each of the 12 archived releases retained under OD-0189, Table 1's "All items" row gives three unadjusted index levels (the reference month, the month before, and the same month a year earlier). Each was compared with the same month in `cu.data.1.AllItems` as retrieved on 2026-11-21. This was a one-off script, run by the author, and not committed.

| Result | Count |
|---|---|
| Releases parsed | 10 of 12. The 2009 and 2011 releases use a different table layout and weren't read |
| Index levels compared | 20 |
| Equal to today's value | **20** |
| Not comparable | October 2025, shown as "-" in the 2026-11-10 release and absent from today's file (never published) |

**Reading.** In this sample, no NSA level differs between first publication and today, from 2002 to 2026. Ten releases can't rule out a correction in another month. Before E-0004's step 1, the state builder should compare every month it uses against the 293 release dates' own tables, or record that it relies on this sample.
