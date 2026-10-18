---
id: HIO-ADR-0007
title: Adopt the return accounting and factor construction standard as a CI-enforced gate
status: approved
approved_by: OD-0008   # at a82aa0d, blob e97a36599575
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [any factor release, any model consuming a factor]
review_record: null
---

# HIO-ADR-0007: the return accounting standard as a gate

## Context

The most damaging silent error in factor research is a **price index masquerading as a return
index**. Examples:
- a dividend-free equity level;
- −D·Δy treated as a bond total return;
- spot FX change treated as a currency return;
- a back-adjusted futures level treated as a return.

The earlier reviews made related errors in acceptance criteria, which the owner corrected:
- matching unlike indices;
- treating trend-index agreement with DBMF as a test;
- treating gold as an inflation proxy.

## Decision (proposed)

1. [`standards/return-accounting-and-factor-construction.md`](../standards/return-accounting-and-factor-construction.md)
   (v0.1) is the authoritative return mathematics. A change is a new standard version, with
   worked-example and invariant updates.
2. Every series declares a `series_class` ∈ {`price_only`, `state_indicator`, `total_return`,
   `excess_return`, `strategy_return`, `reference_academic`}.
   - **Only `total_return`, `excess_return` and `strategy_return` may be used as portfolio
     return factors.**
   - CI fails any model or portfolio spec that references another class as a return.
3. Every factor spec must pass the invariant catalogue (standard §13) that applies to its
   construction. Invariant tests are **identity checks** and must hold exactly (tolerance 1e-12
   relative, unless the standard states otherwise).
4. Comparisons with independent references are **triangulations**:
   - they predict a direction and mechanism, and report differences;
   - they never pass or fail on agreement alone.

## Consequences

- Factors that need income data we lack (for example equity total return without a dividend
  source) cannot ship until that source exists. This is why
  [HIO-ADR-0010](HIO-ADR-0010-first-slice-scope.md) moves equity out of S1.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `e97a36599575`). Edits after that commit record status only.
