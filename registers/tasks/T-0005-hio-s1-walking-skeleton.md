---
id: T-0005
title: "HIO-S1 walking skeleton in two stages: S1a synthetic-fixture foundation (independent repository, contracts, cash legs and investable FX excess return on fixtures); S1b live official observations"
status: proposed
owner: owner
assignee_role: implementation engineer (+ quantitative researcher for specs; independent reviewer)
created: 2026-10-18
authorised_by: null       # no owner instruction to execute is recorded, so not authorised
base_revision: null
links:
  adrs: [HIO-ADR-0001, HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010]
  specs: [cash.aud.overnight@0.2.0, cash.usd.overnight@0.2.0, fx.usd_cash_vs_aud.excess@0.2.0]
  depends_on: {S1a: [G1 (complete, OD-0011), S1a owner authorisation], S1b: [S1a accepted, T-0002, S1b owner authorisation]}
  blocks: [S2]
---

# T-0005: the HIO-S1 walking skeleton

The full definition is in [`../../docs/implementation-plan.md#hio-s1-walking-skeleton-recommended`](../../docs/implementation-plan.md#hio-s1-walking-skeleton-recommended).
This card does not repeat it. The acceptance tests are S1-A1 to S1-A16 there, split by stage in
the plan's *Stage mapping*.

## Stages (HIO-ADR-0010 rev 3)

| Stage | Scope | Entry gate |
|---|---|---|
| **S1a** | synthetic sources and fixtures only: repository and history-preserving migration (operating model §8.1), CI, contracts, local-filesystem object store, observation/vintage/knowability model, the three S1 constructions, rights and publication gates on fixtures. **No network fetch, real data, credentials, buckets or schedules** | G1 (complete) and a separate owner authorisation of S1a's scope. **T-0002 does not gate S1a** |
| **S1b** | real-source adapters, bucket and scoped keys, scheduled capture, soak, triangulations | S1a accepted; T-0002 `owner_verified` rights per operation; timing, calendars and the AUD rate regime evidenced; a separate S1b authorisation |

A draft S1a authorisation is at
[`OD-0017`](../../docs/decisions/owner/OD-0017-authorise-s1a-DRAFT.md) (`draft`; no authority).

## Non-goals
Listed in the implementation plan, under S1 exclusions.

## Review status
_Neither stage is authorised (no recorded OD); do not start._
