---
id: HIO-RESEARCH-T0002-RBA-HISTORY-PACK
title: "Reading pack: the owner's rights decision on pre-2011 AUD cash from the RBA"
status: draft              # for the owner's reading. Verifies nothing, and decides nothing
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-04
task: T-0002
instruction: OD-0171
---

# Pre-2011 AUD cash: reading pack

> **The decision is the owner's own reading of the live pages.** The quotes came through a page-to-text tool on 2026-11-04, so they can't be the sole basis. No data file was requested, so **which series each table holds, and each column's source, are unconfirmed.**

## What's needed, and it's short

E-0003's sleeves are limited by BIL, which starts in May 2007. **Only about 44 months are missing, 2007-05 to 2011-01,** and they hold 2008. Going further back adds nothing to this comparison.

## Read these

| Page | What it showed through the tool |
|---|---|
| <https://www.rba.gov.au/statistics/historical-data.html> | "Interest Rates and Yields – Money Market – Daily – 1976 to 31 December 2010 – F1". It joins the current F1, whose Cash Rate TRI starts 2011-01-04 |
| <https://www.rba.gov.au/statistics/tables/> | "Interest Rates and Yields – Money Market – Monthly – F1.1" (`f1.1-data.csv`); "Changes in Monetary Policy and Administered Rates – A2" |
| <https://www.rba.gov.au/copyright/> | "all RBA Material is provided under a Creative Commons Attribution 4.0 International License", excluding third-party material. Cash Rate use is conditional: no implied endorsement, not presented as from another source. Attribution: "Source: Reserve Bank of Australia [year]". Automated access isn't addressed. ASX material has its own terms |

**The same terms you read for the five capture datasets apply (U1).** The new risks are below.

## The questions

- **A1, which file:** the daily F1 historical file (recommended, because daily accrual is possible) or monthly F1.1 as a fallback? Claude can't choose finally without reading a column header row, which means retrieving the file.
- **A2, third-party columns:** a money-market file may hold third-party columns, as the current F1 does for ASX and FENICS. Is it acceptable to retain the whole file as a sealed receipt and use only the RBA-sourced overnight series, as you decided for the current F1 (OD-0116)? **If the overnight series' own `Source` row isn't the RBA, the download's use stops there.**
- **A3, retrieval:** is one modest, one-off request acceptable, given the terms are silent on automated access? This is the same reasoning as U1.

## The decision, one operation at a time

For the historical overnight cash series only, 2007-05 to 2011-01 in use.

| Operation | Recommended | Condition |
|---|---|---|
| Retrieve, one-off | your judgement | one request, declared User-Agent |
| Retain raw | allow | RBA attribution; no implied endorsement. **State a duration:** proposed "indefinite, for audit and rebuild", as for the capture datasets |
| Calculate, store derived, rebuild | allow | same |
| External processing, `hio_internal`, agent context | allow | same |

**Not covered by a yes:** third-party columns; quotation in documents, including this public repository; any release to a consumer; scheduled capture; any extension of E-0003, which needs its own pre-registration.

## What it would and wouldn't do

**Would:** let the AUD cash comparison include 2008 for the first time.

**Wouldn't:**
- **A different object before 2011.** The TRI is the RBA's own index; before it, HIO would accrue a published rate itself (RA §3.2), so the two pieces join at a seam. They'd be reported separately, and with the seam stated.
- **Calendars.** HIO's cited RITS calendars cover 2026 only. Accruing between published dates needs no holiday calendar, but that's a method choice to pre-register.
- **Rate meaning.** An overnight or target rate isn't what a depositor earned.
- **One crisis is one crisis.** It adds one severe episode, not statistical power, and it can't be independently checked with what's cleared.

**Claude's recommendation:** yes to all, read narrowly. It's cheap and fills the one gap the owner most wants filled. It's also reasonable to leave it until the bigger choice of an independent return reference is made.
