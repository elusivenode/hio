---
id: HIO-IMPL-PLAN
title: HIO current implementation plan
status: proposed
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
decisions: [HIO-ADR-0010]
---

# HIO implementation plan

No slice is approved. **S1 is the recommended next slice.** Each slice needs an **authorised** task
card (an OD record) before work starts.

## Slices

| Slice | Capability | Prerequisites | Status |
|---|---|---|---|
| **S1** | independent repository and harness MVH; scheduled capture of official observations; AUD and USD cash legs; investable USD-cash-versus-AUD excess return with exact decomposition; publication gate | G1, T-0002 (for publication), owner creates the repository and bucket | recommended, awaiting approval |
| S2 | equity total return (USD) → AUD unhedged and hedged, per HIO-ADR-0011 | T-0003 → G3; S1 | planned |
| S3 | AU and US government CMT total and excess returns (2/5/10y), with decomposition | S1; rights for RBA F2 and the Treasury par curve (T-0002 extension) | planned |
| S4 | futures PoC: one root (ZN recommended, GC alternative), individual-contract settlements → rolled excess + collateral TR | procurement (G4-lite: PoC data only); S1 collateral leg; S3 for the ZN triangulation | planned |
| S5 | library v0 release + covariance with uncertainty + hypothetical mandate R1 risk report + D1 demonstration | S1 + at least one of S2/S3 | planned |
| A05 | consumer contract schemas and contract tests (HIO side only) | S1 contracts package | planned |

---

## HIO-S1: walking skeleton (recommended)

### Why this is the best first irreversible investment

1. **It starts the point-in-time capture clock.** This is the only resource that cannot be
   bought back later. Every day before capture starts is a day of `captured` evidence lost for
   Year-4 research.
2. **Every later factor depends on its outputs:**
   - excess returns need cash legs;
   - hedged and unhedged foreign returns need the FX construction;
   - futures total returns need collateral.
3. **Its sources are official and probably keyless**, so it needs no procurement. Its rights are
   verifiable within days (T-0002).
4. **It exercises every foundational contract at small scale:**
   - receipts;
   - observations with `knowable_at` and `captured_at`;
   - vintages;
   - releases;
   - the rights gate;
   - artefacts;
   - the harness and CI.
5. **It avoids the trap in the expected scope.** An S&P 500 total return cannot be built from
   RBA and Treasury data. A mislabelled proxy would violate HIO-ADR-0005 and 0007 on the first
   day.

### Alternatives considered for the first slice

| Alternative | Why not first |
|---|---|
| The owner's expected S1 (cash + FX + validated equity TR) | no verified licensable equity TR source; T-0003 must resolve first |
| Yield curve → CMT first | more construction risk (curve type, interpolation, pricing); depends on the cash legs for excess returns anyway |
| Futures PoC first | procurement lead time and cost; depends on the collateral leg |
| A documentation-only S0 | the harness cannot be CI-checked without a repository; the MVH is part of S1 instead |
| Hosted catalogue and orchestrator from the start | HIO-ADR-0009 and the architecture triggers |

### Capabilities and repository boundary

- **A new private repository `hio`.** The contents of `macsmsf/hio/` are migrated per
  `hio/README.md`, and `macsmsf` gets a pointer commit.
  - **S1 code never imports, connects to or holds credentials for `macsmsf`.**
- **Packages:**
  - `contracts`: observation, manifest, rights, spec and envelope schemas;
  - `marketdata`: four source adapters, receipts, vintages, quality gates;
  - `library`: three constructions from specs;
  - `publish`: envelope, rights and status gate.
- **Harness MVH:** operating model §9, items 1–9.

### Inputs, sources and rights checks

| Series | Source | Use | Rights status now |
|---|---|---|---|
| RBA cash rate (overnight) | RBA statistical tables | `cash.aud.overnight` | unverified → T-0002 |
| RBA AUD/USD 4pm | RBA statistical tables | `fx.usd_cash_vs_aud.excess` | unverified → T-0002 |
| SOFR | NY Fed | `cash.usd.overnight` | unverified → T-0002 |
| T-bill rates (4w, 13w) | US Treasury | USD cash **rate** triangulation: levels and horizon-aligned, `state_indicator`; no bill return is claimed | unverified → T-0002 |
| AUD/USD noon NY (H.10) | Federal Reserve Board | FX triangulation | unverified → T-0002. If it is reachable only via FRED with a key, the owner decides whether to add a secret or drop it |
| RBA bank-bill rate (1m) | RBA | AUD cash **rate** triangulation: levels and horizon-aligned, `state_indicator`; no bill return is claimed | unverified → T-0002 |

**Total-return methodology:** the three specs in `specs/factors/` (v0.2.0) and return standard
(v0.2) §3.2, §4.2, §9 and §10. No equity, no bonds, no futures.

### Minimum infrastructure and workload distribution

| Resource | Rationale | Not chosen |
|---|---|---|
| Private GitHub repository `hio` | independent release, CI and access | a monorepo inside `macsmsf` (HIO-ADR-0001) |
| GitHub Actions: CI + scheduled capture (cron) | no new vendor; jobs run off the operator's machine from day one | Fly scheduled machines or cloud schedulers, held as a trigger-based fallback (punctuality trigger, `architecture.md` §5) |
| One object-storage bucket (Tigris, separate from `macsmsf`'s, with versioning) and two bucket-scoped keys (write: CI capture/publish environment; read: review) | a durable, off-machine system of record for receipts and releases | a hosted database (HIO-ADR-0009) |
| Local and CI DuckDB index | catalogue queries | — |

**Workloads:**
- capture: one entrypoint per source, scheduled after the documented publication times (set from
  T-0002);
- build: after capture;
- CI: per change;
- publish: manual, owner-triggered.

### Acceptance tests (all must pass)

| ID | Test | Category |
|---|---|---|
| S1-A1 | CI proves no `macsmsf` import, dependency, credential or network route (dependency scan + import check + job network allow-list) | independence |
| S1-A2 | import rules (architecture §1) enforced; a deliberate violation fails CI | boundary |
| S1-A3 | receipts are write-once: the content hash verifies on read; a second write to an existing key is refused by code; bucket versioning is on | immutability |
| S1-A4 | OBS-INV-001: an identical re-fetch makes no new vintage; a changed fixture value makes vintage 2; both retrievable | vintages |
| S1-A5 | OBS-INV-002/003 property-based tests for `as_captured_by_hio`, `as_known_by_market` and `reconstructed`; **OBS-INV-007** (the original/revision/current-only-backfill fixture, observations standard §4.1) passes: a schedule-only backfill is absent from `as_known_by_market` | PIT |
| S1-A6 | OBS-INV-005: no `valid_time` is derived from a UTC instant (test + lint rule) | PIT |
| S1-A7 | cash legs: RA-INV-003 and the spec invariants exact, including the RA §3.2 fixtures (Fri→Mon, a four-day holiday, Thu→Mon, the AUD weekend) and the CASH-USD-INV-3 look-ahead trap (Monday's SOFR is not used for the Fri→Mon period); the period `knowable_at` equals the last rate's publication | math |
| S1-A8 | FX: FXC-INV-1/2 exact over the full history; the FXC-INV-4 weekend fixture; RA-INV-007 for rising and falling `q`; RA-INV-016 cumulative test compounds per-period identities | math |
| S1-A9 | decomposition release (spot, carry, cross) published alongside the excess release | math |
| S1-A10 | three triangulation reports, each with the pre-registered expected-difference model and an outcome classification, and **no pass/fail on agreement**: FX RBA vs H.10 (spot); USD cash vs bills; AUD cash vs bills. The cash reports compare **rates**: levels, and horizon-aligned realised overnight compounding against the bill yield, after the declared conversions. They are not return comparisons | validation |
| S1-A11 | every release rebuilt from a clean CI checkout reproduces its `content_sha256`; the releases standard §6.1 fixtures pass (determinism; status events do not change identity; a withdrawn artefact is refused by a pinned consumer while its bytes verify; no self-reference) | repeatability |
| S1-A12 | **fail-closed rights fixtures for every operation S1 performs** (rights standard §3): fetch, store raw, build, store derived, rebuild, publish to `hio_internal`. Each refuses with no partial output on `deny`, `unknown`, an unsatisfied `conditional`, or unverified evidence. A real source is used only once T-0002 records `owner_verified` for every permission that operation requires | licensing |
| S1-A13 | **soak:** ≥10 consecutive Sydney business days of unattended capture; the punctuality distribution recorded; gaps recorded as capture gaps; a deliberately failed run raises an alert | operations |
| S1-A14 | quality gates: a malformed receipt is quarantined; staleness detection fires in a test | quality |
| S1-A15 | harness CI checks pass (links, front matter, YAML schemas, STATUS ≤150 lines, secret patterns); a session handoff is written | harness |
| S1-A16 | **fresh-agent reproduction test** (operating model §10) passes: a new session answers the seven questions with file references and reproduces a release hash | handoff |

### Dependencies and blocker resolution

1. **T-0001 (G1).** This also authorises the owner to create the repository and bucket.
2. **Repository + bucket + keys** (owner). The `macsmsf/hio/` migration commit.
3. **Build on fixtures.** Starts at G1; it does not wait for T-0002.
4. **T-0002 rights verification.** Required **before any live operation on a real source**:
   fetch, store, build, rebuild or publish (rights standard §3). Fixture work on synthetic
   sources does not wait for it.
5. **Soak** (S1-A13), in parallel with review preparation.
6. **Independent review → G2.**

Off the S1 path:
- **S&P 500 TR:** resolved by T-0003 in parallel. It decides S2 and does not block S1.
- **HIO-001 boundary:** T-0004 is independent of S1. It must precede SMSF activation of
  HIO-001, not S1.

### Effort and cost (estimates; no vendor quotes obtained)

| Item | Estimate |
|---|---|
| Engineering effort | about 3–5 weeks of focused, agent-assisted effort; plus a 2-week elapsed soak (overlapping); plus review rounds (the HIO-001 history suggests 2–3 rounds) |
| Monthly running cost | GitHub (private repository, Actions minutes within the free allowance [EXT]): about US$0–5; object storage (<1 GB): about US$0–5; **total about US$0–15 a month** |
| Paid data | none |

### Scope exclusions (S1)

- equity, bonds, credit, futures and commodity series;
- FRED/ALFRED, unless T-0002 decides on H.10 via FRED;
- covariance, risk models, portfolios;
- hosted database, orchestrator, API, UI, event bus;
- any `macsmsf` change beyond the migration pointer;
- vendor contracts;
- autonomous agents.

### Stop conditions

Stop and return to the owner if any of the following happens:
1. A source's terms deny raw retention or derivation.
2. Capture punctuality misses (more than 2 hours late, or skipped) exceed 20% of soak runs.
3. Any S1 work appears to need `macsmsf` data or code.
4. An identity invariant cannot be made exact. That means a spec or standard defect, which needs
   a new version, not a tolerance.
5. Harness and CI overhead exceeds about 25% of slice effort. Review the harness scope.

### Verification evidence required before promotion to S2/S3 (G2)

- the tagged revision, with CI green, including S1-A1 to S1-A16 results;
- release ids and hashes for the three factors and the decomposition;
- soak run records and the punctuality summary;
- the three triangulation reports;
- `owner_verified` rights records for all S1 sources;
- an independent review record (APPROVE, or conditions closed);
- the fresh-agent test record;
- updated `STATUS.md`; the handoff.
