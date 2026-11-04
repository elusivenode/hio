# A. Executive verdict

**HIO is generally aligned with its long-term research mandate, but requires material reprioritisation.**

**Architectural judgement:** Preserve the modular monolith, retained evidence, explicit return accounting, rights controls and separation from MACSMSF. Change the unit of progress from “another assured platform capability” to “another investment question answered with credible evidence.”

The foundation has reached the point where a bounded research programme can proceed alongside operational completion. It has **not** established reliable unattended operation, validated duration returns or produced a useful multi-asset research result.

My principal conclusions are:

1. **The largest immediate constraint is suitable economic data, especially equity total-return history.** Additional storage engineering will not resolve it.
2. **Factor-first sequencing is a sound correction, but remains too centred on individual constructions.** The next meaningful milestone should connect equity, duration, currency and cash in one reproducible analysis.
3. **The duration experiment is worthwhile as a bounded construction investigation.** Its success would not establish a validated Treasury investment return or ETF implementation.
4. **Operational completion remains necessary, but should occupy a constrained supporting track.** H6 should remain parked. Further general hardening should require a demonstrated need.
5. **The first useful analytical product should compare a few fixed hypothetical allocations, quantify uncertainty and explain when diversification fails.** Optimisation and tactical predictions should wait.

There is an important qualification to this criticism: HIO is young. The repository records G1 on 18 October and first live capture on 4 November. An early imbalance between foundations and analytics is unsurprising. **The concern is the next allocation of effort, rather than the mere existence of that imbalance.**

The disappointing outcome to avoid is a highly reproducible collection of weakly validated series that still cannot explain whether adding duration or changing currency exposure improves a hypothetical portfolio.

# B. Evidence baseline

## Revision and scope

**Verified:** At the final remote check, on **4 November 2026 at approximately 02:47 UTC**, accessible `main` remained:

`bde61d74f8b97e7e7c6d50c15a76939a9e77a26e`

This equals the supplied checkout. I inspected repository files directly, including all specifically requested documents, relevant implementation modules, tests, decisions, task cards, review records and operational evidence.

Two open PRs were accessible:

| PR | Exact head | Relevance |
|---|---|---|
| [#92: duration experiment preregistration](https://github.com/elusivenode/hio/pull/92) | `09e29e5741a89e10bfac54d58346df0b7ba674f7` | OD-0157, T-0020, E-0001 and proposed spec 0.1.3 |
| [#72: distil 3](https://github.com/elusivenode/hio/pull/72) | `4c36bae3d8ebb7a3873d9b4772d7d1fc84edd962` | Proposed knowledge-index and navigation updates |

Neither was merged at that check. I considered #92’s **research scope and authority record**, without issuing technical acceptance or assessing an implementation awaiting independent review.

Throughout this report:

- **Verified** means directly checked repository content at the revision above, unless another exact revision is named.
- **Reported** means an operational outcome or another agent’s account that I have not independently reproduced.
- **Owner-decided** means an explicit action recorded in the cited OD.
- **Architectural judgement** means my assessment or recommendation.
- **Unknown** means the available evidence does not establish the fact.

All proposed priorities, scores, severities and sequencing below are **Architectural judgement**.

## What the evidence establishes

| Evidence | Established position |
|---|---|
| [Charter][charter], [architecture][architecture], [return standard][returns], [observations standard][observations], [factor-specification standard][specstandard] | **Verified:** approved documents define the intended system, economic conventions and evidence boundaries. The roadmap, implementation plan and base camp remain proposed. |
| [OD-0139][od139] | **Owner-decided:** factor-first is the working order; exploratory capture need not await C5 resolution. G2, finality and S1 obligations remain. |
| [Implementation tree][src], [dependencies][dependencies], [experiment register][experiments] | **Verified:** construction, capture, storage and publication code exist. `models`, `portfolio`, `taa` and `implementation` directories do not. No NumPy dependency or operational multi-factor analytical implementation was found. The experiment register on `main` is empty. |
| [T-0019 verification][cmtverify], [OD-0153][od153] | **Owner-decided:** T-0019 was accepted at `fa6370dc3f55c4d9e6537d502ab4a4727ca85fbd`, on invented inputs. **Verified:** the acceptance explicitly leaves the spec proposed and pricing-basis error unmeasured. |
| [Cash rebuild evidence][cashreport], [OD-0148][od148] | **Reported:** the rebuild produced 214 AUD and 30 USD periods; all AUD comparisons classified as precision differences, and three USD comparisons lacked reference observations. The repeated payloads matched. This is not independent economic validation by me. |
| [First live run][firstrun], [soak declaration][soak], [OD-0149][od149] | **Reported:** capture ran and a scheduled failure email arrived. **Owner-decided:** that email satisfied I-5. **Verified:** the ten-business-day soak is declared for 5–19 November; no completed soak result is present. |
| [Retained B-2 report][b2] | **Verified:** parsing the retained report reproduces its count of 45 C5 violations in 50 observations. **Reported:** those observations came from the Azure probe. I did not authenticate the live Azure environment. |
| [Source register][sources], [OD-0156][od156] | **Owner-decided:** five cash datasets and the Treasury par curve have bounded rights decisions. **Verified:** the par-curve conditions are unsatisfied on `main`; its `owner_verified` label alone does not permit operations. |
| [OD-0157 at PR #92’s head][od157] | **Owner-decided, recorded off `main`:** a bounded duration experiment is authorised. Download remains held for the page-reading confirmation and merged preregistration. Its strongest permitted conclusion is “construction diagnostics completed; UNREFERENCED.” |
| [OD-0114][od114] | **Owner-decided:** H6 remains parked and unactivated; manual receipts continue. |

## Limits that materially affect this assessment

**Unknown:** actual developer hours, owner minutes per task, agent expenditure, current Azure billing, vendor quotations and net research throughput.

**Reported:** most live operational outcomes. I did not access credentials, the evidence account, retained market-data objects or private research directories.

**Unknown:** the economic accuracy of the reported real cash results beyond the evidence available in the repository. In particular, the market-data bytes underlying those results were not available in this checkout.

**Reported:** the attribution of several earlier recommendations to me. The repository retains summaries, but not all original consultation answers. Agreement between those summaries does not independently authenticate the original advice.

I did not run the test suite: this assignment was strategic advice, not another code review. Reported test results remain attributed to their review records. I changed no files and accessed no MACSMSF content or private financial information.

# C. Alignment scorecard

A score of **3 means adequate for the present phase**. These are deliberately not averaged.

| Dimension | Score | Assessment |
|---|---:|---|
| Investment-mandate alignment | **3** | The charter addresses the right questions. Delivery has not yet connected the foundations to portfolio understanding. |
| Economic correctness | **3** | Strong accounting distinctions and useful independent corrections. Real factor validity remains substantially unestablished. |
| Data fitness | **2** | Provenance is stronger than historical coverage and independent reference availability. Equity remains unresolved. |
| Research capability | **2** | Construction capability exists; aligned panels, portfolio analytics and empirical hypothesis results do not. |
| Statistical discipline | **3** | The documents recognise uncertainty and multiple testing. Some proposed sample-length rules are too categorical, and analytical enforcement is unbuilt. |
| Architecture | **4** | Appropriate boundaries, portable retained evidence and a disposable catalogue. No demonstrated reason for a structural redesign. |
| Operational readiness | **3** | Enough to proceed with bounded exploratory research; insufficient to claim established unattended reliability or recoverability. |
| Agent effectiveness | **3, provisional** | Review records show substantive corrections. Net benefit per owner hour is unknown; repeated receipt and orchestration work is visible. |
| Delivery sequencing | **2** | OD-0139 improves the order, but the analytical result still sits behind too many serial prerequisites. |
| Capital efficiency | **3, provisional** | Incremental procurement and simple hosting are sensible. Actual costs and cost per useful result are unknown. |

The low research and data scores are **prioritisation signals**, not an expectation that a seventeen-day-old programme should already possess a mature risk model.

# D. Findings register

These are advisory findings, not Codex findings or changes to existing finding states.

| ID / severity / type | Evidence and consequence | Approved-decision conflict? | Remedy and smallest closing evidence |
|---|---|---|---|
| **SA-01 — High: capability gap** | **Verified:** no aligned return panel or portfolio-analysis implementation; [source tree][src]. Individual constructions cannot establish diversification. | No; planned capability is absent. | Deliver one reproducible comparison of fixed equity–duration–cash allocations, including currency attribution and uncertainty. Close with an assessable research result, not a panel export. |
| **SA-02 — High: data blocker** | **Verified:** [T-0003 scorecard][equityresearch] has no written vendor answer or selected source. No cleared equity TR history supports the central equity–duration question. | No. | Complete the already-authorised enquiry, then a narrowly licensed trial. Close with written rights, retained sample bytes and independently supported distribution/action reconciliation. |
| **SA-03 — High: research uncertainty** | **Verified:** the [CMT spec][cmtspec] and accepted review explicitly leave pricing-basis error unmeasured. Mathematical consistency does not establish traded-return validity. | No; the limitation is disclosed. | Complete the bounded experiment, then obtain a separately cleared traded/index reference. Same-source repricing closes only the approximation question. |
| **SA-04 — Medium: sequencing problem** | **Verified:** [factor-first][factorfirst] makes the reader follow the duration result; [base camp][basecamp] collects ten criteria before procurement readiness. These dependencies can delay useful learning without improving it. | Revising working order needs an owner decision under OD-0139; the planning documents are proposed. | Permit a minimal reader to develop alongside constructions; separate limited data evaluation from full procurement readiness. Close with an owner-adopted bounded sequence. |
| **SA-05 — Medium: known issue awaiting disposition** | **Verified:** the cash spec declares four reference decimals. **Reported:** live TRI precision reaches six and all 214 comparisons are consequently unclassified by the intended bound; [cash report][cashreport]. | No approved requirement should be silently overridden. | Independently inspect the retained bytes, record the appropriate spec change and rerun comparison classifications. Close with accounted periods and evidenced dispositions. |
| **SA-06 — High before analytical use: boundary gap** | **Verified:** [`resolve_for_use`][resolver] checks identity, lineage, status and current rights, but does not enforce requested knowledge mode or cutoff. A future reader could otherwise admit inappropriate history. | No discovered defect in its stated contract. | Reader acceptance must include incompatible mode/cutoff refusal and cache revalidation. Close with demonstrated refusal cases and retained panel provenance. |
| **SA-07 — Medium: statistical design weakness** | **Verified:** the [data-need statement][dataneed] presents several history lengths as minimums and assumes roughly twelve factors. This risks postponing useful small models while overstating the reassurance provided by long samples. | No; the document is proposed. | Replace universal thresholds with question-specific sample adequacy, episode counts and sensitivity. Close with a defensible sample plan for the first report. |
| **SA-08 — Medium: future evidence gap** | **Verified:** current capture concerns cash datasets; [source register][sources]. It does not establish future vintage coverage for valuation, inflation or other predictive inputs. | No; the charter’s broader aspiration remains ahead. | Identify the actual inputs of the first medium-term hypothesis and establish archive/capture feasibility. Close with source-specific vintage coverage, not a generic PIT claim. |
| **SA-09 — Medium: operator burden** | **Verified:** [H6’s record][od114] documents seven verifications and continued parking. **Unknown:** net owner time saved by the agent system. | No reopening of H6 is needed. | Keep H6 parked; judge collaboration by delivered research and owner attention consumed. Resume automation only when a specific repeated burden has a credible payback. |
| **SA-10 — Medium: operational evidence gap** | **Verified:** soak, dead-man exercise and live recovery evidence remain incomplete; [soak][soak], [base camp][basecamp]. | Existing obligations remain. | Complete the bounded operational evidence without making it a prerequisite for unrelated local analysis. Close with retained results from the actual exercises. |
| **SA-11 — Medium: implementation realism gap** | **Verified:** [return standard][returns] distinguishes theoretical and investable returns, but no ETF implementation-analysis capability exists. A good factor result may not survive vehicle basis and costs. | No. | Add one vehicle comparison early, before broader optimisation. Close with reconciled factor-versus-ETF differences and explicit remaining basis. |

**No new implementation defect is established by this assessment.** The most consequential findings are missing capability, economic uncertainty and sequencing.

# E. Recommended architecture and roadmap corrections

## 1. Work backwards from the investment questions

The following is the minimum useful progression. “Missing” describes this checkout, not an assertion that the capability should already have been delivered.

| Investment question | Minimum inputs and methods | Existing / missing controls and capability | Horizon and useful demonstration |
|---|---|---|---|
| **What risks does a portfolio hold?** | Funded/excess returns, exposure definitions; later ETF metadata, duration and regression exposures | Accounting and provenance exist; exposure estimation and portfolio attribution are missing | **30–90 days:** explain the risks of a hypothetical allocation, including embedded FX |
| **Which exposures are redundant?** | Aligned same-basis returns; covariance, correlation, regression and conditioning diagnostics | Panel and analytics missing | **90 days:** show whether adding duration materially changes risk, and sensitivity to the sample |
| **How does it behave across regimes?** | Return histories plus independently defined inflation/growth states; conditional estimates and historical scenarios | Proposed hypotheses exist; state data and analytical methods missing | **3–12 months:** compare a few prespecified episodes, separating retrospective classification from real-time state knowledge |
| **How certain is diversification?** | Joint histories; shrinkage and joint block resampling | Uncertainty is required in documents, not implemented analytically | **90 days:** uncertainty intervals around portfolio risk differences |
| **Which risks plausibly earn compensation?** | Yields, distributions, losses, valuations and economic arguments | Accounting is a prerequisite; expected-return models absent | **3–12 months:** building-block return ranges with contrary scenarios |
| **How sensitive is an allocation?** | Candidate weights, covariance alternatives, return assumptions and costs | Portfolio machinery absent | **3–12 months:** compare fixed allocations across assumptions before optimising |
| **What is real-return shortfall risk?** | Joint portfolio returns and chosen CPI series; real wealth paths and conditional simulation | Inflation rights/convention and path analytics missing | **First year:** historical shortfall experience, followed by assumption-dependent forward scenarios |
| **What does a tactical decision add?** | A static benchmark, timestamped signals, execution lags, turnover and costs | Proposed hypotheses only | **Years 2–3 onward:** shadow experiments against unchanged strategic allocations |
| **Can ETFs implement the exposures?** | ETF TR, fees, NAV/price basis, liquidity and hedge mechanics | Standards recognise differences; implementation analysis absent | **3–12 months:** one exposure mapped to one or two candidate vehicles |
| **Can the result be challenged later?** | Retained bytes, spec/code/lock pins, run parameters and result lineage | Much of the foundation exists; scientific run reproduction remains to demonstrate | **Every horizon:** rebuild the first report from its retained inputs |

This progression does not require a general-purpose modelling platform.

**The smallest material analytical result** is:

> For a few fixed hypothetical allocations, how much did sovereign duration reduce equity risk and drawdown, how much of that result came from currency, and how stable is the conclusion across samples and uncertainty estimates?

That is a worthwhile investment question even if the answer is “the evidence does not distinguish these allocations.”

If every currently envisaged infrastructure feature were implemented without further quantitative capability, HIO would become easier to trust operationally, but would remain unable to answer that question.

## 2. Economic validity: preserve the accounting, strengthen the evidence

**Verified:** the [return standard][returns] makes the essential distinctions correctly:

- Price, total, excess and strategy returns.
- Income, reinvestment and corporate actions.
- Funded positions and financing.
- Currency translation, hedge reset rules and cross terms.
- Collateral and futures P&L.
- Gross theoretical return and modelled costs.
- Per-period identities versus compounded relationships.

These are substantial strengths. They prevent common errors that can invalidate otherwise sophisticated portfolio analysis.

**Architectural judgement:** The principal weakness is not missing accounting vocabulary. It is the distance between the declared construction and evidence that the construction represents the exposure well enough for a particular use.

Before portfolio analysis, implementation evidence should demonstrate:

1. **Matched periods and bases.** Same start/end intervals, currencies, funding conventions and distribution treatment.
2. **Wealth accounting.** Portfolio wealth reconciles under declared rebalancing, cash and transaction-cost rules.
3. **No double counting.** Cash is counted once; currency embedded in foreign assets is not inadvertently added again as an independent holding.
4. **Economic event handling.** Distributions, splits, coupon dates, holidays, missing observations and revisions produce the intended result.
5. **Independent comparison.** Differences from an appropriate external reference are explained or retained as unresolved basis.
6. **Decision sensitivity.** Plausible construction differences do not silently reverse the research conclusion.

There are two particular traps to prevent.

**First, an ETF-derived equity factor is already a vehicle return.** Fund expenses are generally embedded in its observed return. The later implementation bridge must not subtract the same fee again or treat it as a fee-free index.

**Second, realised overnight accrual cannot automatically price an executable forward at the period’s start.** The existing forward functions are identities on supplied inputs, not evidence of available historical forward prices. A future `cip_implied` hedge needs rates known at initiation and appropriate to its tenor, or an explicit approximation label. Using subsequently realised SOFR to set an earlier hedge would introduce hindsight. This is a future specification requirement, not a discovered defect in the current synthetic functions.

### Duration: a good experiment, an incomplete investment milestone

**Architectural judgement:** One US ten-year CMT construction is a reasonable first difficult construction because it exercises income, discounting, calendar conventions and changing duration with relatively accessible official inputs.

It should remain bounded. It should not become a prerequisite for independently validating every part of the research workbench.

The economic questions are distinct:

| Question | What the experiment can establish | What remains outside it |
|---|---|---|
| Is the declared accounting implemented consistently? | Coupon-inclusive valuation, schedule conventions and reproducibility | Whether the synthetic exposure is tradeable |
| Is flat-yield pricing adequate? | Sensitivity to a declared discount-curve alternative | Accuracy of either model against traded securities |
| Is interpolation consequential? | Sensitivity across defensible interpolation choices | The unavailable underlying security prices |
| Does the series describe Treasury duration risk? | Signs, scale and behaviour consistent with independent return evidence | ETF tracking, costs and implementation |
| Can an investor realise it? | Nothing conclusive from a frictionless daily re-strike alone | Turnover, bid–ask costs, holdings, settlement and vehicle constraints |

**Independently checked external evidence:** Treasury describes the curve as fitted from indicative bid-side quotations rather than transactions. Its CMT points need not equal the yield of a specific security. The methodology changed to monotone convex on **6 December 2021**. These are material construction limitations, not reasons to discard the source. [Treasury methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology), [Treasury FAQ](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions).

The most important challenges are:

- **Par yield is not a zero rate.** Discounting every cash flow at one interpolated par yield is an approximation.
- **A bootstrapped zero curve is also a model.** Its interpolation and instrument conventions matter. Agreement with the original construction is useful sensitivity evidence, not an independent market observation.
- **Daily re-striking is a strategy.** It replaces the synthetic bond continuously; it is not simply holding a ten-year Treasury or a Treasury ETF.
- **The coupon schedule is synthetic.** Its declared strike anchoring resolves an accounting convention without reproducing an actual security’s coupon dates.
- **Yield-curve methodology and input changes can affect historical comparability.**
- **Gross turnover and implementation basis remain unmeasured.**

For **exploratory historical risk analysis**, convincing evidence would combine completed construction diagnostics with a separately cleared Treasury return reference, comparison over materially different yield environments, duration/key-rate-aware interpretation, and sensitivity of downstream covariance and portfolio conclusions.

For **comparison with an actual ETF**, add the fund’s price/NAV convention, distributions, duration profile, maturity band, fees, valuation time, currency treatment and rebalancing. Raw correlation is insufficient: common rate shocks can produce high correlation despite consequential carry or duration differences.

The existing E-0001 proposal appropriately limits its strongest conclusion to **UNREFERENCED**. I support that limitation. A same-source zero-curve comparison cannot close the independent traded-return evidence gap.

**Owner choice:** fund or otherwise obtain a cleared independent reference, or accept an explicitly unreferenced research limit. I recommend closing the gap before using the construction to support substantive allocation conclusions.

### Initial factor universe

Cash, equity, nominal sovereign duration and currency are the right starting set. They permit useful interaction analysis without pretending to span all economic risks.

My recommended order of additional breadth is conditional:

| Exposure | Research value | Recommended timing |
|---|---|---|
| Australian equity alongside US equity | Adds domestic concentration and currency distinctions | Early, if included economically in the first suitable licence |
| Inflation-linked duration | Directly relevant to real-return risk; distinguishes real yields from nominal duration | After the first panel, when a credible return history is available |
| Gold | A different candidate diversifier, with explicit storage/fund/currency basis | Early extension if the first data package supports a well-defined vehicle history |
| Credit | Important for recognising equity-like downside embedded in “defensive” assets | After duration; distinguish spread risk from rate duration |
| Broad commodities | Inflation and supply-shock questions, but substantial roll/collateral complexity | Later, tied to a defined research question |
| Time-series trend | Potentially different dynamic exposure, but breadth, costs and signal timing are demanding | Later replication programme, not a one-contract demonstration |
| Additional sovereign tenors | Useful curve-risk detail | Add when the first report demonstrates a need; several tenors are not several independent asset families |

Gold is not a guaranteed inflation hedge. Inflation-linked bonds are not cash-like protection against all short-horizon inflation shocks. Credit is not independent simply because its product label says “bond.”

## 3. Historical coverage: use reconstructed history, reject false precision

**Architectural judgement:** Decades of reconstructed market-return history should be the main first-year research resource. Prospective capture is a complementary asset for later evidence, not a substitute for those decades.

That approach is sound for descriptive return analysis and qualified historical risk research. It becomes misleading when:

- Current revised state data are represented as information available to a historical decision.
- Current ETF survivors define a purportedly historical opportunity set.
- Constructed proxies are silently joined across changing economic bases.
- Longer history is treated as additional observations from an unchanged distribution.
- A historical simulation is represented as an ex-ante forecasting result.

The [data-need statement][dataneed] needs revision in four respects.

**There is no universal twenty-year requirement for covariance.** A small fixed portfolio can yield useful risk information on a shorter sample, with uncertainty. Twenty years also does not guarantee stable covariance. Start with few economically distinct exposures and compare windows and estimators.

**Bootstrap block length is not a fixed six-to-twelve-month law.** It depends on the statistic and dependence being preserved. Resampling must use the same blocks across factors—and inflation where relevant. It cannot create independent crises that did not occur.

**More frequent data do not manufacture independent stress episodes.** Weekly observations may help assess timing and robustness, but do not turn one crisis into many crises. Tail-conditioned correlations also require care because selection on extreme returns changes their interpretation.

**Point-in-time integrity is not exclusively a Year-4 concern.** It matters whenever an analysis claims to estimate what could have been decided using then-available information. A descriptive regime comparison may use retrospective labels; a real-time regime allocation cannot inherit that permission.

A practical sample policy is:

| Research use | Adequate first step | Principal limit |
|---|---|---|
| Descriptive volatility/correlation | Available clean common history, with window sensitivity | Conditional on the observed period |
| Portfolio drawdown/recovery | Full retained paths and named stress episodes | Few independent severe events |
| Ex-ante covariance | Rolling estimates using only prior data; simple benchmarks | Forecast stability, not historical fit |
| Regime dependence | Prespecified state definitions and episode counts | Regimes may be few, ambiguous and structurally different |
| Three-year real shortfall | Historical rolling outcomes plus non-overlapping summaries | Overlapping windows are highly dependent |
| Valuation mean reversion | Long state/return history, vintage evidence and conservative inference | Few independent multi-year outcomes and substantial specification search |
| ETF implementation | Actual fund life plus separate longer exposure history | Fund history cannot validate pre-inception implementation |

For scale, **twenty years contain only six complete non-overlapping three-year periods**; forty years contain thirteen. These counts are not effective-sample estimates, but expose how misleading hundreds of overlapping windows can be.

Similarly, starting capture in 2026 cannot produce a five-year realised outcome until 2031. It cannot validate a five-year predictive relationship by itself within the earlier part of HIO’s horizon.

## 4. Data strategy: buy an answer, not a catalogue

The AUD 400/month figure and ETF-first preference are **owner-provided constraints**, not an approved mandate convention.

**Verified:** current established rights are much narrower than the candidate-source list. The [source register][sources] does not establish equity, FX, CPI, futures or broad reference permissions.

| Family | Minimum acquisition | Present position and limitation | When expenditure becomes useful |
|---|---|---|---|
| Cash | Applicable rates, dates, calendars and comparison indices | Five cash datasets cleared for bounded uses; historical calendars and pre-SOFR basis remain issues | Prefer official sources; pay only if a defined historical gap blocks a result |
| Equity | Unadjusted closes, complete distributions and splits, identifiers and source methodology | No selected cleared vendor; ETF life limits history | **Now:** a small trial can unlock the central diversification question |
| Duration | Official par curve plus independent return reference | Par-curve rights decided conditionally; independent reference open | A reference may provide more value than additional construction software |
| FX | Declared fixing and quote, historical dates and relevant rights | H.10/F11 unresolved; RBA accessibility does not clear underlying third-party rights | Needed for AUD analysis; forwards become valuable when realistic hedge research begins |
| Inflation/state data | Declared CPI and release/vintage metadata appropriate to use | ABS and broader state rights unverified | Resolve before real-target analysis; broader paid macro data should wait |
| Credit/TIPS | Income-inclusive returns, duration characteristics and methodology | No established route | Acquire when testing a specific weakness of the first allocation report |
| Gold/commodities | Fund TR or individual-contract settlements and contract metadata | Candidate rights unverified | One bounded exposure first; broad futures acquisition later |
| Trend | Multi-market contract histories, costs and timestamped signals | No suitable cleared breadth established | Only after selecting a replication target and its actual data requirements |

### Equity is now the binding acquisition problem

Without credible equity history, HIO can investigate bond accounting and cash accrual. It cannot meaningfully investigate its central equity–duration diversification or strategic allocation questions.

**Architectural judgement:** Equity data is currently more important than additional general software engineering.

The first purchase should be the smallest suitable package covering named US and Australian equity ETFs and, if economical, a Treasury ETF reference. It should not expand into stock selection, fundamentals or broad futures merely because a bundle is available.

Require before recurring commitment:

- Written confirmation of the applicable user class and uses.
- Retention, derivation, cloud-processing and termination rights.
- Instrument-specific history and corporate-action coverage.
- The meaning and provenance of the closing-price field.
- A sample reconciliation against an independent authorised source.
- A complete price including required exchange entitlements.
- A successful small research result.

**Independently checked external evidence:** EODHD’s terms retain a distinction between personal use and use on behalf of others. Its source page describes exchange/partner streams alongside CFD/market-maker data, while its general disclaimer creates further ambiguity. This does **not** establish that a particular ETF series is unsuitable; it means the exact feed and closing-price definition need written clarification. [EODHD terms](https://eodhd.com/financial-apis/terms-conditions), [EODHD source description](https://eodhd.com/financial-apis/our-data-sources-and-data-partners).

The existing enquiry asks useful licensing and content questions. I would add that provenance clarification before selecting a feed.

The budget permits at most **AUD 4,800 annually** if fully used. A capped month is a much smaller commitment than a year. No accessible quotation establishes which suitable package fits; I therefore recommend no vendor or advertised price as a settled choice.

A deletion-on-termination licence must not be placed automatically into the existing long-retention evidence account. Use storage compatible with the actual rights, or decline the licence. That does not require replacing the evidence architecture.

Finally, the Board download change is not a November deadline for losing history: its notice says historical XML remains available on release pages. The old urgency argument should no longer drive priorities. [Federal Reserve notice](https://www.federalreserve.gov/data/data-download-fred-information.htm).

## 5. Architecture: keep the structure, enable scientific work within it

**Architectural judgement:** The modular monolith remains the correct choice.

Keep:

- Separate capture, construction, analytics and publication responsibilities.
- Immutable, retained source evidence.
- Content-addressed release lineage.
- A disposable catalogue derived from manifests.
- Local research execution and scheduled capture.
- Publication as the controlled boundary to consumers.
- Independence from MACSMSF.

No evidence presented here justifies microservices, Kubernetes, a hosted catalogue, event infrastructure or a feature store.

### A two-speed research architecture is appropriate

| Boundary | Exploratory research | Reproducible/governed output |
|---|---|---|
| Inputs | Rights-cleared, pinned local exploratory releases | Inputs satisfying the intended publication and consumer requirements |
| Execution | Local scripts/notebooks; quick iteration | Pinned job, code, lock, parameters and retained inputs |
| Numerical work | Floating-point scientific calculations after an explicit conversion boundary | Declared tolerances and reproducible analytical results |
| Claims | Descriptive, conditional and explicitly limited | Claims supported by the required validation and authority |
| Authority | No new individual approval event merely to inspect already-authorised internal exploratory data | Status changes and consumer publication retain existing owner acts |
| Restrictions | Rights, valid return mathematics and honest knowledge-time labels always apply | Same restrictions, with stronger promotion evidence |

**Owner-decided:** OD-0038 already distinguishes internal exploratory research from consumer approval. A lighter scientific workflow does not require pretending exploratory work is approved.

The minimal reader should:

- Resolve exact releases and actual lineage.
- Enforce compatible knowledge mode and cutoff.
- Preserve period boundaries, currency, funding and economic class.
- Record alignment, missingness, transformation and code/lock identity.
- Recheck current rights and status when cached data are used.
- Refuse attempts to relabel a latest-value release as historical PIT evidence.

Use **canonical CSV as retained release content** and **derived Parquet for analysis**, with DuckDB for selection and alignment. There is no immediate need to rewrite release identity around Parquet.

NumPy is a justified small addition for covariance and resampling, subject to the existing stack-decision requirement. A wholesale numerical stack is unnecessary.

Two further boundaries matter:

- **Do not require bitwise equality of every future floating-point scientific result** merely because canonical accounting outputs are byte-reproducible. Declare numerical tolerances and environment constraints.
- **Do not let a notebook become an undisclosed second system of record.** Its important outputs must rebuild from retained inputs.

The architecture’s existing measured triggers remain appropriate. Twelve cron firings are not twelve dependent research jobs. No measured catalogue rebuild time, concurrency or consumer-latency evidence supplied here triggers a hosted database.

## 6. Analytics: implement comparisons before optimisation

The sequence should be:

1. **Aligned return panel and wealth accounting.**
2. **Descriptive portfolio paths, covariance and risk contribution.**
3. **Uncertainty and sensitivity**, including shrinkage and joint block resampling.
4. **Rolling ex-ante risk estimates** and forecast evaluation.
5. **Conditional risk and scenario analysis.**
6. **Expected-return ranges and strategic allocation comparisons.**
7. **Robust optimisation**, if simpler comparisons demonstrate a need.
8. **Predictive and tactical research**, with separate evidence.

Shrinkage deserves an early place because noisy covariance can materially affect allocation calculations; it is not a cure for changing regimes or bad inputs. [Ledoit and Wolf’s original paper](https://ledoit.net/honey.pdf).

Keep these claims separate:

| Analytical activity | What success establishes |
|---|---|
| Descriptive statistics | What happened in the retained sample |
| Explanatory factor modelling | How historical returns relate to chosen exposures |
| Ex-ante risk modelling | Whether estimates made before outcomes described subsequent risk adequately |
| Expected-return modelling | A defensible conditional distribution or range based on explicit assumptions |
| Predictive research | Incremental out-of-sample information against meaningful alternatives |
| Optimisation/allocation | A proposed decision conditional on objectives, estimates, costs and constraints |

A successful covariance chart establishes none of the later claims automatically.

For the real-return objective, first report historical experience. Later report **conditional** shortfall probabilities under explicit return, inflation and dependence assumptions. Preserve joint inflation/asset behaviour; do not simulate assets and inflation independently by convenience.

## 7. Agents, owner capacity and my earlier advice

**Verified:** independent review has exposed material problems despite passing suites. The T-0014 review found false rebuild assurance; T-0019 distinguished decomposition consistency from pricing validity. Those are valuable corrections, not procedural ornament.

**Unknown:** whether implementation quality is improving systematically, whether Claude devotes enough hours to research, or whether the overall agent system saves owner time. The repository supports evidence of useful interventions, not a net productivity calculation.

The visible work products justify a narrower conclusion: **the collaboration has increased assurance, but has not yet demonstrated increased research throughput.**

Keep the differentiated responsibilities. Reduce the amount of work requiring orchestration by narrowing deliverables and keeping routine research within clear authorised scope. The owner continues to control assignments; this assessment changes no reviewer assignment or test plan.

### Re-examining my advice

The attribution below is **Reported**, from [the performance-review draft][performance] and cited OD summaries. My reassessment is **Architectural judgement**.

| Earlier recommendation | Reassessment |
|---|---|
| **Complete the cash path/base camp before paying for data** — consultation `…182940-ask-9dab`, OD-0129 | **Incomplete.** A minimum integrity demonstration was justified. Making the broader milestone a barrier to a small equity-data trial imposes a weak dependency. Separate evaluating data from production procurement. The original owner’s stable-footing preference still requires an explicit decision to change. |
| **Keep B-3 blocked after the initial C5 result** — `…202344-ask-4dcb` | **Over-conservative as sequencing advice.** Refusing a false C5 pass was sound. Exploratory capture did not need to wait for a finality claim. OD-0139 later made that distinction. I should have separated evidence validity from permission for the narrower activity earlier. |
| **Narrow H6 recovery rather than trust pre-existing imports** — `…103714-ask-15f7`, OD-0109 | **Technically sensible but strategically incomplete.** Narrowing reduced the trust boundary, yet further cycles still produced no activated tool. I should have put more weight on manual receipt as an adequate fallback and the research opportunity cost. |
| **Prioritise prospective capture heavily** — factor-first consultations | **Sound principle, overstated marginal benefit for the current programme.** Cash capture is useful operational evidence and a retained asset. It does not accumulate the valuation and macro-state history required by the eventual predictive programme. |
| **Factor-first, then a reader justified by the duration result** | **Directionally sound, unnecessarily serial.** Reader requirements also follow from cash and equity. The smallest reader can develop alongside the duration experiment without assuming that experiment succeeds. |

The same records support useful earlier contributions on the reader boundary and go-live ordering. Adoption is not proof those recommendations were correct, and no original transcript available here permits a comprehensive retrospective grading.

### Eight-hour owner-week planning scenario

This is a proposal, not an estimate of actual expenditure:

| Owner attention | Hours/week | Intended result |
|---|---:|---|
| Data rights, vendor responses and bounded procurement | **3** | Remove the most consequential external blocker |
| Economic interpretation and construction dispositions | **2** | Decide what the evidence supports |
| Examine the first portfolio analysis and its uncertainties | **2** | Ensure engineering produces investment understanding |
| Operational exceptions and necessary authority decisions | **1** | Keep capture functioning and obligations visible |

Operational incidents override this allocation. Routine assurance should not consume the research allocation indefinitely.

Use existing records to note actual attention consumed; no new dashboard or process is needed. If the eight hours repeatedly disappear into receipts and merges, reduce concurrent work and deliverable fragmentation before building more orchestration.

## 8. Three alternative sequences

The times below are planning judgements, conditional on rights and vendor response; they are not estimates derived from developer-hour measurements.

| Criterion | A — Continue substantially as planned | B — Accelerate quantitative research | C — Consolidate foundation first |
|---|---|---|---|
| Sequence | Soak/base-camp progress, duration, reader, risk | Equity enquiry/trial and small reader alongside bounded duration; operations in background | Finish operational, recovery, finality and broader rights evidence before analytics |
| Research value | Moderate; remains vulnerable to serial delay | **Highest near-term** if data clear | Low initially |
| Architectural integrity | Strong | Strong with existing boundaries preserved | Strong, with diminishing marginal assurance |
| Data/operational risk | Moderate | More explicitly limited exploratory uncertainty | Lowest operational uncertainty; economic gaps remain |
| Owner workload | Continued frequent task/receipt decisions | Greater emphasis on data and interpretation; bounded work packages | Highest assurance burden |
| Rework exposure | Reader may arrive late; equity still blocks | Some exploratory work may be discarded | Risk of assuring machinery that research later changes |
| Financial cost | Purchases later | Small trial earlier; no broad commitment | Lower immediate data spend, longer delay |
| Useful first result | Plausibly within 90 days, but dependencies threaten it | **Target within 30–90 days** | Likely later; no defensible exact date |
| Long-term reproducibility | Strong | Strong if promotion boundary holds | Strong |

**Preferred: B with a bounded portion of C.**

Complete the existing soak and necessary recovery evidence. Do not wait for every base-camp criterion before learning whether the data and basic portfolio analysis are useful.

I would change this preference if capture requires sustained intervention, retained evidence cannot be reliably recovered, or suitable equity rights prove unavailable. Those would be concrete reasons to consolidate or narrow the research claim.

## 9. Direct answers to the fifteen challenge questions

1. **Are we over-engineering?**  
   **Selectively, yes.** H6 recovery automation, repeated administrative receipt handling and a broad procurement-readiness gate have weaker marginal value than an equity history and first portfolio report. The core evidence and accounting architecture is justified.

2. **Single largest threat?**  
   **Confusing an auditable synthetic history with a fit-for-purpose investment exposure.** Strong provenance cannot rescue weak economic representation or unsuitable inference.

3. **Largest architectural strength?**  
   **Reproducible economic accounting tied to retained evidence.** Preserve the ability to trace a conclusion back to its inputs and conventions.

4. **Weakest-connected implementation milestone?**  
   **H6, if parked work is included.** Among proposed forward milestones, requiring all free-history rights decisions before a small equity-data evaluation is particularly weak.

5. **Largest marginal missing capability over ninety days?**  
   **An aligned, economically valid equity–duration–currency–cash analysis with uncertainty and hypothetical portfolio paths.**

6. **Too focused on individual factors?**  
   **Yes at the margin.** Enough individual construction is needed to avoid invalid inputs, but further tenors should not precede the first interaction result.

7. **How soon can useful portfolio analysis begin?**  
   As soon as rights-cleared return inputs and alignment exist—**a 30–90-day target is reasonable**, conditional on acquisition. Begin with fixed hypothetical allocations and descriptive claims.

8. **Does the data strategy support risk and mean-reversion research?**  
   **Partly for descriptive risk; not yet for credible mean-reversion inference.** Long state histories, vintage evidence, independent episodes and out-of-sample design remain unresolved.

9. **What proves duration is economically meaningful?**  
   Independent return comparison, explained duration/curve/carry differences, construction sensitivity and stable downstream conclusions. Passing its own identities is insufficient.

10. **What could a smaller research system do equally well?**  
    The next several covariance, drawdown, fixed-allocation and bootstrap analyses can run locally from a few pinned files. They need no service platform or receipt automation.

11. **Controls I would not weaken?**  
    Rights default-deny; retained evidence for reproducibility claims; correct income/financing/currency accounting; honest knowledge time; exact-revision evidence; independent scrutiny without author self-acceptance; the MACSMSF boundary.

12. **Most plausible six-month disappointment?**  
    More accepted infrastructure and synthetic constructions, but still no reliable equity panel or explanation of portfolio trade-offs. Recognise it if the first thirty days end without a concrete source decision and executable cross-factor analysis.

13. **Strongest argument against my sequence?**  
    The first real operations already exposed assumptions synthetic work missed. Accelerating analytics may compound weak inputs. That is why the recommendation retains bounded operational completion and explicit exploratory limits.

14. **What would I design differently today?**  
    Define the first portfolio comparison at inception, start the equity licensing enquiry immediately, and build foundations only as needed to reproduce that result and maintain capture.

15. **Where was my advice wrong or incomplete?**  
    I over-weighted serial assurance prerequisites, did not constrain H6’s opportunity cost early enough, and did not sufficiently distinguish cash capture from the state-vintage evidence needed for prediction.

# F. Revised 30/90/365-day research milestones

## Horizon 1: next thirty days — three primary priorities

| Priority | Concrete outcome and question | Dependencies and evidence | Authority |
|---|---|---|---|
| **1. Resolve the first equity-data route** | A written source decision: can HIO obtain suitable equity TR inputs and a Treasury reference on acceptable terms? | Existing enquiries, instrument-specific coverage/provenance, rights, price; then a capped trial if approved | Sending existing questions is already covered by OD-0155. Purchase and retrieval require their own authority. |
| **2. Establish bounded factor evidence** | Cash comparison dispositions and the authorised duration experiment’s stated diagnostics; identify what remains economically unproven | Retained bytes, repeatable builds, accounted observations, independent access to underlying evidence where verification is claimed | Cash spec changes/dispositions remain owner acts. OD-0157 records duration authority at #92’s head, with its holds intact. |
| **3. Build the smallest analytical path** | Load pinned releases, align periods and reproduce fixed-portfolio wealth/risk calculations; use real data as it clears | Reader boundary, small numerical dependency, analytical acceptance cases and explicit limitations | New bounded authority needed; reader sequencing must be changed from the serial order in OD-0139. |

**Standing operational obligation:** complete the existing soak and prepare the owed operational exercises. This is not a fourth expansion priority. Respect the authorised research pause if capture needs attention. Keep the 2027 calendar deadline visible.

A thirty-day success can still be “equity licence rejected for stated reasons” or “duration approximation inadequate.” Those are useful independently assessable outcomes.

## Horizon 2: days thirty to ninety

Deliver the first **hypothetical allocation research report**, not merely factor charts.

**Minimum inputs**

- One suitable US equity return history.
- One sovereign-duration history with its validation status clearly stated.
- AUD cash and a cleared FX history for AUD interpretation.
- Australian equity if the first package supports it without material delay.
- CPI only if cleared and its research convention explicitly selected.

Start with funded returns. **Long unhedged foreign-asset analysis does not require a pre-2018 USD cash splice.** Do not make historical hedging or excess-return construction a prerequisite for every initial question.

A US equity proxy must not be called global equity. An AUD-translated US duration series includes currency risk; report that component explicitly.

**Calculations**

- A few prespecified fixed allocations and rebalancing rules.
- Compounded wealth, volatility, drawdown, recovery and time under water.
- Sample and shrinkage covariance, with risk contributions.
- Weekly/monthly alignment sensitivity.
- Joint block uncertainty estimates and named stress episodes.
- Local-return, currency and cross-term attribution.
- Real-return histories only where CPI inputs permit.

**Acceptance evidence**

- Every included/excluded period accounted for.
- Portfolio accounting reconciles.
- Same retained inputs and pinned execution reproduce the report.
- Alternative samples and construction assumptions are shown.
- An unresolved input basis is propagated to the conclusion.
- At least one substantive question receives an answer or an explicit “insufficient evidence.”

If duration remains unreferenced, either use a separately cleared reference for the limited analysis or present a construction-sensitivity demonstration. Do not quietly upgrade its status.

## Horizon 3: months three to twelve

| Capability | Evidence of capability | Actual investment usefulness |
|---|---|---|
| Economically validated initial library | Independent comparisons, documented differences and reproducible histories | Confidence that observed portfolio behaviour is not mainly construction error |
| Risk model v1 | Rolling sample/shrinkage/EWMA estimates, evaluated using subsequent observations | Better awareness of changing risk and estimation uncertainty |
| Scenario and path analysis | Historical replays plus explicit hypothetical shocks | Understanding joint equity, rate, currency and inflation failure modes |
| Exposure-level allocation comparison | Stable results across assumptions, costs and constraints | Clearer trade-offs without pretending one allocation is optimal |
| Expected-return ranges | Building blocks, counterarguments and sensitivity | A disciplined view of plausible outcomes rather than extrapolated averages |
| First ETF implementation bridge | Factor versus vehicle TR, duration, currency, fees and liquidity differences | Evidence about whether the desired exposure is practically obtainable |
| Relevant state-data foundation | Cleared archives/vintages or targeted capture for named hypotheses | A credible route to later predictive work |

By one year, I would prefer **a small trusted library and two useful reports** to a broad catalogue with weak economic references.

## Horizon 4: years two to three and beyond

Progress should depend on research evidence:

1. Add credit, real duration, gold/commodities and broad trend where they address demonstrated portfolio weaknesses.
2. Develop conditional risk models only when simpler estimators and scenario analysis have exposed a specific deficiency.
3. Expand expected-return work with uncertainty and structural-change alternatives.
4. Investigate factor valuation and mean reversion using long historical states, careful vintage claims and conservative treatment of overlapping horizons.
5. Introduce robust allocation methods after showing the fragility of simpler allocation comparisons.
6. Run tactical experiments against fixed strategic benchmarks, with costs, timestamped inputs, honest variant counts and shadow outcomes.
7. Publish independently consumable outputs through the existing rights and authority boundaries.

Successful prediction is not a scheduled deliverable. Neither a three-year programme nor a five-year programme guarantees enough independent evidence to establish medium-term timing skill.

# G. Stop-doing recommendations

| Reduce, defer or stop | Opportunity cost | Resume condition |
|---|---|---|
| **H6 development** | Competes with data acquisition and analytical implementation | A material measured manual burden and a narrowly credible payback case; OD-0114’s conditions remain |
| **Further storage hardening beyond current obligations** | Adds assurance before evidence that it changes research reliability | Demonstrated risk, operational failure or a required approved obligation |
| **More CMT tenors before the first interaction report** | Adds correlated series and construction work | A specific curve-risk question needs them |
| **Broad futures/trend procurement** | Uses budget and integration effort without a defined first result | A chosen replication or allocation question specifies the necessary contracts |
| **Optimisation and tactical infrastructure** | Magnifies estimation error and weak data | Stable descriptive/risk evidence and a justified decision problem |
| **Treating every exploratory iteration as a new approval event** | Consumes owner attention without increasing economic validity | New scope, rights, expenditure, authority or promotion actually requires a decision |
| **Repeated navigation polishing** | Can displace substantive work | A stale pointer materially impedes the active task; keep maintenance bounded |

Do not stop existing capture, erase unresolved findings or describe an obligation as discharged merely because it is deprioritised.

# H. Owner decisions

These are recommendations for fresh authority, not requests made by this report.

1. **Reader and analytical scope**  
   **Yes/no:** Authorise a bounded local exploratory reader and fixed-allocation workbench, including NumPy, alongside the duration experiment rather than after its result?  
   A yes changes the serial working order adopted under **OD-0139** and supplies the required stack decision under **OD-0038**. It approves no factor, consumer use or prediction.

2. **Limited procurement before full base camp**  
   **Yes/no:** Permit a separately approved, rights-cleared one-month data trial before all proposed base-camp criteria are met, within the AUD 400 total monthly subscription ceiling?  
   A yes changes the owner’s earlier procurement sequencing preference recorded around **OD-0129**. It does not select a vendor or establish permissions. I recommend yes once the written evidence packet is adequate.

3. **Historical exploratory hypothesis scope**  
   **Yes/no:** Authorise separately labelled reconstructed-history investigations of the questions behind H-0001 and H-0002, without altering their current proposed PIT requirements or representing the new work as confirmation of them?  
   A yes enables useful descriptive investigation while preserving the stronger claim boundary.

The following are **existing outstanding decisions**, not new proposals to reauthorise work:

- Treasury page-reading confirmation and other OD-0157 prerequisites.
- Cash dispositions and any spec revision.
- C5 resolution before finality claims; changing its normative rule affects **HIO-ADR-0012**.
- Second-copy destination and execution details under the existing first-month obligation.
- Source-specific rights and any consumer publication.

I recommend neither reopening H6 nor adopting a wholesale governance amendment now.

# I. Falsification and confidence

**High confidence:** the approved structural architecture should be preserved; the economic data and analytical gaps are real; additional infrastructure alone will not answer the investment questions.

**Moderate confidence:** accelerating the small analytical path is the best next sequence.

**Low confidence:** elapsed delivery estimates, net agent efficiency and actual procurement economics.

The three strongest reasons this assessment could be wrong are:

1. **Operational burden may be understated.**  
   If the soak reveals repeated failures or recovery cannot reproduce retained evidence, consolidation should take priority until the specific problem is bounded.

2. **Suitable data may be inaccessible within the budget and rights constraints.**  
   If written vendor answers rule out usable equity/reference history, the first report must narrow. More software will not compensate.

3. **Unobserved owner effort may favour the current workflow.**  
   The elaborate process may already save substantial attention that repository records do not show. Conversely, it may cost more than this assessment assumes. Actual attention spent and research delivered would change my judgement.

I would materially revise the recommendation if, within thirty days, there is no feasible data route, capture repeatedly interrupts research, or the minimal workbench proves unable to enforce the existing boundaries simply.

# J. Immediate next action

**Preferred bounded next step: the owner sends the already-authorised T-0003 vendor enquiries.**

**Actor:** owner.

**Authority:** OD-0155 already permits the revised enquiries; no purchase is authorised.

**Prerequisites:** choose recipients and complete the sender details. Ask for instrument-specific closing-price provenance alongside the existing questions on distributions, splits, storage, use and termination.

**Acceptance evidence:** dated written responses identifying the applicable licence, usable fields/history, exact feed basis and complete cost. Retain the correspondence in an appropriate permitted location; do not put personal identifiers or licensed values into the public repository.

**Stop conditions:** no assumption that silence grants rights; no subscription, data retrieval or immutable retention until the applicable decisions and conditions permit them.

Meanwhile, Claude can continue the existing duration authorisation within its stated prerequisites and scope. This advice creates no implementation instruction or reviewer assignment.

**If I were responsible for HIO's architectural direction over the next 12 months, my three highest priorities would be...**

1. **Secure a small, economically credible return dataset**, especially equity and an independent duration reference. This removes the binding research constraint before more engineering accumulates around unsuitable inputs.
2. **Deliver reproducible portfolio-interaction analysis with uncertainty.** This converts the foundations into evidence about diversification, drawdown and allocation trade-offs.
3. **Demonstrate the bridge from factors to actual ETF exposure while keeping operations proportionate.** This tests whether research conclusions survive implementation basis, fees, liquidity and the owner’s limited attention.

[charter]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/charter.md
[architecture]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/architecture.md
[returns]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/standards/return-accounting-and-factor-construction.md
[observations]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/standards/observations-and-point-in-time.md
[specstandard]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/standards/factor-specification.md
[od139]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0139-adopt-capture-gate-revision-and-factor-first.md
[src]: https://github.com/elusivenode/hio/tree/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/src/hio
[dependencies]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/pyproject.toml
[experiments]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/registers/experiments.yaml
[cmtverify]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/reviews/records/VERIFY-2026-11-04-t0019-1-1.md
[od153]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0153-receive-t0019-verification-accept-t0019.md
[cashreport]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/evidence/b3/cash-rebuild-1.md
[od148]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0148-repeatable-cash-rebuild.md
[firstrun]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/evidence/b3/first-run.md
[soak]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/evidence/b3/soak-1.md
[od149]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0149-i5-met-soak-boundaries.md
[b2]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/evidence/b2/rerun-1.md
[sources]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/registers/sources.yaml
[od156]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0156-h2-six-operations.md
[od157]: https://github.com/elusivenode/hio/blob/09e29e5741a89e10bfac54d58346df0b7ba674f7/docs/decisions/owner/OD-0157-authorise-duration-experiment.md
[od114]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/owner/OD-0114-park-h6.md
[equityresearch]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/research/T-0003-equity-total-return-sources.md
[cmtspec]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/specs/factors/rates.us.cmt_10y.total_return.yaml
[factorfirst]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/decisions/factor-first-sequencing-proposal.md
[basecamp]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/base-camp.md
[resolver]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/src/hio/publish/status.py
[dataneed]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/research/data-need-statement.md
[performance]: https://github.com/elusivenode/hio/blob/bde61d74f8b97e7e7c6d50c15a76939a9e77a26e/docs/agents/solution-architect/performance-review-1.md