# Directive to Claude — HIO architecture baseline, agentic harness, durable context, and implementation recommendation

**Date:** 18 October 2026  
**Authority:** HIO solution architecture direction for review and planning  
**Mode:** Inspect, critically assess, refine and **write planning documentation**. Do **not** implement application code, database migrations, cloud resources, data pipelines, or vendor purchases without a separate authorisation.

## 1. Decision and mission

We are proceeding towards **HIO as an independent, sophisticated investment research and portfolio-construction system**, with a five-year capability horizon. The MacDonald Family SMSF is **one consumer** of HIO and remains an independent accounting, investment-implementation and trustee-governance system. These boundaries are not negotiable. Do not conflate HIO's architecture or research priorities with the SMSF's immediate holdings, reporting cadence, or implementation vehicles.

I have reviewed your 18 October architecture proposal, `hio-five-year-architecture-proposal-2026-10-18.md`. Its overall direction is **accepted for further design**, not yet approved for implementation:

- Separate HIO repo, deployment boundary, credentials, storage and data catalogue.
- Modular monolith with explicit bounded contexts and independently runnable/schedulable workloads; extract services when justified, not by default.
- Immutable raw receipts, versioned released datasets, point-in-time semantics, lineage, auditable model runs and pinned consumer artefacts.
- Research findings and factor targets separated from asset/vehicle selection and from SMSF trustee authority.
- Automated quality gates, mathematical validation, licensing controls and strong reproducibility.

Your immediate assignment is to turn this direction into **a coherent, maintainable architecture and programme baseline**, including the **agentic engineering/research harness** that allows multiple Claude/Codex/human collaborators to work accurately over years and across context windows.

You are explicitly authorised to **create and refine documentation and plans** in the appropriate repository location(s), subject to the safeguards below. Do not stop at another advisory essay.

## 2. Investment mission: the architecture must serve the research

The long-term investment objective motivating HIO is to help its portfolio consumers, starting with the SMSF, pursue approximately **CPI + 5% annualised over rolling three-year periods**, while maintaining a strong focus on **downside volatility, drawdown depth, time underwater, liquidity, and probability/severity of missing the real-return objective**. The trustees still need to settle the exact objective convention (tax, fees, CPI series, compounding and horizon); HIO must not silently resolve these governance decisions.

Two research pillars must remain visible in the architecture and roadmap:

1. **True diversification and downside-aware construction**: independently defined economic risks and return premia; factor overlap; tail/conditional dependence; risk budgets; scenario, path and rolling-horizon analysis; resilience when diversification fails.
2. **Factor dynamics and mean reversion**: assess whether factor *valuations and economic states* exhibit useful reversion and predict subsequent factor returns. Test against momentum, carry and structural changes rather than assume reversion always works.

Define separate but linked research entities for **market observations; economic state/characteristics; investable total- and excess-return factors; model specifications; model outputs and uncertainty; hypotheses/signals; portfolio exposure targets; implementation candidates**. Maintain separate explanatory, risk, expected-return and predictive models. **TAA research can start early; live tactical authority stays with each consumer's governance process**.

The HIO reference library can be broad; any fitted model should use a justified, parsimonious subset. Do not design HIO around the 11 current SMSF holdings.

## 3. Non-negotiable factor-return integrity

A central architectural quality gate is to prevent **price indices from masquerading as investment return indices**.

Produce a versioned **Return Accounting and Factor Construction Standard** specifying, with worked examples and invariant tests:

- Price levels versus income-inclusive **total returns**, cash returns and **excess returns**, with precise conventions for compounding and numeraire.
- Equities: cash dividends, corporate actions, timing/reinvestment, withholding where relevant, and distinction between market-price TR, NAV TR, gross/net index returns.
- Bonds: coupon, accrued interest, dirty/clean price, maturity changes, curve shifts, roll-down, coupon reinvestment and day-count conventions.
- Credit: rate duration versus spread duration, coupon/carry, defaults/recoveries and excess-return funding reference.
- FX: spot translation versus *investable* currency positions; forward/hedge settlement, notional, carry, fixing/calendar and financing assumptions.
- Futures/commodities/trend: contract-specific settlement-to-settlement P&L, rolls, contract multiplier/position sizing, margin, collateral, fees, and differences between spot-price, futures excess-return and fully collateralised total-return strategies.
- AUD home-currency treatment and consistent risk-free/collateral legs; ensure no omission or double-counting of cash returns.
- The mathematical distinction between **single-period return identities** and relationships between independently compounded cumulative indices.
- Independent reference comparisons that *diagnose expected differences*, rather than asserting that unlike indices must match.

Every proposed factor specification should declare its **economic exposure, investability, exact return convention, underlying observations, temporal availability, construction algorithm, calendar, unit/currency, financing/collateral legs, limitations, validation and licensing**. State unambiguously when an index is *price-only* or a *non-investable state indicator*. No price-only series may be promoted as a portfolio return factor without a defensible derivation.

Do not assume RBA and US Treasury market data alone can produce a valid S&P 500 total-return series. Identify and resolve the equity total-return source dependency for the first slice, or change the slice rather than using an incorrectly labelled proxy.

## 4. Correct the architecture proposal before implementation

Critically refine these areas of the current proposal; document decisions and alternatives:

### 4.1 Point-in-time semantics

Distinguish **when a value was publicly knowable** from **when HIO actually captured it**. Represent observed values, publisher vintages and rule-inferred backfills honestly. Define `as_known_by_market_at` versus `as_captured_by_hio_at` (or explain a better equivalent), release timestamps, revisions, timezone and market-session semantics. Never permit reconstructed availability to masquerade as proof of historical knowability.

### 4.2 Licensing and publication

Do not rely solely on a single ordered `licence_class`. Model the relevant rights and obligations, including raw retention, internal computation, derivation, storage after termination, distribution to permitted consumers, quotations in trustee packs and audit retention. Default to deny/unknown pending verification; publication and agent use must enforce rights. External vendor assertions remain unverified until checked.

### 4.3 Instrument identity and HIO-001

Before changing or activating the existing, heavily reviewed HIO-001 work, produce a precise **ownership/impact assessment**: what SMSF must own for SF360/broker/accounting reconciliation; what HIO should own as multi-market reference data; identifier history (ISIN, MIC/ticker, other licensed identifiers), futures contracts, and versioned economic classifications. The boundary should avoid duplicate masters and runtime coupling but preserve SMSF functionality. **Do not modify HIO-001 code or migrations now.** Recommend a safe ADR amendment and specific next approval step.

### 4.4 Distributed workloads and evolution

Defend the modular-monolith baseline against alternatives. Make it clear that one codebase can produce independently deployed/scheduled ingestion and research jobs. Define explicit, *measurable* triggers for later split deployments/services, serverless compute, orchestration, agents, eventing and APIs. Evaluate security, data location, observability, recoverability, operational toil and recurring cost. Avoid premature platform complexity without foreclosing it.

## 5. Critical addition: agentic harness and long-term context continuity

This is a **first-class architectural workstream**, not an appendix. The long-lived HIO programme will involve the owner, Claude in repository-editing sessions, Codex as an independent reviewer, and possibly specialised research/data-quality agents. Their context windows, models, tools and session histories will change. Design a collaboration system that **does not depend on chat transcripts or any one model's memory**.

Inspect the current repository's `CLAUDE.md`, project documentation, skills, prompts, roadmap, ADRs, backlog, implementation status and evidence patterns. Assess what has worked and where context has drifted, decisions have been repeated, or research assumptions were lost. Reuse demonstrated patterns, but improve them deliberately.

Produce an **Agentic Operating Model / Harness Specification** addressing:

1. **Canonical knowledge and precedence.** Which version-controlled documents and machine-readable artefacts are authoritative for mission, architectural boundaries, return conventions, approved decisions, research hypotheses, data contracts, project status and next work? Define source-of-truth precedence and conflict resolution. No critical decision may live only in a chat.
2. **Repository navigation and agent onboarding.** A concise root instruction file (e.g. `CLAUDE.md` / `AGENTS.md`) that points to canonical documents without duplicating the entire programme. Use scoped, discoverable skills/adapters and explicit triggers; keep agents from indiscriminately loading enormous context.
3. **Durable task and session handoffs.** Standard task cards with objective, approved scope, non-goals, linked ADRs/specs, dependencies, acceptance tests, environment constraints, evidence, open issues, owner and review status. Define an end-of-session handoff format that a fresh agent can use without undocumented conversational knowledge.
4. **Research memory.** A versioned hypothesis and experiment register recording economic thesis, point-in-time sample, data/return definition, attempts and variants, negative findings, uncertainty, outcomes and follow-up decisions. Preserve failed experiments; avoid rediscovery and multiple-testing amnesia.
5. **Agent roles and permissions.** Architecture lead, implementation engineer, quantitative researcher, data-quality investigator and independent reviewer, with clear inputs/outputs and separation of duties. Do not let autonomous agents certify their own research, silently revise canonical factor definitions or promote research to trading authority.
6. **Change control and review gates.** How a model/agent proposes and amends an ADR, factor specification, licence assessment, dataset release, model promotion or roadmap decision; who approves; what tests/evidence are required; what counts as exploratory versus approved. CI should validate links, schemas, provenance and documentation drift where practical.
7. **Artifact-driven collaboration.** Prefer committed, versioned Markdown/YAML/JSON and executable specifications over lengthy chat summaries. Every handoff must identify exact repository revision, artefact IDs, known assumptions and unresolved questions. Include concise templates and one worked end-to-end example.
8. **Long-term maintainability.** How we retire obsolete guidance, prevent duplicated/conflicting documents, version the harness, detect stale runbooks/links, and periodically review whether the agent workflow remains useful.
9. **Security and licences.** Agents receive least privilege; secrets stay outside prompts and committed files; market-data licences apply to agent contexts and external services too. No research data automatically crosses the HIO/SMSF boundary.
10. **Efficiency.** Distinguish durable knowledge from ephemeral working notes. Define a minimal fresh-session bootstrap path and a context budget so the harness reduces, rather than magnifies, single-operator burden.

Specify the **minimum viable harness we should implement in the very first slice**, and which advanced agent behaviours are deferred. Do not build an elaborate autonomous agent platform before the deterministic research foundation exists.

The result should allow any new Claude/Codex session to answer, from the repository alone: *What is HIO for? What has been decided? Which factor math is authoritative? What is under construction? What was verified? Who owns this boundary? What can I safely change next?*

## 6. Document and refine the programme now

**This request explicitly authorises documentation work, not just a report.** Inspect the current source documents and then create or revise the appropriate canonical files **in the repository you can safely edit**. If a new HIO repository is not yet created or authorised, stage HIO-owned architecture documents in a clearly separated planning location in the existing repo, labelled for later migration; do not pretend the target repo exists. Avoid making the SMSF repo the permanent system of record for HIO research.

At minimum deliver:

1. **HIO five-year vision and architecture charter** — mission, investment philosophy, five-year capability trajectory, HIO/SMSF separation, bounded contexts and deployment evolution.
2. **Architecture decision register** — proposed/approved/deferred decisions, alternatives, trade-offs, owners, consequences and explicit gate into implementation. Do not silently treat proposals as adopted policy.
3. **Data and return-convention standards** — observation/PIT, reference identity, licence permissions, dataset releases, full economic return accounting and factor-specification template.
4. **Agentic harness design and operating manual** — minimal onboarding instructions, canonical context map, role/permission model, task and handoff templates, research hypothesis log and review/promotion process.
5. **Integrated programme roadmap** — 90-day deliverables, 12–18 month research outcomes, and five-year capability horizon, with dependencies, risks and decision gates. Preserve SMSF's independent operating roadmap and specify consumer integration points rather than merging the two plans.
6. **Current implementation plan** — bounded slices with executable acceptance criteria, source/vendor prerequisites, infrastructure decisions, cost hypotheses and explicit exclusions.
7. **Open decisions / architectural risks register** — distinguish what is proposed, approved, externally unverified, blocked and ready.

Update the existing roadmap and planning index so that there is **one clear current plan**, not several competing essays. Cross-link or supersede old documents without destroying useful historical rationale. Follow existing repository conventions and avoid duplicating content across files.

Where the current repository has important existing controls or incomplete work (e.g. HIO-001, backup/promotions, accounting reconciliation), link to them and preserve their independent status; do not silently absorb them into the HIO programme.

## 7. Preferred next implementation step — make an explicit recommendation

After the documentation and architectural challenge, advise **one preferred next implementation slice** and explain why it is the best first irreversible investment of effort.

I currently expect a slice resembling **HIO-S1: independent repo/foundation + scheduled authoritative observations + cash/FX/validated equity total-return experiment**, but you must challenge the scope, data availability and prerequisites. You may recommend a smaller walking skeleton or a reordered first slice if it better reduces risk.

Your recommendation must contain:

- Exact capabilities and repository boundaries.
- Inputs, sources, licensing checks and total-return methodology.
- Minimum infrastructure and workload distribution, with a rationale for each resource.
- Minimum viable agentic harness components included from the start.
- Acceptance tests: mathematical identities, source quality, PIT/vintage behaviour, immutable releases, licensing, repeatability, independence from `macsmsf`, and fresh-agent handoff/reproduction.
- Dependencies and blocker-resolution sequence, especially the S&P 500 TR source and HIO-001 boundary.
- Expected qualitative effort and monthly cost ranges clearly marked as estimates, with vendor quotes distinguished from estimates.
- Scope exclusions and stop conditions.
- Concrete verification evidence required before promotion to the next slice.

Do **not** start implementation merely because you have recommended a slice. We will review and approve it separately.

## 8. Working procedure and safeguards

1. **Inspect before editing.** Check repository state, actual roadmap and existing conventions. Do not infer that a document or feature is implemented from its title.
2. **Ground claims.** Mark repository facts, proposed choices, and unverified vendor assertions separately. Where research has not been performed, state so; do not invent source coverage, licence terms, prices or validation results.
3. **Critique independently.** Challenge my direction wherever the financial mathematics, empirical evidence, operator constraints, or architectural trade-offs warrant it. Do not collapse into agreement.
4. **No non-document changes.** No source-code edits, DB migrations, new cloud resources, broker access, deployment, credential updates, paid subscriptions, or changes to production reporting.
5. **No unapproved HIO-001 changes.** Document the ownership impact and a safe plan only.
6. **Preserve existing functionality and plans.** Documentation edits should be additive and traceable, without rewriting SMSF's legal strategy or trustee decisions.
7. **Do not commit without existing repository conventions permitting it.** If you can safely commit documentation, use a dedicated branch/commit with an informative message; otherwise leave an explicit changeset and instructions. Do not merge or deploy.
8. **Validate documentation.** Check cross-references, document statuses, ADR links, terminology, no conflicting roadmap authorities, and that a fresh collaborator can follow the onboarding path.

## 9. Required response to me

Return a concise **decision-oriented completion report**, not a repeat of the entire architecture:

1. **Architectural verdict** — what you accept, changed or challenge, with reasons.
2. **Files created/updated** — exact relative paths and what each now governs, plus revision/branch if applicable.
3. **Agentic harness** — how long-term context is preserved, how roles collaborate and the minimal session bootstrap/handoff works.
4. **Roadmap delta** — specific changes to the previous 90-day and five-year plans; separate HIO and SMSF dependencies.
5. **Return-integrity proof obligations** — total/excess-return gate and remaining source gaps.
6. **Preferred immediate implementation slice** — one recommendation, alternatives rejected, acceptance criteria and why it should start first.
7. **Decisions requiring my approval** — a short numbered list with your recommended option for each.
8. **Unresolved risks and external checks** — especially vendor licensing, market-data coverage and S&P 500 total-return data.

**Success means that the architecture, roadmap, mathematical standards and agent collaboration practices are durable, findable and actionable from version-controlled artefacts — and that we have one well-justified, safely bounded next implementation step awaiting approval.**
