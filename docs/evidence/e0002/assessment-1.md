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

| Instrument | Q1 to Q3 | Built return against the vendor's adjusted-close return (1 bp bar) | Notes |
|---|---|---|---|
| SPY.US | pass | nearly every period within the bar | |
| VTI.US | pass | nearly every period within the bar | |
| IEF.US | pass | every period within the bar | |
| BIL.US | pass | every period within the bar | **Some calendar years carry no distributions.** Plausible at near-zero yields; unverified. Added as the cash sleeve |
| VAS.AU | pass | nearly every period within the bar | "Special Event" records present |
| IVV.AU | pass | nearly every period within the bar | "Special Event" records present |
| BGBL.AU | pass | nearly every period within the bar | **A record differs from the issuer** |
| AUDUSD.FOREX | not assessed | n/a | weekend rows present; market-maker data. Not a fixing, so not used |

> **Redacted 2026-11-22 (F-REVIEW-2026-11-22-e0004-1-2, OD-0206):** the counts and date spans taken or computed from EODHD data were removed from this file and replaced by readings. They stay in the owner's local report. Earlier revisions in git history still hold them (OD-0196).

Symbols worked as given. Declaration and record dates are absent on all three ASX funds, and declaration dates on many US rows. Weekdays absent are counted, not judged, because no holiday calendar was applied. First dates sit a few days after inception where the issuer date is known (IEF), so history may start at first trade rather than launch.

## C. Economic validity

**Method:** market-price total return under RA §3.1 and §5, from raw closes, `unadjustedValue` and split factors, on the ex-date.

**Internal check, EODHD against itself:** the periods that differ by over 1 bp are all on action dates, none elsewhere. **Nearly all are explained** by a factor-style adjustment (the vendor adjusts by a price factor; HIO reinvests at the ex-date close). The gaps are largest on volatile ex-dates. This isn't an error in either, and it's no independent validation.

**Independent check: BGBL only, the issuer rows read from the page.**
- Every ex-date matches.
- The amounts match once the issuer's figure is rounded to the vendor's decimals, with the exception below.
- **Unresolved finding F-1: the 2026-07-01 record differs from the issuer's.** The detail is in the owner's local report, not here, because agent use and quotation are denied.

**So the dividend endpoint can't be assumed final,** and the evidence can't size this: the difference is in the only fund checked. **SPY, IEF and BIL, the comparison's sleeves, have no independent check.** Their record counts fit their stated frequencies, which is weak evidence. ASX non-income components aren't exposed separately by the fields used, and franking appears only in a beta feed not tested.

**Issuer check of the sleeves, added at `5bb696d`:** HIO's compounded return for SPY, IEF and BIL against the market-price returns in their public fact sheets to 2026-09-30, and IEF's calendar years 2021 to 2025. **Every check is within the pre-declared 0.10 points a year,** for each of SPY, IEF and BIL. Report sha256 `a3bc4720eb7bb5a75f97674755251dc4984e7eaef5a69bd9fecc722d2654069e`, for the owner. **It reaches back only to September 2016,** so 2008, BIL's zero-distribution years and everything earlier stay unchecked. It tests income in aggregate, and one small missing payment over ten years stays inside the bar. The fact sheets aren't committed: State Street's restrict reproduction.

**No series here is economically validated.** The quote currency of all seven funds matches the exchange listing, the listing being EODHD's own. Between `s1` and `s2`, minutes apart, no close or distribution changed, which says little: a later snapshot is the real test.

## D. Technical suitability

24 requests in under a minute per snapshot, no failures, far inside the limits. 5.9 MB in all. Simple JSON, and one tool of about 650 lines including the comparison. Data flowed into HIO's releases and through the reader's checks with no change to contracts. Not tested: symbol changes, incremental updates, repeat-snapshot stability. **Provenance stays unresolved:** EODHD's published statements conflict on whether closes come from exchange feeds, and no letters were sent (OD-0161), so nothing settles it. An independent price source isn't available. **An additional independent source is needed** for anything beyond exploration.

## E. Portfolio demonstration

The comparison ran on the common daily periods from mid-2007 to the snapshot date, BIL setting the start. All three allocations; full, before and from 2020, and 2008, Q1 2020 and 2022. Wealth reconciled in every window. **Results are the owner's to read.** Limits: three named funds and one history, no trading costs or tax, BIL isn't overnight cash, IEF validates no factor, and about six non-overlapping three-year periods. It isn't a recommendation or forecast. F-1 is in a fund outside the comparison, but these three are unchecked.

## E2. AUD variant (V2)

Ran at `475173b`: the three allocations, unhedged, monthly, on H.10's noon New York rate, 2007-05-31 to 2026-10-30, 233 months, all windows available. Results are the owner's to read, in `reports/owner-report-aud.md`. H.10 manifest sha256 `07cff3c0929a96bdfe8938c3f1f9242777621f9bbe39deb0515202d816199b21`; summary sha256 `5bb515e36ac3c2c57b8dc42c720d5ddf1a2308c56563b4ad685add216cadf701`. **Archive:** the Australian series is labelled USD per AUD, 13,993 rows from 1971-01-04 to 2026-10-30, with 572 rows holding no value. It has month-end rates from May 2007 on, within the 2006 to 2009 publication gap; earlier in that gap is unchecked. **Rates:** 2 month ends used an earlier rate, the oldest a day old. **EODHD's AUD/USD against H.10:** within 1% on enough of the common dates to pass the declared bar, which can flag but not validate, at different times of day. EODHD's weekend rows sit in that span too. BIL in AUD is USD bills plus currency risk, not AUD cash; it's unhedged, and there's no long AUD cash leg.

## F. Recommendation

**Continue conditionally.**
- **Internal exploratory research:** usable, with the limits above, once SPY, IEF and BIL have an independent distribution check and a second snapshot is clean.
- **Governed releases or SMSF-facing output: not suitable.** The rights record denies it, the commercial licence is over the ceiling, and provenance is unresolved.

## G. Next decision

Keep it until a second snapshot late in the month, then decide before renewal. Cancelling leaves retained data unaddressed by the terms, which is the owner's call then.

## Not established

Accuracy of any closing price against any independent source; whether the vendor accepts this use; whether F-1 is isolated.
