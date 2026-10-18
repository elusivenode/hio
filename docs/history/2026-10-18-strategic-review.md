# HIO: strategic review of the investment research and portfolio construction direction

**Status:** assessment for discussion. No code, schema, documentation or roadmap was changed.
**Prepared:** 18 October 2026, against `main` at `1502ab8` and the local `macsmsf` database
(last refreshed 10 October 2026).
**Reviewer stance:** senior quantitative researcher and critical technical reviewer. The aim is
to test the proposed direction, not to endorse it.

### Evidence tags

| Tag | Meaning |
|---|---|
| **[REPO]** | read directly from code, migrations or documentation in this repository |
| **[DB]** | queried from local Postgres in this session |
| **[ASSESSMENT]** | my judgement, with reasons given |
| **[EXTERNAL]** | general knowledge of the literature or of vendors. **Not re-verified in this session**: check it before relying on it. |

---

## A. Executive assessment

**Short answer.** The current roadmap (`docs/investment-process-roadmap.md`) is a sound
foundation for the first year. In several ways it follows the brief's own operating principles
more closely than the brief's proposed research universe does. It is not yet a foundation for a
*systematic multi-asset research capability*, and it does not try to be one. That is mostly
right for now. It has three structural gaps that will matter within 6–12 months:

1. **There is no market-observation layer independent of the holdings.** All market data comes
   from yfinance, and only for tickers the fund currently holds
   (`ingestion/etf_price_worker.get_currently_held_tickers`) **[REPO]**. Apart from CPI, the
   research question cannot look at anything the fund does not already own. This contradicts
   the brief's principle that "the research framework should not be constrained by current
   holdings". It is the most important architectural gap.
2. **There is no returns-based view of exposure.** Roadmap area 1 measures exposure from
   issuer documents (holdings-based look-through). That is the right first step. But nothing
   estimates exposure *from returns*, and nothing reconciles the two. This repo's own method
   finds errors by comparing two figures that must agree (`CLAUDE.md`). Disclosed and estimated
   exposure is exactly such a pair, and it is the natural entry point for factor research.
3. **Nothing separates a target exposure from a target asset class.** The only portfolio target
   in the system is the strategy's section 4 asset-class table (`reporting/asset_classes.py`)
   **[REPO]**. Its labels say what a vehicle is, not what risk it carries. There is no concept
   of "target equity beta", "target duration" or "AUD exposure range". The brief's separation
   of research from implementation needs one.

**Where I would push back on the brief itself** **[ASSESSMENT]**:

- **The proposed universe is too broad for the decisions this fund can make.** The fund is about
  $680k, holds 11 ETFs/LITs, has two trustees, one operator and four months of history
  **[DB, REPO]**. Seven factor families, futures-curve carry, volatility risk premia and
  currency carry/value add estimation burden faster than they add decision value. A
  parsimonious library of about seven macro factors explains most of the variance in a
  portfolio like this. The style factors (value, size, quality, momentum, low volatility) only
  matter if the trustees intend to tilt toward them, and nothing in the strategy says they do.
- **Building factors from futures (CME DataMine, roll methodology) is premature.** The fund
  implements through ETFs. Academic factor series plus long-history ETF and index proxies are
  enough for every decision on the 12-month roadmap. Build your own series only where a decision
  depends on it and no published series fits. AUD-based financing and hedging conventions are
  the likely first case.
- **The brief's factor table leaves out three return drivers that matter more to this fund than
  most of what it lists:**
  - **Tax and franking.** For an Australian SMSF in accumulation phase, franking credits and the
    15% / 10% CGT structure are first-order return drivers.
  - **Illiquidity and valuation risk.** MXT is the fund's largest realised risk event so far. It
    was a valuation dispute, a suspension and a redemption freeze, not a factor move
    (`docs/quarterly-pack-v2-investigation.md` A1.8) **[REPO]**.
  - **The AUD as a defensive asset.** For an AUD investor, unhedged foreign currency is usually a
    diversifier: the AUD tends to fall when risk assets fall **[EXTERNAL]**. The fund's roughly
    30% unhedged foreign currency is "from the vehicles chosen, not from a decision"
    **[REPO]**. That is the most consequential currency question, and it is a strategic
    hedge-ratio decision, not a carry factor.
- **Tactical asset allocation (TAA) needs to be handled more sceptically than the brief does.**
  Statistically, the fund's own record can never validate a TAA process within the trustees'
  horizon (see E.4). The defensible first form of TAA is rules-based rebalancing within bands,
  plus a written cash-deployment rule. The roadmap already proposes the latter, and it is
  already an implicit tactical position: 17.3% cash against a 15% benchmark **[REPO]**.

**Bottom line.** Keep the roadmap's four areas and their order. Add a small, separate research
data lane and a returns-based exposure cross-check, timed to feed the March 2027 downside work.
Settle the objective before any strategic asset allocation (SAA) work, because everything is
measured against it. Defer futures, own-built style factors, volatility premia, optimisation
and signal-driven TAA until a specific decision needs them.

---

## B. Current-state assessment

### B.1 What exists: implemented and live

| Capability | Where | Status | Reusable for research? |
|---|---|---|---|
| Medallion pipeline: Bronze receipts → Silver conformed → Gold-Base daily | `sql/001–049`, `pipeline/local_refresh.py` | live, promoted to Neon | **Pattern yes, tables no.** Keep research out of the accounting medallion |
| Per-asset TWR/MWR indices, price/income split | `gold/asset_performance.py`, `fact_asset_daily_index` | live; IVV/QPON provisional (trade recon open since 2026-08-10) | Yes: realised holding returns are the "actual" leg of any proxy-error test |
| Whole-fund daily TWR, unit price, member equity | `gold/fund_index.py`, `unit_pricing.py`, `member_equity.py` | live | Yes: the fund series that factor models must explain |
| Contribution attribution, Carino-linked, raises if it doesn't reconcile | `api/attribution.py`, `api/contributions.py` | live | **Yes, a template**: factor attribution should follow the same reconcile-or-raise rule |
| Reference indexes (Rest, Hostplus, UniSuper, VDHG/VDBA/VDCO), with revision tracking | `ingestion/reference_index_registry.py`, `sql/039–041` | live | Peer context only, not risk factors |
| CPI + 5% benchmark index | `gold/cpi_benchmark_index.py` | live; seasonality issue noted (A2) | Yes, for the inflation leg |
| Market data: yfinance unadjusted close + distributions; USD/AUD FX | `etf_price_worker.py`, `fx_rate_worker.py` | live, **held tickers only** | Proxy history exists by accident: IVV and GOLD back to 2008, DBMF to 2019, BGBL/GLIN only to 2023 **[DB]** |
| Append-on-change revision tracking for market data | `sql/043` | live | **Yes, directly.** It is the vintage-storage pattern a research lane needs. It was built after a real yfinance revision moved a settled receivable **[REPO]** |
| Quarterly pack, minute, agenda; market-conditions table | `reporting/` | live, Q1 FY2027 finalised | The delivery channel for research outputs |
| Strategy asset-class map with ranges | `reporting/asset_classes.py` | live | It is the current "SAA". Label-based, not exposure-based |

### B.2 Code-complete, not activated

| Item | Status | Relevance |
|---|---|---|
| **HIO-001 instrument master** (`silver.dim_instrument`, dated identifiers, versioned economic taxonomy, provenance-backed classification) | merged `fea8203`; **not applied to the authoritative database**: `to_regclass('silver.dim_instrument')` is null **[DB]**. Five classification calls and the vehicle types await owner confirmation | **This is the implementation-layer identity the brief asks for.** It covers vehicles the fund does not hold. It is not a factor or exposure model: ADR 0003 explicitly defers look-through and characteristics |
| **A17-A backup tooling** | merged `c06b664`; not activated (F-11, key ceremony, provisioning) | Operational safety; not on the research critical path |
| **A17-B verified promotion procedure** | not built | Blocks *production* activation of any new schema. **It does not block local-only research** (see F) |

### B.3 Planned: the proposed roadmap (for discussion today)

- Four areas, in order:
  - exposures (December 2026);
  - downside (March 2027);
  - feasibility of the objective (June 2027);
  - a decision register (from December, then every quarter).
- A formal review of the objective in parallel.
- Explicitly out of scope: optimisation, an extensive backtester, macro forecasting, and
  speculative database structures.
- The Phase 1 to 4 backlog in `docs/quarterly-pack-v2-investigation.md`:
  - reporting integrity;
  - look-through and risk;
  - research documents (the capital-market assumptions paper, stresses);
  - decision discipline.
- Other open directions from earlier sessions: Azure and Prefect orchestration, CMC and
  Macquarie APIs, a frontend date-range filter. These are infrastructure, not research.

### B.4 Gaps that matter (ranked by effect on investment decisions)

| # | Gap | Evidence | Why it matters |
|---|---|---|---|
| G1 | **The investment objective is unresolved.** The adopted strategy says CPI + 3% over five years; the stated intent is CPI + 5% over three years with low drawdowns | `investment-process-roadmap.md` | No SAA, risk budget or TAA rule can be evaluated without it. This is the binding dependency |
| G2 | **No risk analytics at all**: no volatility, drawdown, correlation or tracking error | `CLAUDE.md` known gaps; the `portfolio-analytics` skill | Area 2 needs them |
| G3 | **Market data is scoped to holdings and depends on one unofficial source** | `get_currently_held_tickers`; yfinance only | Research cannot see non-held exposures. yfinance has no licence, no point-in-time guarantee, and revises history (already observed) |
| G4 | **No macro or market observations beyond CPI**: no yields, curves, credit spreads, cash rate, trimmed mean, or AUD trade-weighted index | `sql/` inventory | Duration, credit and inflation exposures cannot be estimated or stressed from data |
| G5 | **No exposure-level target**, only asset-class ranges | `asset_classes.py` | The research → allocation → implementation separation has nowhere to land |
| G6 | **No hypothesis or decision record** | roadmap area 4 (planned) | Without it, research results cannot be audited against outcomes |
| G7 | **Tax is not modelled in returns**: no earnings-tax accrual; franking not separated | A1.6, A1.7 | After-tax SAA comparisons are impossible; for an SMSF this is material |
| G8 | **Four months of fund history** | fund inception 2026-06-08 | Any statistic on the fund's own returns is anecdotal. Research must use proxy history, labelled as such |

---

## C. Recommended target capabilities

### C.1 Concepts that must not be conflated

The brief is right to insist on this. Here is a working vocabulary, with one example from this
fund's context for each concept.

| Concept | Definition | Example | What it is used for | Lives in |
|---|---|---|---|---|
| **Economic state variable** | An observable condition of the economy or markets. Not a return | headline CPI YoY; RBA cash rate; AU 10y yield level; term spread; credit spread level; PMI | conditioning, regime labels, building-block expected returns | Research datasets |
| **Systematic risk factor** | A shock common to many assets that investors care about. Often unobservable, proxied by changes in state variables | inflation surprise; growth surprise; real-rate shock; credit-spread shock | explaining co-movement; stresses | Investment models |
| **Tradable factor return** | The return on a portfolio built to carry one factor, in excess of a stated financing rate | global equity excess return (AUD); AU 7–10y government bond excess return; IG credit excess return over duration-matched government bonds; AUD/USD return; TSMOM portfolio | regressions, covariance, attribution | Research datasets |
| **Risk premium / expected-return source** | The *expected* value of a tradable factor return, an assumption with uncertainty | equity risk premium ≈ earnings yield + growth − cash; term premium; credit spread net of expected default | SAA and capital-market assumptions | Investment models (trustee-approved) |
| **Dynamic strategy** | Rules that change exposures over time from signals | trend following; rebalancing bands; a cash-deployment rule | TAA; describing what DBMF and GROW do | Investment models or decisions |
| **Holding / instrument** | A vehicle that delivers some mix of the above, plus residual, costs, tax and operational risk | IVV, GROW, DBMF, MXT | implementation and accounting | `dim_instrument` (HIO-001), `dim_asset` |

Three consequences:

- **A macro "factor" in the brief's table (inflation, growth, monetary policy, liquidity) is a
  state variable or a shock, not a return.** It enters portfolio work in only two ways:
  - through a factor-mimicking portfolio, for example the excess return of nominal over
    inflation-linked bonds for inflation; or
  - as a condition, for example "returns in high-inflation months".

  Regressing fund returns on CPI *levels* is a category error.
- **A dynamic strategy is not a factor.** DBMF's managed futures exposure is a time-varying
  combination of factors. Its static beta to anything is close to meaningless (see E.3).
- **A holding is never "an exposure".** GROW is an active multi-asset fund whose exposures change
  monthly. Treating its asset-class label as its exposure is the error the current strategy
  table makes, and the error area 1's look-through corrects.

### C.2 Target capability map: the brief's seven layers mapped to this repository

| # | Layer | Contents | Proposed home | Exists today? |
|---|---|---|---|---|
| 1 | **Market observations** | raw and validated series from official and academic sources, with vintages | a new, isolated lane: separate schemas (for example `mkt_bronze`, `mkt_silver`), reusing the Bronze receipt and `sql/043` append-on-change patterns. No foreign keys into the accounting medallion | no (yfinance for held tickers only) |
| 2 | **Research datasets** | constructed AUD factor returns, proxy-asset returns, state variables, regime labels; versioned and reproducible from layer 1 | `research` schema, or versioned files with a manifest. **Files first** (see F.3) | no |
| 3 | **Investment models** | exposure estimates, covariance, capital-market assumptions, scenarios; each a dated, versioned, owner-approved artefact | documents plus versioned parameter files; a database table only once reused quarterly | no |
| 4 | **Portfolio construction** | target *exposure* ranges and risk budget; the asset-class table derived from them | a new strategy artefact; `asset_classes.py` stays the trustee-facing compliance surface | asset-class ranges only |
| 5 | **Tactical decisions** | proposed deviations, with rule, size, confidence, triggers to review and reverse | the decision register (roadmap area 4) | planned |
| 6 | **Implementation** | instrument selection: tracking error to target exposure, fees, liquidity, tax (franking, CGT), currency hedging, operational and manager risk | `dim_instrument` and classification (HIO-001) plus an implementation-assessment template | identity exists, not activated |
| 7 | **Performance evaluation** | attribution of realised returns to the policy portfolio, tactical deviations, implementation and residual; decision review | the existing Gold-Base, attribution and pack, **extended** with policy-vs-actual attribution | partly (holding-level contribution) |

**Boundary rule** **[ASSESSMENT]**: layers 1–4 name exposures, never tickers. Layer 6 is the
only place a ticker meets an exposure. Layer 7 is the only place research meets the accounting
core, and it does so by reading Gold-Base, never writing to it. This rule fits the HIO
preservation principle naturally: nothing in layers 1–5 can regress SMSF accounting, because
nothing there touches it.

### C.3 What "portfolio construction" should mean at this scale

The fund will hold perhaps 8–14 vehicles. Each change costs brokerage and spread, and may
crystallise CGT. A decision is therefore a small number of discrete, reasoned moves, not a
continuous optimisation. The target capability is:

- a **policy portfolio** stated as exposure ranges: equity beta, duration, credit, real assets
  and inflation sensitivity, foreign-currency share, defensive diversifiers, liquidity floor;
- a **risk budget**: an approximate split of expected volatility and stress loss across those
  exposures, consistent with the drawdown tolerance;
- an **implementation map**: which vehicles deliver which exposure, and with what residual;
- **rebalancing bands**.

The trustees can understand and own this. Mean-variance optimisation would add false precision
on top of it **[ASSESSMENT]**.

---

## D. Data acquisition priorities

### D.1 Principles

1. **Acquire data for a decision, not for coverage.** Each new series should name the work
   package and the question it serves.
2. **Official and academic first, commercial when a named gap appears.** For a fund of this size,
   most of the value is in free, high-quality series. Commercial data is justified for
   survivorship-free history or licence clarity, not for breadth.
3. **Store vintages from day one.** Use append-on-change, as `sql/043` already does. Revisions
   are real: yfinance revised a distribution and moved a settled receivable **[REPO]**, and
   macro series are revised by design.
4. **Every research series carries a provenance record:** source, licence terms, retrieval time,
   the vintage used, and its transformation from raw.
5. **Separate the observation from the construction.** A factor return is computed from stored
   observations by versioned code. It is never fetched precomputed and then edited.

### D.2 Critical quality criteria for an economically valid factor return

| Criterion | What it means here | Practical test |
|---|---|---|
| Total return, not price | distributions, coupons and roll yield included | reproduce a published TR index or ETF NAV within tolerance |
| Stated numeraire | AUD; hedged or unhedged stated explicitly | unhedged = local return × FX; hedged ≈ local return + (AUD cash − foreign cash) |
| Stated financing rate | an excess return needs a cash leg: RBA cash rate or bank bill for AUD | excess-return series reconciles to TR minus cash |
| Point-in-time | a backtest uses only the data available at the time, including macro vintages and publication lags | CPI used only after its release date; trimmed mean likewise |
| Survivorship | the universe includes delisted and closed vehicles | matters for ASX equity factors and for "proxy ETF" choices. Low importance for macro factors |
| Corporate actions | splits, distributions, ex-dates on the local calendar | already solved in the accounting lane (Policy A, ex-date handling) **[REPO]**. Reuse the rules |
| Roll methodology (futures only) | roll schedule, adjustment method, carry measured on the curve | only if futures are adopted (deferred) |
| Reproducibility | the same inputs and code version give a byte-identical series | content hash on the series and its manifest |
| Licence | storage, derived-work and redistribution rights | recorded per source before ingestion. The pack is shown to two trustees and an auditor, so check whether that counts as redistribution |

### D.3 Recommended sources, in acquisition order

This is a suitability judgement, not procurement. Every licence and coverage claim below is
**[EXTERNAL]** and must be checked first.

**Tier 0: already held (no acquisition, reuse with labels)**

- yfinance ETF closes and distributions for held tickers. Fine as a *proxy history* for research
  in the short term, labelled "unofficial". Not a long-term research source.
- ABS CPI: monthly from April 2024 (29 months), quarterly from 2010 **[DB, REPO]**.

**Tier 1: free, official or academic; enough for areas 1–3 of the roadmap**

| Source | Series | Serves | Notes |
|---|---|---|---|
| **RBA statistical tables** | cash rate and bank bills (F1); government bond yields (F2); exchange rates and the trade-weighted index (F11); Australian corporate bond spreads (F3); trimmed-mean and weighted-median CPI (G1) | AUD financing leg; AU duration; AU credit; AUD; the inflation-series choice (A2) | The most important single source for this fund. Mostly CSV/XLSX downloads |
| **ABS** | CPI (headline, trimmed mean), GDP, labour force | inflation, growth state | Lane exists for CPI; extend it |
| **FRED / ALFRED** | US Treasury curve, breakevens, real yields (TIPS), the Fed funds rate; ALFRED for vintages | global rates, inflation-mimicking legs, vintage discipline | Some third-party series on FRED carry restrictive licences, for example ICE credit indices. Check each series |
| **Kenneth French Data Library** | global and regional (developed, Asia Pacific ex Japan) market, size, value, profitability, investment, momentum; monthly and daily | **validation only** for equity style factors | USD-based; convert. No Australia-only set |
| **AQR datasets** | time-series momentum, value and momentum everywhere, betting against beta, quality minus junk, century of factor premia | validating trend and defensive premia; describing DBMF's strategy class | Terms of use apply; check whether derived storage is allowed |
| **BIS** | effective exchange rates; credit-to-GDP; policy rates | AUD real effective exchange rate (value); global state variables | Low-frequency, for the strategic layer |
| **ECB SDW** | euro-area yields and inflation | only if euro exposure becomes material | defer |
| **CFTC Commitments of Traders** | futures positioning | not a priority: weak decision value at this scale | defer indefinitely |

**Tier 2: low-cost commercial, adopted when a named gap appears**

| Candidate | Gap it would close | Trigger to evaluate |
|---|---|---|
| **Norgate Data** | survivorship-free ASX and US equity history with delisted securities; continuous futures | if ASX equity factor construction (D.4 tier 3) or futures research is approved |
| **EODHD** (or a similar end-of-day vendor) | a licensed replacement for yfinance with broad ETF and index coverage | when yfinance licence or reliability becomes the binding risk, or the proxy universe grows beyond about 20 series |
| **Nasdaq Data Link** | assorted curated datasets | case by case; no standing need |

**Tier 3: deferred; justify individually**

- **CME DataMine and Barchart futures data:** only if the trustees decide to analyse trend and
  carry from their own construction rather than from AQR, DBMF and similar published series.
  That decision is not on the 12-month horizon.
- **Institutional vendors** (Bloomberg, Refinitiv, FactSet, MSCI): disproportionate cost. The
  reason to reconsider would be index licensing, for example S&P/ASX total-return levels for
  proxies. Even then, ETF NAVs as proxies are usually adequate.

### D.4 Australian-specific data limitations to plan around [ASSESSMENT / EXTERNAL]

- **S&P/ASX and MSCI index levels are licensed.** Free proxies are ETFs: IOZ and STW back to
  about 2001; IVV.AX. That introduces fees and tracking error, which should be measured, not
  ignored.
- **The Australian inflation-linked bond market is thin.** A domestic breakeven series is
  noisy. Use US breakevens as a global inflation-mimicking leg, and AU CPI (headline and
  trimmed mean) as the state variable.
- **Long AU bond total-return history** must be built from RBA yields with a duration
  approximation, or taken from an ETF proxy (for example VGB or IAF, about 2012 onward). Either
  is acceptable if labelled, and the two can be cross-checked against each other.
- **The proxy history is short.** BGBL and GLIN start in 2023 **[DB]**. Area 2's historical
  replays through 2008 or 2020 need substitute proxies, as the investigation already noted
  ("excludes BGBL/GLIN or uses proxies") **[REPO]**.

### D.5 Procurement dependencies

- A licence-review checklist per source, recorded before any source enters the lane.
- A decision on whether research data is ever promoted to Neon. **Recommendation: no.** Keep it
  local plus backup, which removes A17-B from the research critical path.
- A storage-rights question for AQR and French data, held as derived series inside a private
  pack.

---

## E. Quantitative research methodology

### E.1 Initial factor library: parsimonious and AUD-based

**Tier 1: the core macro factor set.** About seven tradable factor returns, monthly (weekly
where the data allows), in AUD:

| # | Factor | Construction (first version) | Primary purpose |
|---|---|---|---|
| F1 | Global equity | developed-market TR in AUD, unhedged and hedged versions, minus AUD cash | the dominant risk in almost every portfolio |
| F2 | AU equity relative to global | AU equity TR minus global equity (hedged) | home bias, franking, resources tilt |
| F3 | Duration (AU) | AU 7–10y government bond TR minus AUD cash (RBA F2 yields, or an ETF proxy cross-checked) | interest-rate sensitivity; the stock–bond hedge question (Q4 in the investigation) |
| F4 | Credit | AU and US IG and HY excess return over duration-matched government bonds (or spread change × spread duration) | the MXT, QPON and GROW credit sleeve |
| F5 | Inflation-mimicking | US 10y breakeven change, or nominal minus inflation-linked bond return; plus a commodities and gold leg | real-return objective; inflation sensitivity |
| F6 | AUD | AUD trade-weighted index, or AUD/USD return (sign: AUD falling = positive for an unhedged holder) | currency policy; defensive role of foreign currency |
| F7 | Trend (TSMOM) | an AQR TSMOM series, or an SG Trend-style proxy; cross-checked with DBMF's realised returns where they overlap | describing managed futures' conditional behaviour |

**Tier 2: added only when a specific decision requires it**

- Commodities split: energy, metals, agriculture versus gold. Gold behaves differently and is
  held separately.
- Equity styles (value, momentum, quality, low volatility) from French or AQR. These are
  **validation and diagnosis**, for example "is BGBL's residual a style tilt?", not targets.
  The trustees implement through broad market ETFs with no deliberate style tilts
  **[REPO, holdings]**.
- Currency carry and value: only if an active currency decision beyond the hedge ratio is ever
  on the table.

**Tier 3: deferred or omitted, with reasons**

- **Volatility risk premia and tail convexity.** Harvesting short volatility contradicts a
  low-drawdown objective. Buying convexity is costly and hard to implement in an SMSF ETF
  universe. Keep it as a *stress-test concept* (tail correlation), not a factor to hold.
- **Own-built cross-sectional ASX equity factors:** require point-in-time fundamentals and
  survivorship-free data (Tier 2 data) for a decision nobody has proposed.
- **Futures-curve carry:** see D.3 Tier 3.

**Redundancy to expect:**
- F5 overlaps F1 and F3: inflation surprises move both.
- F7 is by construction a time-varying combination of the others.
- Equity styles overlap F1 heavily in crisis periods.

This argues for a small set and explicit overlap diagnostics, not for adding factors.

**What is missing from the brief's universe and should be handled outside the factor model:**
- illiquidity and valuation risk (MXT);
- manager, governance and operational risk;
- tax (franking, CGT, foreign withholding: DBMF's 15% is already modelled **[REPO]**).

These go into the implementation assessment and stress scenarios, not into regressions.

### E.2 Modelling progression: earn each step

| Stage | Method | Question it answers | Promote to the next stage only when |
|---|---|---|---|
| **S0** | holdings-based look-through from issuer documents (roadmap area 1) | what does the fund *say* it holds? | done for all holdings, dated, sourced |
| **S1** | **returns-based time-series regression** of each holding and of the policy mix on F1–F7: monthly, about 10 years of proxy history, HAC (Newey-West) standard errors, rolling 36- and 60-month windows | what does the fund *behave* like? With what uncertainty? | estimated and disclosed exposures are reconciled, or each disagreement is explained (E.3) |
| **S2** | factor covariance: sample, EWMA and shrinkage (Ledoit-Wolf), compared; conditional covariance by regime (stock–bond correlation sign, inflation above or below a threshold) | how do the exposures combine? Does diversification survive bad regimes? | S1 exposures are stable enough to multiply through, and the regime split has enough observations per regime |
| **S3** | stresses and scenarios: historical replays (2008, 2013 taper, 2020, 2022) and hypothetical shocks through S1 exposures, cross-checked against replaying proxy returns directly | what falls, by how much, and why? (area 2) | the two stress methods agree within a stated tolerance, or the gap is explained |
| **S4** | PCA on the factor and asset return panel **as a diagnostic only** | are there common moves the economic factors miss? | never used as factors in themselves |
| **S5** | dynamic and conditional exposures (rolling or Kalman betas, regime-dependent betas) for GROW and DBMF | how do the active holdings change their exposure? | S1 rolling windows show material instability that matters to a decision |
| **S6** | building-block capital-market assumptions per factor: yield + growth + valuation change; carry + roll; ranges, not points (area 3) | what might each exposure earn? | trustee approval of the assumptions paper |

**Explanatory versus predictive.** Stages S0–S5 are explanatory: they describe co-movement and
exposure. Stage S6 is assumption-setting. **Nothing above is predictive.** A predictive model,
meaning a signal that forecasts a factor's return over the next period, belongs to TAA (section
5 of the brief) and has to pass the separate standard in E.5.

### E.3 Specific methodological hazards and their treatment

- **Multicollinearity.**
  - F1 and F2 (global and AU equity) and F1 and F4 (equity and HY credit) are highly correlated
    in stress.
  - **Treatment:** report variance inflation factors and use the residualised versions where
    needed, for example credit orthogonalised to equity *for interpretation only*. Report
    exposures with confidence intervals, not point estimates.
- **Orthogonal is not independent.**
  - PCA components are orthogonal *in sample*. They rotate between samples and have no economic
    label.
  - **Treatment:** use PCA only to test whether F1–F7 leave a large common component
    unexplained.
- **Residual is not diversification.** A holding's unexplained residual counts as genuine
  diversification only if all four of these hold:
  1. it is persistent across rolling windows;
  2. it has a mandate-consistent economic explanation, such as active duration timing for GROW;
  3. it is not concentrated in a few months;
  4. it does not turn correlated with equities in stress windows.

  Otherwise it is noise, or an omitted factor. The MXT case shows that a residual can be
  *hidden risk* (smoothed or stale pricing understates beta), not diversification. For any
  vehicle with possible stale pricing, use Dimson lagged-beta regressions.
- **Time-varying exposures (DBMF, GROW).**
  - Static regressions on trend followers give near-zero average betas that hide large
    conditional exposures.
  - **Treatment:** evaluate them conditionally. What did they do in the worst decile of equity
    months? In 2022's rate shock? Report "crisis beta" and "conditional correlation" alongside
    static betas.
  - GROW's disclosed monthly positioning (from its reports) is a second, holdings-based check on
    its returns-based betas.
- **Estimation uncertainty.**
  - With 120 monthly observations, a beta's standard error is commonly 0.05–0.15.
  - **Treatment:** report it. Treat any exposure change smaller than about 2 standard errors as
    no change.
- **Overfitting and data-snooping.**
  - Count and record every specification tried (the hypothesis register, E.5).
  - Prefer pre-specified factor definitions taken from the literature over tuned ones.
- **Proxy error.** Every proxy has a measured tracking error to the vehicle it stands for, over
  their common period. That error is carried into stress results as an uncertainty band.

### E.4 Why the fund's own record cannot validate TAA [ASSESSMENT, standard statistics]

- To distinguish an information ratio of 0.3 from zero at about 95% confidence takes roughly
  (2 / 0.3)² ≈ 44 years of independent annual observations. Monthly sampling helps only if the
  signal's edge is monthly and independent, which slow valuation signals are not.
- Two trustees, a handful of tactical decisions a year, and a three-year objective horizon
  produce far too few independent outcomes for the decision register to say whether TAA added
  value.
- So the case for any TAA rule must rest on:
  - external evidence (decades, many markets);
  - an economic rationale;
  - paper-traded out-of-sample behaviour.

  It cannot rest on the fund's realised results.

**Implication:** the decision register's main value is *discipline and learning*: recording the
rationale, avoiding hindsight, enforcing review triggers. It does not provide statistical
validation. That should be stated in the register's design so nobody later reads three good
quarters as proof.

### E.5 Validation standards for promotion into live decisions

Proposed **minimum promotion standard**, applied to any finding before it changes a strategic
target or becomes a tactical rule:

1. **Hypothesis registered first.** Record the economic rationale, the expected sign and size,
   the data and the test. Do this before the result is seen.
2. **Point-in-time data, with stated lags.** Macro data uses vintages or the publication date
   plus a lag.
3. **Out-of-sample evidence.** Use walk-forward or expanding-window estimation, with no
   parameter fitted on the evaluation period.
4. **Robustness.**
   - The sign holds across sub-periods (pre- and post-2008, and the 2022 regime), across
     neighbouring parameter choices, and across at least two data sources where available.
   - For example, a trend result should hold on both AQR TSMOM and DBMF.
5. **Costs and tax included:** brokerage and spread, CGT on realisation (15%, or 10% after 12
   months), and the loss of franking where relevant.
6. **Multiple-testing awareness.** The register counts how many variants were tried. Haircut the
   headline statistic accordingly, for example with a deflated Sharpe ratio.
7. **A decision-relevant effect size.** The effect must change a decision by more than the
   rebalancing band, after costs. Otherwise it is interesting, not actionable.
8. **Reproducibility.** Re-running the stored manifest gives the same numbers.
9. **Owner and trustee sign-off**, recorded in the decision register, with the review date and
   the falsification trigger.

**Anti-backtester guardrails** **[ASSESSMENT]**:
- no parameter search tooling;
- every backtest output carries the `[BACKTEST]` tag already used in the pack investigation
  **[REPO]**;
- historical replays use *today's or a proposed policy's weights*, never weights fitted to the
  replay window;
- an "interesting result" does not reach the pack until it passes 1–9.

---

## F. Roadmap reconciliation

### F.1 Existing work: keep, accelerate, defer

| Existing item | Recommendation | Rationale |
|---|---|---|
| Phase 1 reporting integrity (tax provision, zero-volume carried forward, hurdle labels, minute draft status, invariants) | **Keep, first** | Research built on a pack the trustees can't fully trust is wasted. Cheap, mostly additive |
| Formal review of the objective (December) | **Keep; make it the gate for all SAA work** | G1. Ask the review to also settle: the inflation series (headline or trimmed mean), before or after tax, the drawdown definition and the horizon, because the research datasets depend on each |
| Area 1 exposures (December) | **Keep; extend with a disclosed-versus-estimated column in March** | S0 now, S1 cross-check as soon as WP-2 lands |
| Area 2 downside (March) | **Keep; bring its data work forward to November–January** | Needs long proxy history, RBA yields and spreads, and the AUD index. It is the first place the research lane pays for itself |
| Area 3 feasibility (June) | **Keep** | Building-block assumptions need yields, spreads and earnings yields (Tier 1 data) |
| Area 4 decision register | **Keep; accelerate; widen to a hypothesis register** | One structure, two record types. The cash-deployment rule is its first tactical entry |
| HIO-001 activation | **Keep; low urgency** | Needed for layer 6 (implementation). The five classification calls can be confirmed at the December meeting. Production activation waits for A17-B |
| A17-A activation, A17-B promotion gate | **Keep, on their own track** | Operational safety; **decoupled** from research if research stays local-only |
| Trade reconciliation (IVV/QPON), other accounting gaps | **Keep, on the BAU track** | Accounting truth; not on the research path |
| Bitemporal querying (F-03) | **Defer** | The research lane needs vintages of *market* data (the `sql/043` pattern), not bitemporal accounting identity |
| Azure migration, Prefect orchestration | **Defer** | Infrastructure with no research or decision outcome in the next 12 months. Research jobs can run manually and monthly |
| CMC/Macquarie APIs, frontend date filter, peer-table polish | **Defer** | Not decision-relevant |
| "Out of scope: optimisation, backtester, macro forecasting, speculative tables" | **Keep, with one clarification** | Area 2's historical replay *is* a minimal backtest. Name it as a bounded, labelled replay so the exclusion doesn't block it |

### F.2 New foundational capabilities missing from the roadmap

1. **A research data lane (layer 1–2), isolated from the accounting core.** Smallest version:
   - RBA F1/F2/F3/F11/G1, extended ABS CPI, and a dozen FRED series;
   - French and AQR series for validation;
   - long-history ETF proxies.

   Store each with its vintage and licence record.
2. **A returns-based exposure estimator (S1)**, with the disclosed-versus-estimated
   reconciliation.
3. **An exposure-level policy statement** (layer 4): about seven exposure ranges, from which the
   asset-class table follows. It is introduced as a proposal only after the objective is settled.
4. **A hypothesis register**, merged with the decision register.
5. **A minimal risk-metrics module**: volatility, drawdown and correlation on *proxy* history
   (labelled), with the fund's own figures shown only once the history supports them. This
   closes G2.

### F.3 Architectural recommendation: start with files, not tables

To avoid "designing a large generic data platform", the research lane should start as:

- a `research/` package with fetchers that write raw receipts to the existing storage pattern
  (local plus a Tigris backup, as with source files);
- a **manifest** (source, licence, vintage, content hash) per dataset;
- versioned derived datasets (Parquet or CSV) produced by deterministic code;
- results consumed by `reporting/` through a read-only loader, with the same reconcile-or-raise
  discipline as `api/attribution.py`.

Promote to Postgres tables (`mkt_*` and `research` schemas) only when:
- a dataset is used in two consecutive quarterly packs; or
- the API or frontend needs it.

This keeps the HIO preservation principle trivially satisfied: no existing schema, stage or
contract is touched, and `local_refresh` never sees the research lane.

### F.4 Dependency chain

```
Objective review (Dec) ─────────────┬──────────────────────────────▶ Policy exposure ranges (Sep 2027)
                                    │                                        ▲
Phase 1 integrity (Nov–Dec) ──▶ Pack trustworthy                             │
                                                                             │
WP-1 data lane v0 (Nov–Jan) ──▶ WP-2 exposures S1 (Jan–Mar) ──▶ Area 2 downside (Mar) ──▶ Area 3 feasibility (Jun)
        │                                    ▲                                 ▲
        └──▶ proxy history, RBA, FRED ───────┘                                 │
Area 1 look-through S0 (Dec) ────────────────┘            WP-5 building-block CMA (Apr–Jun)
Decision + hypothesis register (Dec, ongoing) ──▶ cash rule (first TAA entry) ──▶ quarterly review
HIO-001 confirm (Dec) ──▶ (A17-B) ──▶ implementation assessments (2027 H2)
```

---

## G. Near-term priorities: five bounded work packages

Each work package is research-only and additive. None changes an existing table, stage, API or
pack figure unless stated otherwise.

### WP-1: research data lane v0 (November 2026 to January 2027)

**Question it serves:** "how would today's mix, and the alternatives, have behaved through the
episodes we fear?" (area 2), and "what does each holding actually behave like?" (WP-2).

**Scope:**
- RBA F1, F2, F3, F11 and G1;
- ABS CPI (monthly and quarterly, existing lane reused read-only);
- about 12 FRED series;
- French developed and Asia Pacific factors, AQR TSMOM (validation);
- long-history ETF proxies for each policy exposure:
  - existing yfinance data, labelled unofficial;
  - extended to non-held proxies such as IOZ/STW, VGB/IAF, a hedged global equity ETF and a
    US aggregate bond series.

**Build:** manifests, vintages, a licence record per source, deterministic construction of
F1–F7 in AUD at monthly frequency.

**Acceptance criteria:**
- Each factor reconciles to an independent figure within a stated tolerance. For example:
  - the constructed AU bond TR from RBA yields matches an AU bond ETF's TR (net of fees), within
    tolerance, over their common period;
  - the constructed global equity series in AUD matches IVV.AX or BGBL's TR plus fees;
  - TSMOM matches DBMF's realised direction in the 2022 drawdown.
- A re-run from manifests reproduces byte-identical series.
- Zero changes to existing relations, shown by fingerprint comparison using the HIO-001 evidence
  method **[REPO]**.

**Demonstrable value:** a one-page "proxy history card" per exposure: source, span, gaps, and
error versus the actual vehicle.

### WP-2: disclosed versus estimated exposure (January to March 2027)

**Question:** "do our holdings behave like what their documents say?"

**Scope:** S1 regressions for each holding and for the current-weight mix: static, rolling 36 and
60 months, HAC errors, crisis betas. Use Dimson lags for MXT and any other stale-priced
vehicle.

**Acceptance criteria:**
- For each of these, the table shows the estimated exposure with its confidence interval, the
  disclosed figure, and an explicit verdict (agrees / disagrees / explained):
  - equity, duration, credit and FX exposure for every holding;
  - the fund-level roll-up.
- Named expected checks:
  - GROW duration (disclosed about 3.0 years inside GROW) versus estimated;
  - the fund's equity beta versus about 37% look-through equity;
  - the unhedged foreign-currency estimate (about 30%) versus the AUD beta.
- Any disagreement larger than 2 standard errors gets a written explanation, or becomes an open
  item.

**Demonstrable value:** the first evidence-based answer to "which exposures are deliberate?"
(the area 1 "done when"), and a cross-check that can catch look-through errors.

### WP-3: downside page inputs (February to March 2027; feeds area 2)

**Question:** "what could produce a 10–15% fall, and which exposures would cause it?"

**Scope:** replays of today's weights through 2008, 2013, 2020 and 2022 using proxies, with
proxy-error bands. Exposure-based shocks run through WP-2 betas. The two methods are compared.
Liquidity coverage is included (it needs Phase 1's tax line).

**Acceptance criteria:**
- Replay and exposure-shock results agree within a stated tolerance per episode, or the gap is
  explained. For example, "2022 replay worse than the shock implied, because the stock–bond
  correlation flipped".
- Every figure carries the `[BACKTEST]` or `[ESTIMATE]` tag.
- The trustees receive a drawdown-tolerance decision paper.

**Demonstrable value:** the trustees set a drawdown tolerance against evidence (the area 2
"done when").

### WP-4: decision and hypothesis register, plus the cash-deployment rule (December 2026, then ongoing)

**Question:** "are decisions recorded so that they can be reviewed honestly?"

**Scope:**
- One register, two record types:
  - **decision:** date, evidence, thesis, alternatives, risks, triggers, size, review date,
    outcome;
  - **hypothesis:** rationale, pre-registered test, variants tried, result, status.
- **Files first** (Markdown or YAML in a controlled directory), rendered into the pack.

**First entries:**
- the cash-deployment rule, written explicitly as a *tactical* position with a size, trigger,
  expiry and reversal condition;
- the MXT monitoring triggers;
- hypotheses H1 ("the unhedged foreign currency is a net defensive exposure for this fund") and
  H2 ("DBMF provides positive conditional returns in equity drawdowns"), both tested in WP-2
  and WP-3.

**Acceptance criteria:**
- Every December decision has an entry.
- The March pack reviews them.
- A test fails the pack build if a pack claim cites a non-existent or unapproved register entry.
  This mirrors the provenance-register idea in the investigation **[REPO]**.

### WP-5: building-block capital-market assumptions v0 (April to June 2027; feeds area 3)

**Question:** "can the agreed objective plausibly be met at the agreed drawdown?"

**Scope:**
- Expected excess returns per exposure F1–F6, using:
  - equity: earnings or dividend yield + real growth (+ franking for AU);
  - bonds: yield − expected roll and default;
  - credit: spread − expected loss;
  - cash: RBA.
- Conservative, central and optimistic ranges.
- Fees and tax stated explicitly.
- Combined with WP-2/S2 covariance for a *feasibility envelope*: the distribution of rolling
  3-year real returns for the current mix and for two or three alternative policy mixes. **No
  optimiser.**

**Acceptance criteria:**
- Each input is sourced and dated.
- The result is reproducible from its manifest.
- A sensitivity table shows which single assumption flips feasibility.
- Results are compared with at least one external published set of assumptions, labelled as
  manager material.

**Demonstrable value:** the area 3 "done when", plus the first quantitative basis for a policy
exposure range.

**Deliberately not in the first five:**
- futures data;
- own-built style factors;
- optimisation;
- regime-switching models;
- any predictive TAA signal;
- any database schema for research.

---

## H. Strategic risks and open decisions

### H.1 Decisions to make together before changing the programme

| # | Decision | Options | My recommendation |
|---|---|---|---|
| D1 | The objective's exact definition (series, tax basis, horizon, drawdown measure) | trustee review | Settle at the December meeting. Everything downstream depends on it |
| D2 | Does research data ever go to production (Neon)? | local only / promote | **Local only** until a pack or API needs it. This decouples research from A17-B |
| D3 | Files-first or tables-first for research datasets | files + manifest / Postgres schemas | **Files first** (F.3) |
| D4 | Is TAA in scope for 2027? | none / rules-based bands + cash rule / signal-based | **Bands plus a written cash rule only.** Signal-based TAA is reconsidered in 2028 after paper trading |
| D5 | What size of factor library? | about 7 macro factors / full brief universe | **About 7** (E.1), extended per decision |
| D6 | Data budget and licence appetite | free only / low-cost commercial / institutional | **Free for WP-1 to WP-5.** Revisit Norgate or EODHD when a named gap appears |
| D7 | The policy portfolio's form | asset-class ranges (today) / exposure ranges with derived asset-class ranges | exposure ranges, **proposed only after D1 and WP-3** |
| D8 | Currency policy | leave it implicit / set a foreign-currency exposure range | set a range; WP-2 and WP-3 inform it |
| D9 | Treatment of private, illiquid and stale-priced holdings in risk figures | market price / NAV / both with a flag | both, with Dimson betas and a stale-price flag (Phase 1 item 1.3 already plans the flag) |
| D10 | Who reviews research? | owner only / owner + independent reviewer (Codex, as with HIO-001) | an independent review for promotion decisions (E.5), **not** for exploratory work. Otherwise review cost will dominate |

### H.2 Methodological uncertainties

- **Stock–bond correlation.** Its sign has changed historically (positive pre-2000 and since
  2022; negative 2000–2021) **[EXTERNAL]**. Any duration recommendation is regime-dependent and
  must be shown under both signs.
- **Proxy validity for active vehicles.** GROW, DBMF and MXT are poorly represented by any static
  proxy. Their own histories (GROW from 2016, DBMF from 2019, MXT from 2017 **[DB]**) are short
  relative to the episodes of interest.
- **Inflation hedging.** The evidence is weaker and more horizon-dependent than commonly assumed:
  gold and commodities hedge poorly at short horizons **[EXTERNAL, Erb & Harvey; Neville et al.]**.
  The real-return objective must not rest on assumed inflation hedges.
- **Franking and tax.** These must enter the capital-market assumptions explicitly, or the AU
  versus global equity comparison will be systematically wrong for this fund.

### H.3 Data limitations

- yfinance is unofficial and revises history; there is no licence.
- ASX index levels are licensed.
- The AU breakeven market is thin.
- Proxies for BGBL and GLIN are needed before 2023.
- Macro vintages exist (ALFRED) for US data but are patchy for Australian data. ABS revisions
  need their own vintage capture going forward.

### H.4 Architectural risks

- **Coupling.** Research code imports accounting-core modules and then constrains their
  evolution. **Mitigation:** the research package depends only on read-only views and on its own
  data.
- **Drift into a platform.** Generic "data platform" features (schedulers, catalogue UI,
  multi-vendor abstraction) get built before a second consumer exists. **Mitigation:** the F.3
  promotion rule.
- **Two classification systems.** The trustee classification (`asset_classes.py`) and the HIO
  taxonomy (HIO-001) diverge without an explicit mapping. **Mitigation:** derive the trustee
  table from exposures (D7) once approved, with a reconciliation check between them.

---

## I. Critical challenge: how this could fail even if the engineering succeeds

1. **The research outruns the fund's decision capacity.**
   - At about $680k, with ETF implementation, two trustees and CGT on realisation, the number of
     cost-effective, distinct decisions per year is small: perhaps a handful.
   - A sophisticated factor framework can produce insight faster than the fund can act on it,
     and many of its implied actions are smaller than their transaction and tax costs.
   - The risk is a beautiful research capability that changes almost nothing, or that
     encourages more trading than is good for after-tax returns.
   - **Test:** for each work package, name the decision it could change. If none, don't build
     it.

2. **Explanation is mistaken for prediction.**
   - A model that explains 90% of past variance says nothing about next quarter's returns.
   - The pull will be strong: once exposures are measured, it will feel natural to "tilt toward
     what is cheap" or "away from what is risky now".
   - The fund's own record cannot discriminate skill from luck within the trustees' horizon
     (E.4).
   - If TAA is adopted on the strength of explanatory models plus a few good quarters, the
     framework will have produced confident, unvalidated market timing.

3. **The objective is wrong, or infeasible, and the research rationalises it.**
   - CPI + 5% net, over three years, with low drawdowns, is a demanding combination. At about 4%
     CPI it means about 9% a year **[REPO]**.
   - If the feasibility work (area 3) shows it can't be met at an acceptable drawdown, the
     honest outcome is to revise the objective, not to add risk, leverage-like exposures or
     tactical activity to close the gap.
   - A research capability is especially good at producing reasons to take more risk.

4. **The material risks aren't factor risks.**
   - The fund's worst event so far, MXT, was a valuation dispute, a suspension and a frozen
     feeder fund **[REPO]**.
   - Factor models are blind to illiquidity, stale pricing, manager governance and
     concentration by manager (two credit holdings "one manager apart",
     `portfolio-analytics` skill) **[REPO]**.
   - If the factor framework becomes the main lens on risk, these will be under-weighted because
     they don't appear in a regression.
   - **Mitigation:** keep the implementation assessment and qualitative risk register as
     co-equal inputs to the factor view, not subordinate to it.

5. **Engineering gravity consumes the research.**
   - This repository's track record is excellent rigour, applied heavily to infrastructure.
   - HIO-001 (an instrument master) went through five review rounds and is still not activated.
     A17-A backup tooling is merged and not activated **[REPO]**.
   - Applying the same production-grade standard to an *exploratory* research lane would
     consume most of 2027 before a single trustee decision changed.
   - **Mitigation:** two standards, explicitly.
     - **Exploratory:** files, notebooks or scripts, reproducible manifests; no independent
       review.
     - **Promoted:** E.5 plus the existing preservation evidence method, applied only to
       findings that reach the pack or a decision.

---

## Appendix: what this review did and did not do

- **Read:**
  - `CLAUDE.md`, `BACKLOG.md`, `IMPLEMENTATION_PROGRESS.md` (status, assessment, gaps, next
    steps);
  - `docs/investment-process-roadmap.md`, `docs/quarterly-pack-v2-investigation.md`,
    `docs/architecture.md`, `docs/data-sufficiency-matrix.md`;
  - ADR 0003 and the HIO-001 review record;
  - the benchmark plans (outline), the `portfolio-analytics` skill, `reporting/asset_classes.py`,
    the market-data workers, `sql/043`;
  - project memory.
- **Queried locally (read-only):**
  - price history span per held ticker;
  - FX history span (USD/AUD from 2006-05-16);
  - monthly CPI span (2024-04 to 2026-08);
  - reference-index registry;
  - the absence of `silver.dim_instrument` in the authoritative database.
- **Not done:**
  - no external source, licence or vendor claim was re-verified (all are **[EXTERNAL]**);
  - no regression, backtest or stress was computed;
  - no code, schema, document or roadmap was changed.
- **Timing note:** the roadmap is marked "for trustee discussion on 18 October 2026", which is
  today. Nothing here argues for changing what goes to that meeting. The recommended additions
  (WP-1, WP-2, the hypothesis register, an objective review that also settles the series, tax
  basis and drawdown definitions) fit into the December quarter without displacing anything.
