---
id: HIO-MAP
title: HIO map (purpose, architecture, threads, settled facts, open questions)
status: proposed   # seed draft for harness-0.9 H1 (OD-0068), revision 2; no effect and no authority until the owner approves it
owner: owner (approves changes); drafted by claude/implementation-agent
last_reviewed: 2026-10-28
max_length: 110 lines
---

# HIO map

> **Navigation only** (precedence rank 5, like `STATUS.md`). Read right after `AGENTS.md`. Every
> line cites a source; where they disagree, the source wins. **No operational state here:** what
> is live, blocked or next is in [`STATUS.md`](STATUS.md). Changes need the owner's approval.
> **Codex:** read only *Purpose*, *Pillars* and *Architecture* before your test plan.

## Purpose

HIO builds **investable factor returns from point-in-time observations of known provenance and
rights**, then uses them for risk, expected-return and exposure-space portfolio analysis
([charter](docs/charter.md) §1). It informs consumers and never decides for them. The first
consumer is the MacDonald Family SMSF. Its objective (about CPI + 5% over rolling three years,
convention unsettled) is a parameter HIO is given, never one it resolves (charter §2).

## Pillars

Two research pillars stay visible in every phase (charter §2):
1. **True diversification:** independent economic risks, tail and conditional dependence, and
   resilience when diversification fails.
2. **Factor dynamics:** whether valuations and states revert in ways that predict factor
   returns. HIO does not assume that they do.

**Year 1 trajectory** (charter §6; a sequencing hypothesis, not a commitment):
- validated cash, FX, rates, equity and futures factor returns in AUD and USD, with uncertainty;
- the risk of hypothetical portfolios explained by factors;
- **daily point-in-time capture running.** Captured vintages cannot be recovered later, so
  every week before capture starts is a week of evidence lost (charter §6, "Must exist from
  Year 1").

## Architecture

| | Current | Target (Year 1) | Undecided |
|---|---|---|---|
| Shape | one repository, modular monolith, import rules in CI ([architecture](docs/architecture.md) §1) | same | services only on a measured trigger (architecture §5) |
| Storage | local filesystem store; no cloud storage (STATUS one-line state) | object store as system of record for receipts, releases, artefacts and catalogue; DuckDB index rebuilt from manifests (architecture §2; HIO-ADR-0009) | provider subscription named `hnf-prod` ([OD-0066](docs/decisions/owner/OD-0066-assign-t0009-review-and-name-subscription.md)); immutability period, replication and second copy (branch `impl/t0009-shared-receipt-and-storage`, `infra/tofu/README.md`, not on `main`) |
| Data | synthetic fixtures only (OD-0019; `tools/check_repo.py` `check_public`) | RBA and NY Fed official data, captured daily ([roadmap](docs/roadmap.md) §1) | every source right unverified (`registers/sources.yaml`; OD-0013) |
| Consumers | none | contract-only clients; the SMSF reads pinned artefacts (HIO-ADR-0002) | consumer contract A05 not started (roadmap §1) |

## Threads (state lives in `STATUS.md`)

| Thread | Serves | Detail |
|---|---|---|
| S1b-1 cash capture (T-0009) | starting the PIT capture clock | [OD-0067](docs/decisions/owner/OD-0067-receive-t0009-review-and-authorise-remediation.md); `reviews/records/REVIEW-2026-10-25-t0009-1.md`; the T-0009 card and OD-0062 to OD-0065 (branch `impl/t0009-shared-receipt-and-storage`, not on `main`) |
| T-0002 source rights | every live operation | `registers/tasks/T-0002-verify-s1-source-rights.md`; `docs/research/T-0002-owner-verification-matrix.md` |
| T-0003 equity TR source | S2 and gate G3 | `registers/tasks/T-0003-equity-total-return-source.md` |
| Futures data procurement | S4 and gate G4 | roadmap §1 (task not yet raised) |
| Research memory | both pillars | `registers/hypotheses.yaml`, `registers/experiments.yaml` |
| Harness-0.9 | long-term context for Claude and Codex | `docs/decisions/harness-0.9-proposal.md` |

## Settled facts worth knowing before you start

- HIO never writes SMSF accounting truth and never imports `macsmsf` (`AGENTS.md` Boundaries;
  HIO-ADR-0002).
- A price-only or state series is never a return factor (`AGENTS.md` Boundaries; return
  standard).
- Unknown rights mean deny; licensed data never enters a prompt (`AGENTS.md`; HIO-ADR-0005).
- S1a's four `data.csv` hashes must be preserved through T-0009 remediation (OD-0067); S1a was
  accepted at its reviewed head (OD-0042).
- Without evidenced publication instants, S1b vintages use P3 `schedule_only`, excluded from
  `as_known_by_market`, until Q-013 is decided (HIO-ADR-0012, P1 to P3 table and gate d3).
- Engineering facts and dead ends: [`knowledge/findings.md`](knowledge/findings.md).

## Open strategic questions (owner)

| Question | Blocks | Source |
|---|---|---|
| Source rights per dataset and operation (RBA, NY Fed) | all live capture | T-0002; OD-0013 |
| Network and credential controls (successor to OD-0038) | provisioning, live runs | OD-0038 |
| Storage immutability, replication, second copy, network default | provisioning | branch `impl/t0009-shared-receipt-and-storage`, `infra/tofu/README.md` (not on `main`) |
| Q-013: capture-time knowability for unevidenced publication instants | `as_known_by_market` claims | [`open-decisions.md`](docs/decisions/open-decisions.md) |
| Q-003, Q-004, Q-005b, Q-006, Q-010 | research use, S1b design, consumers | `open-decisions.md` |
| Q-014: harness-0.9 | how agents keep context | `open-decisions.md` |
