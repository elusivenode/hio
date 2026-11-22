---
id: HIO-RESEARCH-T0024-HEDGE-INCEPTION
title: "Rates lockable at hedge inception: what HIO holds, what it may use, and the cheapest credible anchor (T-0024 package A3)"
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0225
base_revision: 09f255f11259c29ec4531870f5543ba454b5c11f
---

# Hedge inception assessment

> **Proposed.** From the repository, the rights register and the series already held. Nothing was fetched. No value from a licensed series is recorded here; the sizes behind the readings are in the owner's session report.

## The question

The hedged AUD series (`tools/factor_translate.py`, hedged mode) imply each period's forward from the two cash legs' **realised** returns over that period. A real forward is priced from rates known when it is struck. Do such rates exist in sources HIO may already use?

## What the construction does

- **Reset:** every period, the period being consecutive dates common to the fund, both cash legs and a fresh H.10 rate. Most periods are one business day; a weekend is one period; a few span two or more business days because one market was closed.
- **AUD leg:** `cash.aud.overnight_reconstructed`, an overnight accrual.
- **USD leg:** `cash.us.bil.market_total_return`, a bill fund's market return.

## Answer, by leg and tenor

| Need | Held or permitted? | Reading |
|---|---|---|
| AUD overnight, known at the start | **Yes, nearly.** The cash rate target is set in advance, and the realised overnight rate has stayed within a few basis points of it (T-0023's R1). RA §3.2 calls the published rate in arrears, so the label is `replicable_with_basis` | the AUD leg is not the problem |
| USD overnight, known at the start | **Partly.** `nyfed.sofr` is owner_verified (OD-0116) and has been captured since 2026-11-04, but its history, which starts in April 2018, has not been fetched. Before 2018 nothing is permitted: the effective federal funds rate has no rights row | the USD leg is the problem, and it is package B1 |
| One-month rates, for a monthly reset | **USD yes, AUD no.** The Treasury par curve's one-month point is held from 2001 (OD-0156), a government rate. For AUD, the one-month bill and swap columns in the RBA's historical table are third-party columns HIO may not use (OD-0172) | a monthly-reset hedge is not feasible under current rights |
| Market forward points | **No.** None held; no source row | the CIP basis stays unmeasured |

## How much the defect matters

Measured on the held hedged series; sizes not recorded here.

- **It is visible.** The implied one-day forward premium is negative on a material share of days, which a real forward between these two currencies would not have been. It is far noisier than a rate differential can be, and its largest values fall in the last four months of 2008, when bill prices jumped.
- **It is small where the comparisons look.** The premium's variance is a negligible share of the hedged return's, and its long-run average is close to the average rate differential. So the hedged volatilities and correlations reported as diagnostics in `build-6.md` and `build-8.md` are unlikely to move materially with a proper USD rate.
- **What a proper rate cannot fix:** the CIP basis, forward spreads and the reset convention. Those need a market anchor, not a better cash leg.

## Recommendation

1. **Keep the label.** Both hedged specs are marked diagnostic-only at 0.1.1 (OD-0225). The series are unchanged.
2. **Anchor with a traded hedged fund before building anything.** The specs already name "an AUD-hedged share class of a comparable fund" as the triangulation reference. An ASX-listed AUD-hedged S&P 500 fund [EXT] is in the vendor's symbol list HIO holds, and its unhedged twin (IVV) is already in snapshot `s2`. One fetch of that symbol under the existing vendor row (and, if the owner wants the bond side too, one AUD-hedged US Treasury fund) would give a market-realised hedged return to set the CIP-implied SPY series against, with an expected-difference model (fund and index differences, fees, the fund's own reset). That measures the whole gap, basis and costs included, which a better USD rate alone would not.
3. **Then decide on B1 and B2** by the size of that gap. If it is small, the diagnostic label can be narrowed to "CIP-implied, anchored against a traded fund over its history" without a new cash leg. If it is large, a SOFR history fetch (from 2018) is the next step, and pre-2018 hedged figures stay diagnostic.

## Limits

- The traded fund's history is shorter than SPY's [EXT, not checked]; it anchors only its own span.
- The same symbol list names AUD-hedged US Treasury funds too [EXT; their maturity ranges and histories are not checked]. One of them could anchor the IEF series if its maturities are close to IEF's; if not, IEF is anchored only by analogy.
- One vendor, unvalidated, for the anchor too.

## Not proposed

A monthly-reset hedge, a paid forward-points feed, or any change to the hedged series now.
