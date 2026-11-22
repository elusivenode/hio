---
id: HIO-PROPOSAL-GOLD-MARTS-CONTRACT
title: "Gold marts contract, version 1 (proposed): bundles, pins, the monthly panel and the portfolio path"
status: proposed            # built under OD-0233; approves nothing
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
base_revision: 62e7f9ddba78b1fb615fd3cabe330f3a33a15d24
instruction: OD-0233
amends_if_adopted: "nothing: the factor store and today's analytics outputs are unchanged"
sources: ["architect consultation 20261122T193241-ask-cee5 (advice only)", docs/decisions/silver-v2-contract.md, src/hio/portfolio/fixed_allocation.py]
---

# Gold marts contract, version 1

> **Proposed.** The exact formats the gold-mart foundation is built to. Several workers build to this at once, so every header, key and formula is literal. A change is a new schema version.

## 1. What gold is

| Tier | Holds | State |
|---|---|---|
| Factor series | one return series for each factor build, in the factor store | exists, unchanged; a mart pins a build by `build_id` and `series_sha256` |
| **Marts** | tables built from pinned parents, to query when reasoning about portfolios | new: `panel` and `portfolio_path` |

Today's analytics tools and their outputs are untouched. They use floating point; the marts here use exact decimals and are a **separately versioned calculation**, compared with those outputs and not replacing them.

## 2. Encoding and arithmetic

- Canonical JSON, sha256 and CSV exactly as `docs/decisions/silver-v2-contract.md` §1. Every cell is text.
- **Arithmetic** is `decimal` with `Context(prec=50)`, named numeric policy `decimal-50/1`. A result is written as `format(value, "f")`. Nothing is rounded or normalised.
- Dates are ISO text.

## 3. Bundles

```text
<gold_root>/<kind>/<build_id>/
  manifest.json
  tables/<name>.csv
```

**Recipe** (what was asked for):

```text
schema           "hio.gold/1"
kind             "panel" | "portfolio_path"
spec             {name, version, sha256}
parameters       the spec's calculation fields, as written in §5 and §6
parents          [{role, kind, id, payload_sha256, ...}] sorted by role
numeric_policy   "decimal-50/1"
code_commit
```

- `build_id` is the sha256 of the recipe's canonical JSON: 64 hex characters, never shortened.
- `manifest.json` is `{"build_id", "recipe", "tables": [{name, header_sha256, file_sha256, rows}] sorted by name, "payload_sha256"}`, indent 1, sorted keys, a trailing newline. `payload_sha256` is the sha256 of the canonical JSON of the `tables` list.
- A parent that is a factor series has `kind` `factor_series`, `id` its `build_id`, `payload_sha256` its `series_sha256`, and also `factor_id` and `spec_version`. A parent that is a bundle has its `kind`, `id` its `build_id` and its `payload_sha256`.
- Files 0600, directories 0700. The same recipe gives the same bytes; an existing bundle with different bytes is refused. A bundle is written through a temporary sibling directory renamed into place.

**Verifying a bundle:** the directory name equals `build_id`; `build_id` is recomputed from the recipe; exactly the manifest's tables are present; each file's sha256, header and row count match; `payload_sha256` is recomputed.

## 4. Inputs

**A factor series** is `<factor_store>/<factor_id>/<spec_version>/<build_id>/` holding `build.json` and `series.csv`. Read it only after checking the directory names against the record and `series.csv` against `series_sha256`. `series.csv` starts with `period_start,period_end`; a `total_return` series has a `total_return` column, an `excess` series has `asset_return`, `cash_return` and `excess_return`. The record's `series_class` is `total_return` or `excess`, and it has a `numeraire`.

**A lock** (`specs/gold/locks/<name>.yaml`) pins the factor series a build may read:

```yaml
identity: {name: example, version: 0.1.0, status: proposed}
factor_series:
  some.factor.id: {spec_version: 0.1.0, build_id: "<16 hex>", series_sha256: "<64 hex>"}
```

Nothing resolves "latest": a member with no lock entry is refused.

## 5. The panel mart

**Spec** (`specs/gold/panels/<name>.yaml`):

```yaml
identity: {name: example, version: 0.1.0, status: proposed}
kind: panel
frequency: monthly                 # the only value
alignment: common_boundaries       # the only value
incomplete_periods: exclude        # the only value
members: {equity: some.factor.id}  # member code -> factor_id; a code is [a-z][a-z0-9_]*
```

Recipe `parameters` are `{frequency, alignment, incomplete_periods, members}`. Parents are the members' factor series, each with `role` its member code.

**Refused:** members that do not share one `numeraire`, or one `series_class`; a member whose periods do not join end to start, or are not strictly increasing.

**Calculation**, for each member:

1. Its **boundaries** are every `period_start` and the last `period_end`. The **common boundaries** are the dates every member has, ascending. Fewer than two is refused.
2. On the common boundaries, the member's growth from one to the next is the product of `1 + r` over its own periods in between, where `r` is `total_return`. For an `excess` member the asset and cash legs are each compounded this way, separately.
3. A **mark** is a common boundary whose next common boundary falls in a different calendar month. The last common boundary is never a mark. Fewer than two marks is refused.
4. A **month** runs from one mark to the next. Its return is the product of the growths in between, minus 1. For an `excess` member, `return = asset_return − cash_return`, each leg compounded over the month first. Daily excess is never compounded.

The time before the first mark and after the last is left out: both may be part months.

| Table | Columns | Sort |
|---|---|---|
| `bridge_panel_member` | `panel_build_id,member_code,column_order,factor_id,spec_version,input_build_id,input_series_sha256,series_class,numeraire` | `member_code`; `column_order` counts from 0 in that order |
| `fact_panel_return` | `panel_build_id,member_code,period_start,period_end,return,asset_return,cash_return` | `member_code,period_end`; the two leg cells are empty for a `total_return` member |
| `fact_panel_coverage` | `panel_build_id,member_code,first_boundary,last_boundary,boundaries,omitted_boundaries,common_first,common_last,months` | `member_code`; `omitted_boundaries` counts the member's boundaries that are not common |

## 6. The portfolio-path mart

**Spec** (`specs/gold/portfolios/<name>.yaml`):

```yaml
identity: {name: example, version: 0.1.0, status: proposed}
kind: portfolio_path
panel: example                     # a panel spec's name
rebalance: month_end               # the only value
weights: {equity: "0.60", bonds: "0.40"}   # decimal strings by member code
```

Recipe `parameters` are `{panel, rebalance, weights}`. The one parent is the panel bundle, `role` `panel`.

**Refused:** weights that do not name exactly the panel's members; a weight that is not a decimal string, or is negative; weights that do not sum to exactly 1; a panel whose members are not `total_return` (an excess return is not a holding).

**Calculation.** Weights reset to target at every month end, so for each month the portfolio return is the sum over members of `weight × member return`. The wealth index starts at 1 and is multiplied by `1 + portfolio return` each month. A contribution is `weight × member return`; the contributions of a month sum to its portfolio return, checked to within `1e-30`.

| Table | Columns | Sort |
|---|---|---|
| `fact_target_allocation` | `portfolio_build_id,member_code,target_weight` | `member_code` |
| `fact_portfolio_return` | `portfolio_build_id,period_start,period_end,portfolio_return,wealth_index` | `period_end` |
| `fact_return_contribution` | `portfolio_build_id,member_code,period_start,period_end,start_weight,member_return,contribution` | `member_code,period_end` |

**None of these measures adds across time.** Contributions add across members within one month only.

## 7. Planning and building

A **plan** names a target spec and a lock. The planner resolves the target's parents from the specs (a portfolio needs its panel; a panel needs its members' factor series from the lock), orders them, computes each `build_id`, and marks each node `present` (a verified bundle exists) or `missing`. Running a plan builds the missing nodes in order and verifies each before the next. No orchestrator, no clock and no "latest" are involved; a correction upstream changes a pin in the lock, which changes every dependent `build_id`.

## 8. Module placement

| Module | Holds | May import |
|---|---|---|
| `hio.contracts.gold` | the schema, tables, numeric context, recipe and `build_id`, bundle writing and verification, the factor-series reader, the spec and lock readers | `hio.contracts` only |
| `hio.models.panels` | the panel calculation, pure | `hio.contracts` |
| `hio.portfolio.paths` | the portfolio-path calculation, pure | `hio.contracts` |
| `hio.jobs.gold` | the planner and the runner. It is handed the two calculations as functions and imports neither | what the import rules allow `hio.jobs`: not `hio.models`, not `hio.portfolio` |
| `hio.jobs.research` | the read API: a store that opens pinned silver and gold | `hio.contracts`, `hio.marketdata` |
| `tools/gold_build.py` | the command: it imports the calculations and passes them to the planner | outside the import rules, like every tool |

## 9. The read API

```python
store = ResearchStore(silver_root=..., factor_store=..., gold_root=...)
silver = store.silver(release_id, selection)          # verified; selection by name or id
silver.table("fact_listing_bar_day")                  # rows as dicts of text
series = store.factor_series(factor_id, spec_version, build_id)   # verified
panel = store.bundle("panel", build_id)               # verified
panel.table("fact_panel_return")                      # rows as dicts of text
panel.decimals("fact_panel_return", "return")         # the same column as Decimal
store.connect()                                       # an in-memory DuckDB with every opened table registered
```

Reading never builds, and every open names an exact identity.
