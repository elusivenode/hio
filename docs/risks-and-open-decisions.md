---
id: HIO-RISKS
title: Open decisions and architectural risks
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-18
---

# Open decisions and architectural risks

Status vocabulary:

| Status | Meaning |
|---|---|
| `proposed` | recommendation awaiting the owner |
| `approved` | decided |
| `ext-unverified` | depends on an unchecked external claim |
| `blocked` | cannot proceed (blocker named, with a re-verify date) |
| `ready` | can start once approved |

## 1. Decisions requiring owner approval

| # | Decision | Recommendation | Status |
|---|---|---|---|
| D1 | Approve HIO as a separate system and repository, with a modular monolith (HIO-ADR-0001) | approve | proposed |
| D2 | Systems of record and the SMSF projection boundary, fund-level only (HIO-ADR-0002) | approve | proposed |
| D3 | HIO-001 boundary option C1: activate unchanged; amend ADR 0003 to declare `HIO_ECONOMIC` SMSF-local (HIO-ADR-0003, T-0004) | approve C1 | proposed |
| D4 | Temporal semantics: `knowable_at`/basis versus `captured_at` (HIO-ADR-0004) | approve | proposed |
| D5 | A multi-dimensional rights model with default deny, including agent and external-processing rights (HIO-ADR-0005) | approve | proposed |
| D6 | Immutable releases, artefact envelope, pin-by-id (HIO-ADR-0006) | approve | proposed |
| D7 | The return accounting standard v0.1 as a CI gate (HIO-ADR-0007), optionally after independent review | approve after review | proposed |
| D8 | The harness: precedence, roles, MVH (HIO-ADR-0008) | approve | proposed |
| D9 | A manifest-derived catalogue; no hosted database initially (HIO-ADR-0009) | approve | proposed |
| D10 | S1 is the cash and FX walking skeleton; equity moves to S2 (HIO-ADR-0010) | approve | proposed |
| D11 | Futures PoC root: ZN (an independent duration construction) or GC (gold carry) | ZN | proposed |
| D12 | The object-storage vendor for HIO: Tigris (an existing vendor, separate bucket and keys) or another | Tigris | proposed |
| D13 | Whether H.10 triangulation may use FRED (needs an API key secret) | decide after T-0002 | proposed |

## 2. Risks

| ID | Risk | Likelihood / impact | Mitigation | Status |
|---|---|---|---|---|
| R-01 | **A price index masquerades as a return** in a factor or model | medium / high | the return standard; `series_class` CI gate; invariant catalogue | proposed |
| R-02 | **Reconstructed availability treated as PIT evidence** | medium / high | HIO-ADR-0004; knowledge modes; promotion rule | proposed |
| R-03 | **No licensable equity TR source** within the 90 days | medium / medium | T-0003 in parallel; S3 can substitute for S2 in the schedule | ext-unverified |
| R-04 | **A licence breach through publication or agent context** | low–medium / high | the rights model; default deny; procedural agent rule in S1; a tool-enforced gate when the first licensed source arrives | proposed |
| R-05 | **Futures data procurement slips**, or the terms forbid storage | medium / medium | start procurement at G1; PoC-sized purchase; vendor scorecard | ext-unverified |
| R-06 | **Dual instrument master** if HIO-001 activates without a boundary decision | medium / medium | T-0004 before SMSF activation | proposed |
| R-07 | **Coupling to accounting** (HIO reading SMSF tables, or the SMSF pack depending on HIO timing) | low / high | HIO-ADR-0002; CI independence check; the March pack independent | proposed |
| R-08 | **Spurious diversification**: residuals read as diversification; stale prices understate beta | medium / high | triangulation and residual tests; non-market-risk listing on artefacts; H-0004 | proposed |
| R-09 | **Operator capacity**: one person, holiday period, review rounds | high / medium | small slices; the toil budget; harness efficiency targets; review only for gating work | proposed |
| R-10 | **Harness overhead exceeds its value** | medium / medium | MVH only; the 25% overhead stop condition; quarterly harness review | proposed |
| R-11 | **GitHub Actions cron unpunctual** for capture | medium / low–medium | soak measurement; punctuality trigger to move the scheduler | ext-unverified |
| R-12 | **Weak TAA evidence** promoted on in-sample results | medium (later) / high | pre-registration; variant counts; captured-vintage requirement; authority stays with the consumer | proposed |
| R-13 | **Vendor lock-in** through vendor-specific continuous series or formats | low / medium | own constructions from contracts; raw receipts in our format; vendor-exit rehearsal (Y2) | proposed |
| R-14 | **Staged documents diverge** from the future repository, or are mistaken for SMSF policy | low / medium | the staging notice; `macsmsf` pointer lines; migration procedure | proposed |
| R-15 | **Overengineering**: services, orchestrator or database before a trigger | medium / medium | measurable triggers; ADR required to adopt | proposed |
| R-16 | **Objective convention unresolved** in the SMSF, so HIO analyses use the wrong target | medium / medium | mandate parameters supplied by the consumer; HIO shows sensitivity to conventions; never defaults them | proposed |

## 3. External claims awaiting verification

All are tracked in [`../registers/sources.yaml`](../registers/sources.yaml):
- the terms of use and access methods of RBA, NY Fed, Treasury and FRB;
- publication times and time zones;
- SOFR's start date;
- RBA table coverage;
- GitHub Actions free minutes and cron behaviour;
- Tigris versioning and object lock;
- the licensing and cost of the S&P DJI index, EOD vendors, issuer files, CME DataMine,
  Databento and Norgate;
- French and AQR terms;
- the conventions noted [EXT] in the return standard (day-counts, coupon frequency, FX futures
  quoting).

## 4. Blocked

| Item | Blocked on | Re-verify by |
|---|---|---|
| S1 implementation | G1 (T-0001) | at G1 |
| S1 publication beyond exploratory | T-0002 | at G1 + 2 weeks |
| S2 | T-0003 / G3 | at G1 + 4 weeks |

## 5. Ready, once approved

T-0002, T-0003 and T-0004 can start immediately on approval. T-0005 (S1) can start on fixtures
at G1.
