---
id: HIO-ARCH
title: HIO architecture baseline
status: approved
approved_by: OD-0008   # at a82aa0d, blob 9e384d1c9de2
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
decisions: [HIO-ADR-0001, HIO-ADR-0002, HIO-ADR-0006, HIO-ADR-0009]
---

# HIO architecture baseline

## 1. Shape

**One repository, one codebase, many independently runnable workloads.** Bounded contexts
(charter §5) are packages with enforced import rules. Each workload is an entrypoint of the same
versioned image or lockfile, and can be scheduled, sized and deployed on its own.

```
hio (repository)
├── src/hio/contracts/       # schemas: observation, release manifest, factor spec, artefact envelope, projections
├── src/hio/marketdata/      # source adapters → receipts → observations; quality gates
├── src/hio/reference/       # instruments, listings, identifiers, indices, futures contracts, taxonomies
├── src/hio/library/         # factor construction from released observations, per spec
├── src/hio/models/          # exposure, covariance, scenarios, CMAs (reads releases only)
├── src/hio/portfolio/       # mandates, exposure-space portfolios, risk budgets
├── src/hio/taa/             # hypotheses, signals, walk-forward (reads PIT views only)
├── src/hio/implementation/  # exposure → vehicle analysis
├── src/hio/publish/         # envelope, rights gate, status checks
├── specs/                   # factor and model specifications (versioned data)
├── registers/  docs/  templates/  handoffs/   # harness (see harness/operating-model.md)
└── tests/
```

**Import rules**, enforced in CI from S1:
- `models`, `portfolio`, `taa` and `implementation` may import `contracts` and read released
  datasets. They never import `marketdata` adapters.
- `taa` reads only point-in-time views.
- Nothing imports `macsmsf`.
- `publish` is the only code that writes artefacts.

## 2. Storage and catalogue

| Store | Holds | Authority |
|---|---|---|
| Object store (dedicated HIO bucket) | `receipts/` (raw, content-addressed), `releases/` (Parquet + manifest), `artefacts/` (published envelopes), `catalogue/` (append-only manifest records) | **System of record.** Write-once by convention, content-hash keys, versioning on |
| Local or CI derived index (DuckDB) | a queryable catalogue rebuilt from `catalogue/` records | derived; disposable; rebuildable |
| Git | specs, standards, registers, decisions, code | system of record for definitions and decisions |

**No hosted database in the first slices** (HIO-ADR-0009). This is a deliberate change from the
18 October proposal, which proposed a hosted Postgres catalogue. The catalogue's content is
small, append-only and derivable from immutable manifests. A hosted database would add a
second system of record, a credential, a backup obligation and a running cost before anything
needs online, concurrent query. The trigger to adopt one is in §5.

## 3. Workload topology (initial)

| Workload | Runs as | Rationale |
|---|---|---|
| Source capture (one entrypoint per source) | **scheduled job, off the operator's machine, from S1** | point-in-time capture continuity: a missed day of `captured` data cannot be recovered |
| Release builds and factor runs | on-demand or scheduled job, same image | deterministic; reruns are safe because inputs are immutable |
| Model runs (later: bootstrap, walk-forward) | ephemeral job, sized per run | compute-heavy, but bursty |
| CI | per change | tests, import rules, schema checks, reproducibility rebuild, documentation checks |
| Research workbench | local notebooks or scripts reading releases via `hio` APIs | exploratory; outputs are not artefacts until re-run as pinned jobs |
| Publication | job | the single point that enforces rights and status |

**Initial hosting hypothesis (to be confirmed in S1 approval):**
- GitHub Actions for CI and scheduled capture;
- an S3-compatible bucket from an existing vendor (Tigris is already used by `macsmsf` per
  `macsmsf` ADR 0001), as a **separate bucket with separate, bucket-scoped keys**.

Unverified [EXT]:
- GitHub Actions cron punctuality;
- free-tier minutes;
- Tigris versioning and object-lock features.

## 4. Why a modular monolith, not services, now

| Alternative | Why not now | What would change the answer |
|---|---|---|
| Domain services (3–5 deployables) | multiplies release coordination, secrets, telemetry and failure modes for one operator. Context integrity is achievable with import rules and contracts | a trigger in §5 fires for a specific context |
| Serverless functions per source | per-function packaging and secrets for sources that each run for seconds a day; the scheduled-job model gives the same isolation per run | a source needs a different network or secret boundary, or event-driven triggering |
| Event-driven or agent platform | ordering, replay and idempotent consumers before there are two consumers; an agent platform before the deterministic foundation exists | ≥2 consumers needing push; agents with proven, governed value (harness §8) |
| Hosted orchestrator (Prefect/Dagster) | a scheduler plus the catalogue's run records covers fewer than ten jobs | §5 trigger |

The baseline **does not foreclose** any of these:
- workloads are already separate entrypoints;
- contracts are explicit schemas;
- storage is object-store-native and portable;
- lineage lives in manifests, not in a tool.

## 5. Measurable evolution triggers

A trigger is evaluated at each quarterly harness review (operating model §8), using run records.
Adoption still needs an ADR.

| Adopt | When any of these is measured |
|---|---|
| Hosted catalogue database | concurrent catalogue writers are needed (>1 job writing in the same minute, regularly); **or** index rebuild exceeds 60 s; **or** a consumer needs online lookups |
| Workflow orchestrator | >10 scheduled jobs with inter-job dependencies; **or** >2 manual backfill or rerun interventions a month for two consecutive months |
| Separate scheduler or host for capture | scheduled-run punctuality misses (start delayed >2 h, or skipped) on >5% of runs over 20 business days; **or** a source requires a fixed egress IP or a private network |
| Separate deployable for a context | its failure or release cadence disturbs another context twice in a quarter; **or** it needs a different secret or rights boundary; **or** its compute exceeds the shared runner limits |
| Serverless or elastic compute for models | a model run exceeds 30 minutes or the runner memory on standard hardware; **or** >20 runs are queued in a week |
| Artefact API (HTTP) | a consumer needs parameterised queries; **or** ≥3 consumers; **or** artefact download plus local query is >10 s for a consumer's normal use |
| Event notifications | ≥2 consumers need to act within one hour of publication |
| Agent automation beyond the minimum viable harness | harness §8 criteria |

## 6. Security, data location and rights

- **Separate blast radius.** HIO credentials never grant access to `macsmsf` resources, and
  vice versa.
- **Least-privilege keys:**
  - a write key used only by capture and publish jobs, held in the CI secret store;
  - a read-only key for review and research.
- **No personal data in HIO.** The future SMSF projection is fund-level, with no member data
  (HIO-ADR-0002).
- **Data location.** HIO's data in S1 is public market data, so location is not legally
  material. Prefer an Australian or nearby region for latency and because the SMSF projection
  will follow later.
- **Rights travel with data:**
  - every release and artefact carries a rights record;
  - publication and agent use are gated ([rights standard](standards/rights-and-licensing.md)).

## 7. Observability, recoverability and toil

- **Observability.** Every job writes a run record (start, end, revision, image digest, inputs,
  outputs, outcome) to `catalogue/`, plus logs. One alert channel receives failures and missed
  schedules.
- **Recoverability:**
  - the object store plus git is the complete state;
  - the catalogue index is rebuildable;
  - bucket versioning protects against overwrite;
  - a periodic inventory of receipt hashes is kept in a second location, using the
    `macsmsf` A17-A practice as the pattern.
- **Toil budget.** The target is <1 hour a week of operator attention for running capture and
  releases. Exceeding it for a month triggers a harness and architecture review.

## 8. Cost hypotheses (estimates, not quotes)

| Item | Estimate |
|---|---|
| Repository, CI and scheduled capture (GitHub) | US$0–10 a month at S1 scale |
| Object storage (<5 GB) | US$0–5 a month |
| Paid data | none in S1 |
| Equity total-return source (T-0003) | open; vendor EOD plans are commonly tens of US$ a month |
| Futures PoC data | one-off, plausibly hundreds to low thousands of US$ |

No quotes have been obtained. Every figure above is [EXT] and unverified.
