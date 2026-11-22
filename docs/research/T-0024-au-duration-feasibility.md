---
id: HIO-RESEARCH-T0024-AU-DURATION
title: "Australian government duration through a bond fund: feasibility (T-0024 package B3, first step)"
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0221
base_revision: 75bd6e00477639eff2cae72f0f2bd3ec84155355
---

# Australian duration through a fund: feasibility

> **Proposed.** Fund facts are **[EXT], unverified**: read on 2026-11-22 from public web pages, some of which disagree on fees. Nothing was fetched from a data vendor. Check each fact on the issuer's page before relying on it.

## The question

T-0024 needs an Australian government duration sleeve. HIO holds no data for one. Can a listed fund's total return serve, built with the tools that built VAS?

## Answer

**Yes, from April 2012.** `tools/factor_build.py` built an ASX fund unchanged (`docs/evidence/factors/build-5.md`). A bond fund needs the same three files per symbol (closes, distributions, splits). The vendor's ASX symbol list, already held in snapshot `s2`, names every candidate below.

## Candidates

| Fund | Holds [EXT] | Index [EXT] | Listed [EXT] | Fit |
|---|---|---|---|---|
| **VGB** | Commonwealth and state government bonds, all maturities | Bloomberg AusBond Govt 0+ Yr | April 2012 | the broad government sleeve; longest listed history; duration about 5 years |
| **IGB** | Commonwealth bonds only | a Bloomberg AusBond Treasury index | 2012 | the pure sovereign comparator: shows what the state bonds in VGB add |
| **AGVT** | government bonds of 7 to 12 years | Solactive Australian Government 7–12 Year | July 2019 | the closest maturity match to IEF (US Treasuries of 7 to 10 years), but a short history; duration about 7 years |
| GOVT | Commonwealth and state bonds | S&P/ASX iBoxx Australian & State Governments 0+ | July 2012 | overlaps VGB |
| RGB | government bonds of 5 to 10 years | DBIQ 5–10 year Australian Government Bond | not confirmed | a maturity match if its history is long; unconfirmed |

## Recommendation

**Fetch VGB and IGB; add AGVT as a maturity check.**

- **VGB is the sleeve.** It is the broad, long-listed government fund.
- **IGB tests the label.** If VGB and IGB differ materially, the sleeve is "government and semi-government", not sovereign.
- **AGVT answers the maturity question.** IEF holds 7 to 10 year bonds and VGB about 5 years of duration, so an Australia–US difference mixes country and maturity. AGVT's shorter history shows how much.

## What it needs

One fetch of three symbols under the existing `eodhd.personal_evaluation` row, into a new pinned snapshot. That is the owner's yes. No new source, no cost beyond the subscription, no new rights reading. Then three proposed specs and three builds, with the same real-data checks as VAS.

## Limits

- **History starts in 2012.** The comparison would hold no 2008 and no 2009 to 2011. A longer history needs a constructed series from yields, which is the curve route (T-0020), not this one.
- **Thin early trading.** A bond fund's close can be stale on quiet days, and its market price can sit away from its net asset value in stress. The real-data check should count zero-volume days and flag March 2020.
- **Duration is not fixed.** Each fund's duration drifts with its index. The sleeve is a maturity basket, not a constant-duration factor.
- **One vendor, unvalidated,** as for every other fund here.
- **The Australian and US funds differ in maturity,** as above.

## Sources

Read 2026-11-22; [EXT], unverified.

- https://www.etfstream.com/articles/the-best-australian-government-bond-etf-blackrocks-igb-vs-vanguards-vgb-vs-betashares-agvt
- https://betashares.com.au/fund/australian-government-bond-etf
- https://www.ssga.com/au/en_gb/intermediary/etfs/spdr-spasx-iboxx-australian-government-bond-etf-govt
- https://fund-docs.vanguard.com/AU-Vanguard_ETFs_at_a_glance.pdf
- https://pearler.com/explore/invest/au-shares/compare/AGVT-vs-RGB
