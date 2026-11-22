---
id: HIO-PROPOSAL-FACTOR-PROGRAMME
title: "Factor programme sequence (proposed): three milestones to a first AUD multi-asset comparison"
status: proposed            # drafted under OD-0218; authorises nothing; each package needs its own yes
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
base_revision: 6d7535a290107a899436bfa912996c7644555abc
instruction: OD-0218 (draft only)
amends_if_adopted: "docs/decisions/factor-first-sequencing-proposal.md tracks 4 to 7 (order of first effort); docs/roadmap.md stays HIO's only roadmap"
sources: [docs/history/2026-11-22-chatgpt-factor-programme-guidance.md, "architect consultation 20261122T133335-ask-3fa5", handoffs/s1b1/2026-11-22-factor-builds-session-roll.md]
---

# Factor programme sequence (proposed)

> **Proposed, one page.** It orders the work in [T-0024](../../registers/tasks/T-0024-factor-programme.md). It is a linked detail beneath `docs/roadmap.md`, not a second roadmap, and the factor-first proposal (OD-0139) stays the working order until the owner adopts this.

## The target

One research comparison in AUD across five sleeves, each a declared vehicle proxy: AUD cash, Australian equity, US equity, Australian government duration and US Treasury duration. It should say how they behave together, what drives the risk, how much the hedge and timing assumptions matter, and what cannot yet be answered.

## The sequence

| Milestone | Packages | Can run at once | Deliverable |
|---|---|---|---|
| **A: equity comparison** | A1 Australian equity; A2 targeted source check of the US funds; A3 hedge inception assessment and diagnostic label; A4 research note | A1, A2, A3 | Australian and US equity against AUD cash, unhedged, with the currency effect separated |
| **B: defensive sleeves** | B1 USD overnight cash leg; B2 hedge from rates lockable at inception, if they exist; B3 Australian government duration (feasibility, then build); B4 report | B1 and B3's feasibility note | duration against cash, in AUD, with a 60/40 sensitivity |
| **C: later** | shrinkage against sample covariance on the five sleeves, out of sample; credit and gold each on a separate case | to be specified | an estimator comparison with uncertainty |

**Alongside:** a deletable backup of the local stores with one restore test, after the owner's reading of the licence.

The milestones are planning estimates, not dates.

## Why this order

- **Australian equity first** because its data is already held (snapshot `s2`) and it is the first domestic risky sleeve.
- **The source check runs beside it, not ahead.** The files are disjoint, and T-0023 has done part. Unresolved US differences limit conclusions that use those inputs; they do not block the Australian build. T-0023 is parked (OD-0215), so extending it is the owner's call.
- **The hedge is assessed and labelled now, and fixed in B only if inputs exist.** The forward is implied from realised cash returns in both currencies. A proper one needs rates lockable at inception for both, at the hedge tenor; an overnight leg alone does not supply that. Until then Milestone A is unhedged.
- **Australian duration through a fund first.** E-0001's par-curve approximation failed its bars, so a fund is the smaller route. That does not rule out every curve construction.
- **Shrinkage waits for the five sleeves, not for credit.** With few series, unstable relationships across regimes matter more than the estimator.

## Differences from the advice

| ChatGPT's guidance | Here | Why |
|---|---|---|
| validation at priority 2, ahead of Australian equity | in parallel | disjoint files; partly done |
| a 2027 calendar item | dropped | done (OD-0185); the 2028 files are owed before 2028-01-01 |
| hedge improvement as a stage | assess and label in A, fix in B if inputs exist | needs inception rates in both currencies |
| three acceptance tiers | the existing terms: `exploratory`, `validated`, `approved_for_consumer` | no second regime |
| backup as hygiene | a proposal behind a rights reading | OD-0210 |

## What each step needs from the owner

Each package is one yes. A1, A3 and A4 need no new data. A2 also needs a decision on extending parked T-0023 work. A2, B1, B2 and B3 may each need a source permission, and B3 a fetch. Nothing here spends money.

## Not proposed

An optimiser, a hedge recommendation, a consumer release, a new standard, or any work on E-0004 or H6.
