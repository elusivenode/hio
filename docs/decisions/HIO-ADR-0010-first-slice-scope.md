---
id: HIO-ADR-0010
title: "The first slice is a cash and FX walking skeleton in two stages: S1a synthetic-fixture-only, S1b live data; equity total return moves to S2"
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [G1 completion, S1a authorisation, S1b authorisation]
revision: 3   # rev 1 (blob fe651aca746d at a82aa0d) returned by OD-0008; rev 2 at f2275e2; rev 3 clarifies the S1a gate (OD-0010)
review_record: null
---

# HIO-ADR-0010: first-slice scope

## Context

- The owner's expected S1 included "cash/FX/validated equity total-return".
- The 18 October proposal's S1 relied on "a declared, licensable stand-in" for S&P 500 total
  return, without identifying one. RBA and US Treasury data cannot produce an equity total
  return.

Equity total-return sources assessed. All of the following is [EXT] and unverified:

| Source | Total return? | Problem for S1 |
|---|---|---|
| yfinance `Adj Close` | approximately, with an undocumented adjustment | unofficial, no licence, retroactive revisions ([OBS] `macsmsf` `sql/043`); **rejected** |
| S&P DJI index levels (TR, net TR) | yes, the true index | licensed; cost and terms unknown |
| Issuer NAV + distribution history files (US-listed S&P 500 ETF) | NAV TR of an investable fund: not the index; fees embedded | website terms unknown; retrieval possibly scraping |
| Licensed EOD vendor (prices + dividends + splits) | market-price TR of an investable ETF | procurement needed; rights to store and derive unknown |
| Kenneth French US market return | TR of the CRSP US market, **not the S&P 500** | academic data from licensed CRSP inputs; terms unknown |
| ES futures rolled excess + collateral | investable excess return | needs futures data (the PoC, later slice) |

None of these is verified as usable within S1's timeframe.

## Options

| Option | Assessment |
|---|---|
| S1 with equity via an unverified stand-in | violates HIO-ADR-0005 and 0007; **rejected** |
| Delay S1 until an equity source is procured | delays the irreversible part (PIT capture) for a reversible part; **rejected** |
| **S1 = walking skeleton + cash legs (AUD, USD) + an investable FX position (USD cash held by an AUD investor); equity TR is S2, gated on T-0003** | every later factor needs these legs (excess returns, hedged returns, futures collateral). All S1 sources are official and keyless [EXT]; the capture clock starts at S1b (revision 2) |

## Decision (proposed, revision 3)

Option 3, delivered as **two separately authorised stages**:

| | **S1a: synthetic-fixture foundation** | **S1b: live official observations** |
|---|---|---|
| Purpose | make every A01 contract executable before real data touches it | start point-in-time capture of the official S1 sources |
| Includes | the `hio` repository and history-preserving migration (operating model §8.1); CI; contracts; a **local-filesystem object-store adapter**; the observation, vintage and knowability model with the three query modes; manifest-derived catalogue; the three S1 constructions; the rights gate and publication gate, exercised **only with synthetic sources and fixtures** | real-source adapters (RBA, NY Fed, US Treasury, FRB H.10) behind the rights gate; a cloud bucket with scoped keys; scheduled capture; the soak; the three triangulation reports |
| Excludes | **any network fetch or live data operation**; real sources; credentials; buckets; schedules | equity, bonds, futures; publication beyond `hio_internal` |
| Acceptance | OBS-INV-001…007; RA §3.2 fixtures and CASH-USD-INV-3; FXC-INV-1…4; RA-INV-021; releases §6.1; rights fail-closed fixtures for fetch, store raw, build, store derived, rebuild and publish (synthetic); import and independence checks; reproducible rebuild; harness CI checks; Codex review at an assigned head | S1-A1…A16 of the implementation plan against real sources, including the soak (S1-A13) and the triangulations (S1-A10) |
| Entry gate | **G1 complete** (including approval of this revised ADR) **and a future, separate owner authorisation of S1a's scope**, recorded in its own owner decision record. OD-0009 *requires* that authorisation; it is **not** that authorisation, and no record yet authorises S1a | S1a accepted; **T-0002 `owner_verified` rights for every operation S1b performs, per source**; publication timing, calendars and the AUD rate regime evidenced; the owner authorises S1b's scope and infrastructure |

**S1a authorises no live data operation.** G1 completion does not by itself authorise S1a, and S1a
acceptance does not by itself authorise S1b. The implementation plan's S1 section remains a
recommendation, and will be updated to this split once this ADR is approved.

## Consequences

- The point-in-time capture clock starts at S1b, not at S1a. T-0002 runs in parallel so that S1b
  is not delayed.
- S1's research output is narrow but real:
  - the investable AUD-investor USD cash excess return, decomposed exactly into spot, carry
    and cross term;
  - a triangulation of RBA and Federal Reserve FX fixings;
  - a triangulation of overnight cash versus bills.
- Equity source selection runs in parallel (T-0003) and decides S2's shape:
  - *licensed EOD market-price TR*;
  - or *issuer NAV TR*;
  - or *index licence*;
  - or wait for futures.

## Approval

_Unapproved._ Revision 1 was returned by OD-0008. Revision 2's S1a gate wording was corrected on the owner's instruction (OD-0010). **This revision 3 awaits the owner's revision-specific decision.**

## Changelog

- 2026-10-18: created (85ef0fa).
- 2026-10-18: revision 2, split into S1a (synthetic-fixture-only) and S1b (live data), as the owner requested in OD-0008.
- 2026-10-18: revision 3, the S1a entry gate states that a future, separate owner authorisation is required, and that OD-0009 is not it (OD-0010).
