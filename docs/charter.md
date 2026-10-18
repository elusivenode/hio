---
id: HIO-CHARTER
title: HIO five-year vision and architecture charter
status: proposed
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
supersedes: "docs/history/2026-10-18-five-year-architecture-proposal.md (as the statement of direction)"
---

# HIO charter

## 1. Mission

HIO helps its portfolio consumers construct and govern portfolios from **deliberately chosen,
independently understood sources of economic risk and return**. It does this by producing:

- point-in-time market and economic observations of known provenance and rights;
- investable factor return series built from those observations by specified, reproducible
  constructions;
- explanatory, risk, expected-return and predictive models, kept separate, each with explicit
  uncertainty;
- exposure-space portfolio analysis that is independent of the vehicles that may later
  implement it;
- implementation analysis that maps desired exposures to candidate vehicles;
- research memory: hypotheses, experiments, failures and outcomes, kept so that knowledge
  compounds.

HIO **informs** decisions. Investment authority belongs to each consumer's own governance. For
the SMSF, that is the trustees.

## 2. The investment problem motivating HIO

The first consumer, the MacDonald Family SMSF, intends to pursue approximately **CPI + 5% a
year over rolling three-year periods**, with strong attention to:

- downside volatility;
- drawdown depth;
- time under water;
- liquidity;
- the probability and severity of missing the real-return objective.

The trustees have not yet settled the objective's exact convention: the CPI series, before or
after tax and fees, compounding and horizon. The adopted strategy still states CPI + 3% over
rolling five years (`macsmsf` `docs/investment-process-roadmap.md`). **HIO must not resolve
these governance questions.** It represents each mandate's objective as a parameter supplied by
the mandate's owner, and it can show the consequences of alternative conventions.

Two research pillars stay visible in every phase:

1. **True diversification and downside-aware construction.** Independently defined economic
   risks and premia; factor overlap; tail and conditional dependence; risk budgets; scenario,
   path and rolling-horizon analysis; and resilience when diversification fails.
2. **Factor dynamics and mean reversion.** Whether factor *valuations and economic states*
   revert in ways that predict subsequent factor returns, tested against momentum, carry and
   structural change. HIO does not assume that reversion works.

## 3. Investment philosophy (design commitments)

1. **Explanation, risk, expected return and prediction are different models.** A model that
   explains past returns has not thereby shown any ability to forecast them.
2. **Returns are accounted, not approximated.** A price index is not a return index. Every
   factor declares its exact return convention, numeraire and financing leg
   ([return accounting standard](standards/return-accounting-and-factor-construction.md)).
3. **The library is broad; models are parsimonious.** HIO maintains many specified series. Each
   fitted model uses a justified subset, and the choice is recorded.
4. **Point-in-time honesty.** What was knowable, and what HIO actually captured, are recorded
   separately. Reconstructed availability is never presented as proof
   ([observations standard](standards/observations-and-point-in-time.md)).
5. **Uncertainty is part of every result.** Estimates without intervals or diagnostics are
   drafts.
6. **Failure is data.** Failed and abandoned experiments are kept, and multiple-testing counts
   are honest.
7. **Exposure before vehicle.** Portfolio construction names exposures. Vehicle selection is
   downstream, and considers tracking, liquidity, fees, tax, execution and operational risk.
8. **Research is not authority.** TAA research can start early. Live tactical authority stays
   with each consumer's governance.
9. **Non-market risks stay visible**: illiquidity, valuation and stale pricing, manager and
   governance risk, tax. A factor model does not see them, so every artefact lists them.
10. **Rights are respected by construction.** Unknown rights mean deny.

## 4. Separation from the SMSF (non-negotiable)

| | HIO | SMSF (`macsmsf`) |
|---|---|---|
| Purpose | research, models, portfolio analysis, implementation analysis | accounting, tax, holdings, cash, realised performance, trustee records, statutory reporting |
| System of record for | observations, reference data, factor library, models, research memory, proposals | everything accounting and governance |
| Writes to the other | **never** | never; it exports a read-only projection |
| Reads from the other | a fund-level projection artefact, once the contract exists | pinned, approved HIO artefacts |
| Release cycle | its own | its own |
| Credentials, storage, deployment | its own | its own |

Detail: [HIO-ADR-0002](decisions/HIO-ADR-0002-systems-of-record-and-smsf-boundary.md).

**No existing SMSF functionality migrates to HIO by default.** Any SMSF-side integration is an
additive SMSF slice, under the SMSF preservation principle.

## 5. Bounded contexts

| Context | Owns |
|---|---|
| **Market data** | acquisition, receipts, observations, vintages, availability, corporate actions, quality, rights records |
| **Reference** | instruments (held or not), listings, identifiers, indices, futures roots and contracts, economic taxonomies |
| **Research library** | state variables, factor specifications, factor runs, reference and academic series |
| **Quantitative models** | exposure estimation, covariance and risk, scenarios, capital-market assumptions, regimes, validation |
| **Portfolio construction** | mandates, policy exposures, constraints, risk budgets, candidate allocations, marginal diversification |
| **TAA research** | hypotheses, signals, walk-forward tests, shadow portfolios, promotion controls (never trade authority) |
| **Implementation analysis** | exposure-to-vehicle mapping, costs, liquidity, tax, tracking, operational constraints |
| **Publication** | artefact envelopes, the rights gate, the status lifecycle, consumer pinning |

Architecture, deployment and evolution triggers: [`architecture.md`](architecture.md).

## 6. Five-year capability trajectory

This is a sequencing hypothesis, reviewed annually, not a commitment.

| Year | Research outcome | Capability |
|---|---|---|
| **1: foundations** | first own-built investable cash, FX, rates, equity and futures factor returns in AUD and USD, validated, with uncertainty; risk of hypothetical portfolios explained by factors | contexts and contracts; PIT capture running daily; releases; the return standard enforced in CI; the harness; first consumer contract |
| **2: multi-asset coverage** | robust cross-asset risk; conditional and tail dependence; credit, carry and trend v1; reference portfolios | paid data where needed; quality monitoring and quarantine; independent validation reports; scenario engine |
| **3: portfolio construction** | capital-market assumptions with uncertainty; factor risk budgets; robust allocation comparison across mandates; after-tax and implementation bridges | mandate abstraction with ≥2 portfolios; implementation analysis |
| **4: tactical research** | evidence on whether valuation, carry, momentum and state signals survive PIT walk-forward testing, costs and multiple-testing haircuts; shadow portfolios | signal library; walk-forward harness reading only captured or publisher-vintage data; decay monitoring; promotion controls |
| **5: mature office** | multiple consumers and mandates; auditable lineage from a decision back to the vendor receipt | replaceable providers (one proven swap); independently scaled workloads where justified; services or APIs where consumers need them |

**Must exist from Year 1**, because it cannot be retrofitted:
- point-in-time capture (lost days cannot be recovered);
- immutable receipts and releases;
- the rights model;
- versioned specifications;
- exposure-space versus instrument-space separation;
- the artefact contract;
- the harness.

## 7. Success criteria for the charter

A new collaborator, human or agent, can answer from the repository alone:
- what HIO is for;
- what has been decided;
- which factor mathematics is authoritative;
- what is under construction;
- what was verified;
- who owns each boundary;
- what can safely change next.

The harness tests this in every slice
([operating model §10](harness/operating-model.md#10-fresh-agent-reproduction-test)).
