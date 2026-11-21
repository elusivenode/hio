---
id: HIO-RESEARCH-CPI-SOURCE-1
title: "A CPI source with release dates, for the inflation-acceleration state"
status: draft              # for the owner's reading. Verifies nothing and decides nothing
owner: owner (decides); drafted by claude/implementation-agent
created_at: 2026-11-22
task: T-0002
instruction: OD-0181 (item 4)
---

# A CPI source with release dates

> **A draft for the owner's rights reading. Nothing has been downloaded,** and both register rows stay `unverified` (deny). Every claim below comes from web search on 2026-11-22, not from the owner reading the live pages.

## What the state needs

T-0023 recommendation 1 (adopted, OD-0181) defines the state as follows. At each month end, is the latest **published** year-on-year CPI rate above the rate published twelve months earlier? That needs two things: original release values, and the date each one was released. Missing publication evidence means the state is unavailable.

## Proposal

| Role | Source | Register row |
|---|---|---|
| Values | BLS CPI-U, US city average, all items, **not seasonally adjusted** (`CUUR0000SA0`) | `bls_cpi` |
| Release dates | BLS's own records: the release-dates PDF for 1953 to 2000, the archived schedules, and the archived news releases (2007 on) | `bls_cpi` |
| Cross-check of dates | ALFRED release 10 (Consumer Price Index) and `CPIAUCNS` vintages | `alfred_fred.cpi_release_dates` |

**Why the NSA index.** Seasonally adjusted CPI is revised for up to five years, and BLS warns against it for escalation. NSA CPI-U is what escalation contracts use. If it is revised only by flagged corrections, today's values equal the first-published ones, and the release dates are the only point-in-time data needed. **That is unconfirmed.** I didn't find BLS saying it outright, and it is the first thing to check. The archived news releases give the published year-on-year rates directly, so they can test the claim.

**One known gap.** October 2025 CPI wasn't published, because of the 2025 lapse in appropriations. Under E-0004's rule the latest published rate carries forward, so September's rate stayed latest until November's was published, as it did at the time; no state is filled in (corrected 2026-11-22 to match `docs/evidence/e0004/preregistration-1.md`).

## Rights, as read by search (unverified)

| Point | BLS | ALFRED / FRED |
|---|---|---|
| Status | public domain (17 U.S.C. §105). BLS: text, charts and tables "may be reproduced without permission" with credit | a copyright tag on each series: public domain, citation requested, or copyrighted. Some CPI graphs are tagged copyrighted, so the series page decides |
| Attribution | credit BLS. The API terms ask for the retrieval date, and modified data mustn't be cited as BLS.gov | "Source: BLS via FRED" |
| Automated access | API terms exist (with registration limits); not yet read in full | the API needs a key; the terms not yet read in full |
| Agent context, distribution | likely allowed for public-domain data; for the owner to decide | depends on the tag |

## What the owner would decide, and what it would authorise

1. **The rights reading.** The owner reads the live BLS copyright page and the API terms (and FRED's legal page, if ALFRED is kept as a cross-check). If they agree, the rows become `owner_verified` under an OD.
2. **A download.** That is a separate yes: a one-off retrieval with a declared User-Agent, like the par-curve and H.10 downloads.

Sources: [BLS copyright](https://www.bls.gov/opub/copyright-information.htm), [BLS API terms](https://www.bls.gov/developers/termsOfService.htm), [BLS CPI release archive](https://www.bls.gov/bls/news-release/cpi.htm), [BLS release dates 1953–2000](https://www.bls.gov/bls/histreleasedates.pdf), [BLS archived schedules](https://www.bls.gov/bls/archived_sched.htm), [BLS 2025 lapse dates](https://www.bls.gov/bls/2025-lapse-revised-release-dates.htm), [BLS seasonal adjustment](https://www.bls.gov/cpi/seasonal-adjustment/questions-and-answers.htm), [ALFRED CPI release dates](https://alfred.stlouisfed.org/release/downloaddates?rid=10), [FRED legal](https://fred.stlouisfed.org/legal/).
