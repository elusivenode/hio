---
id: HIO-RESEARCH-T0003-VENDORS-2026-11-04
title: "T-0003: equity data vendor assessment (no candidate is cleared)"
status: draft              # research findings; verifies no right, chooses no vendor, authorises no purchase
owner: owner (decides; HIO-ADR-0011); researched by claude/implementation-agent
created_at: 2026-11-04
task: T-0003
instruction: OD-0160
method: >-
  Public pages read 2026-11-04 through a page-to-text tool or search extracts, not by a lawyer. No vendor contacted,
  no account opened, no data retrieved, no sample downloaded. Prices and coverage are the vendors' own claims.
---

# Equity data vendor assessment

> **The stop condition applies. No candidate is cleared for HIO's proposed workflow, and no purchase is recommended now.** That doesn't show that no suitable licence exists: it shows that published terms don't establish one. **Unknown means unverified, not permitted.** Every licence reading below is a non-lawyer's, from text a tool extracted, so read the live clause before relying on it.

## The result

- **First enquiry candidate:** EODHD, for US and ASX ETFs. It isn't a provisional purchase, and permission and price provenance outrank its coverage.
- **Independent reference:** issuer-published distributions and returns, subject to their own rights. Not any vendor's adjusted close.
- **Second vendor, conditional:** Tiingo, for the USD series only. Its internal commercial plan is the only commercial licence found under the ceiling, but its data must be deleted on cancellation.
- **Not for this slice:** Norgate (individuals only; the data goes at expiry), EODData (personal only; undocumented basis), S&P DJI (quote only; a separate requirement).

## Scorecard

Evidence: **R** read on the vendor's page; **X** search extract only; **?** not established.

| | EODHD | Tiingo | EODData | Norgate | S&P DJI |
|---|---|---|---|---|---|
| **Fit** | ETF histories, US and ASX | ETF histories, US only | Possibly both; basis undocumented | ETF histories, US and ASX; also delisted | Index histories; a different object |
| **ASX** | claimed (R) | **no** (R) | listed (R) | yes (R) | S&P/ASX indices (X) |
| **Unadjusted close** | yes: "raw" (R) | `close` (R); raw not stated in those words | ? | NONE setting (X) | n/a |
| **Distributions** | ex-date, `unadjustedValue`, currency (R); ASX declaration and record dates can be absent (R) | `divCash` on the ex-date (R) | listed, no fields (R) | ? on the pages read | embedded in TR and net series |
| **Adjustment method** | "both splits and dividends", method not on the page; recomputed (R) | CRSP method (R) | ? | TotalReturn setting (X) | index methodology |
| **Provenance** | **conflicting** (below) | "at least 3 data sources on average" (R); not named | not named (R) | "upstream data partners, including some exchanges" (R); not named | index provider itself |
| **History** | "30+ yrs" (R) | 1962 (R) | "30+ years" (R) | to 1990 at Platinum, 1950 at Diamond (R) | by index |
| **API or platform** | REST; 100,000 calls a day (R) | REST (R) | REST (R) | **Windows updater** must run (X); data may be processed elsewhere (R) | by contract |
| **All-in cost** | USD 19.99 a month personal; **USD 399 commercial, +200 server download** (R) | USD 30 individual; **USD 50 internal commercial** (R) | USD 19.95 to 69.95 personal; commercial feed example USD 750 (R) | Platinum USD 346.50 for 6 months (US); AUD 346.50 ex GST (AU); no monthly term (X) | **quote only** |
| **Short test** | one-month minimum (R) | monthly (R) | monthly, 30 days' notice (R) | **3-week free trial**, 2 years' history (X) | none found |

**Ceiling:** AUD 400 is about USD 280 at EODHD's own indicative AUD/USD of 0.7054, a rough figure only. EODHD's commercial plan exceeds the whole ceiling. Exchange fees aren't stated for EODHD and may be separate.

## Permissions

| Use | EODHD | Tiingo | EODData | Norgate | S&P DJI |
|---|---|---|---|---|---|
| Owner's personal research | **allowed in terms**, for "private, non-commercial purposes" | allowed: individual plan, "own personal use" | allowed: personal use | **allowed**: research, backtesting | "non-commercial, personal use" of site data only (X) |
| Use by a two-trustee SMSF | **unverified.** Not "on behalf of any other individual or business" | unverified on the individual plan; **internal commercial plan may fit**, unconfirmed | **denied** on published terms: not "in connection with any business" | **denied** on published terms: not for "another person, business or organisation", no business licence | licence needed |
| Derived results in private trustee and auditor reports | **unverified**; personal terms bar "displaying" the data; derived data not addressed | **unverified**: "may not display or share the data" | unverified: may not "disseminate" | unverified: only derived data qualifies, narrowly | licence needed |
| Azure and GitHub Actions | unverified: not addressed | unverified on what was read | unverified | **allowed** for Personal Use, with limits (R) | licence needed |
| Coding agents and hosted AI | unverified: not addressed | **unverified**; restrictions possible, terms not fully read | unverified | unverified: third-party processing allowed, AI not named (R) | licence needed |
| Ten-year retention, raw | unverified: not addressed | only while subscribed | unverified | only while subscribed | licence needed |
| After termination | **unverified: not addressed** | **raw denied**: delete, including backups and compliance systems (X, reported section 1.6) | unverified | **raw denied**: delete all, including backups; derived kept only if it can't reconstruct the content (R) | licence needed |

No vendor's published terms establish the fund's use, private reports, ten-year retention and rebuild together.

## Blockers

**Rights**
1. **The purpose.** "Owner-only personal research" isn't a safe class merely because one person runs HIO: its stated purpose is to inform an SMSF. Whether that defeats personal status is unknown, so disclose it and ask. Don't assume it either way.
2. **The return series may be the licensed data in another form.** Norgate's definition is the clearest: derived data must not resemble or reconstruct the content, and its examples are backtests and statistics. A daily ETF return series with its closes could fail that. Others are silent.
3. **Reproducibility against deletion.** HIO's rebuild depends on retained bytes. A delete-on-exit licence means rebuilds last only while the subscription does, so stopping costs the ability to reproduce. Licensed data can't go in the 3,650-day evidence store unless retention is cleared (architect, OD-0158).
4. **Agent use.** Unless `agent_context` is allowed, Claude and Codex can't see values, so review of a data run has to be on metadata or by the owner.

**Data quality**
1. **EODHD's provenance conflicts.** It claims a direct ASX agreement and the Nasdaq Cloud API for US data, yet its pricing and ASX pages say "We are not using exchanges data feeds for the pricing data", describe VWAP aggregation, and call data indicative. Those statements may refer to different endpoints, and an exchange agreement needn't cover this one. **This is the first question to settle, because an aggregated price isn't a closing price.**
2. **Adjusted closes rewrite history.** EODHD says so itself: each dividend rescales the past. They are diagnostic at most, and RA §5 already bars them as a return without a verified method.
3. **ASX distributions are untested.** No evidence was found either way. Dates can be absent, and franking appears only in a beta feed. Components and specials need an issuer comparison.
4. **FX isn't a fixing.** EODHD's forex is market-maker data, and is called indicative. It can't serve as RA §4.4's declared fixing, so no vendor here solves AUD translation.
5. **Delistings.** EODHD says a delisted ticker keeps its history, but a renamed one doesn't. Norgate covers delisted ETFs at Platinum. E-0002's named survivors don't test this.

## The six instruments

| Instrument | Symbol form | Inception | Issue |
|---|---|---|---|
| SPY | `SPY.US` (EODHD) | 1993-01-22 (X, third party) | longest; market-price basis differs from NAV |
| VTI | `VTI.US` (EODHD) | 2001-05-24 (X, third party) | |
| IEF | `IEF.US` (EODHD) | **2002-07-22** (issuer, R) | monthly distributions; a heavy test |
| VAS | `.AU` form unconfirmed: pages show `LEVR.AU`, `VDAL.AU` | 2009 from memory; one report says 2004: **unconfirmed** | quarterly; page unread |
| IVV (ASX) | unconfirmed; issuer shows `IVV.AXW` | **unread**: issuer page refused the tool | don't confuse it with US-listed IVV |
| BGBL | unconfirmed | **2023-05-09** (issuer, R) | about 3.5 years, so it holds no 2008, 2020 or 2022 peak-to-trough stress |

**Coverage is unconfirmed for every instrument on every vendor:** no ticker list was downloaded. Tiingo cannot supply the three ASX funds. VAS, IVV (ASX) and BGBL can't support long stress analysis on their own histories.

**Up to three additions:** **BIL** (E-0002's cash sleeve; inception unverified), one **high-distribution ASX ETF** to test components, and one **delisted ETF**, named once coverage is known.

## Two separate requirements

| | Investable ETF histories | Longer index histories |
|---|---|---|
| **Object** | Price return of a fund, with fees embedded, built by HIO from raw closes and actions (RA §3.1, §5) | Provider-calculated price, gross and net series, no fees |
| **Length** | Fund life only | S&P/ASX 200 net: first value 2000-03-31, launch 2000-04-03 (X). S&P 500 dates unconfirmed |
| **Labels** | Reconstructed; survivor selection | Values before launch are **back-tested** by S&P's own definition (X). Label them. Net means a provider withholding assumption |
| **Route** | A vendor above | **S&P DJI quote**. Its terms bar historical databases and derived data without written consent (X). No licence for an individual is published |
| **Slice** | E-0002 | Out of this slice. Revisit if the ETF window can't answer a question |

Style-factor indices weren't assessed further: no vendor above is a clear source, and E-0002 doesn't need them.

## Recommended sequence

1. **Questions first.** No account and no data until written answers arrive.
2. **Then, only if EODHD's answers clear it, one month** on the USD 19.99 plan, under its own owner decision. Sample as above. It stays outside the evidence store and CI, with the data on the owner's Mac.
3. **If EODHD can't clear:** Tiingo internal commercial for USD-only E-0002, knowing data goes on cancellation. Then ASX waits.
4. **If neither clears:** E-0002 stays at synthetic Stage A, with the written reasons as the result.

Norgate's free trial could add a second price source for two years of data, but its licence excludes the fund's purpose. Don't use it unless Norgate agrees in writing.

## Minimal validation sample: declared before any data

Window: every instrument's full history for distributions; closes on a declared sample of dates.

| # | Test | Pass | Evidence against |
|---|---|---|---|
| V1 | Identity: ticker, issuer, exchange, currency | matches the issuer | any mismatch |
| V2 | Close definition | written, and it's an official or consolidated close | aggregated or undefined close **fails the source** |
| V3 | Closes against an independent cleared record, on declared dates | equal to the tick; each difference listed | unexplained differences |
| V4 | Distributions against issuer records | every ex-date and amount present and equal to its rounding; currency right; specials included | one unexplained missing or wrong row is a finding, and three stop the trial |
| V5 | Splits and consolidations | RA-INV-020 holds: no spurious return | a jump on an action date |
| V6 | HIO's return against issuer-published returns, with an expected-difference model for NAV against market price and timing | RA §11 categories: explained, partly explained, unexplained | "unexplained" opens an investigation |
| V7 | Revisions: same pull at the start and end of the month | raw closes and dividends unchanged, or each change listed | silent revision |
| V8 | Missing dates, counted per instrument | counted and reported; nothing filled | uncounted gaps |
| V9 | Written rights for each operation used | answers on file before retrieval | no answer means no operation |

**Vendor's adjusted close is only a diagnostic.** Agreement doesn't verify its distributions: the same inputs would produce it. **Hand transcription isn't independent authentication either**, and issuer pages need their own rights check: iShares' US terms bar systematic collection, so read them by hand, occasionally, and record that.

**These criteria can't show:** that the fund's future data will be right, that an unchecked instrument is right, or that returns are achievable after costs.

## What it could and couldn't support in E-0002

**Could support, if every check passes:** a USD descriptive comparison over the window the youngest sleeve allows, with the first three US funds, BIL as a labelled sleeve, and the owner as the reader.

**Couldn't support:**
- AUD translation or hedging: no fixing is cleared.
- Long Australian or global stress analysis: VAS, IVV (ASX) and BGBL histories are too short or unconfirmed. The ASX funds could be described only over their own lives.
- Any report to the other trustee or auditor, until rights say so.
- Point-in-time claims, the investable performance of a real portfolio after costs and tax, or any statement about the future.
- Rebuild after a subscription ends, unless written retention says otherwise.

## Not established

- Tiingo's terms: the page refused the tool. Claude has a search extract, and the architect read section 1.6 (paid plans may persist while active; cancellation triggers deletion). **Read it directly.** S&P terms come from extracts too.
- Vanguard's fund page gave no content, and BlackRock Australia refused the tool.
- Whether any vendor offers a suitable small-entity or trustee licence. No vendor was asked, by instruction.
- ASX distribution accuracy on any vendor: no data was read.

## Sources

[EODHD terms](https://eodhd.com/financial-apis/terms-conditions), [pricing](https://eodhd.com/pricing), [commercial pricing](https://eodhd.com/commercial-pricing), [data sources](https://eodhd.com/financial-apis/our-data-sources-and-data-partners), [EOD API](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes), [dividends and splits](https://eodhd.com/financial-apis/api-splits-dividends), [ASX](https://eodhd.com/asx-data), [AUD/USD](https://eodhd.com/financial-summary/AUDUSD.FOREX). [Tiingo terms](https://app.tiingo.com/tos/), [pricing](https://www.tiingo.com/about/pricing), [EOD documentation](https://www.tiingo.com/documentation/end-of-day), [EOD product](https://www.tiingo.com/products/end-of-day-stock-price-data), [general documentation](https://www.tiingo.com/documentation/). [EODData terms](https://www.eoddata.com/about/terms.aspx), [products](https://www.eoddata.com/products/default.aspx), [API](https://www.eoddata.com/products/API.aspx), [commercial feed](https://www.eoddata.com/products/datafeed.aspx). [Norgate EULA](https://norgatedata.com/subscribe/eula.php), [FAQ](https://norgatedata.com/faq.php), [content tables](https://norgatedata.com/data-content-tables.php), [packages](https://norgatedata.com/stockmarketpackages.php), [prices](https://norgatedata.com/prices.php), [trial](https://norgatedata.com/freetrial.php), [Python package](https://pypi.org/project/norgatedata/). [S&P Global terms](https://www.spglobal.com/en/terms-of-use), [S&P/ASX brochure](https://www.spglobal.com/spdji/en/documents/additional-material/brochure-spdji-asx.pdf). [Betashares BGBL](https://www.betashares.com.au/fund/global-shares-etf/), [iShares IEF](https://www.blackrock.com/us/individual/products/239456/ishares-710-year-treasury-bond-etf), [ETF Central](https://www.etfcentral.com/compare-etfs/SPY-vs-VTI).
