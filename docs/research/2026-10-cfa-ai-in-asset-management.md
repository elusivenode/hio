---
id: HIO-RESEARCH-CFA-AI-ASSET-MANAGEMENT-2025
title: "Research brief: CFA Institute (2025), AI in Asset Management, and its implications for HIO"
status: draft              # non-binding research brief; NOT an approved decision, standard or roadmap change
owner: owner (decides); brief supplied by the owner; integrated by claude/documentation-agent
created_at: 2026-10-25
binding: false
source_publication: 2025-11-18
method: >-
  An original synthesis supplied by the owner (file hio-research-brief-cfa-ai-asset-management-2025.md,
  sha256 d4249cfa676d8033bc4f69d7544c462a9db261e6ae5a40cffc9e01bd9acdc4d5, 2026-10-25). On integration
  it was checked for consistency with the approved charter, roadmap, ADRs, standards and harness,
  and its internal references were adjusted. The chapter-level statements about the monograph
  were NOT re-verified against the monograph by the integrating agent; check them against the
  publication before relying on them. No monograph text is stored in this repository.
---

# AI in Asset Management (CFA Institute, 2025): implications for HIO

## 0. Purpose and authority

This is a **non-binding research brief**, not an approved architecture decision, standard, roadmap revision, implementation authorisation, or statement of investment performance. Its purpose is to keep the Home Investment Office (HIO) oriented toward robust, investment-useful multi-asset research and an eventual agentic investment office.

**Primary source:** Joseph Simonian (editor), *AI in Asset Management: Tools, Applications, and Frontiers*, CFA Institute Research Foundation, 2025, 214-page monograph. https://rpc.cfainstitute.org/research/foundation/2025/ai-in-asset-management-book

**Full monograph:** https://rpc.cfainstitute.org/sites/default/files/docs/research-reports/rf_aiinassetmanagement_full-monograph_online.pdf

**Publisher's practitioner brief:** https://rpc.cfainstitute.org/sites/default/files/docs/support/rf_aiinassetmanagement_practitioner-briefs_full-monograph_online.pdf

The monograph is a collection of contributions with different techniques and perspectives; it does **not** constitute a validated HIO design, nor demonstrate that an autonomous multi-agent investment office outperforms simpler methods. Distinguish below between **[SOURCE]** (themes explicitly addressed by the publication), **[HIO INTERPRETATION]** (architectural inference), and **[PROPOSAL]** (not yet approved).

> **Integration note (2026-10-25).** Where this brief touches approved HIO material, the approved
> material governs (HIO-ADR-0008 precedence). Consistency notes added on integration are marked
> **[INTEGRATION NOTE]**; they cite the approved document and change nothing in it.

Do not copy or check the copyrighted monograph into a public repository. Store this original synthesis and links instead. Verify rights separately before ingesting third-party text into persistent agent knowledge bases.

## 1. Executive findings

1. **[SOURCE]** The book examines unsupervised learning, network theory, support vector machines, ensemble learning, deep learning, reinforcement learning (RL), natural language processing (NLP), commodity futures prediction, quantum computing and ethical AI. Its editor explicitly frames the collection around using AI to deepen understanding of market phenomena and practical decision-making (preface; chapters 1–10).
2. **[HIO INTERPRETATION]** The most durable lesson for HIO is to separate the **financial research engine** (measurable, point-in-time, independently reproducible) from the **agent coordination layer** (planning, synthesis, challenges, escalation). ML methods and LLM agents play different roles.
3. **[SOURCE]** The network-theory and unsupervised-learning chapters make methods for studying changing market relationships relevant to asset management. **[PROPOSAL]** Evaluate network and regime features as complements to, not substitutes for, simple covariance, drawdown and factor-exposure baselines.
4. **[SOURCE]** Ensemble-learning and supervised/deep-learning chapters examine nonlinear relationships and forecasting, including overfitting and model validation. **[PROPOSAL]** Use walk-forward testing, stable baselines, genuine publication/capture timestamps, economic interpretability, cost-adjusted outcomes and data-snooping controls before giving signals portfolio influence.
5. **[SOURCE]** The RL chapter treats portfolio and hedging decisions as sequential problems incorporating practical constraints and trading frictions. **[PROPOSAL]** Reserve RL for comparative research after classical constrained allocation, rebalancing and control-policy baselines are established; RL is not a first production allocator.
6. **[SOURCE]** Fabozzi's NLP chapter discusses financial documents, LLM applications and agent-like workflows and explicitly raises historical-model knowledge contamination as a backtesting issue. **[HIO INTERPRETATION]** This is especially relevant to HIO's two-clock observation/quality model and future text-derived signals ([observations standard](../standards/observations-and-point-in-time.md); [HIO-ADR-0004](../decisions/HIO-ADR-0004-temporal-semantics.md)).
7. **[SOURCE]** The commodity futures chapter links economic theories (including term structure, hedging pressure and momentum-related features) with empirical prediction and implementation considerations. **[HIO INTERPRETATION]** It supports our planned futures factor research (roadmap §2, S4), but does not license price-only commodity indexes as investable total returns ([HIO-ADR-0007](../decisions/HIO-ADR-0007-return-accounting-standard.md); [return accounting standard](../standards/return-accounting-and-factor-construction.md): a `price_only` series never becomes a total return).
8. **[SOURCE]** The ethical-AI chapter addresses transparency, accountability, explainability, privacy and human oversight. **[PROPOSAL]** Bind agent authority to mandates and evidence, with owner approval for investment actions.

**Bottom line:** Treat AI as a research-method and information-processing capability to be rigorously evaluated, not as a substitute for return accounting, capital-market expertise or portfolio risk discipline.

## 2. Chapter-level relevance map

| Chapter (monograph page) | Source focus | HIO relevance and proposed evaluation |
|---|---|---|
| 1. Unsupervised Learning I (p. 1) | Clustering, latent structure, unlabeled financial observations | Explore conditional regimes and factor clustering; test stability against simple rolling correlations and macro labels. |
| 2. Unsupervised Learning II: Network Theory (p. 15) | Graph relationships and systemic interconnectedness | Explore factor-dependence networks, concentration and contagion diagnostics; avoid overstating predictive power. |
| 3. Support Vector Machines (p. 40) | Classification/regression methods | Possible benchmark classifier for regime/risk-state experiments; not first architecture priority. |
| 4. Ensemble Learning in Investment (p. 52) | Combining predictive models, nonlinear effects | Use diversified forecasts only where out-of-sample evidence beats transparent baselines after costs. |
| 5. Deep Learning (p. 72) | Neural models and representation learning | Potential future research for high-dimensional or sequential data; data requirements and explainability limit near-term usefulness. |
| 6. Reinforcement Learning and Inverse RL (p. 92) | Sequential portfolio/hedging decisions under uncertainty and frictions | Future tactical allocation laboratory; compare to deterministic constrained allocation/rebalancing rules. |
| 7. Natural Language Processing (p. 127) | Document extraction, embeddings, LLMs, sentiment, workflows | High potential for specialist research agents extracting issuer disclosures and assembling source-grounded dossiers. |
| 8. Machine Learning in Commodity Futures (p. 151) | Theory-grounded commodity return prediction, basis, momentum and cross-sectional models | Research tradable futures excess returns, collateral and roll mechanics before constructing TAA signals. |
| 9. Quantum Computing for Finance (p. 178) | Emerging quantum approaches | Horizon scanning only; no current HIO implementation dependency. |
| 10. Ethical AI in Finance (p. 187) | Transparency, risk, accountability, human oversight | Evidence-backed recommendations, mandate-scoped permissions, human approvals and ongoing agent evaluation. |

*Page numbers are the book's printed pages, not PDF viewer page indices.*

## 3. The HIO research architecture implied by this reading

The following is **HIO architectural interpretation**, not a book-prescribed system:

```
Authoritative market evidence and instrument information
        ↓
Point-in-time capture, rights and quality gates
        ↓
Economically valid return/factor constructions and versioned releases
        ↓
Research laboratory: baselines, hypotheses, ML models and evaluations
        ↓
Mandate-specific risk and portfolio-construction research
        ↓
Agentic investment office: orchestrator and specialist research roles
        ↓
Owner-approved decisions for SMSF / future family trust
```

**Boundary rules**:
- Never replace captured evidence with an LLM summary; link each extracted claim to a source, location, acquisition date and applicable rights.
- Keep prices distinct from total returns; express excess returns, funding, coupons, distributions, collateral, roll costs and currency conversion explicitly.
- Specify the information availability cutoff for every backtest input, including revisions, derived features, agent-produced labels and model versions. An LLM's pretrained knowledge may contain future information; historical text-signal research must control this rather than assuming that the document timestamp alone suffices.
- Quantitative calculations remain deterministic and testable. Agents can request computations, synthesise findings, propose investigations and challenge hypotheses; their narrative is not authoritative numeric data.
- Keep public/common HIO research separate from each mandate's private positions, permissions and decisions. Preserve MACSMSF accounting and trustee authority.

**[INTEGRATION NOTE]** These boundary rules restate approved commitments rather than add new
ones: captured evidence and rights ([HIO-ADR-0005](../decisions/HIO-ADR-0005-rights-model.md),
[rights standard](../standards/rights-and-licensing.md)); prices versus returns (HIO-ADR-0007);
information cutoffs (HIO-ADR-0004); and the SMSF boundary, under which HIO never writes to the
SMSF ([charter §4](../charter.md#4-separation-from-the-smsf-non-negotiable);
[HIO-ADR-0002](../decisions/HIO-ADR-0002-systems-of-record-and-smsf-boundary.md)). The point
about an LLM's pretrained knowledge leaking future information is not yet covered by an approved
standard; it would need one before any text-derived signal is used historically.

## 4. Proposed agentic investment-office capability model

This is a **future target-role taxonomy**, not a recommendation to deploy a fleet of agents now. Start with tools and role contracts, splitting into persistent agents when needed.

**[INTEGRATION NOTE]** These are *investment-research* roles. They do not change the approved
engineering harness, its roles or its permissions ([operating model](../harness/operating-model.md);
[HIO-ADR-0008](../decisions/HIO-ADR-0008-canonical-knowledge-and-harness.md)). Adopting any of
them would need its own decision.

| Role | Inputs | Output contract | Required challenge |
|---|---|---|---|
| Investment-office orchestrator | Mandates, agenda, task/evidence state, current capabilities | Work plan, bounded delegation, exception brief, proposed owner decision | Cannot grant itself trading or standards authority |
| Evidence/data steward | Source licences, receipts, vintage/quality/release IDs | Eligible dataset and audit trail; refusals when incomplete | Independent rebuild and quality checks |
| Macro and factor researcher | Validated return series, macro vintages, cited research | Explicit hypothesis, assumptions, factor exposures, uncertainty | Regime changes, spurious correlations, ex-ante availability |
| Quantitative methods researcher | Fixed experiment specification and permitted datasets | Baseline/ML comparison, OOS scores, uncertainty, reproducible code/results | Leakage and multiple testing |
| Risk and portfolio specialist | Research releases and mandate constraints | Exposure decomposition, stress scenarios, proposed allocations | Tail risk, diversification failure, implementation constraints |
| Instrument/implementation analyst | Fund documents, terms, fees, NAV/price/liquidity | Instrument-to-factor mapping and implementation comparison | Residual exposure, costs, liquidity and stale valuation |
| Independent investment challenger | Immutable evidence and proposals, separate instructions | Findings, alternative explanation, stop/escalation | Methodological independence from proponent |

All recommendations should identify: *research release IDs; known-at times; method and version; assumptions; limitations; costs; confidence/uncertainty; mandate; recommendation status; and owner decision reference if acted upon*.

### Distinguish three kinds of agent output

1. **Facts with provenance:** exact source pointers and temporal status.
2. **Quantitative research:** reproducible computations with signed/hashed artefacts, baseline comparisons and risk measures.
3. **Judgement:** hypotheses, interpretations and recommended actions, labelled as such and never silently promoted into fact.

## 5. Investment outcomes: two mandates, common research

**SMSF — first practical mandate.** Prioritise factor-pure implementation of a resilient retirement portfolio, risk decomposition, downside and liquidity tests, robust return measurement and sustainable retirement-income research. The owner's medium-term objective is about **$1m of SMSF retirement capital supporting approximately $40k/year**; treat sustainability as a scenario/risk question, not a proven safe withdrawal rate.

**Future family investment trust — second mandate.** Long-lived intergenerational capital, potentially wider tolerance for **bounded tactical asset allocation**, factor tilts, valuation/mean-reversion and momentum decisions. It should consume the same neutral HIO evidence, but maintain separate mandate limits, tax considerations, position records and decision authority.

**Common principle:** Research once, test against multiple mandates; do not embed vehicle-specific accounting or trustee rules into general factor constructions.

**[INTEGRATION NOTE]**
- The SMSF's approved objective in the charter is about CPI + 5% a year over rolling three-year
  periods, with the convention still unsettled by the trustees
  ([charter §2](../charter.md#2-the-investment-problem-motivating-hio)). HIO represents each
  mandate's objective as a parameter supplied by its owner and does not resolve these questions.
  The capital and income figures above are the owner's stated medium-term aim, included with the
  owner's approval (2026-10-25); they are not a charter parameter.
- The charter provides for several portfolio consumers but names only the SMSF. The family trust
  is therefore a **[PROPOSAL]**: making it an HIO consumer would need an owner decision and its
  own mandate parameters.

## 6. Concrete research agenda (prioritised by dependencies, not calendar urgency)

### Foundation: complete existing approved work

- Finish independently verified S1a observation/rights/provenance controls; proceed to S1b only with acceptance, verified source rights and authorisation ([HIO-ADR-0010](../decisions/HIO-ADR-0010-first-slice-scope.md); [roadmap §1](../roadmap.md)).
- Build cash, FX and then equity/rates return series that meet the HIO economic-return requirements (roadmap §1–2: S1, then S2/S3).
- Establish human-readable and machine-readable releases that a future specialist agent can reliably retrieve and cite.

### First applied research laboratory

- **Factor exposure explainability:** Compare interpretable exposures to equity, duration, credit, currency and diversifying strategies against issuer-documented holdings and actual SMSF exposures.
- **Regime/dependence experiment:** Compare rolling covariance and shrinkage with unsupervised clustering/network-based diagnostics, measuring whether additional complexity improves *out-of-sample risk assessment*, not just explanatory plots.
- **Signal laboratory:** Pre-register a small TAA hypothesis (e.g., valuation-conditioned mean reversion versus trend persistence) with explicit data availability, baseline, costs, turnover, sensitivity and holdout period. A failed experiment is useful research.
- **Text evidence pilot:** Use an NLP agent to assemble a dated ETF/fund implementation dossier from permitted issuer documents, with line-level evidence and a human-verifiable extraction test set. Do not use unconstrained LLM judgements as historical returns or predictive signals.

**[INTEGRATION NOTE]** Mapping to the hypothesis register (`registers/hypotheses.yaml`) and the
roadmap:
- The regime/dependence experiment fits **H-0001** (duration–equity correlation by regime) and
  **H-0004** (diversifiers failing together); roadmap §2 schedules the first registered experiments
  for H-0001 and H-0002, explanatory and risk only.
- The valuation-versus-trend signal laboratory touches **H-0003**, which roadmap §3 places as a
  **Year 3–4** track because it depends on vintages captured from S1 onwards. Running it earlier
  would be a roadmap change for the owner, not something this brief authorises.
- The factor-exposure work fits the risk model v1 milestone (roadmap §2).

### After sufficient data and validation

- Theory-grounded futures excess-return and collateral research; commodity/managed-futures trend and carry decomposition.
- Ensemble models for cross-asset signals, with economic hypotheses and challenge from simpler models.
- RL policy experiments *only in a sandbox* against robust classical rebalancing, with realistic turnover, taxes and risk limits. No automated trading.
- Multi-agent orchestrator coordinating recurring evidence capture, experiments, challenges, monitoring and owner briefings.

## 7. Evaluation standards to develop (proposed, NOT automatically approved)

| Evaluation dimension | Minimum question |
|---|---|
| Economic validity | Is each series total return, excess return or state indicator correctly identified? What costs/financing/distributions are missing? |
| Point-in-time integrity | Could source vintages, model training, extracted text or publication timing leak future information? |
| Baselines | Does the model improve on a simple, understandable benchmark? |
| Research validity | Are hypotheses registered; multiple comparisons tracked; walk-forward / untouched OOS periods used? |
| Implementation realism | Does benefit survive turnover, spread, fees, capacity and taxes as applicable? |
| Stability | Does performance degrade materially across regimes, sample windows and plausible parameters? |
| Explainability | Can the research team identify what drives predictions and where they fail? |
| Agent reliability | Can all material factual claims be traced? Does the agent refuse when evidence is unavailable? |
| Risk and mandate | Are portfolio constraints explicit and tested under tail scenarios? |
| Human control | Is there an explicit approval boundary before a recommendation becomes an action? |

Avoid turning this into a new gate for every implementation commit. Apply proportionately at the **research experiment / investment-decision boundary**.

**[INTEGRATION NOTE]** Several dimensions already follow from approved charter commitments
(§3: uncertainty in every result, failure is data, honest multiple-testing counts, point-in-time
honesty) and from the experiment register (`registers/experiments.yaml`). A new evaluation
standard would still need its own approval.

## 8. What the monograph does *not* establish

- It does **not** validate an HIO agent-orchestrator architecture or establish that numerous specialist agents outperform a simpler coordinated system.
- It does **not** demonstrate persistent alpha for HIO's intended instruments, markets, mandates, capacities or cost structures.
- It does **not** authorise using copyrighted text as a training or retrieval corpus, nor resolve market-data licences.
- It does **not** justify automatic trading or replacing owner judgement.
- It does **not** resolve the SMSF's sustainable-income assumptions or the tax/legal design of the future trust.
- Individual chapter examples, backtests and simulations are **research illustrations**, not independent live-performance evidence for HIO.

## 9. Repository integration proposal

**Location:** `docs/research/2026-10-cfa-ai-in-asset-management.md`, listed in the [research index](README.md) (integrated 2026-10-25).

**Integration treatment:** research reference only. Link from the research index or architecture reading list; do **not** modify approved ADRs, standards, roadmap, owner decisions, statuses, review records or code merely to land the brief. A later separate architectural decision could adopt a mandate-aware research/agent interface if specific use cases demand it.

**Suggested next trigger for review:** when S1b has validated real research releases, or when the first text-analysis/research-agent proof of concept is proposed. At that time, choose one narrow demonstrator and measurable evaluation criteria.

**Owner-facing success metric:** At each milestone ask: *What economically valid investment question can we now answer, and how does it improve understanding or construction of the SMSF portfolio while remaining reusable for the future family trust?*

## 10. References and reading order

Primary: Simonian, Joseph, ed. (2025). *AI in Asset Management: Tools, Applications, and Frontiers*. CFA Institute Research Foundation. https://doi.org/10.56227/25.1.32 . See publisher monograph and practitioner-brief URLs above.

**HIO reading order:** Ch. 7 (NLP and agents); Ch. 8 (commodity futures and theory-grounded ML); Chs. 1–2 (clustering/networks); Ch. 4 (ensembles); Ch. 6 (sequential decisions); Ch. 10 (ethical AI). Chs. 3 and 5 support specific later modelling choices; Ch. 9 is horizon scanning.

Related HIO material: [charter](../charter.md); [roadmap](../roadmap.md); [implementation plan](../implementation-plan.md); [HIO-ADR-0004](../decisions/HIO-ADR-0004-temporal-semantics.md); [HIO-ADR-0007](../decisions/HIO-ADR-0007-return-accounting-standard.md); [HIO-ADR-0010](../decisions/HIO-ADR-0010-first-slice-scope.md); the [observations](../standards/observations-and-point-in-time.md), [rights](../standards/rights-and-licensing.md) and [releases](../standards/datasets-releases-and-artefacts.md) standards; `registers/hypotheses.yaml`. In the SMSF's own (separate, private) repository: `macsmsf` `docs/investment-process-roadmap.md`. This brief creates no new authority.
