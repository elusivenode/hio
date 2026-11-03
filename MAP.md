---
id: HIO-MAP
title: HIO map (purpose, architecture, threads, settled facts, open questions)
status: current   # approved as part of harness-0.9a by OD-0091 (seed at 2df83b4); navigational, rank 5, no independent authority; substantive changes need the owner's approval (operating model §4.1)
owner: owner (approves changes); drafted by claude/implementation-agent
last_reviewed: 2026-10-29
max_length: 110 lines
---

# HIO map

> **Navigation only** (precedence rank 5, like `STATUS.md`). Read right after `AGENTS.md`. Every
> line cites a source; where they disagree, the source wins. **No operational state here:** what
> is live, blocked or next is in [`STATUS.md`](STATUS.md). Substantive changes need the owner's
> approval; mechanical link, path or citation fixes follow operating model §4.1 (proposed).
> Codex's bootstrap does not include this file (harness-0.9 H11 is not adopted).

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
| Storage | the evidence store is provisioned in `hnf-prod` and empty (B-1, [OD-0125](docs/decisions/owner/OD-0125-receive-verify-2-accept-t0011-authorise-b1.md) correction 2); the B-2 probe ran once ([evidence](docs/evidence/b2/README.md)) | object store as system of record for receipts, releases, artefacts and catalogue; DuckDB index rebuilt from manifests (architecture §2; HIO-ADR-0009) | immutability, replication and network settings decided ([OD-0119](docs/decisions/owner/OD-0119-adopt-h3-h4-decline-h5-codex-assignment-draft.md)); the second copy is deferred to the first capture month (H4 S-7); C5 timing open (B-2) |
| Data | synthetic fixtures (OD-0019; `tools/check_repo.py` `check_public`), plus the dated 2026 RITS and NSW reference calendars from the RBA (`src/hio/reference/calendars/`; D7, OD-0076) | RBA and NY Fed official data, captured daily ([roadmap](docs/roadmap.md) §1) | five S1b-1 cash datasets owner_verified for `hio_internal` ([OD-0116](docs/decisions/owner/OD-0116-rights-answers-u1-u6.md) correction 1, OD-0118) and D7 (OD-0076); every other source unverified (`registers/sources.yaml`) |
| Consumers | none | contract-only clients; the SMSF reads pinned artefacts (HIO-ADR-0002) | consumer contract A05 not started (roadmap §1) |

## Threads (state lives in `STATUS.md`)

| Thread | Serves | Detail |
|---|---|---|
| S1b-1 cash capture (T-0009) | starting the PIT capture clock | [T-0009 card](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) (S1b-1.0 accepted, [OD-0079](docs/decisions/owner/OD-0079-accept-t0009.md)); OD-0062 to OD-0067, OD-0074 to OD-0078; `reviews/records/REVIEW-2026-10-25-t0009-1.md` and its `VERIFY-2026-10-28-*` records; next: finality staging (card §7) and Authorisation B (card §8) |
| T-0002 source rights | every live operation | `registers/tasks/T-0002-verify-s1-source-rights.md`; `docs/research/T-0002-owner-verification-matrix.md` |
| T-0003 equity TR source | S2 and gate G3 | `registers/tasks/T-0003-equity-total-return-source.md` |
| Futures data procurement | S4 and gate G4 | roadmap §1 (task not yet raised) |
| Research memory | both pillars | `registers/hypotheses.yaml`, `registers/experiments.yaml` |
| Harness-0.9 | long-term context for Claude and Codex | `docs/decisions/harness-0.9-proposal.md` |
| hiomux orchestration pilot | parallel workers and Codex runs from one orchestrator | outside the repository (`~/.hio-runs/PROTOCOL.md`); [OD-0072](docs/decisions/owner/OD-0072-hiomux-orchestration-pilot.md), OD-0073, [OD-0077](docs/decisions/owner/OD-0077-codex-reviewer-network.md) |

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
| Source rights beyond the five S1b-1 datasets (free history sources: draft rows) | criterion 8 of base camp; history research | T-0002; `docs/research/T-0002-free-history-sources-matrix.md` |
| C5 timing rule on Azure (whole-second `Last-Modified`) | B-3 go-live | `docs/evidence/b2/README.md`; HIO-ADR-0012 §4.3.3 |
| Base camp, the procurement-readiness milestone (proposed) | data purchases | [`docs/base-camp.md`](docs/base-camp.md) |
| Q-013: capture-time knowability for unevidenced publication instants | `as_known_by_market` claims | [`open-decisions.md`](docs/decisions/open-decisions.md) |
| Q-003, Q-004, Q-005b, Q-006, Q-010 | research use, S1b design, consumers | `open-decisions.md` |
| Q-014: harness-0.9 | how agents keep context | `open-decisions.md`; `docs/decisions/harness-0.9-proposal.md` |
