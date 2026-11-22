---
id: HIO-EVIDENCE-FACTORS-GOLD-MARTS-1
title: "Gold-mart foundation: a monthly panel and a portfolio path built from pinned factor series, with a planner and a read API (OD-0233)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0233
---

# Gold marts 1

> **Exploratory and unaccepted.** The contract is `docs/decisions/gold-marts-contract.md` (proposed). **No value from a series is recorded here** (OD-0210). Run once, by the author; not reviewed. The portfolio is hypothetical and is not a recommendation.

## What was built

Six worker tasks in three phases, each integrated at its checked commit:

| Code | Does | Checked commit |
|---|---|---|
| `src/hio/contracts/gold.py` | bundle formats, recipes and ids, verification, the factor-series reader, the spec and lock readers | `f444da0` |
| `src/hio/models/panels.py` | the monthly panel, in exact decimals | `b1fd76a` |
| `src/hio/portfolio/paths.py` | the portfolio path: returns, wealth index, contributions | `0b3db35` |
| `src/hio/jobs/research.py` | `ResearchStore`: pinned reads of silver and gold, and a DuckDB connection over what was opened | `2c90d57` |
| `tools/lake_catalogue.py` | indexes mart bundles, with lineage | `c557a17` |
| `src/hio/jobs/gold.py`, `tools/gold_build.py` | the planner and runner | `87f3803` |

Proposed specs: a lock (`specs/gold/locks/first.yaml`), a panel of the four AUD sleeves of build-8's blend (`specs/gold/panels/aud-four-sleeve.yaml`) and that blend's weights as a portfolio (`specs/gold/portfolios/aud-eq60-dur40.yaml`).

## The run on real data

`tools/gold_build.py run` planned four pinned factor series, then built two bundles in `~/.hio-research/gold/`:

| Mart | Build id | Rows |
|---|---|---|
| panel `aud-four-sleeve` | `f4a91b61b8f316ae52bcf8104c82c05e625266f1fe909fc57ae230e8f6b394f4` | 696 member-months over 174 months |
| portfolio path `aud-eq60-dur40` | `1188b14bcde7e55967130449b2f51a18992f1ca4d22c0c52694513137bbcde48` | 174 months; 696 contributions |

A second run built nothing. `verify` passes.

## Checks

| Check | Result |
|---|---|
| Against today's analytics output for the same blend (`analytics/b4-blend-eq60-dur40/monthly.csv`, floating point) | the same 174 month ends; the largest difference in any portfolio return, member return or contribution is below 1e-15 |
| An independent recomputation in exact rationals from the series files, sharing no HIO code | all 696 member-months and all 174 portfolio months agree to within 1e-48 |
| A lock pinning the silver-built builds of two members (the same series bytes) | a different panel id, identical returns: the pin is in the identity |
| Through the API | the bundles open verified; a SQL join across the opened tables returns the expected counts |
| Catalogue | 2 bundles, 0 problems; a recursive query walks from the portfolio to its panel, its four factor series, their parent builds and the snapshots |
| Broken on purpose: one digit changed in a copy of the panel | the run refuses: the bundle exists but does not verify |

## One correction during the build

The contract first let the planner import the two calculations. The approved import rules do not allow `hio.jobs` to import `hio.models` or `hio.portfolio`, and the commit hook refused the worker's code. The rules were left alone: the planner is handed the calculations as functions by the tool. The contract was corrected.

## Limits

- **Two marts only.** No covariance, risk or comparison mart; today's risk and analytics tools are unchanged and their outputs are not in the catalogue.
- **The marts are a new exact-decimal calculation.** They agree with today's floating-point output and do not replace it.
- **Factor series are pinned inputs.** The planner does not build them: a silver correction reaches a mart when its lock is updated to the rebuilt series.
- Funded total-return panels only for a portfolio; a panel may hold excess series, untested on real data.
- Monthly frequency and month-end rebalancing only.
- Checked by the author on real data and by the workers' tests on invented data; no independent review.

## Not established

That any series, panel or portfolio is right for any purpose. Nothing is accepted, and the contract stays proposed.
