---
id: HIO-ADR-0004
title: "Temporal semantics: knowable versus captured"
status: approved
approved_by: OD-0008   # at a82aa0d, blob bd86ec3938c8
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
| `knowable_at` + `knowable_basis` | the earliest instant (UTC) **this vintage's value** was publicly knowable, with the evidence for that vintage: `publisher_timestamp` \| `publisher_vintage` \| `archived_receipt` \| `captured_on_schedule`, or the non-evidential `schedule_only` \| `rule_inferred` | a claim, with an evidence grade, specific to the vintage |
| `captured_at` | the instant (UTC) HIO's receipt was fetched | a fact, proven by the receipt |
| `vintage_seq` | the order of distinct values for the same key | a fact |

Query modes, never mixed implicitly:
- **`as_known_by_market(T)`:** the latest vintage with `knowable_at ≤ T` **whose basis is
  vintage evidence**. A key with no such vintage is absent, not filled from a later revision.
- **`as_captured_by_hio(T)`:** the latest vintage with `captured_at ≤ T`. This is **provable**.
- **`reconstructed(T)`:** may use `schedule_only` or `rule_inferred` vintages. It is always
  labelled "reconstructed availability", and is never described as point-in-time evidence.

**A release schedule is not evidence for a value.** A current-only backfill cannot serve an
earlier `as_known_by_market(T)` (fixture in observations standard §4.1).

**Promotion rule.** A predictive or TAA result promoted beyond `exploratory` must declare its
mode and its weakest basis.

Full rules, timezone and session semantics: the
[observations standard](../standards/observations-and-point-in-time.md).

## Consequences

- The *capture clock* starts the day each source's scheduled capture starts. It is recorded per
  source. Captured history cannot be backfilled.
- Publisher vintages (for example ALFRED) are first-class and distinct from HIO captures.

## Rollback or exit

- Not reversible for data already captured without these fields. That is why it is decided
  before S1.

## Changelog

- 2026-10-18: created (85ef0fa).
- 2026-10-18: vintage-specific knowability and the `reconstructed` mode (T-0008, F-REVIEW-2026-10-18-a01-1). Status unchanged: proposed.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `bd86ec3938c8`). Edits after that commit record status only.
