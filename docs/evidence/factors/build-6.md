---
id: HIO-EVIDENCE-FACTORS-BUILD-6
title: "Equity comparison: Australian and US equity against AUD cash, currency effect separated (T-0024 package A4)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0220
---

# Factor builds 6

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the note and its figures are in local files for the owner.

## What was built

- **An excess series.** `tools/factor_excess.py`, unchanged, built the proposed spec `specs/factors/equity.au.vas_vs_aud_cash.excess.yaml` at 0.1.0 from the VAS build `3400cc7b06bfff70` and the AUD cash build `9b5f8ec28901f475`: build id `77ef72a85a6ef59c`, `series.csv` sha256 `3adb371b5684f32b8f2f08f4ed8da9fb0c7d8ae787ed607bfc8ed8fd08fbf50c`; RA-INV-004, RA-INV-005 and alignment pass.
- **A comparison tool.** `tools/sleeve_comparison.py` (worker W1, checked `da75ec4`): funded sleeves in one numeraire, side by side and against cash on their common complete months; excess over cash; pairwise correlation and differences; a currency split from a translation build's decomposition; block-bootstrap intervals.
- **The comparison.** VAS and SPY in AUD (unhedged, build `9ad40573699716eb`) against AUD cash, with SPY's currency split: `comparison.json` sha256 `2ce6e4cd5c569e0e101dd058d0e8bcb46e185683564a9583e9ede17dbbd51e57`, `monthly.csv` sha256 `36fd708b9b9a61df0f8cedc3f48eecfeaa0c2ac71b1d2f285893c0f425b6ecd8`. A second run adds the CIP-implied hedged SPY series as a labelled diagnostic.

Local outputs: `~/.hio-research/analytics/a4-equity-comparison/` (with `note.md` for the owner) and `a4-equity-comparison-hedged-diagnostic/`.

## Checks on the real data, beyond the worker's tests

- **Independent recomputation.** A separate script, using no HIO code, rebuilt the monthly returns from the three series in exact rational arithmetic and recomputed the volatilities, the excess means and volatilities, the correlation, the difference volatility, the currency legs, their correlations and the variance fractions. Every month agrees within 1e-9, and every recomputed statistic is in `comparison.json`.
- **Currency identity.** `(1 + F)(1 + S) - 1` equals the AUD return in every month within 1e-9, checked by the tool and by the script.
- **Plausibility.** The worst month and drawdown of each sleeve fall on a known market episode, and the sign of the spot leg matches the known direction of the exchange rate over the span.

The bootstrap intervals were not independently recomputed; they come from the library's seeded resampler.

## Limits

- **The sample is the common span only,** and it excludes the 2008 crisis. Its figures describe that sample.
- **One vendor, unvalidated,** for both funds (T-0003 undecided; package A2 not authorised).
- **Franking credits are excluded** from the Australian sleeve.
- **Month ends are not simultaneous** across Sydney, New York and the noon FX rate.
- **The hedged series is a diagnostic,** not a tradable return (T-0024 package A3).
- **Vehicles, not factors.** No costs, tax, forecast or recommendation.

## Not established

That any series is fit for a consumer; that any spec is adopted; that any difference seen would persist. Packages A2 and A3 and Milestones B and C of T-0024 are not authorised.
