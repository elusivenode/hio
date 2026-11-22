---
id: HIO-EVIDENCE-FACTORS-BUILD-3
title: "The AUD view: a reconstructed AUD cash series, unhedged and CIP-hedged AUD series, AUD excess returns, and the analytics and risk model in AUD"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0216
---

# Factor builds 3

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the series and outputs are in local files for the owner. The H.10 rate is from the Board of Governors of the Federal Reserve System; the cash history is from the Reserve Bank of Australia. No endorsement by either is implied.

## What was built

All at spec version 0.1.0, proposed. Tools: `tools/factor_cash_aud.py` (worker W1, checked `a495bfa`), `tools/factor_translate.py` (worker W2, checked `9076732`) and `tools/factor_excess.py`.

| Factor | Build id | `series.csv` sha256 | Invariants |
|---|---|---|---|
| `cash.aud.overnight_reconstructed` | `9b5f8ec28901f475` | `87f7f5e8f5961239875cb8db5c0d37f06c5d6c0e1e340736d64679bf56af2f6e` | RA-INV-001 pass, index_chain pass, level_ratio pass, non_negative_before_seam pass, seam pass |
| `equity.us.spy.aud_unhedged.total_return` | `9ad40573699716eb` | `5df3a562ac388f2022c1f641983e29d3d70f3c0e4963a94da817510865a81f6f` | RA-INV-001 pass, RA-INV-006 pass, RA-INV-007 pass, fx_dates pass, index_chain pass |
| `rates.us.ief.aud_unhedged.total_return` | `9c03a1228c882966` | `3d99990ed7fdf3e9f0a2b34213d230173f7aaa240e9490993199ad877ab29d22` | RA-INV-001 pass, RA-INV-006 pass, RA-INV-007 pass, fx_dates pass, index_chain pass |
| `cash.us.bil.aud_unhedged.total_return` | `506cd95465c0852d` | `0d1e2d4ad8426ab41f241aa23d49e366c0a9e249e483429c3c8b25fd2efe71c5` | RA-INV-001 pass, RA-INV-006 pass, RA-INV-007 pass, fx_dates pass, index_chain pass |
| `equity.us.spy.aud_hedged.total_return` | `c967a07f3b568372` | `d63eb64227f4ae1a94df75423b8f278b1c7769363180930346eddf9590675697` | RA-INV-001 pass, RA-INV-007 pass, RA-INV-009 pass, alignment pass, cip_forward pass, fx_dates pass, index_chain pass |
| `rates.us.ief.aud_hedged.total_return` | `30b762fab22a4205` | `7535f858ab684f6e1915fb057815ac8ae79cd1cfc9c95861d3f178529f84a0fa` | RA-INV-001 pass, RA-INV-007 pass, RA-INV-009 pass, alignment pass, cip_forward pass, fx_dates pass, index_chain pass |
| `equity.us.spy_aud_unhedged_vs_aud_cash.excess` | `fcf690ebe2c95399` | `38e82c019f1906a6a6247a64a6ac9c890666f6c7eff78ec641d2bd0cf5d5856d` | RA-INV-004 pass, RA-INV-005 pass, alignment pass |
| `rates.us.ief_aud_unhedged_vs_aud_cash.excess` | `812d62c8efa08d3e` | `2946be5cc59b652d92a5b6d0a1b9d188763f3fd5244998d321955922864039fc` | RA-INV-004 pass, RA-INV-005 pass, alignment pass |

- **AUD cash:** the RBA's published interbank overnight rate accrued ACT/365 up to 2011-01-04, then the RBA's own Cash Rate Total Return Index scaled to continue it, as E-0003 assembled it. Every return from the seam on equals the RBA index's own ratio.
- **Unhedged AUD:** each USD period return translated at the H.10 USD-per-AUD rate, `s = q_(t-1)/q_t - 1` (RA-INV-007), with the cross term in `decomposition.csv`. The series stop where H.10 stops; the periods after it are dropped and counted.
- **Hedged AUD, hedge ratio one:** `R_H = R_f + f + R_f s`, with the forward premium implied from the AUD cash series and BIL's return (covered interest parity), reset every period.
- **AUD excess:** the unhedged AUD series over AUD cash, arithmetic per period.

## Checks on the real data, beyond the workers' tests

- **Unhedged:** a separate script with its own H.10 parser and exact rational arithmetic recomputed every period of all three series; all agree within 1e-12, and no rate used is more than five days old. The archive labels the series "USD per AUD", which is the quote the inversion rule assumes.
- **Sign, on a known episode:** the quote fell between the ends of July and October 2008, so `s` is positive for an Australian holder of USD, and SPY's AUD return over those months is higher than its USD return. An inverted formula would give the opposite.
- **Hedged:** the same script recomputed every period of the SPY hedged series from the three legs and the rates; all agree within 1e-12.
- **Reasonableness:** over the hedged span, the hedged series' pick-up over the USD series is smaller than the cash-rate differential, by an amount of the size the cross term `R_f s` predicts when equities and the AUD fall together. Stated as a reading; the values are local.
- The analytics and the risk model ran on unhedged, hedged and part-hedged AUD portfolios; contributions and risk contributions reconcile in every run.

Local outputs: `~/.hio-research/factor-store/`, `~/.hio-research/analytics/aud-*/` and `~/.hio-research/risk/aud-*/`.

## Limits

- **The hedged series is not a tradable return.** Its forward is implied from a rate differential, not market forward points, so the CIP basis and hedge costs are missing; its USD rate is a bill fund's own return; and a reset every period is a modelling choice. The specs mark it `replicable_with_basis`.
- **Fixing time.** H.10 is a noon New York rate and the funds close at 4 pm, so each daily period mixes two instants. This matters most for the daily cross term in the hedged series; monthly figures are less affected.
- **Different spans.** The unhedged series start when each fund does; the hedged series start when BIL does. Comparisons across them must use a common span.
- One vendor's unvalidated fund prices under all of it; reconstructed, not point-in-time.

## Not established

That any series is fit for a consumer; that any spec is adopted; that the hedged series approximates an investable hedged return.
