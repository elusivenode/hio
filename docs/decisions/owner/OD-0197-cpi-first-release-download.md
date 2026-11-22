---
id: OD-0197
title: "Owner authorises the archived CPI releases download (245 pages, cap 250) and the first-release comparison for F-REVIEW-2026-11-22-e0004-1-1; no rerun"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-cpi-releases.md (owner's message, verbatim, with Claude's question)
  sha256: 84023ae6549ff46cc859ffbe0e818401fb6eb2e4130a640bb3d3b17df66076d5
  date: 2026-11-22
  quote: "y"
base_revision: 692fa8a4514417d1fbff1cd50b11bfb19d8d39b3
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1], ods: [OD-0188, OD-0189, OD-0190, OD-0191, OD-0195]}
---

# OD-0197: first-release CPI levels

**Authorised, once:** the archived BLS CPI news releases dated 2006-05-01 to 2026-10-31 in `~/.hio-research/E-0004/raw/release-dates.csv`: **245 pages**, a hard cap of **250 requests**. Claude told the owner "about 235"; the exact count, found while recording this, is 245, because the state's first month looks back a year and its year-on-year rate needs levels from April 2005. Same rights and notice as `bls_cpi` (OD-0188), a declared User-Agent naming the owner's contact at run time only, bytes kept in `~/.hio-research/E-0004/releases/` under a manifest.

**Then:** a worker extends the release parser (Table 1, "All items", unadjusted indexes) to every layout in the period, tested on trimmed real BLS snippets (public domain). Claude compares, for every reference month used, the level first published in its own release, and the year-ago level each release printed, with the flat-file level the run used.

- **All equal:** the run used first-release values in fact; F-1 is remediated without a rerun, and the state and result stand.
- **Any difference:** Claude stops and puts the choice between an amendment and a new run to the owner.

`bls_cpi`'s automated-retrieval condition is satisfied for this download only.

## Not authorised

A rerun of E-0004; any design change; any other download.

## Corrections (append-only)
