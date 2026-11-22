---
id: HIO-EVIDENCE-FACTORS-BUILD-4
title: "Hedge-ratio sweep on the US equity leg for an Australian investor: descriptive, on the local AUD series"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0217
---

# Factor builds 4: the hedge-ratio sweep

> **Exploratory, descriptive and unaccepted.** It reports one sample and recommends no hedge ratio. No value from the series is recorded here (OD-0210): the sweep is in local files for the owner. The H.10 rate is from the Board of Governors of the Federal Reserve System; the cash history is from the Reserve Bank of Australia. No endorsement by either is implied.

## What was run

`tools/hedge_sweep.py` (worker W1, checked `56f5ccc` on its second attempt) on the builds of `build-1.md` and `build-3.md`: the SPY USD series as the asset, the reconstructed AUD cash series and BIL as the two cash legs, and the H.10 archive, pinned by hash. Hedge ratios 0, 0.25, 0.5, 0.75 and 1, per RA §4.3: `R(h) = (1 + R_f)(1 + s) − 1 − h (s − f)`, with the forward CIP-implied. For each ratio: annualised return, volatility, the worst drawdown and the worst month, for the asset alone and for a 60/40 portfolio with the hedged IEF series. It also reports the sample's minimum-variance hedge ratio for the asset alone, labelled in-sample and descriptive.

- **Identities, every period:** `R(0)` equals the unhedged return, `R(1)` the fully hedged return, and `R(h)` is linear between them. All hold.
- **Local output:** `~/.hio-research/analytics/hedge-sweep-spy60-ief40h/sweep.json` (sha256 `395601906a6bbec20248db30115aa9c7c233b0f965ff3afcaf7b6c201c45ca31`) and `sweep.csv` (sha256 `2114c9a4c3afba571ae7ea053193c3d6c7c1ad92ef1f7cbcd795d036625b7560`).

## Checks on the real data, beyond the worker's tests

- **Independent recomputation.** A separate script built `R(h)` for each grid ratio and for the reported minimum-variance ratio from the independently verified unhedged and hedged series, in exact arithmetic, and computed monthly volatility. Every figure agrees with the tool within 1e-9.
- **Agreement with the earlier tools.** At ratios 0 and 1 the asset's figures equal those the analytics tool gave for the unhedged and hedged builds.

## First attempt rejected

`hiomux check` rejected the worker's first commit: one test asserted that a year from its invented dates never appears in the output, and a printed sha256 contained those digits by chance in the check's checkout. The tool was unchanged in the second attempt; the test now ignores the hash lines. Claude's command chain had integrated the rejected commit before reading the check result; that commit was removed and the sweep rerun from the accepted one. The two runs' output hashes are equal.

## Limits

As `build-3.md`: the forward is implied from a rate differential with a bill fund as the USD rate, with no hedge cost; a reset every period; a noon fix against a 4 pm close; one vendor's unvalidated prices. **The minimum-variance ratio is a property of this sample** (about nineteen years, one large crisis), with no out-of-sample test. It is not advice.

## Not established

That any hedge ratio is better than another for any investor; that the hedged series approximates an investable return.
