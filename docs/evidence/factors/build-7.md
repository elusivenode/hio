---
id: HIO-EVIDENCE-FACTORS-BUILD-7
title: "Australian government duration: VGB, IGB and AGVT market total return in AUD from EODHD snapshot s4 (T-0024 package B3)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0222
---

# Factor builds 7

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the series are in local files for the owner.

## The fetch

One fetch under OD-0222 on 2026-11-22: `tools/eodhd_eval.py fetch --snapshot s4 --symbols VGB.AU IGB.AU AGVT.AU`. Ten files (closes, distributions and splits for each fund, and the ASX symbol list), no stop. Manifest sha256 `02b24e78d77aba7ef2bb65c7fdf0e0c740611169acf327b09871eee2138de1a5`. The tool first needed a small change (worker W1, checked `fdd7b9c`): an `EXTRA_FUNDS` map that `--symbols` may name, with the default fetch and the evaluation unchanged.

## What was built

`tools/factor_build.py`, unchanged, at code commit `0e32cdc3a53ac7554fd4ff85bc425b7432ddfc9d`, each spec at version 0.1.0, proposed.

| Factor | Build id | `series.csv` sha256 | RA-INV-001 | Index chain | RA-INV-020 |
|---|---|---|---|---|---|
| `rates.au.vgb.market_total_return` | `e3e895a2ce53e464` | `ff9cc2f60be1c659a3efe93bcb3be7105b6c1ff84a3d07dd49148aa2c6b1ff20` | pass | pass | pass (no split) |
| `rates.au.igb.market_total_return` | `199fc6678055c500` | `a41395d7ac656704fa0afafb1fbe4e5e2336d4e10b3dd09884a9bd29ac15649a` | pass | pass | pass (no split) |
| `rates.au.agvt.market_total_return` | `d6212e7ff903725a` | `8a822487865be1390ff47b717b32c62dceba48a01c81e7fa7b4358a180cb1966` | pass | pass | pass (no split) |

Local store: `~/.hio-research/factor-store/<factor_id>/0.1.0/<build_id>/`.

## Checks on the real data

- **Inputs.** For each fund every distribution is in AUD and falls on an observed date; no close is missing, duplicated or out of order; the listing's currency is AUD.
- **Independent recomputation.** A separate script, using no HIO code, recomputed every period's total return from the raw snapshot files in exact rational arithmetic. Every period of all three series agrees within 1e-12, and each final index within 1e-9.
- **Triangulation, not an identity (RA §11).** Each cumulative return was set against the vendor's adjusted close; each gap is small. This compares the vendor with itself and validates nothing independently.
- **Plausibility.** Each fund's worst drawdown and worst month fall in a known bond sell-off, and the three funds move closely together over their common months.
- **Determinism and refusal.** A second build reports "already built"; snapshot `s2`'s pin against `s4` refuses.

## Limits

- **Stale early closes.** In each fund's first two years a material share of days show no trading, so the close on those days may not be a fresh price. After that the share is negligible. Daily figures from the early years should not be relied on; monthly figures are less affected.
- **Short histories.** VGB and IGB start in 2012 and AGVT in 2019. None covers 2008.
- **Maturity baskets, not duration factors.** Each fund's duration drifts with its index, and the three differ in maturity from each other and from the US fund.
- **VGB is not sovereign-only** [EXT]; IGB is the Commonwealth-only comparator.
- **One vendor, unvalidated.** The distributions are not checked against the issuers. Market price, not net asset value.

## Not established

That any series is fit for a consumer; that any spec is adopted. No comparison report was made: package B4 and every other open package of T-0024 are not authorised.
