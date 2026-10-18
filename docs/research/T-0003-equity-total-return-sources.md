---
id: HIO-RESEARCH-T0003
title: "T-0003 research: equity total-return source scorecard"
status: draft              # research findings; no vendor contacted; no decision made
owner: owner (decides; HIO-ADR-0011); researched by claude/documentation-agent
created_at: 2026-10-18
task: T-0003 (authorised OD-0009; begun on OD-0010)
method: >-
  Published terms pages and search extracts only, retrieved 2026-10-18. No vendor was contacted,
  no account opened, no data downloaded. Third-party copies of terms are labelled as such.
---

# T-0003 research: the first equity total-return source

> **Rule from HIO-ADR-0007 / RA v0.2 §5:** an adjusted-close series of undocumented method is
> `price_only`. No such proxy may become a total return.

## Scorecard

| # | Option | Return construction (`series_class`) | Rights (published terms) | History; timeliness; corporate actions | Cost | Exit |
|---|---|---|---|---|---|---|
| 1 | **S&P DJI index levels** (S&P 500 TR, net TR) | `total_return` of the *index* itself; no fund fees | Third-party copies of the S&P DJI website terms: "personal, non-commercial purposes"; prior written consent to copy, distribute or create derivative works; no use with investment products. Institutional licences forbid redistribution. **A paid data licence would be needed** (third-party copies, not S&P's current page) | full index history; provider methodology | **quote needed** (not obtained) | per licence |
| 2 | **Licensed EOD vendor** (e.g. EODHD): prices, dividends and splits for a US-listed S&P 500 ETF | `total_return`: **market-price TR of an investable ETF**, built by HIO per RA §3.1 from *unadjusted* closes plus explicit distributions | EODHD terms (no date shown): "Non-Professional User … solely in a personal capacity" may "store, manipulate, and analyze the data for private, non-commercial purposes". Redistribution, retransmission and display are prohibited. **Open:** whether SMSF trustee use counts as "personal"; whether derived returns may appear in a trustee pack; post-termination retention is not addressed. Whether raw versus adjusted prices are supplied is not stated on the terms page | to be checked per vendor; dividend completeness must be validated against issuer distribution history | subscription tiers exist [EXT]; **quote and tier needed** | export before termination (terms silent) |
| 3 | **Issuer NAV and distribution files** (iShares) | `total_return`: **NAV TR of the fund** (fees embedded; not the index) | US site terms prohibit "creat[ing] a database by systematically downloading and storing Content" and "screen scraping … any robot". Report-tool downloads are "for your internal use only" (search extracts; regional terms vary) | issuer history; authoritative distributions | free | — |
| 4 | **Kenneth French US market** (Mkt-RF + RF) | `reference_academic`: the CRSP all-US value-weighted market, **not the S&P 500** | footer copyright only; no use terms stated; data derived from licensed CRSP (US) and MSCI/Bloomberg (international) | monthly and daily; **"we reconstruct the full history of returns each month"**, so it is not point-in-time and needs vintage capture; missing values are coded −99.99 / −999 | free | — |
| 5 | **ES futures rolled excess + collateral** | `excess_return` / `total_return` (RA §8) | per futures data vendor (S4 PoC) | per vendor | per vendor | per vendor |

## Assessment (Claude's recommendation, not a decision)

- **Option 2 is the most direct route** to an investable, HIO-constructed equity TR without an
  index licence. **It is blocked on one question:** the vendor's professional/personal
  classification for SMSF trustee use, and the right to show derived returns in a trustee pack.
  This needs a written vendor answer.
- **Option 3** is the best *triangulation* reference (an authoritative distribution history).
  The issuer's terms appear to forbid systematic collection, so use it only for manual,
  occasional checks, if at all.
- **Option 1** is the cleanest object, but a commercial licence, so likely the most expensive.
- **Option 4** is useful only as a labelled academic reference, with vintage capture, given
  its monthly history rewrites.
- **Option 5** belongs with the futures PoC.

## Not done (acceptance Q2/Q3 of T-0003)

- **No vendor response obtained** (Q2): EODHD and S&P DJI need written questions on
  professional status, derived-data display and post-termination retention.
- **No HIO-ADR-0011 drafted** (Q3). That follows the vendor answers and the owner's choice.

## Questions to send, if the owner approves contacting vendors

1. Is use by an individual trustee of a two-member SMSF "personal / non-professional"?
2. May returns HIO computes from your prices and dividends be shown, as derived figures, in a
   private trustee report?
3. What may be retained after cancellation?
4. Are unadjusted closes, and separate dividend and split records, provided for US ETFs?
