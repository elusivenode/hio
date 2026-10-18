---
id: HIO-ADR-0001
title: HIO is a separate system; modular monolith with independently runnable workloads
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [creation of the hio repository, HIO-S1]
review_record: null
---

# HIO-ADR-0001: separate system, modular monolith, independently runnable workloads

## Context

- HIO's research scope and lifetime are independent of the SMSF.
- `macsmsf` is live production for a real fund, under a strict preservation principle: additive
  changes, baselines, rollback ([OBS] `macsmsf` `CLAUDE.md`, the HIO-001 review record).
- Its release path to production is itself the subject of unfinished work (A17-B) [OBS].
- One operator runs everything, with agent assistance.

## Options considered

| Option | For | Against |
|---|---|---|
| HIO inside `macsmsf` (new package and schemas) | no new repository | couples release cycles, schema, CI and credentials; makes `macsmsf` HIO's system of record; violates the owner's direction |
| **Separate repository; one codebase with bounded-context packages; workloads as separate entrypoints** | independent release; one lockfile and image keeps reproducibility simple; contexts enforced by import rules; any workload can be scheduled or sized alone | relies on discipline (import rules, contracts) rather than process boundaries |
| Separate repository; 3–5 domain services | process-level isolation | multiplies deployment, secrets, telemetry and failure modes before any trigger justifies it |
| Distributed, event-driven, agent platform | maximum independence | highest toil and failure surface; agents before a deterministic foundation exists |

## Decision (proposed)

Option 2. Detail in [`../architecture.md`](../architecture.md), with measurable split triggers
in §5.

## Consequences

- A new private repository `hio`, with its own CI, secrets and storage.
- Until it exists, planning is staged in `macsmsf/hio/`, which no `macsmsf` code reads.
- Contracts (schemas) are owned by HIO and versioned. Consumers validate against them.

## Rollback or exit

- Before code exists: nothing to roll back.
- Later: extract a context to its own deployable when a §5 trigger fires (a new ADR).

## Evidence required before approval

- The owner agrees the triggers in `architecture.md` §5 are measurable from run records.

## Approval

_Unapproved._

## Changelog

- 2026-10-18: created from the accepted direction of the 18 October proposal, refined.
