---
id: HIO-EVIDENCE-FACTORS-GOLD-MARTS-2
title: "Covariance and risk-contribution marts, compared with today's risk model output (OD-0234)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0234
---

# Gold marts 2

> **Exploratory and unaccepted.** The contract is `docs/decisions/gold-marts-contract.md` §6a (proposed); the comparison and its bar are in OD-0234, declared before the build. **No value from a series is recorded here** (OD-0210). Run once, by the author; not reviewed. The figures describe one sample of a hypothetical portfolio: they are not forecasts and not a recommendation.

## What was built

Five worker tasks, each integrated at its checked commit:

| Code | Does | Checked commit |
|---|---|---|
| `src/hio/contracts/gold.py` | the two new kinds, the floating-point policy, the environment in a recipe | `4df6c68` |
| `src/hio/models/risk.py` | sample covariance, correlation and volatility by window; risk contributions | `cefa7d7` |
| `src/hio/jobs/gold.py`, `tools/gold_build.py` | the planner builds the two kinds and their parents | `b91029b` |
| `tools/lake_catalogue.py` | tables, views and two-parent lineage for them | `8e241dc` |
| `tests/test_jobs_research.py` | the read API's tests for all four kinds | `fcd0bbb` |

Proposed specs: `specs/gold/covariances/aud-four-sleeve-36m.yaml` and `specs/gold/risk/aud-eq60-dur40.yaml`.

## The run on real data

One command planned and built the chain for the risk target:

| Mart | Build id |
|---|---|
| panel `aud-four-sleeve` | `317e802fffaf886ef1729004497e5e829e3d74d2b474b43be93ba802a658283f` |
| covariance `aud-four-sleeve-36m` | `3cc55aebdbe92fbf365fa2795900f54bf7440b5ffeaa1e89ffc6c159696d1fdc` |
| portfolio path `aud-eq60-dur40` | `7094d3fe7b213df26d77d17b82157f1b0df4aa67c899dfaba2b860563a71b90c` |
| risk contribution `aud-eq60-dur40` | `5f6c4cfa9f6d248b6b4acdfcb0998a7697a6c2fd171b7650a8241c5b4de892e7` |

The panel and portfolio have new ids because the code commit is part of an identity; the bundles built for `gold-marts-1.md` are kept and still verify. The covariance bundle holds the full-sample window and 139 trailing 36-month windows. The two floating-point builds record their environment (NumPy 2.5.4, Python 3.13) in their identity. A second run built nothing.

## The declared comparison

Against `risk.json` and `rolling.csv` of today's `tools/risk_model.py` run for the same blend. The bar was a relative difference below 1e-9 in every figure.

| Figures | Count | Worst relative difference | Reading |
|---|---|---|---|
| Full-sample covariance, correlation and volatility | 36 | 9.1e-15 | pass |
| Full-sample portfolio variance, volatility, diversification ratio and each sleeve's three contributions | 15 | 3.6e-15 | pass |
| Trailing volatilities, pairwise correlations and portfolio volatility, 139 windows | 1,529 | 3.9e-11 | pass |

The same 139 trailing windows, ending on the same month ends, in both.

**Other checks:** the catalogue rebuilt with 0 problems (6 bundles, 160 lineage rows). Broken on purpose: one digit changed in a copy of the covariance bundle, and the run refuses because the bundle does not verify.

## Limits

- **A sample covariance with no shrinkage.** Four sleeves, one sample, one estimator. Whether it is a good estimate of anything is not examined (Milestone C of T-0024).
- **Floating point is reproducible in one environment.** Another NumPy or Python version gives a different build id, by design, and may differ in the last digits.
- Today's risk tool is unchanged and its outputs are not in the catalogue.
- Funded portfolios only for risk contributions; an excess-return panel can have a covariance bundle, untested on real data.
- Checked by the author on real data against a separately written tool, and by the workers' tests on invented data; no independent review.

## Not established

That the estimates are right for any purpose. Nothing is accepted, and the contract stays proposed.
