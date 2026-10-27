---
id: HIO-MAP
title: HIO map (big picture, active threads, settled facts, open questions)
status: proposed   # seed draft for harness-0.9 H1 (OD-0068); no effect and no authority until the owner approves it
owner: owner (approves changes); drafted by claude/implementation-agent
last_reviewed: 2026-10-28
max_length: 120 lines
---

# HIO map

> **Navigation only.** One page to read right after `AGENTS.md`. Every line points to its
> source; where they disagree, the source wins. Changes need the owner's approval (harness-0.9
> H1, proposed).

## What HIO is for, now

HIO builds **investable factor returns from point-in-time observations of known provenance and
rights**, then uses them for risk, expected-return and exposure-space portfolio analysis
([charter](docs/charter.md) §1). It informs consumers; it never decides for them. The first
consumer is the MacDonald Family SMSF; its objective (about CPI + 5% over rolling three years,
convention unsettled) is a parameter HIO is given, never one it resolves (charter §2).

Two research pillars stay visible in every phase (charter §2):
1. **True diversification**: independent economic risks, tail and conditional dependence,
   resilience when diversification fails.
2. **Factor dynamics**: whether valuations and states revert in ways that predict factor
   returns. Not assumed to work.

**Year 1 goal** (charter §6): validated cash, FX, rates, equity and futures factor returns in AUD
and USD, with uncertainty; **daily point-in-time capture running**, because lost days cannot be
recovered.

## Where we are (2026-10-28)

| Stage | State | Source |
|---|---|---|
| G1 (A01 baseline: ADRs, standards, harness) | done 2026-10-18 | OD-0008, OD-0011 |
| S1a: synthetic-fixture foundation (contracts, cash legs, investable FX excess) | **accepted** | OD-0042 |
| S1b-1.0 (T-0009): live cash capture, staged | built on synthetic fixtures; review **NOT READY**, 7 findings open; remediation authorised, not started | OD-0062 to OD-0067; `REVIEW-2026-10-25-t0009-1` |
| S1b live operation | **not authorised**: needs owner-verified rights, network and credential controls, storage, and an explicit go-ahead | HIO-ADR-0012; T-0009 card |
| S2 (equity TR) / S3 (rates CMT) | not started; after G2 | [roadmap](docs/roadmap.md) §1 |
| Research | 4 hypotheses `proposed`, 0 experiments | `registers/hypotheses.yaml` |

The roadmap's 90-day plan put S1b live capture in weeks 4 to 8 (mid-November to mid-December
2026). The **PIT capture clock has not started**; every week of delay is a week of lost
captured vintages (charter §6).

## Architecture

| | Current | Target (Year 1) | Proposed / undecided |
|---|---|---|---|
| Shape | one repository, modular monolith, import rules in CI | same | services only on a measured trigger ([architecture](docs/architecture.md) §5) |
| Storage | local filesystem store and an in-memory blob fake; no cloud | object store (receipts, releases, artefacts, catalogue) as system of record; DuckDB index rebuilt from manifests | Azure Blob in `hnf-prod` named (OD-0066); OpenTofu authored, never applied; immutability period, replication and second copy undecided |
| Data | synthetic fixtures only | RBA and NY Fed official data, captured daily | every source right **unverified**; the F1 file's ASX and FENICS columns are an open rights question (OD-0064) |
| Scheduling | none | scheduled capture with a local-time due check | workflow definition required by F-7, disabled |
| Consumers | none | contract-only clients; SMSF reads pinned artefacts | consumer contract (A05) not started |

## Active threads

| Thread | Serves | State | Detail |
|---|---|---|---|
| T-0009 remediation | starting the PIT capture clock (S1b-1) | 7 findings open; plan agreed | OD-0067; `reviews/records/REVIEW-2026-10-25-t0009-1.md`; `handoffs/` |
| T-0002 source rights | every live operation | in progress; U1 to U7 await the owner's reading | `docs/research/T-0002-owner-verification-matrix.md` |
| T-0003 equity TR source | S2 and gate G3 | in progress | `registers/tasks/T-0003-equity-total-return-source.md` |
| Harness-0.9 | long-term context for Claude and Codex | proposed | `docs/decisions/harness-0.9-proposal.md` |
| Futures data procurement | S4 and gate G4 | **not raised** although planned for weeks 4 to 8 | roadmap §1 |

## Settled facts worth knowing before you start

- HIO never writes SMSF accounting truth and never imports `macsmsf` (ADR-0002).
- A price-only or state series is never a return factor (return standard).
- Unknown rights mean deny; licensed data never enters a prompt (ADR-0005).
- S1a outputs and release identities are frozen: the four S1a `data.csv` hashes and the S1a
  `spec_ref` strings must not change (accepted at OD-0042; preservation required by OD-0067).
- S1b capture uses P3 `schedule_only`; no `as_known_by_market` claim until Q-013 is decided.
- Finality (C1 to C7) is deferred in S1b-1.0 (OD-0063).
- Further facts and dead ends: [`knowledge/findings.md`](knowledge/findings.md).

## Open strategic questions (owner)

| Question | Blocks | Source |
|---|---|---|
| Source rights per dataset and operation (RBA, NY Fed) | all live capture | T-0002; OD-0013 |
| Network and credential controls (successor to OD-0038) | provisioning, live runs | OD-0038; T-0009 card |
| Storage: immutability period and lock, replication, second copy, network default | provisioning | `infra/tofu/README.md` |
| Q-013: capture-time knowability for unevidenced publication instants | `as_known_by_market` claims | `docs/decisions/open-decisions.md` |
| Q-003, Q-004, Q-005b, Q-006, Q-010 | research use, S1b design, consumers | `docs/decisions/open-decisions.md` |
| Harness-0.9 (this map's own adoption) | how agents keep context | `docs/decisions/harness-0.9-proposal.md` |
