---
id: HIO-RESEARCH-T0002-2026-10-25
title: "T-0002 evidence, 2026-10-25: RBA and NY Fed rights, timing, calendars and revisions; S1b staging recommendation"
status: draft              # evidence for owner verification; NOT owner_verified; no permission changed
owner: owner (verifies and decides); researched by claude/implementation-agent
created_at: 2026-10-25
task: T-0002 (authorised OD-0009; held by OD-0013; continued under OD-0045)
supplements: docs/research/T-0002-source-rights-and-timing.md   # the 2026-10-18 note, unedited
method: >-
  Manual inspection only, 2026-10-25 between 01:00Z and 01:30Z. (1) Publishers' terms and
  documentation pages, read with WebFetch; quotations are the fetch tool's short extracts and
  must be checked against the live page before verification. (2) One manual download each of
  RBA F1 and F11.1 (CSV) and the RBA F1 expert-judgement CSV, and of two NY Fed Markets API
  responses (SOFR last 5; all rates latest), into a session scratchpad outside the repository.
  Only their structure was examined (headers, source rows, date labels, which cells are filled,
  HTTP Last-Modified). No value is recorded here. The samples were deleted the same session,
  because the F11 AUD/USD rights are now known to be third-party and unresolved. No ingestion
  was automated, nothing was scheduled, no vendor or publisher was contacted.
---

# T-0002 evidence: RBA and NY Fed (2026-10-25)

> **Not verification.** Every permission in [`registers/sources.yaml`](../../registers/sources.yaml)
> stays `unverified` and `unknown` (OD-0013). This note gives the owner primary-source evidence to
> verify, or not. §5 is a recommendation, not a decision.

## 1. RBA: the terms, and why the datasets differ

**Terms:** <https://www.rba.gov.au/copyright/>, accessed 2026-10-25. The page shows no
"last updated" date; its footer reads © 2001–2026. Its sections are:
- §3 Attribution;
- §4 Cash Rate;
- §5 Financial Data;
- §7.2 Third party.

| Clause (short extracts) | Effect |
|---|---|
| "all RBA Material is provided under a Creative Commons Attribution 4.0 International License"; "may be reproduced, published, communicated to the public and adapted provided that the RBA is properly attributed" | copy, store and adapt RBA-sourced material, with attribution |
| Attribution: "Source: Reserve Bank of Australia [year] OR Source: RBA [year]"; it "cannot be done in any way that suggests that the RBA endorses you" | a condition every derived artefact must satisfy |
| §4 Cash Rate: "for personal or commercial use only if it is not stated, represented or in any way implied" that the RBA endorses it; "must not engage in improper commercial exploitation". "Cash Rate Materials" are materials the RBA publishes "that include the Cash Rate" (summary of §2) | AONIA is allowed, with no implied endorsement |
| §5 Financial Data: everything numerical "other than the Cash Rate", "not formally administered by the RBA as a financial benchmark"; users "assume the entire risk"; it may be withdrawn or modified without notice; third-party content needs that party's consent (summary) | RBA-sourced series other than AONIA |
| §7.2: third-party material "may not be reproduced, published, communicated to the public, adapted or otherwise used in whole or part" without consent | **any series whose source row is not RBA** |
| Automated access, scraping, bulk download | **not addressed.** `robots.txt` (Last-Modified 2025-01-22) disallows only `/assets/`, `/search/`, `/s/` and three specific paths; `/statistics/tables/csv/` is not disallowed. `robots.txt` is a crawler convention, **not a licence** |

**The decisive structural evidence: the CSV files' own `Source` rows.**

| Table and series | Series ID | `Source` row | Clause that applies |
|---|---|---|---|
| F1 Interbank Overnight Cash Rate (AONIA) | `FIRMMCRID` | RBA | §4 Cash Rate |
| F1 Cash Rate Total Return Index (base 04-Jan-2011 = 100) | `FIRMMCTRI` | RBA | **ambiguous**: §4 if it is a "Cash Rate Material", otherwise §5. Both permit use with attribution and no implied endorsement |
| F1 Cash Rate Target | `FIRMMCRTD` | RBA | §5 (not the benchmark) |
| F1 EOD 1-, 3- and 6-month BABs/NCDs | `FIRMMBAB30D`… | **ASX** | **§7.2: third party (ASX consent)** |
| F1 1-, 3- and 6-month OIS | `FIRMMOIS1D`… | **FENICS** | §7.2: third party |
| F1 1-month Treasury Note | `FIRMMTN1D` | RBA | §5. **Empty in every 2026 row**, so unusable |
| F11.1 A$1=USD | `FXRUSD` | **WM/Reuters** | **§7.2: third party (LSEG)** |
| F11.1 Trade-weighted Index | `FXRTWI` | RBA | §5 |

**What the third-party sources mean:**
- **F11's AUD/USD is the WM/Reuters Australian Dollar Fix.** The RBA's definitions page
  (<https://www.rba.gov.au/statistics/frequency/definitions-sources.html>, accessed 2026-10-25,
  no date shown) says: "Since 1 July 2008, the rate shown for the US dollar is" the "WM/Reuters
  Australian Dollar Fix at 4.00 pm (Sydney) on the day concerned", "sourced from page AUDFIX on
  Thomson Reuters", "rounded to four decimals". It is RBA material only where the fix is
  unavailable (marked `*`; none in the 2023-to-current file).
  - The other F11 cross rates are calculated "by crossing the rate for the US dollar", so they
    carry the same input.
  - LSEG's own published materials state that "Use and distribution of LSEG data requires a
    licence from LSEG and/or its licensors" (search extract, LSEG WMR documents; not a clause by
    clause licence).
  - **The RBA terms cannot clear this series.** The 2026-10-18 proposal that it was CC BY was
    wrong.
- **The 1-month BAB is ASX material.** This confirms the suspicion OD-0013 item 2 recorded.

**Other F11 caveats:**
- The exchange-rate page says "These data should not be relied upon for any regulatory or
  commercial purposes".
- "Exchange rates are published daily except on public and bank holidays observed in New South
  Wales" (<https://www.rba.gov.au/statistics/frequency/exchange-rates.html>, accessed
  2026-10-25, no date shown).

## 2. NY Fed: terms and the API

**Terms:** <https://www.newyorkfed.org/privacy/termsofuse>, "Last Updated: 6/9/2023", accessed
2026-10-25. The extracts confirm the 2026-10-18 reading.

| Clause (short extracts) | Operation it supports |
|---|---|
| "a non-exclusive license … to use, copy, and distribute Content" "for your personal or business purposes" | internal compute; `hio_internal` |
| "Access the Content, manually or through an automated process or device," provided it does not impair the site | **fetch (automated): explicit** |
| "Download, store, and use Content in any format or media" | store raw; store derived; rebuild |
| "Modify and create derivative works from the Content"; modified content must be clearly labelled | derivation, with a **labelling condition** |
| Republication: "The [DATA NAME] is subject to the Terms of Use posted at newyorkfed.org." plus a disclaimer that the New York Fed "does not [sanction] or [endorse] any particular republication" | a condition for any republication (not `hio_internal`) |
| SOFR "calculated using data provided under a license granted to the New York Fed by DTCC Solutions LLC"; DTCC and its sources "have no liability" | a liability disclaimer, not a consent requirement |
| "Third-party content the New York Fed publishes … the New York Fed may only allow you to view those materials as they appear" | **open point:** whether SOFR counts as third-party content. The SOFR clause above presents SOFR as NY Fed content calculated from licensed inputs. Owner judgment needed |
| "certain Content is subject to more specific restrictions on use" (named: Blog posts) | none named for reference rates |

**API (manual sample, 2026-10-25T01:07Z):**
- `https://markets.newyorkfed.org/api/rates/secured/sofr/last/5.json` and
  `…/api/rates/all/latest.json` are **keyless**. `markets.newyorkfed.org/robots.txt` is empty.
- SOFR fields: `effectiveDate`, `percentRate`, percentiles, `volumeInBillions`,
  `revisionIndicator`, `type`.
- SOFR Index (`SOFRAI`) fields: `effectiveDate`, `index`, the 30-, 90- and 180-day averages,
  `revisionIndicator`.
- **There is no publication timestamp in the payload**, so captured vintages are
  `captured_on_schedule`, not `publisher_timestamp`.
- The API documentation page did not render through the fetch tool. Its endpoint conventions
  are taken from the responses, not the documentation.

## 3. Timing, revisions and date labels (evidence for R2/R4)

| Series | Evidence | Finding |
|---|---|---|
| AONIA | methodology (<https://www.rba.gov.au/mkt-operations/resources/cash-rate-methodology/>, "last updated 21 July 2026"): published "prior to 9.20am AEST/AEDT for each day that RITS is open"; the rate is "the rate applicable on the business day preceding the Publication Date"; republication "up until 04.00pm AEST/AEDT on the Publication Date", after which the RBA "will not revise". Publication is **on market data services**; the website table is a separate channel | **in arrears**; final at 16:00 Sydney |
| AONIA website timing | F1 CSV `Last-Modified` 2026-10-22T21:59:28Z = **08:59 AEDT on Fri 23 Oct**. The Fri 23-Oct row had the Cash Rate **empty** and the TRI **filled**; the Thu 22-Oct row's Cash Rate was filled | **F1 rows are labelled by the rate's applicable date** (`valid_time` = b), and the website already had b's rate at 08:59 on b+1. One observation, not a schedule: evidence only that the website can precede 09:20 |
| AONIA fallback | the methodology names fall-back procedures; the F1 expert-judgement CSV lists types A (last published rate), B (new Cash Rate Target) and C (expert rate), dated, including 2026-07-31, 2026-10-02 and 2026-10-05 (type A) | capture the expert-judgement CSV beside F1, as a quality flag; **a type-A day repeats the prior rate by design and must not trip the staleness gate** |
| AONIA rounding | "rounded to two decimal places" | exact under RA §3.2 |
| Cash Rate TRI | "measures the performance of an investment earning the Cash Rate, where interest is reinvested"; base "4 January 2011 = 100"; non-business days accrue at the preceding business day's rate; it "applies on the Publication Date" (the 23-Oct row was filled at 08:59) | **labelled by publication date, not by rate date**: the triangulation must shift one RITS day |
| AUD/USD (F11) | "4.00 pm (Sydney)" (definitions page); F11.1 `Last-Modified` 2026-10-23T05:43:38Z = **16:43 AEDT** with the 23-Oct row filled | **the fixing is Sydney local time, AEDT in summer**. This resolves OD-0013's DST question, subject to owner verification. Publication can precede the indicative 17:00 |
| SOFR | additional information page, "Last updated: 10/5/2026": "published one business day following its value date"; averages and index "shortly after the SOFR is published at approximately 8:00 a.m. ET"; revision "at approximately 2:30 p.m. ET", "only if the change in the rate exceeds one basis point and only on the same day"; "a footnote would indicate the revision"; SOFR "rounded to the nearest basis point"; ACT/360 | in arrears; final after about 14:30 ET; `revisionIndicator` in the API |
| SOFR Index | "initial value set to 1.00000000 on April 2, 2018"; in the sample, `SOFRAI` had `effectiveDate` 2026-10-23 while the latest SOFR was 2026-10-22 | **labelled by publication date**, like the RBA TRI |

## 4. Calendars (evidence for R2)

| Calendar | Evidence | Finding |
|---|---|---|
| RITS (AONIA) | RITS business hours (<https://www.rba.gov.au/payments-and-infrastructure/rits/business-hours.html>, no date shown): closed "on weekends" and on New Year's Day, Australia Day, Good Friday, Easter Monday, Anzac Day, King's Birthday, Christmas Day and Boxing Day "where they are observed in NSW and Victoria". An RBA RITS document (search extract) says RITS stays open on Sydney-only holidays (NSW Bank Holiday in August, NSW Labour Day in October); NSW added a Monday-after-Anzac holiday in 2026 and 2027 (RITS Advice 02/2026, search extract) | **RITS days ≠ NSW days.** AONIA exists on NSW-only holidays, when no F11 fixing exists. This confirms the `cash.aud.overnight` calendar issue (readiness §2): rate selection must use RITS (RA §3.2 step 2). The annual list is at `/schedules-events/bank-holidays/` (not retrieved) |
| NSW (F11, joint calendar J) | "published daily except on public and bank holidays observed in New South Wales" | the J calendar = NSW business days |
| SIFMA (SOFR) | "not published on, or for, days for which SIFMA recommends a full closure" | the SIFMA recommendations themselves (SIFMA terms) not yet read |

## 5. Recommendation: stage S1b (for the owner's decision)

**The evidence changes the readiness assessment's E1.** It recommended starting with "RBA and
NY Fed", on the assumption that RBA's AUD/USD was RBA material. It is not. So the primary
factor `fx.usd_cash_vs_aud.excess` **cannot be cleared by any publisher terms read so far**.

**The three originally approved triangulations** (HIO-ADR-0010 rev 3, S1-A10):

| Triangulation | Its blocking input | Status |
|---|---|---|
| FX: RBA vs H.10 | RBA side is WM/Reuters (third party); H.10 is weekly, and its DDP is being removed in "the week of November 9" ([H.10 page](https://www.federalreserve.gov/releases/h10/), "Last Update: October 19, 2026"), leaving FRED (other terms, an API key) | **blocked** on both legs as a capture design |
| AUD cash vs bills | the 1-month BAB is ASX material; the RBA Treasury Note column is empty | **blocked** (ASX consent needed) |
| USD cash vs bills | US Treasury terms not located (2026-10-18) | **unresolved**, not researched today |

**Proposed staging:**
- **S1b-1, cash legs only.** Capture AONIA and its expert-judgement flags, the Cash Rate TRI,
  SOFR and the SOFR Index: two publishers, all publisher-sourced. Outputs:
  - `cash.aud.overnight` and `cash.usd.overnight` releases at `as_captured_by_hio`;
  - two publisher-index triangulations, **added alongside** the approved bill triangulations,
    each with an expected difference of about zero: the index ratios against the compounded
    legs, after the one-day label shift.

  This starts the capture clock for the two series whose point-in-time record matters most
  (in-arrears rates with same-day republication), and **needs no third-party consent**.
- **S1b-2, the FX leg.** It is gated on an owner decision about the FX source:
  1. a WM/Reuters licence or written consent (vendor contact: owner only);
  2. FRB H.10 as the primary fixing, via FRED (a key, and a different `knowable_at`: weekly);
  3. a new official source, for example ECB euro reference rates crossed to AUD/USD (not yet
     registered or researched);
  4. a written RBA answer on redistribution of F11.

  The cost of delay is small: spot FX revisions are rare [EXT], so a later start loses less
  point-in-time evidence than a delayed cash-rate start would.
- **The bill triangulations** follow when their rights clear: Treasury terms, and ASX consent
  or a substitute.

**Implications for HIO-ADR-0010 rev 3:**
- It names "real-source adapters (RBA, NY Fed, US Treasury, FRB H.10)", "the three
  triangulation reports" and S1-A1…A16 as S1b acceptance. Its consequences name "a triangulation
  of RBA and Federal Reserve FX fixings".
- Staging, a changed FX source, or a changed triangulation set therefore needs **an ADR
  revision (rev 4), approved by the owner**. An implementation-plan edit alone is not enough.
- **Adding** the two publisher-index triangulations needs no ADR change. **Deferring** the
  three approved ones to S1b-2 or later does.
- **The primary factor's spec input changes** if FX moves off RBA F11
  (`fx.usd_cash_vs_aud.excess` observations, `rba.fx.audusd_4pm`). That is a spec version
  change, and possibly a change to the RA-INV-007 quote convention if the new source quotes
  AUD per USD.
- None of this changes an approved standard or the return mathematics.
