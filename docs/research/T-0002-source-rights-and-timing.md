---
id: HIO-RESEARCH-T0002
title: "T-0002 research: rights, coverage and publication timing of the S1 sources"
status: draft              # research findings for owner verification; NOT owner_verified
owner: owner (verifies); researched by claude/documentation-agent
created_at: 2026-10-18
task: T-0002 (authorised OD-0009; begun on OD-0010)
method: >-
  Read publishers' published terms and documentation pages only (WebFetch/WebSearch,
  retrieved 2026-10-18). No data file was downloaded, because the owner ruled out live data
  operations. Quotations are the fetch tool's extracts of the pages and must be checked against
  the live page before owner verification.
---

# T-0002 research: S1 source rights and timing

> **Not verification.** These are the publishers' own published statements, as read by an
> agent. Under the rights standard §3 they count as `vendor_asserted`, which still **refuses
> every operation** until the owner records `owner_verified` (section, date, URL).

## 1. Findings by source

### 1.1 Reserve Bank of Australia (RBA)

**Terms:** <https://www.rba.gov.au/copyright/> (no "last updated" date shown).

- RBA material is under **CC BY 4.0**. Attribution: "Source: Reserve Bank of Australia [year]".
  It must not imply endorsement.
- **"Cash Rate"** (the Interbank Overnight Cash Rate) is a separately named item. It may be
  used for personal or commercial purposes "only if it is not stated, represented or in any
  way implied" that the RBA endorses the use.
- **"Financial Data"** is "information, rates, facts or knowledge represented in numerical or
  statistical form … published by the RBA other than the Cash Rate". The RBA "does not
  administer [it] as a benchmark", "may withdraw, modify or amend" it without notice, and users
  "assume the entire risk".
- **Third-party material** "may not be reproduced, published, communicated to the public,
  adapted … or otherwise used" without the third party's consent.
- **Not addressed:** automated access and scraping.
- **Exchange-rate page caveat** (<https://www.rba.gov.au/statistics/frequency/exchange-rates.html>):
  "These data should not be relied upon for any regulatory or commercial purposes."

**Timing:**

| Series | Finding | Source |
|---|---|---|
| Cash rate (AONIA) | published "prior to 9.20am AEST/AEDT for each day that RITS is open". It applies to the **preceding business day**. Republication is possible until **4.00pm AEST/AEDT on the publication date**; after that, no revision. The RBA also publishes a **Cash Rate Total Return Index (TRI)** | <https://www.rba.gov.au/mkt-operations/resources/cash-rate-methodology/> (last updated 21 July 2026) |
| AUD/USD | "a representative mid-point … on the basis of quotations in the interbank foreign exchange market at **4.00 pm Australian Eastern Standard Time**"; published on weekdays except NSW public and bank holidays. **Open:** "Standard Time" all year, or local time during AEDT? | search extract of RBA exchange-rate notes (the primary note was not retrieved) |
| Release times (indicative) | Exchange Rates – Daily **5.00 pm**; F1 Money Market – Daily **9.15 am**; F2 Government Bonds: **weekly, Fridays**, "for daily yields up to 2 business days earlier", 2.00 pm. No time zone stated | <https://www.rba.gov.au/schedules-events/frequency-statistical-releases.html> |
| F1 1-month bank-accepted bill | **source not determined.** Bank-bill rates are commonly ASX BBSW-derived [EXT], which would make them third-party material needing ASX consent. The table notes sit inside the data file, which was not downloaded | — |

### 1.2 Federal Reserve Bank of New York (SOFR)

**Terms:** <https://www.newyorkfed.org/privacy/termsofuse> (last updated 9 June 2023).

- A licence "to use, copy, and distribute Content".
- "Download, store, and use Content in any format or media"; "Modify and create derivative
  works", with modified content clearly labelled.
- Automated access is permitted: "manually or through an automated process or device", provided
  it does not impair the site.
- Redistribution carries the same permissions and conditions.
- Reference-rate republication requires the notice "… is subject to the Terms of Use posted at
  newyorkfed.org", and a disclaimer that the New York Fed does not sanction or endorse the
  republication and has no liability.
- No use of the New York Fed's name for endorsement. SOFR is calculated from DTCC-licensed data.

**Timing** (<https://www.newyorkfed.org/markets/reference-rates/sofr>;
<https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates>,
last updated 5 October 2026):
- published each business day at about **8:00 a.m. ET** for the previous business day;
- revisions only **on the same day**, at about **2:30 p.m. ET**, and only if the change
  **exceeds one basis point** (a revised rate carries a footnote);
- calendar: **SIFMA US government securities** (not published on SIFMA full-closure days);
- first value date **2 April 2018** (first published 3 April 2018);
- the NY Fed also publishes a **SOFR Index** (1.00000000 on 2 April 2018).

### 1.3 US Treasury (daily bill rates)

- **Terms:** no reuse or copyright statement was found on
  <https://home.treasury.gov/subfooter/site-policies-and-notices> or the interest-rate pages.
  US federal government works are generally not subject to copyright (17 U.S.C. §105) [EXT,
  legal presumption, not verified for this data].
- **Timing:** "indicative closing market bid quotations on the most recently auctioned Treasury
  Bills", obtained by the NY Fed "at approximately 3:30 PM each business day"
  (<https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics>).
  The posting time is not stated on that page. Search extracts mention yield curve rates
  "usually" posted by about 6:00 PM ET [unconfirmed for bills]. The bank discount rate uses a
  360-day year.

### 1.4 Federal Reserve Board (H.10)

- **Terms:** <https://www.federalreserve.gov/disclaimer.htm> (last updated 2 August 2024).
  "Unless otherwise indicated, information on Board's website is in the public domain and may
  be copied and distributed without permission. Please cite to the Board as the source."
  Third-party material needs that party's permission. Automated access is not addressed.
- **Timing:** <https://www.federalreserve.gov/releases/h10/>.
  - "On Mondays at 4:15 p.m." the Board releases the daily rates, i.e. **weekly**, so a daily
    value is first knowable up to about a week later.
  - The Board's Data Download Program is being retired, in favour of FRED (separate terms, API
    key).
  - The weekly release ceased from 22 May 2006 to January 2009.

## 2. Proposed rights records

These are proposed values for the owner to verify. All carry `verification: vendor_asserted`
in `registers/sources.yaml`.

| Permission | RBA cash rate | RBA AUD/USD (F11) | RBA 1m BAB (F1) | NY Fed SOFR | Treasury bills | FRB H.10 |
|---|---|---|---|---|---|---|
| automated_retrieval | unknown (not addressed) | unknown (not addressed) | unknown | **allow** | unknown | unknown (not addressed; DDP retiring) |
| raw_retention | allow (CC BY) | allow (CC BY) | **unknown (possible third party)** | allow | unknown (§105 presumption) | allow (public domain) |
| internal_compute / derivation | conditional (no implied endorsement) | allow (CC BY) | unknown | allow (label modified) | unknown | allow |
| derived_storage | allow | allow | unknown | allow | unknown | allow |
| external_processing (CI, cloud) | allow (no restriction found) | allow | unknown | allow | unknown | allow |
| distribution.hio_internal | allow | allow | unknown | allow | unknown | allow |
| distribution.smsf_trustee_pack | conditional (attribution; no endorsement) | conditional (attribution; note the "not for commercial purposes" caveat) | unknown | conditional (notice + disclaimer) | unknown | conditional (citation) |
| quotation_in_documents | conditional (attribution) | conditional (attribution) | unknown | conditional (notice + disclaimer) | unknown | conditional (citation) |
| agent_context | allow (CC BY) | allow | unknown | allow | unknown | allow |
| post_termination_* | n/a (no subscription) | n/a | n/a | n/a | n/a | n/a |
| attribution_required | "Source: Reserve Bank of Australia [year]" | same | — | notice + disclaimer text | — | cite the Board |

**Blocking for S1b live fetch** (`automated_retrieval` is unknown): RBA (all series), Treasury and
FRB H.10. **Only SOFR is explicitly cleared for automated access.** The owner may:
- judge that the absence of a prohibition, together with CC BY or public-domain status,
  suffices (an owner decision, recorded with reasoning);
- ask the publishers; or
- use an alternative channel.

## 3. Proposed spec patches (R4): NOT applied, pending owner verification

1. **`cash.aud.overnight`:**
   - regime **in arrears**;
   - `knowable_at` for rate_b = the publication before 09:20 Sydney on the next RITS business
     day, **final at 16:00 Sydney** (republication window);
   - captured vintages should record both;
   - calendar: RITS business days.
2. **`cash.usd.overnight`:**
   - `knowable_at` = 08:00 ET on the next SIFMA business day, final after the 14:30 ET
     revision window;
   - calendar: SIFMA US government securities;
   - history from value date 2018-04-02.
3. **`fx.usd_cash_vs_aud.excess`:**
   - fixing at 16:00 AEST, with the DST question open;
   - published about 17:00 Sydney;
   - calendar: NSW business days.
4. **Triangulation references** (replace or supplement bills):
   - AUD cash against the **RBA Cash Rate TRI**, and USD cash against the **NY Fed SOFR Index**;
   - both are publisher-computed compounded indices of the same rate, so the *expected
     difference is ~0*, apart from day-count and rounding conventions;
   - this is a much stronger check than bills, and avoids the BAB third-party question.

## 4. Open questions for the owner

1. Is **automated retrieval** acceptable for RBA, Treasury and H.10 where the terms are silent?
   Or should the publishers be asked?
2. The **RBA 1m BAB:** confirm its source (the table notes), or drop it in favour of the TRI.
3. The **RBA 4.00pm "AEST" during daylight saving:** ask the RBA, or infer from captured data at
   S1b.
4. **H.10:** keep it (weekly, about a week lagged), or use another FX reference?
5. Accept the §2 values as `owner_verified`, recording the section, date and URL, per source.
