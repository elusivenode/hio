---
id: HIO-EVIDENCE-E0002-ASSESSMENT-1
title: "EODHD evaluation: first consolidated assessment (continue conditionally)"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0162
---

# EODHD evaluation: assessment 1

> **Recommendation: continue conditionally, for internal exploratory USD research only.** One snapshot, one independently checked fund. **No value is recorded here:** the rights record denies agent use and quotation. Claude saw counts, hashes, dates and pass or fail, and hasn't read the portfolio results. They are in `~/.hio-research/E-0002-eodhd/reports/owner-report.md`, for the owner.

Run at `475173b`, snapshot `s2`, compared with `s1`, 2026-11-04, after the remediation of REVIEW-2026-11-04-t0022-1 and VERIFY-2026-11-04-t0022-1-1; values unchanged from `185c33a`. Manifest sha256 `bb40a84650a8b7104e3d116a5d0773619dd4870ee20190a80bab370135fee38d`; summary sha256 `905e4db5de033be01e2c4ee5b87297c356f412656fbe4e67f03323370872fb25`.

## A. Subscription and cost

Historian (EOD Historical All-World), personal. `/user` reports `monthly`. About $19.99 a month as advertised; **the owner confirms the currency, renewal date and cancel control.** Payments are non-refundable. One small key vault (OD-0164) adds a negligible cost. Commercial use is USD 399 or more a month, over the ceiling, so **nothing here extends to SMSF use without a different licence.**

## B. Coverage

| Instrument | First | Last | Rows | Distributions | Splits | Q1 to Q3 | Periods within 1 bp, internal | Notes |
|---|---|---|---:|---:|---:|---|---:|---|
| SPY.US | 1993-01-29 | 2026-11-03 | 8,499 | 136 | 0 | pass | 8,493 of 8,498 | |
| VTI.US | 2001-05-31 | 2026-11-03 | 6,395 | 102 | 1 | pass | 6,388 of 6,394 | |
| IEF.US | 2002-07-26 | 2026-11-03 | 6,108 | 291 | 0 | pass | 6,107 of 6,107 | |
| BIL.US | 2007-05-30 | 2026-11-03 | 4,890 | 128 | 1 | pass | 4,889 of 4,889 | **No distributions in 2010, 2012 to 2015 or 2021.** Plausible at near-zero yields; unverified. Added as the cash sleeve |
| VAS.AU | 2009-05-08 | 2026-11-03 | 4,429 | 70 | 0 | pass | 4,412 of 4,428 | One "Special Event" |
| IVV.AU | 2007-10-10 | 2026-11-03 | 4,823 | 78 | 1 | pass | 4,816 of 4,822 | Four "Special Event" |
| BGBL.AU | 2023-05-09 | 2026-11-03 | 887 | 7 | 0 | pass | 885 of 886 | **One record differs from the issuer** |
| AUDUSD.FOREX | 1979-12-24 | 2026-11-03 | 13,387 | n/a | n/a | not assessed | n/a | 1,242 weekend rows; market-maker data. Not a fixing, so not used |

Symbols worked as given. Declaration and record dates are absent on all three ASX funds, and declaration dates on many US rows. Weekdays absent are counted, not judged, because no holiday calendar was applied. First dates sit a few days after inception where the issuer date is known (IEF), so history may start at first trade rather than launch.

## C. Economic validity

**Method:** market-price total return under RA §3.1 and §5, from raw closes, `unadjustedValue` and split factors, on the ex-date.

**Internal check, EODHD against itself:** 34 periods differ by over 1 bp, all on action dates and none elsewhere. **33 are explained** by a factor-style adjustment (the vendor adjusts by a price factor; HIO reinvests at the ex-date close). The gaps are largest on volatile ex-dates. This isn't an error in either, and it's no independent validation.

**Independent check: BGBL only, 7 issuer rows read from the page.**
- All 7 ex-dates match.
- 6 amounts match once the issuer's figure is rounded to the vendor's decimals.
- **Unresolved finding F-1: the 2026-07-01 record differs from the issuer's.** The detail is in the owner's local report, not here, because agent use and quotation are denied.

**So the dividend endpoint can't be assumed final,** and the evidence can't size this: it's one differing row in the one fund checked. **SPY, IEF and BIL, the comparison's sleeves, have no independent check.** Their record counts fit their stated frequencies, which is weak evidence. ASX non-income components aren't exposed separately by the fields used, and franking appears only in a beta feed not tested.

**No series here is economically validated.** The quote currency of all seven funds matches the exchange listing, the listing being EODHD's own. Between `s1` and `s2`, minutes apart, no close or distribution changed, which says little: a later snapshot is the real test.

## D. Technical suitability

24 requests in under a minute per snapshot, no failures, far inside the limits. 5.9 MB in all. Simple JSON, and one tool of about 650 lines including the comparison. Data flowed into HIO's releases and through the reader's checks with no change to contracts. Not tested: symbol changes, incremental updates, repeat-snapshot stability. **Provenance stays unresolved:** EODHD's published statements conflict on whether closes come from exchange feeds, and no letters were sent (OD-0161), so nothing settles it. An independent price source isn't available. **An additional independent source is needed** for anything beyond exploration.

## E. Portfolio demonstration

The comparison ran: 4,889 common periods, 2007-05-30 to 2026-11-03, BIL setting the start. All three allocations; full, before and from 2020, and 2008, Q1 2020 and 2022. Wealth reconciled in every window. **Results are the owner's to read.** Limits: three named funds and one history, no trading costs or tax, BIL isn't overnight cash, IEF validates no factor, and about six non-overlapping three-year periods. It isn't a recommendation or forecast. F-1 is in a fund outside the comparison, but these three are unchecked.

## E2. AUD variant (V2)

Ran at `475173b`: the three allocations, unhedged, monthly, on H.10's noon New York rate, 2007-05-31 to 2026-10-30, 233 months, all windows available. Results are the owner's to read, in `reports/owner-report-aud.md`. H.10 manifest sha256 `07cff3c0929a96bdfe8938c3f1f9242777621f9bbe39deb0515202d816199b21`; summary sha256 `5bb515e36ac3c2c57b8dc42c720d5ddf1a2308c56563b4ad685add216cadf701`. **Archive:** the Australian series is labelled USD per AUD, 13,993 rows from 1971-01-04 to 2026-10-30, with 572 rows holding no value, and it has rates across the 2006 to 2009 publication gap. **Rates:** 2 month ends used an earlier rate, the oldest a day old. **EODHD's AUD/USD against H.10:** within 1% on 4,772 of 4,863 common dates, which passes the declared bar and can flag but not validate, at different times of day. 1,139 weekend rows sit in that span. BIL in AUD is USD bills plus currency risk, not AUD cash; it's unhedged, and there's no long AUD cash leg.

## F. Recommendation

**Continue conditionally.**
- **Internal exploratory research:** usable, with the limits above, once SPY, IEF and BIL have an independent distribution check and a second snapshot is clean.
- **Governed releases or SMSF-facing output: not suitable.** The rights record denies it, the commercial licence is over the ceiling, and provenance is unresolved.

## G. Next decision

Keep it until a second snapshot late in the month, then decide before renewal. Cancelling leaves retained data unaddressed by the terms, which is the owner's call then.

## Not established

Accuracy of any closing price against any independent source; whether the vendor accepts this use; whether F-1 is isolated.
