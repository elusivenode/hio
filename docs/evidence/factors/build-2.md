---
id: HIO-EVIDENCE-FACTORS-BUILD-2
title: "Excess-return series over BIL (US equity and duration premium proxies) and a first risk model, on the s3 builds"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0215
---

# Factor builds 2

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the series and the risk outputs are in local files for the owner.

## Excess-return series

`tools/factor_excess.py` (worker W1, checked `8063a44`) built two proposed specs at version 0.1.0 from the total-return builds of `build-1.md`. Each leg is compounded exactly between the dates both legs observe; the excess is arithmetic per period (RA §3.3).

| Factor | Legs | Build id | `series.csv` sha256 | RA-INV-004 | RA-INV-005 | Alignment |
|---|---|---|---|---|---|---|
| `equity.us.spy_vs_bil.excess` | SPY over BIL | `693623a44b438748` | `1d14dd2742a199aa708735cbcfbc7591820166bb789604f534c2a3114a29ac4c` | pass | pass | pass |
| `rates.us.ief_vs_bil.excess` | IEF over BIL | `8d03bb361d2de0bc` | `896202b3ef9e2ddff4da76b5d88d628871638ab2b2468f8d6c7cf353f52e1c05` | pass | pass | pass |

**These are proxies.** The cash leg is a fund of one-to-three-month Treasury bills at market price, not an overnight rate. Both specs say so, and name `cash.usd.overnight` as the proper leg once it has a captured series.

## Risk model

`tools/risk_model.py` (worker W2, checked `d40f381`) ran on three sets of builds: two funded portfolios (60/40 SPY and IEF; 60/30/10 with BIL) and one pair of excess-return exposures (0.6 equity premium, 0.4 duration premium). It gives the annualised covariance and correlation of monthly returns, each sleeve's volatility, each sleeve's marginal and component contribution to portfolio volatility, a diversification ratio, and 36-month rolling volatility and correlation.

- **Euler:** the component contributions sum to portfolio volatility within 1e-15 relative in all three runs.
- **Cross-check between tools:** the risk model's 60/40 volatility equals the portfolio analytics tool's volatility for the same portfolio.
- **Funded and excess forms are never mixed** (RA-INV-015): a run given one of each refuses.

## Checks on the real data, beyond the workers' tests

- **Excess series:** a separate script recomputed every period's excess from the three total-return series in exact rational arithmetic. Both series agree within 1e-12 in every period.
- **Risk model:** a separate script, without numpy, recomputed the monthly returns, the covariance matrix, the portfolio volatility and each component contribution for the 60/40 funded run and for the excess run. All agree with the tool's outputs within 1e-9. (The first attempt disagreed because the script kept the final, partial month, which the library drops by its stated convention.)
- **Broken on purpose:** the wrong build in the asset role refuses; mixed series classes refuse.

Local outputs: `~/.hio-research/factor-store/` (the two excess builds) and `~/.hio-research/risk/<run>/risk.json` and `rolling.csv`.

## Limits

- One vendor, unvalidated; a sample of about nineteen years for the excess series, set by BIL's start.
- Sample covariance on monthly returns: no shrinkage, no factor structure, no forecast. A rolling window describes the past window and nothing else.
- Two premia from three funds are a start, not a factor set.

## Not established

That either excess series is a valid premium estimate; that any spec is adopted; that the risk model is fit for any decision.
