---
id: HIO-ADR-0010
title: The first slice is a cash and FX walking skeleton; equity total return moves to S2
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [HIO-S1 approval]
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
| **S1 = walking skeleton + cash legs (AUD, USD) + an investable FX position (USD cash held by an AUD investor); equity TR is S2, gated on T-0003** | every later factor needs these legs (excess returns, hedged returns, futures collateral). All S1 sources are official and keyless [EXT]; the capture clock starts now |

## Decision (proposed)

Option 3. Detail in [`../implementation-plan.md`](../implementation-plan.md).

## Consequences

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

_Unapproved._
