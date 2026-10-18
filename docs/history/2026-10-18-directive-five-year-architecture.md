# HIO — Five-Year Architecture Direction and Programme Reassessment

**To:** Claude (repository-aware engineering and research collaborator)  
**From:** HIO solution architecture lead  
**Date:** 18 October 2026  
**Assignment:** Strategic architecture and roadmap reassessment — **review and propose; do not implement**

## 1. A material correction to the framing

The previous strategic review (`hio-strategic-review-research-and-portfolio-construction-2026-10-18.md`) contains valuable observations about the current repository and SMSF investment process. But it conflates two fundamentally different concerns:

1. **Home Investment Office (HIO):** A sophisticated, general-purpose, extensible investment research, portfolio construction, risk and decision-support capability. Its strategic horizon is **five years**, with the intention to develop and compound its capabilities over much longer periods.
2. **MacDonald Family SMSF and its existing application (`macsmsf`):** One investment entity, one implementation portfolio and **one consumer** of HIO outputs. Its accounting, tax, trustee governance, performance measurement, reporting and operational controls are distinct concerns.

**The SMSF does not define HIO's research universe, technical ceiling, architecture, factor coverage or long-term ambition.** The fund's present size, number of positions, age and cadence of trustee decisions are relevant to its *investment implementation and governance*, not to the allowable sophistication of HIO.

The architecture must preserve the freedom for HIO to serve other portfolios, hypothetical portfolios, investment mandates and research questions without requiring changes to `macsmsf`.

Do **not** recommend that HIO remain a handful of local scripts merely because the SMSF presently has 11 positions and four months of performance history. Equally, do **not** design a distributed platform just to demonstrate architectural sophistication. Make decisions based on bounded contexts, workloads, operating cost, isolation, reproducibility, security, growth options and measurable value.

## 2. Your role and expectations

Act as a principal solution architect working with a quantitative investment researcher and a platform engineering lead. Be independent and critical. The user is an experienced data engineer; avoid elementary explanations of ETL, schemas or API integration.

We want an **excellent, modular base** from which HIO can evolve over five years: rigorous quantitative research, high-quality market data, systematic multi-asset factor construction, robust risk estimation, portfolio construction, capital-market assumptions and evidence-driven tactical asset allocation (TAA).

**You have architectural latitude** to evaluate separate applications and repositories, independently deployed services, managed databases, object storage, event-driven/serverless compute, scheduled batch, workflow orchestration, specialist agents, research workbenches and dedicated model execution environments. You should evaluate operational complexity and cost critically; no particular topology or cloud platform is pre-approved.

The design should allow research workflows to scale without coupling them to the SMSF application's release cycle, database schema or runtime availability.

## 3. System-of-systems boundaries (non-negotiable)

Propose explicit ownership, interfaces and data flows among at least the following bounded contexts:

- **HIO market data:** Vendor acquisition, historical backfills, revisions, corporate actions, point-in-time availability, licensing, lineage and quality monitoring.
- **HIO research data and factor library:** Economic state variables, raw market observations, tradable factor returns, benchmark/reference series, derived features and reproducible construction specifications.
- **HIO quantitative models:** Exposure estimation, covariance/risk, scenarios, expected-return assumptions, regime analysis, model validation and research results.
- **HIO portfolio construction:** Policy/target exposures, constraints, risk budgets, candidate allocations and marginal diversification analysis, independent of investable tickers.
- **HIO TAA research and decision support:** Hypotheses, signals, walk-forward tests, shadow allocations and promotion controls. Separate research from authority to trade.
- **HIO implementation analysis:** Mapping target exposures to investable products, execution constraints, costs, liquidity, tax, tracking and operational considerations.
- **SMSF (`macsmsf`):** Existing broker/bank ingestion, accounting, tax, authoritative holdings and cash flows, realised performance, trustee records and statutory/operational reporting.

Specify which system is authoritative for each domain. HIO may consume holdings and cash-flow *snapshots* from the SMSF through a stable, read-only contract; HIO must not mutate accounting truth. Conversely, HIO can publish dated research results, risk estimates, factor exposures and allocation proposals to consumers, including the SMSF, without embedding their calculations into the SMSF accounting pipeline.

**Avoid dual ownership of the instrument master.** The existing HIO-001 work contains a security identity and taxonomy foundation inside `macsmsf`, but it is not necessarily the long-term master for a multi-portfolio research platform. Examine whether to retain a narrow local implementation/instrument dimension, move reference ownership to HIO, or establish an explicit synchronisation/translation contract. Do not assume that a database migration is the correct boundary.

The existing `macsmsf` application must remain fully functional. New work must be additive, backward-compatible, separately testable and safely deployable. There should be **no migration of existing accounting functionality to HIO by default**.

## 4. Five-year capability vision

Lay out a credible evolution, not an indiscriminate feature list.

**Year 1 — Research foundations:** Establish bounded contexts, governance and interfaces; verified multi-source observations; point-in-time datasets; factor specification contracts; an independently deployable research execution path; first factor return series and risk experiments; maintain the SMSF quarterly process separately.

**Year 2 — Multi-asset factor coverage:** Expand equity, rates, credit, FX, commodities, carry and trend, prioritised by data fidelity and research value; versioned reference portfolios; robust covariance/exposure estimation; scenario and conditional-risk analysis; automated quality monitoring and independent validation.

**Year 3 — Portfolio construction:** Documented capital-market assumptions, factor risk budgets, constraints and robust allocation evaluation; model uncertainty; after-tax/implementation bridges; historical and forward-looking scenario engines; candidate portfolio comparison across mandates.

**Year 4 — Tactical research and policy intelligence:** Test economically justified predictive signals with point-in-time and walk-forward designs; paper portfolios, model monitoring, decision journals and controlled promotion into policy or bounded live tactical decisions. Model confidence and signal degradation explicitly.

**Year 5 — Mature modular investment office:** Multiple portfolio consumers/mandates; replaceable market-data providers; explainable research lineage; independently scaled workloads; portfolio and scenario services; decision governance; auditable outcomes and mature operational resilience.

Treat this as a *hypothesis for sequencing*, not a rigid commitment. Identify which capabilities or architectural options must be preserved early to avoid costly redesign later, and which can be deliberately deferred.

## 5. Quantitative and financial-design requirements

Maintain a strict separation among:

1. Economic state variables and realised macro observations.
2. Economic shocks and systematic risk exposures.
3. Independently constructed **factor-mimicking or tradable strategy returns**.
4. Expected return premia and forward-looking assumptions.
5. Signal forecasts and tactical policies.
6. Instrument holdings and legal implementation vehicles.
7. Actual realised portfolio performance and tax/accounting outcomes.

The **factor reference library must be broader than any particular model's chosen factors**. We may maintain dozens of series and fit only a parsimonious subset for a specific purpose.

Initial coverage should consider global/Australian equity beta, AUD/USD and other currency exposures, AUD and US sovereign duration, gold, broad commodity futures, credit excess returns, cross-asset trend and selected carry strategies; later expand to equity styles, curve and volatility exposures where warranted. Each series needs a specification: underlying observations, universe, benchmark, weighting, currency/numeraire, financing, collateral, roll rules, rebalancing, transaction costs, return convention, history, release availability, vendor rights and validation methodology.

Do not treat spot prices, yield changes, inflation levels or adjusted closes as investable total returns without defensible construction. Do not confuse an apparently uncorrelated residual with alpha or genuine economic diversification. Treat active and trend-following portfolios as potentially time-varying exposures. Require uncertainty, proxy limitations and non-market risks to be visible.

**HIO should be able to assess a hypothetical exposure that the SMSF does not yet hold and may never implement.** Portfolio construction specifies desired economic exposures; vehicle selection is a separate downstream exercise.

## 6. Data acquisition as a core competency

We are prepared to pay for high-quality data when necessary. Evaluate a heterogeneous sourcing strategy across official central banks/statistical agencies, exchanges, specialist commercial providers, research libraries and institutional datasets. We are particularly interested in *underlying observations* from which independent factor indices can be constructed, with **timely updates**, broad histories and durable storage/derived-data rights.

Assess:

- Source authority, completeness, reliability, revisions and service availability.
- Daily or otherwise appropriate timeliness, market calendars, release timestamps, vintages and backfill behaviour.
- Historical contract chains and settlement data for futures; curves and cash legs for fixed income; spot/forward data for FX; corporate actions, dividends and point-in-time fundamentals for equities.
- Licensed raw storage, derived-index ownership, audit retention, internal API consumption and vendor exit.
- Independent cross-checks, quality gates and quarantining incomplete data.
- Data acquisition expenditure versus coverage and scientific validity, not just cost per API request.

Start procurement evaluation early but only contract for material capability gaps. Do not categorically defer contract-level futures data because the SMSF currently uses ETFs. A small futures data proof of concept may be one of the most informative early investments.

## 7. Architecture choices to compare, not prejudge

Please compare **at least three feasible deployment patterns**, for example:

A. Modular monolith / separate HIO application with object storage and scheduled local/batch jobs.

B. Small set of domain services with serverless ingestion and computation, shared durable storage and independent research workers.

C. More distributed event-driven, agent-assisted research platform with specialised compute and independently deployed APIs.

For each, evaluate bounded-context integrity, code ownership, service contracts, latency/timeliness, batch versus interactive workloads, reproducibility, observability, secrets/licence controls, operational burden, failure recovery, deployment safety, cost at realistic and expanded workloads, and ease of evolution.

**We value modularity and replaceability above premature microservices.** A clean service boundary can be established in code and contracts before independent deployment is justified. Conversely, source-ingestion workloads or compute-intensive research jobs may deserve independent serverless execution immediately when the benefits are clear.

Consider where agents meaningfully help: vendor documentation research, quality anomaly triage, experimental hypothesis generation, independent reviews, research summarisation and decision-pack production. Agent outputs must be reproducible or explicitly marked as qualitative, governed and subject to human approval. Agents are **not** autonomous trade authorities, unreviewed data arbiters or substitutes for deterministic numerical computation.

Assess whether research should be in a separate repository and deployment domain, and how versioned outputs should be delivered to consumers through APIs, object-store artefacts or events. Be specific about why you would choose one boundary over another.

## 8. Reassess Claude's previous review

Read the full strategic review and inspect the relevant repository files before reaching conclusions. Do not simply paraphrase the previous review.

Preserve useful conclusions: separation from accounting, provenance, disciplined modelling, data uncertainty, tax/liquidity/governance risk, preservation of the existing app, and scepticism about unsupported predictive TAA.

Revisit conclusions that depend too heavily on today's SMSF: restricting factor research to seven series; deferring futures construction categorically; limiting HIO to local-only files; treating 2027 TAA research as out of scope; and using the fund's transaction cadence as the ceiling for quantitative capability.

Also correct methodological issues: holdings-based exposure and returns-based beta are related but not numerically interchangeable; global equity proxies must match their index definitions; a commodity future rolled return is not a continuous adjusted-price change; gold is not interchangeable with an inflation index; trend-index versus DBMF agreement is not an acceptance test; and independent risk models need not agree by construction.

**Distinguish what you observed in the repository from what you infer or propose.** The prior review was against `main` at `1502ab8` and a database refreshed 10 October 2026; verify the current state before citing it as current.

## 9. Near-term work: deliver an extensible base without an infrastructure detour

Propose a revised first **90-day programme** alongside a five-year capability roadmap.

My tentative preferred order (challenge if appropriate):

1. **HIO-A01: Architecture and research charter.** Bounded contexts, systems of record, separation from SMSF, initial domain contracts, factor methodology template, security/licensing posture, and ADRs for repository/deployment boundaries.
2. **HIO-A02: Market-data and research reference foundation.** A minimal but durable isolated HIO project, observation/availability/vintage semantics, storage/versioning, dataset catalogue, deterministic calculations and tests. No dependence on the SMSF accounting refresh.
3. **HIO-A03: Three vertical experiments.** (i) sovereign yield curve to constant-maturity bond return; (ii) foreign equity plus FX translated into AUD with exact decomposition; (iii) single-market individual-contract futures settlements to rolled excess return, including financing/collateral assumptions. Each should identify real vendor/data limitations.
4. **HIO-A04: Factor library v0 and independent model.** Reproducible first series, source cross-checks, explicit limitations and a small factor-covariance/risk experiment for a *hypothetical portfolio* independent of the SMSF.
5. **HIO-A05: Consumer integration contract.** Define (not necessarily implement) how `macsmsf` reads approved dated HIO research results and how HIO optionally reads authorised SMSF positions. No core accounting changes.

Keep existing SMSF Phase 1 reporting integrity, trustee objective review, exposure look-through and production-safety tasks on their separate operational roadmap. Show interfaces and dependencies; do not subsume those tasks into HIO research work packages.

For each near-term work package provide: purpose, boundary/owner, essential decisions, deliverable, acceptance tests, data dependencies, operational costs, and what specifically should **not** be built yet.

Include a **first end-to-end demonstration** proving HIO is not an extension of SMSF: independently source data, construct and validate two or more factors, analyse a hypothetical multi-asset portfolio, and publish a versioned risk/research artefact that can later be consumed by multiple clients.

## 10. Deliverables for this review

Produce a single cohesive strategic architecture proposal (Markdown) containing:

1. **Executive recommendation** and where the earlier assessment should be retained, modified or rejected.
2. **Five-year target operating model:** capabilities and evolution by phase.
3. **Bounded-context diagram and ownership matrix:** HIO versus SMSF, with explicit source-of-truth and contract boundaries.
4. **Options assessment:** three architecture/deployment patterns with honest cost/complexity trade-offs and a selected *initial* architecture.
5. **Conceptual domain and data contracts:** observations, factor definitions, factor runs, model results, portfolios, decisions and consumed projections; no speculative exhaustive schema.
6. **Initial factor programme and data procurement hypotheses:** scientifically defined return series, raw inputs, independent validation and when to pay.
7. **First 90 days:** sequenced, bounded work packages with independently verifiable acceptance criteria.
8. **Roadmap reconciliation:** what to keep from `docs/investment-process-roadmap.md`, what belongs to the SMSF programme and what belongs to the new HIO programme, with a dependency map.
9. **Architecture decision log:** the irreversible or costly decisions to resolve now, those to defer, and explicit exit criteria for scaling/distributing a service.
10. **Top failure modes and mitigations:** factor misspecification, spurious diversification, look-ahead, vendor lock-in, licence breaches, overengineering, coupling to accounting, weak TAA evidence and operational fragility.
11. **Recommended immediate next implementation slice**, sufficiently precise to commission separately **after** we approve this review.

Where possible, ground recommendations in evidence from the repo. Mark external claims requiring current vendor/licensing validation rather than asserting them as fact.

## 11. Operating constraints and immediate instruction

- This assignment is **review and design only**. Do not change code, schemas, migrations, live applications, deployment configuration or the existing roadmap.
- Do not reorganise repositories or instantiate cloud resources as part of this review.
- Preserve all current SMSF accounting, analytics, reporting and UI/API behaviour; any future integration must be additive and independently regression-tested.
- Do not conflate a research prototype with a production service, or a research hypothesis with investment authority.
- Do not force factor science into the existing `macsmsf` database just because that is the repository currently available.
- Do not over-index on today's fund size or holdings in designing a five-year HIO.
- Do not mistake architectural restraint for an instruction to build an unsophisticated system.

**The immediate goal is to agree an excellent, extensible HIO foundation and a credible first 90 days of work.** Bring back the architecture assessment, options, trade-offs and proposed roadmap for joint review before implementation begins.
