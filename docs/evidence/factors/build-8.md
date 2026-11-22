---
id: HIO-EVIDENCE-FACTORS-BUILD-8
title: "Five-sleeve AUD comparison with a 60/40 sensitivity (T-0024 package B4)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0223
---

# Factor builds 8

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the note and its figures are in local files for the owner.

## What was run

No new series and no tool change. On the common complete months of five built series:

| Sleeve | Factor | Build id |
|---|---|---|
| Australian equity | `equity.au.vas.market_total_return` | `3400cc7b06bfff70` |
| US equity in AUD, unhedged | `equity.us.spy.aud_unhedged.total_return` | `9ad40573699716eb` |
| Australian government bonds | `rates.au.vgb.market_total_return` | `e3e895a2ce53e464` |
| US Treasuries in AUD, unhedged | `rates.us.ief.aud_unhedged.total_return` | `9c03a1228c882966` |
| AUD cash | `cash.aud.overnight_reconstructed` | `9b5f8ec28901f475` |

- **`tools/sleeve_comparison.py`**, four sleeves against cash, with the currency split of both translated sleeves: `comparison.json` sha256 `edf0fbc75827691e51262eec57c61ffa2c577a8fa683e835dd8a51741c029b3a`, `monthly.csv` sha256 `01f75a3dacf7a26724afb7dd919d73551d099646e265e3d38db896e99d338d46`.
- **`tools/portfolio_analytics.py` and `tools/risk_model.py`** on a 30/30/20/20 blend of the four sleeves (equity 60, bonds 40): `analytics.json` sha256 `49af5deab7bd74736230443982b9cc0f48f7da15de2ea8537638480f65214704`, `risk.json` sha256 `946a6443ea36324a9b42e18cabefe139d650dfb81464b4f79f37ad2b26f9482a`.
- **Other 60/40 pairings** (each equity sleeve with each bond sleeve) were computed by a script from the comparison's monthly returns, since the portfolio tool takes no zero weight and so cannot hold a two-sleeve portfolio to the four-sleeve span. Under monthly rebalancing a month's portfolio return is the weighted sum of its sleeves' returns. The script's blend agrees with the tool's.
- **A hedged diagnostic:** the same comparison with the CIP-implied hedged US series, labelled not tradable.

Local outputs: `~/.hio-research/analytics/b4-five-sleeve/` (with `note.md` for the owner), `b4-blend-eq60-dur40/`, `b4-five-sleeve-hedged-diagnostic/`, and `~/.hio-research/risk/b4-blend-eq60-dur40/`.

## Checks on the real data

- **Independent recomputation.** A script using no HIO code rebuilt every monthly return of the five series in exact rational arithmetic and recomputed each sleeve's volatility and all six pair correlations. Every month agrees within 1e-9 and every statistic agrees.
- **Currency identity.** `(1 + F)(1 + S) - 1` equals the AUD return in every month for both translated sleeves, by the tool and by the script.
- **Cross-tool agreement.** The blend's volatility and return from the script match `portfolio_analytics.py`; contributions and risk contributions reconcile.
- **Plausibility.** Each sleeve's worst drawdown falls in a known episode.

The bootstrap intervals and the two-sleeve 60/40 figures were not independently recomputed.

## Limits

- **The common span starts in 2012,** set by the Australian bond fund. It holds one equity crash and one bond sell-off.
- **The Australian bond fund's early closes are stale** (`build-7.md`).
- **The unhedged US bond sleeve carries a currency position** as well as a duration one; the currency split separates them. A like-for-like duration comparison needs a tradable hedged form (package B2).
- **No proper USD cash leg** (package B1). The funds differ in maturity.
- **One vendor, unvalidated.** Franking excluded. Month ends are not simultaneous.
- **Descriptive only:** no costs, tax, forecast, allocation or hedge recommendation.

## Not established

That any series is fit for a consumer; that any spec is adopted; that any relationship seen would persist. Packages A2, A3, B1 and B2 and Milestone C of T-0024 are not authorised.
