---
id: HIO-ROADMAP
title: HIO integrated programme roadmap
status: proposed
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-24
supersedes: "the 90-day and five-year sections of docs/history/2026-10-18-five-year-architecture-proposal.md"
---

# HIO programme roadmap

**This is HIO's only roadmap.** The SMSF's operating roadmap remains `macsmsf`
`docs/investment-process-roadmap.md`, which is independent and owned by the trustee programme.
This document lists the **integration points** between the two. It does not merge them.

Dates count from **G1** (owner approval of the A01 baseline), written as `G1 + n weeks`.
Calendar estimates assumed G1 in early November 2026, and include the December–January holiday
period. **G1 completed on 2026-10-18** (OD-0008, OD-0011), so `G1 + n weeks` counts from then.

## 1. The next 90 days (G1 → G1 + 13 weeks)

| Weeks | Deliverable | Research outcome | Task / slice |
|---|---|---|---|
| 0 (now) | A01 baseline (this directory) | a binding vocabulary and mathematics for every later result | T-0001 |
| 0–4 | S1 source rights and timing verified (in parallel with S1a; gates S1b only) | knowability claims for S1b have evidence | T-0002 |
| 0–4 | equity TR source scorecard and decision | knowing whether, and how, an investable equity TR can be built | T-0003 → HIO-ADR-0011 |
| 0–4 | HIO-001 boundary decision (SMSF documentation only) | no dual instrument master | T-0004 |
| 1–4 | **S1a: synthetic-fixture foundation** (repository + history-preserving migration, harness MVH, contracts, cash legs + investable FX excess on fixtures; no network or real data) | every A01 contract executable and tested before real data touches it | T-0005 (S1a) |
| 4–8 | **S1b: live official observations** (real sources behind the rights gate, bucket, scheduled capture, soak, triangulations) | the first validated factor: AUD-investor USD exposure, decomposed exactly; the **PIT capture clock starts** | T-0005 (S1b) |
| 4–8 | futures data procurement for the PoC (vendor terms, a sample) | the rights to build our own futures returns are known | task to be raised at G1 |
| 6–9 | **S2 equity TR** (if T-0003 resolves) or **S3 rates CMT** (if not) | investable equity in AUD, unhedged and hedged; or AU and US duration factors | S2 / S3 |
| 9–12 | the other of S2/S3 | a four-family factor set: cash, FX, rates, equity | S3 / S2 |
| 8–11 | consumer contract specification (schemas + contract tests; **no `macsmsf` code**) | the SMSF can later consume HIO without coupling | A05 |
| 12–13 | **D1 demonstration**: a hypothetical-mandate risk report published as an artefact, consumed by two contract-only clients | proof that HIO is independent and produces a research result | S5 (part) |

**Moved out of the 90 days, compared with the 18 October proposal:**
- **The futures PoC build (S4)** moves to about G1 + 14–18 weeks. Procurement lead time and the
  holiday period make it the most likely item to slip. Procurement still starts in the 90 days.
- **The factor covariance experiment** in D1 uses only the series that exist by week 12, so
  D1 does not wait for futures.

## 2. 12–18 month research outcomes

| By about | Outcome | Depends on |
|---|---|---|
| G1 + 4 months | validated AUD-numeraire factor set: cash, FX (spot, carry, cross), AU and US duration (CMT), equity in AUD (unhedged and hedged), each with a triangulation report | S1–S3 |
| G1 + 6 months | futures excess returns (rates, equity index, gold), with the futures-versus-funded construction comparison explained; first gold carry decomposition | S4; paid data |
| G1 + 6 months | **first registered experiments** for H-0001 (the regime dependence of the duration–equity correlation) and H-0002 (AUD defensiveness), pre-registered, explanatory and risk only | factor set; ALFRED or ABS vintages for regimes |
| G1 + 8 months | risk model v1: sample, EWMA and shrinkage covariance with bootstrap uncertainty; conditional and tail dependence; scenario replays on reference mandates | factors; S5 |
| G1 + 8 months | **SMSF integration point**: an HIO risk artefact available to the SMSF's June 2027 feasibility work, *if* the SMSF approves the exporter and reader slices | A05; SMSF slices |
| G1 + 12 months | capital-market assumptions v0 (building blocks, ranges, uncertainty), not optimisation | yields, spreads, earnings yields (some paid) |
| G1 + 12–18 months | trend v0, by replication of a published study; credit data procurement decision; automated quality monitoring; first vendor-exit rehearsal | futures breadth; budget |

## 3. Five-year capability horizon

The charter's Year 1–5 trajectory ([charter §6](charter.md#6-five-year-capability-trajectory))
is the horizon. It is reviewed annually, at gate G6.

The factor-dynamics pillar (H-0003, valuation mean reversion) is a **Year 3–4** research track
by design. Its evidence quality depends on captured vintages that start in S1.

## 4. Decision gates

| Gate | Decision | Evidence required |
|---|---|---|
| **G1** | approve the A01 baseline (ADRs 0001–0010, the standards, the harness) | T-0001 complete |
| **G2** | promote S1 (after S1b) and start S2/S3 | the S1 verification evidence (implementation plan) |
| **G3** | equity TR source (HIO-ADR-0011) | T-0003 scorecard |
| **G4** | futures data contract beyond the PoC | the PoC results; rights verified |
| **G5** | first consumer integration (SMSF exporter and reader slices, in `macsmsf`) | A05 contract; SMSF preservation evidence plan; trustee interest |
| **G6** | annual charter and architecture review | trigger metrics; the harness review |

## 5. SMSF integration points

| SMSF programme item (`macsmsf`) | Relationship to HIO | Rule |
|---|---|---|
| Phase 1 reporting integrity; Q2 pack | none | — |
| December 2026 review of the objective convention | becomes the SMSF **mandate parameters** HIO uses | HIO does not decide or default these |
| Area 1 exposure look-through (December 2026) | SMSF-owned, issuer-document based | HIO exposure artefacts may complement it later; never a dependency |
| Area 2 downside (March 2027) | SMSF computes it as planned | **must not depend on HIO** |
| Area 3 feasibility (June 2027) | candidate first consumer of HIO risk and CMA artefacts | only through G5, pinned artefacts, and rights allowing pack quotation |
| Area 4 decision register | trustee decisions stay in the SMSF; they may cite HIO artefact ids | HIO holds no decisions with authority |
| HIO-001 activation | SMSF-owned; preceded by the T-0004 decision | no HIO dependency on activation |
| A17 backup and promotion | SMSF programme | independent of HIO |

## 6. Risks to this roadmap

See [`risks-and-open-decisions.md`](risks-and-open-decisions.md). The schedule-critical ones are:
- R-03: the equity source;
- R-05: futures procurement;
- R-09: operator capacity and the holiday period.
