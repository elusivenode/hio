---
id: HIO-EVIDENCE-FACTORS-BUILD-5
title: "Australian equity: VAS market total return in AUD from EODHD snapshot s2 (T-0024 package A1)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0219
---

# Factor builds 5

> **Exploratory and unaccepted.** No series is accepted, no spec is adopted, nothing is published. No value from the series is recorded here (OD-0210): the series is in a local file for the owner.

## What was built

`tools/factor_build.py`, unchanged, built the proposed spec `specs/factors/equity.au.vas.market_total_return.yaml` at version 0.1.0 from snapshot `s2`, pinned by its manifest hash `bb40a84650a8b7104e3d116a5d0773619dd4870ee20190a80bab370135fee38d`. No tool change and no worker were needed: the tool reads the symbol, the exchange and the numeraire from the spec and the snapshot.

| Factor | Build id | `series.csv` sha256 | RA-INV-001 | Index chain | RA-INV-020 |
|---|---|---|---|---|---|
| `equity.au.vas.market_total_return` | `3400cc7b06bfff70` | `d44937a4760f899fe67c76035535530e3a40e8f7c5a37403efc6c02b7666ed63` | pass | pass | pass (no split in the series) |

Spec sha256 `9133a11da46999f789c683af9ea15e3e63a03da447c43a0f0b4021149e99bf4f`; code commit `160c01eb7b46de692a1e917543a910b2c998ebf4`. Local store: `~/.hio-research/factor-store/equity.au.vas.market_total_return/0.1.0/3400cc7b06bfff70/`.

## Checks on the real data

- **Inputs.** Every distribution is in AUD and falls on an observed date; no close is missing, duplicated or out of order; the exchange list gives the fund's currency as AUD.
- **Independent recomputation.** A separate script, using no HIO code, recomputed every period's total return from the raw snapshot files in exact rational arithmetic. Every period agrees within 1e-12 and the final index within 1e-9.
- **Triangulation, not an identity (RA §11).** The cumulative return was set against the vendor's adjusted close. The gap is small and of the predicted kind (the vendor adjusts by a price factor; HIO reinvests at the ex-date close). This compares the vendor with itself and validates nothing independently.
- **Determinism.** A second build reports "already built", byte-identical.
- **Broken on purpose.** Snapshot `s3`'s pin against `s2` refuses.

## Limits

- **Franking credits are excluded.** Only the cash distribution is reinvested. For an investor who can use the credits, the series understates the return; the size is not estimated here.
- **Snapshot `s2` is older than `s3`.** The series ends before the US builds do, so a comparison uses the common span.
- **One vendor, unvalidated,** as in `build-1.md`. The distributions are not checked against the issuer.
- **A vehicle, not an index.** The fund's fees are inside its price.

## Not established

That the series is fit for a consumer; that the spec is adopted; that T-0003 is decided. Package A4 (the comparison note) and every other package of T-0024 are not authorised.
