---
id: HIO-ADR-0004
title: "Temporal semantics: knowable versus captured"
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [HIO-S1]
review_record: null
supersedes_proposal: "18 Oct proposal §5.1 (single available_at + pit_basis)"
---

# HIO-ADR-0004: temporal semantics, knowable versus captured

## Context

- The 18 October proposal used one `available_at` per observation, plus a `pit_basis` label.
  That conflates two different claims:
  - **when the market could have known a value**, a claim about the world, often inferred;
  - **when HIO actually held it**, a fact about HIO.
- Backfilled history then looks point-in-time when it is not.
- [OBS] `macsmsf` already learned that vendors revise history silently (`sql/043`): a yfinance
  revision moved a settled receivable.

## Decision (proposed)

Every observation carries:

| Attribute | Meaning | Nature |
|---|---|---|
| `valid_time` | what the value refers to: a trade date, settlement date, month or tenor date, in the **market-local calendar** | a fact about the series |
| `knowable_at` + `knowable_basis` | the earliest instant (UTC) the value was **publicly knowable**, with how we know it: `publisher_timestamp` \| `publisher_vintage` \| `documented_schedule` \| `rule_inferred` | a claim, with an evidence grade |
| `captured_at` | the instant (UTC) HIO's receipt was fetched | a fact, proven by the receipt |
| `vintage_seq` | the order of distinct values for the same key | a fact |

Two query modes, never mixed implicitly:
- **`as_known_by_market(T)`:** the latest vintage with `knowable_at ≤ T`. Results inherit the
  weakest `knowable_basis` used.
- **`as_captured_by_hio(T)`:** the latest vintage with `captured_at ≤ T`. This is **provable**.

**Promotion rule.** A predictive or TAA result promoted beyond `exploratory` must declare its
mode and its weakest basis. A result relying on `rule_inferred` knowability is labelled
"reconstructed availability", and cannot be described as point-in-time evidence.

Full rules, timezone and session semantics: the
[observations standard](../standards/observations-and-point-in-time.md).

## Consequences

- The *capture clock* starts the day each source's scheduled capture starts. It is recorded per
  source. Captured history cannot be backfilled.
- Publisher vintages (for example ALFRED) are first-class and distinct from HIO captures.

## Rollback or exit

- Not reversible for data already captured without these fields. That is why it is decided
  before S1.

## Approval

_Unapproved._
