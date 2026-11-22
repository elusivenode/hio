---
id: HIO-EVIDENCE-FACTORS-BUILD-1
title: "First local factor series builds: SPY, IEF and BIL market total return from EODHD snapshot s3, with portfolio analytics"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0213
---

# Factor builds 1

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the series and the analytics are in local files for the owner.

## What was built

`tools/factor_build.py` (worker W1, checked `7deca93`) built each proposed spec at version 0.1.0 from snapshot `s3`, pinned by its manifest hash `ce6b17c9f2590c26adabf37856d79e607597027a1701e7833bf386a9fe4757cc`, with `src/hio/library/vehicle_return.py`. Each build holds the per-period price, income and total return and the chained index, with a build record of its spec hash, snapshot hash, input hashes and code commit.

| Factor | Build id | `series.csv` sha256 | RA-INV-001 | Index chain | RA-INV-020 |
|---|---|---|---|---|---|
| `equity.us.spy.market_total_return` | `d4ef493e70d0a9d5` | `0fd0ec39865c9cc919fc07bfd79ec2509872ed46ac6c3f9a85ee547443d8c01c` | pass | pass | pass |
| `rates.us.ief.market_total_return` | `0f81c557ccd2cd80` | `27d5eb8f8a53b38f64c72d666957b47b890658d877ff59533b4eb5eec5f1348c` | pass | pass | pass |
| `cash.us.bil.market_total_return` | `316e1ae416c2b9ca` | `7b1f88f5fa6946b1e4f7d80795825deebfed54cd42bac19ab9f1fe154076635d` | pass | pass | pass |

Local store: `~/.hio-research/factor-store/<factor_id>/0.1.0/<build_id>/`.

## Checks on the real data, beyond the worker's tests

- **Independent recomputation.** A separate script, using neither `hio.library` nor `tools/eodhd_eval.py`, recomputed every period's total return from the raw snapshot files in exact rational arithmetic. Every period of all three series agrees within 1e-12, and each final index within 1e-9.
- **Triangulation, not an identity (RA §11).** Each series' cumulative return was set against the vendor's adjusted close over the span. A small gap is predicted, because the vendor adjusts by a price factor and HIO reinvests at the ex-date close. All three gaps are small and of the predicted kind. This compares the vendor with itself and validates nothing independently.
- **Determinism.** A second build reports "already built", byte-identical.
- **Broken on purpose.** A wrong pin refuses; snapshot `s2` under `s3`'s pin refuses.

## Portfolio analytics

`tools/portfolio_analytics.py` (worker W2, checked `b2ce900`) ran on three fixed-weight, monthly-rebalanced portfolios of the built series (60/40 SPY and IEF; 60/40 SPY and BIL; 60/30/10), with `src/hio/portfolio/fixed_allocation.py`. It gives annualised return and volatility, the worst drawdown with its dates, the best and worst month, the sleeves' correlation, and each sleeve's contribution.

- Monthly contributions sum to the portfolio's month return within 1e-12 in every month of all three runs.
- The arithmetic sum of contributions differs from the compounded return, as it must (RA-INV-016); the tool reports that residual and does not force it to zero.
- An independent script recomputed every month's 60/40 return from the two series; all months agree within 1e-9.
- A weight set not summing to one refuses.

Local outputs: `~/.hio-research/analytics/<portfolio>/analytics.json` and `monthly.csv`, and a readable `~/.hio-research/analytics/owner-report.md`.

## Limits

- **One vendor, unvalidated.** The closes and distributions are EODHD's, whose price source is unresolved, and whose history changes between snapshots; that is why every build pins its snapshot. The only checks against anything outside the vendor are the earlier, partial T-0023 corroborations.
- **Vehicles, not factors in the strict sense.** Each series is the market-price return of one fund with its fees inside, as its spec says. None is an index return or an excess return.
- **Descriptive only.** No costs, tax, forecast or recommendation.

## Not established

That any series is fit for a consumer; that any spec is adopted; that T-0003 is decided.
