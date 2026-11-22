# HIO Factor Programme — Architecture Guidance for Claude and Codex

**Date:** 22 November 2026  
**Audience:** HIO owner, Claude (implementation/orchestration), Codex (independent review), solution architect  
**Status:** Architectural recommendation for owner consideration; **not** an owner decision, implementation assignment, approval, waiver, acceptance or authorisation to acquire or publish data.  
**Repository baseline reviewed:** `elusivenode/hio`, `main` at `6d7535a290107a899436bfa912996c7644555abc` (merged PR #144). Other relevant baseline: PRs #141–#144; OD-0213, OD-0215, OD-0216, OD-0217; factor build records 1–4; approved return-accounting standard v0.2.  
**Provenance:** Repository statements below are based on the referenced GitHub records. Statements about local licensed-data computations are *author-reported*, not independently reproduced by the adviser. Interpret all candidate priorities as architectural judgement.

## 1. Executive direction

HIO should now advance from *demonstrating that it can build return series* to *producing economically coherent and independently challengeable AUD multi-asset research*. Build breadth and targeted validation concurrently. Do not let governance, increasingly sophisticated optimisers or idealised proxy factors displace portfolio research that can improve real decisions.

The near-term goal is **an AUD multi-asset research comparison** including AUD cash, Australian and global equity, Australian and US sovereign duration, explicit FX effects, and then credit. This is a research-capability milestone, not authority to advise, trade or publish to MACSMSF. Its first useful output should answer how these exposures behave together, what drives risk, how much implementation assumptions matter, and which questions cannot yet be answered defensibly.

Core distinctions to preserve:

- **Factor vs vehicle:** an economic driver is not the same thing as an ETF or trust return. SPY, IEF, BIL and future ASX vehicles are observable implementation proxies with basis, fees, liquidity and instrument-specific residuals.
- **Correct calculation vs correct source:** independent recomputation from the same market observations checks mathematics but cannot establish economic validity of those observations.
- **Funded vs excess return:** do not mix return classes or chain arithmetic excess as if funded total return.
- **Research vs decision:** historical analysis, expected-return hypotheses, allocation recommendations and acceptance for consumption require different evidence.
- **Proposed vs authorised:** design guidance does not modify approved standards, open findings or the owner’s authority.

## 2. Evidence baseline and status

At the cited main revision, the repository documents:

- Live exploratory capture of RBA and NY Fed data since 4 November; soak recorded as 80/80 reconciled with zero misses. The underlying cloud receipts were read and assessed by Claude; the adviser did **not** independently query Azure. Follow-on dead-man, CI-run audit, replay, reconstruction and finality prerequisites remain owed.
- Local, exploratory and unaccepted EODHD-sourced USD total-return builds for SPY, IEF and BIL; excess returns over BIL; AUD reconstructed cash; unhedged and CIP-implied hedged AUD builds; AUD excess returns; portfolio statistics, sample covariance and hedge-ratio sweep. Fourteen factor specifications remain **proposed**. Build evidence names content hashes and reports independent recomputation, but the adviser has not seen licensed source values or repeated those checks.
- T-0023 provides partial independent corroboration and recorded unresolved discrepancies, notably a BIL close/NAV check around 2008, an IEF comparison to an unreferenced construction, a SPY audited-NAV-versus-traded-close comparison, and missing IEF issuer NAV. A passed numerical invariant is not a substitute for these distinctions.
- The USD cash leg is currently proxied by the BIL bill ETF rather than overnight cash; the current hedging forward is **CIP-implied using AUD cash and BIL realised returns**, not directly observed matching-tenor FX forwards; the H.10 FX fix and ETF close are asynchronous.
- E-0004 (CPI state experiment) and H6 (automation) are parked with open findings. Their parked status is not an invitation to restart remediation.
- Licensed-dependent research results are retained in local private stores. They currently lack a tested backup. HIO and MACSMSF remain separate; no research series here is approved for the SMSF consumer.

**Authority order:** owner decisions and approved standards; exact task and review records; verified Git branches/commits; then status and handoff summaries. Check current Git state before acting: this document is a dated architectural snapshot, not a substitute for a fresh repository read.

## 3. Recommended sequencing

These are a **logical priority order**, not a mandate to wait for one task to finish before beginning another.

| Priority | Workstream | Intended decision-useful outcome | Dependencies and limits |
|---|---|---|---|
| 1 | Small factor programme card + short roadmap | Makes scope, outputs and bounded acceptance gates visible | Draft only until owner authorises; do not replace existing standards or create new governance machinery |
| 2 | Targeted independent validation of existing US ETF inputs | Establishes known reliability and unresolved basis for each consequential sleeve | Use public issuer data and permitted independent references; no unapproved licensed retrieval |
| 3 | Australian broad equities | First domestic risky-asset sleeve for AUD portfolio comparisons | Check ASX source coverage, income, distributions, franking treatment if relevant, splits, calendars, tax/gross-net conventions and rights |
| 4 | USD overnight cash | Replace BIL as an explicitly labelled *proxy* when economic excess return requires a proper short-rate leg | Identify permitted, historically adequate source; constrain early use to available observations and separate old-history proxies |
| 5 | Covariance shrinkage comparison | Test whether a simple estimator improves out-of-sample risk forecasts | Do not promote shrinkage simply because it produces a smoother matrix |

**Insert near priority 3:** Australian government-bond duration is more decision-useful than a second or third US equity proxy. Give it a bounded source-and-methodology feasibility check and construct an income-inclusive return, rather than treating yield levels or a naive constant-maturity price estimate as investable return.

**Parallel operational hygiene:** implement a minimal, encrypted and rights-compliant backup for the local factor/results stores, accompanied by one successful restore test. This is not a redesign of HIO storage. Keep known 2027 RITS/NSW calendar rollover requirements on a dated operations track to avoid a year-boundary failure. Do not allow them to consume the research programme unless the deadline or reliability demands it.

Suggested order of *portfolio research expansion*: AUD cash -> global equity and Australian equity -> Australian and US government duration -> liquid investment-grade credit -> gold -> transparent time-series trend. USD overnight funding and FX overlays support multiple steps. This sequencing may change when evidenced current SMSF holdings indicate a near-term risk that merits earlier attention.

## 4. Minimal useful multi-asset factor set

Start with a handful of economically distinct risk dimensions. **Do not equate each sleeve’s historical ETF return with a pure factor.**

1. **AUD cash / opportunity cost:** RBA overnight-derived research benchmark; distinguish accrual from a deposit that can actually be transacted.
2. **Global equity risk:** broad global equities preferable eventually; SPY currently serves as a narrower US implementation proxy.
3. **Australian equity risk:** broad ASX exposure with a clearly defined total-return and income convention.
4. **Sovereign duration:** Australian government bond total return first, US Treasury duration alongside it; sensitivity to rates, inflation and term premia.
5. **Credit spread / default / liquidity:** liquid Australian investment-grade corporate credit first. Credit **excess over cash** is not automatically a pure spread premium; duration-match to government debt where practicable.
6. **Gold:** compare AUD spot returns with real implementable gold holdings or ETF returns; custody, fees and currency matter.
7. **Trend / defensive alternative premia:** later, a transparent time-series strategy with cash collateral, financing, rolling, costs and index rules included. Do not promote price-only futures histories as return factors.

Treat AUD/USD currency exposure and hedge ratio as **explicit overlays** or separate priced exposures, not accidental contamination of asset risk. Use a portfolio in AUD for practical comparisons and preserve USD versions for mechanism diagnosis.

The first deliverable need not include credit, gold and trend. Five core sleeves—AUD cash, Australian equity, global/US equity, Australian government duration and US Treasury duration—already enable useful AUD risk analysis.

### Credit-vehicle lesson

The owner’s MXT experience illustrates a critical capability not fully addressed by a conventional factor model. Assess **asset class, market segment and investment implementation** separately:

- Credit economic exposure: spread compensation, default, recovery, duration, liquidity and state dependence.
- Segment: senior bank floating-rate, investment grade, subordinated, high yield, leveraged loans, securitised or private credit.
- Vehicle: NAV valuation and mark-to-market mechanism, independent price verification, manager concentration, governance and auditor changes, liquidity under stress, fees and market-price/NTA discount for listed trusts.

Historical return smoothness may reflect stale or modelled marks, not low economic risk. HIO should be able to decline to rank a vehicle confidently when structural risk is not observable. Do not make retrospective claims that a specific audit or governance event was predictable merely because the *class of risk* was identifiable.

## 5. Validation policy: enough to move forward, enough to trust

Validation should scale with **intended use and potential decision impact**, not merely the number of sources or unit tests.

| Layer | Test question | Minimum useful work |
|---|---|---|
| Numerical integrity | Are the calculations right? | Synthetic adversarial cases, return invariants, independent recomputation without shared calculation code, deterministic rebuild from pinned input |
| Source integrity | Are prices, splits, distribution ex-dates and FX observations faithfully represented? | Schema and date checks, selected exceptional events, documented corporate-action treatment, data-source documentation |
| Economic corroboration | Does the series agree with an independent economic reference? | Issuer total-return/NAV or audited returns, independent index or price source; stress periods; acknowledge different pricing/reinvestment conventions |
| Decision consequence | Could a discrepancy reverse an investment interpretation? | Bounded sensitivities showing what changes in factor ordering, correlations, contribution or portfolio conclusion |

**Before more exploratory builds:** one transparent targeted validation package for each *consequential* existing sleeve is preferable to broad vendor recertification. Do not require every historical observation to be independently reconstructed before adding Australian equity or bonds for research. Conversely, do not promote an unvalidated vendor series to a decision-grade consumer input merely because independent scripts agree to 1e-12.

Retain unresolved reference failures exactly as such. For example, SPY audited NAV return and closing-price return need not agree under the same reinvestment and valuation conventions; explanatory post-hoc diagnostics are not preregistered validation. IEF’s independent NAV absence should remain visible. Any proposed exception must be tied to a **specific use** and materially bounded; no generic “vendor verified” declaration.

## 6. FX hedging: appropriate current use and next improvement

The present CIP-implied hedged series and hedge-ratio sweep are **valid idealised diagnostics when the equations and assumptions are labelled**. They are **not validated tradable return histories**. In particular, using a bill fund’s *realised* return to infer the forward at hedge inception can introduce an ex-post convention; investigate whether all pricing inputs would have been knowable at that inception.

Recommended cheapest improvements:

**Stage A — methodology and inexpensive observables:** use matching-tenor, point-in-time AUD and USD interest-rate observations known at contract inception; specify hedge notional, maturity, rollover, FX quote direction, compounding and collateral/funding convention. Treat zero cross-currency basis as an explicit assumption, not an observed fact. Record hedging-cost and basis sensitivities. If matching-tenor rates cannot be obtained, keep a proxy label.

**Stage B — actual forward anchor:** obtain a small permitted sample of historical AUD/USD forward points for matching maturities, including ordinary periods and stresses. Compare actual forwards with CIP-implied values and quantify material deviations. Avoid a full premium FX-feed purchase until a concrete research decision demonstrates the need.

Ensure that the calculated series is *not* represented as a readily achievable investor return unless spread, execution, rollover, notional rebalancing and cash-flow effects are reasonably captured. Hedging the initial USD notional does not necessarily neutralise FX sensitivity on within-period asset gains or losses. A sample-minimum-variance hedge ratio is not a hedge recommendation.

## 7. Risk modelling: why simple shrinkage should be a benchmark, not the destination

Keep sample covariance as the transparent baseline. Compare it against a simple shrinkage estimator:

`Sigma_shrunk = (1 - delta) * Sigma_sample + delta * Sigma_target`.

With few factors, invertibility is unlikely to be the principal problem; unstable economic relationships and a small number of independent stress regimes are greater concerns. Do not promote an estimator based solely on in-sample Sharpe ratios or a nicer-looking covariance matrix.

Before changing model default, run rolling or expanding-window forecasts using only information available at the estimation cutoff; compare subsequent realised volatility, covariance/correlation and risk contribution stability. Keep common sample windows explicit across sleeves. Investigate whether forecasts deteriorate across inflation/rates regimes or equity stress episodes.

A later structural model can decompose assets by factor loadings: `Sigma_assets = B Sigma_factors B' + D`. This fits HIO’s long-term goal, but `D` is not a magic catch-all for unobserved private-credit governance, liquidity or valuation risks. Those may need separate qualitative and scenario flags.

**Do not start with unconstrained mean–variance optimisation based on historical sample mean returns.** Expected returns have more estimation uncertainty than covariance, and optimisation will amplify errors. Begin with constrained allocations, scenario comparisons, rolling real-return distributions and transparent expected-return hypotheses.

## 8. Timestamp alignment and monthly versus daily use

H.10 is a New York noon FX observation; US funds generally close later, and ASX closes in another time zone. At **monthly** frequency, the difference may be tolerable for broad descriptive comparisons, but test that claim against matched-close or alternative FX dates, particularly in volatile months. It can remain a material endpoint error.

At **daily** frequency, do not report precise asset/currency contribution or correlations as if both observations came from one contemporaneous market snapshot. Use time-aligned FX with specified valuation cutoff where available. Otherwise mark the series as asynchronous and unsuitable for fine-grained attribution or live replication.

For every FX-translated return, distinguish the economic return period, price timestamp, FX fixing timestamp and *knowable_at*. Point-in-time availability is independent of the choice of economic return convention. Test the inversion of H.10’s USD-per-AUD quote and the sign of translated returns on known episodes.

## 9. From exploratory build to purpose-specific consumer eligibility

**Do not create a competing new standards regime.** Map the following practical checkpoints to the existing approved standards, factor-specification and promotion gates:

**Exploratory research:** proposed spec; lawful usage; declared class, currency, calendar, funding leg, income/FX convention, pinned inputs, repeatable build, tested calculations, and explicit limits. May support internal exploratory discussion but not an investment claim or MACSMSF publication.

**Research-validated for named purpose:** independent consequential input corroboration (or owner-approved, quantitatively bounded exception), documented price/income/action handling, stress-period checks, material sensitivity analysis and reproducible evidence. Distinguish whether the result is adequate for **historical description**, **risk attribution**, **comparative instrument assessment**, or **prospective signal**—these are not equivalent approvals.

**Consumer-eligible:** exact immutable build and schema, approved rights for that consumer, complete lineage and source terms, operational release/rollback controls where required, versioned caveats, and **explicit owner authorisation for a named use**. The factor’s acceptance must not silently authorise an allocation algorithm, trade or recommendation.

For Codex, one bounded independent review of a coherent slice is preferable to repetitive blanket reviews. A material finding blocks the affected claim or publication, not every unrelated exploratory build. Preserve open findings on parked E-0004/H6 without expanding those loops unless newly authorised.

## 10. Architectural risks and mitigations

| Risk | Why six months may expose it | Proportionate mitigation |
|---|---|---|
| Single data vendor | Shared, correlated errors across every portfolio report | Cross-check the most consequential inputs with independent issuer/index references; source-class-specific limitations |
| Single local copy | Loss or corruption defeats reproducibility even if hashes still exist in Git | Encrypted, licensed, versioned backup with a demonstrated restore |
| ETF-as-factor conflation | False economic interpretations; mistaken risk diversification | Distinct identifiers for economic factor, reference index, vehicle and realised investable return |
| Risk model false precision | Stable-looking matrices and mean forecasts mask regime dependence | Out-of-sample risk forecasting, sample/coverage reports, uncertainty and scenario ranges |
| Hedging and asynchronous timestamps | Synthetic results mistaken for feasible portfolio performance | Match timestamps where possible, observable forward benchmark, explicit basis/cost labels |
| Governance disproportion | Time spent on receipt machinery instead of investment questions | Bounded tasks, review materiality, leave parked findings parked |
| No portfolio-to-research path | More factors without practical decisions | Define one periodic AUD portfolio comparison and a clear consumer-use boundary early |
| Hidden rights constraints | Future source use or sharing of results becomes impossible | Rights checked **for use case** before purchase, storage, agent access or publication |

A qualitative vehicle-risk overlay should address valuation uncertainty, liquidity, concentration, auditor/governance and redemption/secondary-market design. These dimensions cannot always be inferred from price history.

## 11. Suggested next-quarter research milestones (not authorisations)

**Milestone A — meaningful equity comparison:** short programme card, local store backup, targeted independent ETF evidence, Australian equity total-return proxy, AUD/global equity versus cash analysis. Deliverable: a research note that distinguishes equity beta, currency effect, return basis and uncertainties.

**Milestone B — defensive allocation:** Australian government-duration return with valid coupon/price/roll treatment; a defensible historical USD overnight leg; comparable AUD and US duration views. Deliverable: an AUD defensive-sleeve and 60/40 sensitivity report with timing and hedge assumptions named.

**Milestone C — credit and model comparison:** liquid Australian IG credit and a duration-matched government comparator; simple shrinkage versus sample covariance; start gold if data permit. Deliverable: portfolio exposure and implementation-risk comparison, avoiding retrospective certainty about MXT.

**Later:** broadly investable trend returns, richer inflation-conditioned analysis if E-0004 is independently rehabilitated and authorised, and an explicit route for validated research to be consumed in MACSMSF without modifying SMSF accounting logic.

## 12. Claude: responsibilities, bounded next deliverable and stop conditions

Claude should **not** treat this document as approval to implement. Upon an owner request to prepare the next programme slice:

1. Confirm current `origin/main`, owner decisions, approved standards, open findings and current source rights. Report any mismatch. Read the latest handoff and inspect the relevant tools/specs directly; never rely on this dated summary alone.
2. Draft **one concise task card and short roadmap** for the factor programme, mapping new work onto existing registers and standards; do not invent a second acceptance regime. Prioritise a small AUD multi-asset comparison with tangible outputs and clearly separate feasibility, implementation, validation and promotion.
3. Identify bounded work packages that can run concurrently: targeted price/distribution validation; ASX equity source feasibility and implementation; Australian sovereign duration source feasibility; USD overnight cash feasibility; backup/restore. Give each a specific artefact and explicit rights/return-accounting requirements. Only execute individually authorised packages.
4. Require worker-authored tools to pass invented-data adversarial fixtures *and* real-input shape checks where lawful, then independently recompute consequential figures without reusing worker calculation code. Keep restricted values solely in permitted stores.
5. Preserve proposed factor specs as proposed until their defined adoption. State exactly which outputs are empirical, which are synthetic, and which are estimated or unvalidated. Do not claim investment replicability for CIP-only hedging.
6. Do not begin new source downloads, subscriptions, permissions, deployments, MACSMSF changes, factor/spec adoption, research-acceptance decisions, publication or consumer integration without the appropriate owner authority. Stop if data rights or evidence integrity fail.
7. Protect the existing live capture and the 2027 calendar cutoff in an independent, dated operational thread. Do not restart parked E-0004 or H6 assurance unless the owner explicitly changes its priority.

**Claude’s first proposed output:** one bounded factor-programme task card and a roughly one-page implementation sequence, including dependencies, named output artefacts, independent validation, operational safeguards and explicit asks for owner approval. No code or data acquisition is required to prepare the draft.

## 13. Codex: independent review responsibilities

Codex should review only an **owner-assigned exact base/head and scope**, on the approved reviewer branch/worktree, and preserve its independent evidence provenance. Do not treat an architectural note or Claude’s proposed card as an assignment.

For a factor-series slice, focus adversarial testing on:

- **Return semantics:** distributions, dividends, coupons, clean versus dirty bond prices, splits, missing observations, exact cash-day conventions, compounding and excess-return arithmetic. Check that price levels or yield changes are not misrepresented as income-inclusive investment returns.
- **FX and hedging:** quote inversion, timestamp/knowability, period joins, hedge notional, CIP basis, cash-leg provenance and explicit non-tradability of idealised series.
- **Determinism and integrity:** unpinned input refusal, corruption/tamper detection, deterministic rebuild, independent arithmetic checks and realistic source layout edge cases.
- **Statistical validity:** covariance annualisation, Euler contributions, consistent funded/excess forms, sample-window treatment, estimation data leakage, in-sample hedge-optimisation labels, inference over too few stress clusters and misleading uncertainty.
- **Independent source evidence:** trace permitted references, distinguish issuer-NAV from market-close conventions, and explicitly mark source values outside reviewer access **unverified** rather than assuming the author’s numbers.
- **Consumer boundaries:** no unauthorised licensed data in public records, no unapproved factor promotion, and no MACSMSF data or functionality changed.

A review should separate (a) independently reproduced facts, (b) author assertions supported only by local evidence, (c) methodological judgement and (d) findings that materially affect the claimed use. Do not demand universal source revalidation if the assignment is a synthetic calculation tool; equally do not certify economic validation from code tests alone. A READY result means READY **for the scoped proposition at the reviewed exact revision**, not that a factor is accepted or can be traded.

Do not widen findings into new design standards without owner approval. Keep high-severity unresolved issues visible; a bounded technical close is not a rights approval, owner acceptance or publication authorisation.

## 14. Owner decisions needed, one at a time

**First suggested decision:** Authorise Claude to **draft** the factor programme card and short roadmap, including the validation plan, Australian-equity/sovereign-duration feasibility, USD overnight cash feasibility, rights-compliant store backup, and a first meaningful AUD portfolio research output. Drafting authorises no implementation or source acquisition.

Later separate decisions may authorise individual bounded builds, new data-source permissions, a paid data feed within the owner’s budget, reviewer assignments, adoption of proposed factor specs, promotion of particular research outputs, and MACSMSF consumer release.

The current research-data budget context is **AUD 400 per month ceiling, acquired incrementally**; do not assume availability of paid source data until the owner approves the particular cost and licence. Priority should go to economical, independently challengeable, reusable observations and economically valid *total returns*, rather than mere price histories.

## 15. Confidence and falsifiability

| Judgement | Confidence | Evidence that would change the view |
|---|---|---|
| Australian equities and sovereign duration should be early | High | Verified holdings/exposures demonstrate another materially more urgent unmapped driver |
| Vendor corroboration must precede consumer-grade conclusions | High | Additional independent issuer/index references reduce the known source uncertainty |
| CIP-implied hedging is exploratory rather than tradable | High | Historical actual forward-point evidence, known-at-inception rates, realistic costs and basis reconciliation |
| Shrinkage is a useful comparison but not the core bottleneck | Medium–high | Out-of-sample covariance errors or severe numerical instability demand earlier work |
| Noon FX versus close is often manageable monthly | Medium | Matched-close comparisons materially change monthly risk and return interpretation |
| Initial factor set is sufficient for meaningful first AUD comparisons | Medium | Evidence from actual SMSF weights and portfolio-risk decomposition finds a major omitted driver |
| Quarter-sized milestones can be achieved | Medium–low | Unexpected data-rights, independent-reference or implementation constraints |

## 16. Close

**Current state:** The repository contains initial reproducible USD/AUD factor and risk research tooling at an identified Git revision. The series remain exploratory and unaccepted. Local numerical verification is author-reported, and single-vendor, hedge, currency-timing, reference and storage limitations remain.

**Assessment:** The architecture is ready to prioritise **economically meaningful breadth and bounded validation together**. The largest near-term value comes from a realistic AUD multi-asset comparison and from making implementation-specific risks visible, not from a new modelling or governance framework.

**Next actor:** The **owner** for a narrow draft authorisation; then **Claude** to prepare the card and proposed sequence. **Codex** acts only on a separately assigned exact-revision review.

**Ready-to-use owner instruction:** “Claude: draft, but do not implement, one HIO factor-programme task card and short roadmap using this architecture guidance and current repository authority. Include the first AUD multi-asset research output, workstream-specific source and validation gates, backup/restore and 2027 calendar dependencies. Identify each required subsequent authorisation and stop on any revision or rights mismatch. Return the draft for my decision.”
