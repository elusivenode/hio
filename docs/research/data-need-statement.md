---
id: HIO-RESEARCH-DATA-NEED
title: "Data-need statement for the Year-1 factor families (base-camp criterion 9)"
status: proposed
owner: HIO architecture lead (owner); drafted by Fable for claude/implementation-agent
created_at: 2026-10-29
instruction: OD-0132 (base-camp criterion 9)
base_revision: 775f7e0
---

# Data-need statement (proposed)

> **Advice only (OD-0090).** It authorises no download, contact or purchase. Labels: **[V file:line]** is verified
> against the repository at `775f7e0`. **[J]** is judgement. **[GK]** is general knowledge and is unverified; check it
> before relying on it. Every source right is `unknown` (deny) unless the register shows `owner_verified`.
> `knowledge/findings.md` has no entry on history lengths or data needs. It does record the H.10 and FRED points below
> through the T-0002 matrix.

## 1. Derivation

**Uses.** The Year-1 and Year-1.5 uses are:
- the AUD factor set (cash, FX spot, carry and cross, AU and US CMT, equity in AUD unhedged and hedged) [V docs/roadmap.md:57];
- futures excess returns for rates, equity index and gold [V roadmap.md:58];
- H-0001 and H-0002 [V roadmap.md:59];
- risk model v1 (sample, EWMA and shrinkage covariance with bootstrap uncertainty; conditional and tail dependence)
  [V roadmap.md:60]. The charter places conditional and tail dependence in Year 2 [V docs/charter.md:121]. This
  statement plans for the roadmap's earlier date;
- CMAs v0 [V roadmap.md:62];
- trend v0 by replication [V roadmap.md:63].

**Assumptions.**
- **A1.** About 10–15 factors, so N ≈ 12 [J].
- **A2.** Risk statistics are explanatory, not predictive. Both hypotheses are `model_kind: risk`
  [V registers/hypotheses.yaml:7,24].
- **A3.** Daily AU and US closes are not synchronous. The standard says statistics should prefer weekly or monthly
  sampling [V docs/standards/return-accounting-and-factor-construction.md:255-259].

**Statistical reasoning** (all [J] unless labelled):

| Use | What binds | Implication |
|---|---|---|
| Sample covariance | Estimation error grows with N/T. At N = 12, monthly T = 120 (10 years) gives N/T = 0.1, which is noisy for the smallest eigenvalues | **≥ 20 years monthly** for a stable sample matrix. Daily data gives T ≈ 1,250 in 5 years but carries the A3 timing noise, so use daily for volatility and weekly or monthly for cross-market correlation |
| Shrinkage | Ledoit–Wolf-type shrinkage exists for the regime T ≈ N to 10N [GK]. It lowers the requirement but does not remove it | 10 years monthly is a workable floor with shrinkage; 20+ years is preferred |
| EWMA | Effective sample ≈ (1+λ)/(1−λ): about 32 observations at λ = 0.94 and about 66 at λ = 0.97 [GK] | Daily data; a short estimation window, but burn-in plus backtesting across several stress episodes needs **≥ 15–20 years daily** |
| Bootstrap uncertainty | A block bootstrap needs many blocks of 6–12 months for monthly data [J] | 20–40 blocks means **20–40 years monthly** |
| Tail dependence; H-0002 worst decile | The worst equity decile of T months has T/10 points. A correlation's standard error is about 1/√n [GK]: 360 months give n = 36 and SE ≈ 0.17 | Monthly data from the **AUD float (December 1983)** gives n ≈ 50 and SE ≈ 0.14, which is marginal for "distinguishable from zero" [V hypotheses.yaml:32]. Add weekly data for power; the float is a hard ceiling [GK] |
| H-0001 regimes | The binding count is independent regime episodes, not months [V hypotheses.yaml:12 "multi-decade sample"]. The high-inflation episode is about 1966–1990, the low one about 1998–2021, plus 2022– [GK] | **Monthly from ≤ 1970** for US yields, equity TR and CPI; AU as far back as available. A post-1993 sample contains almost no high-inflation regime |
| CMAs v0 | Building blocks and ranges [V roadmap.md:62] | Current yields and spreads, plus long monthly history for the ranges. Earnings and dividend yields are likely paid [V roadmap.md:62 "some paid"] |
| Trend v0 | Replicate a published study on its own sample [V RA standard:405-406]. TSMOM-type studies use dozens of futures over about 25+ years [GK] | **Individual contract settlements**, broad and long. This is the largest data need |

**Captured versus reconstructed.** Risk, regime and replication uses can run on labelled `reconstructed(T)` history
[V docs/decisions/HIO-ADR-0012-staged-s1b.md:160; specs/factors/fx.usd_cash_vs_aud.excess.yaml:34]. Point-in-time
captured or publisher-vintage data is needed only for walk-forward signal claims, which are Year 4
[V charter.md:123], and for `as_known_by_market` releases.

**Two conflicts to flag:**
- H-0002 declares `min_knowable_basis: captured_on_schedule` [V hypotheses.yaml:30]. Captured history starts in 2026,
  so the hypothesis cannot be tested for decades unless the owner relaxes that basis to `reconstructed(T)` before
  registration.
- H-0001 requires `publisher_vintage` inflation states [V hypotheses.yaml:13]. ALFRED is recommended denied for
  retention [V docs/research/T-0002-free-history-sources-matrix.md:49,54-58]. US CPI-U NSA is not revised [GK], so
  final values might stand in for vintages, but that needs an owner decision.

## 2. Per-family table

Labels for the History column: **Min** is the minimum and **Pref** the preferred history.

| Family | History | Freq. | Fields | Construction inputs (RA standard) | PIT? | Candidate sources (rights state) |
|---|---|---|---|---|---|---|
| **Cash AUD** | Min 1990. Pref Dec 1983, with a declared monthly bill splice before that | daily | rate, effective date, publication instant, expert-judgement flag; RITS/NSW calendar | §3.2 window, applicable rate, ACT/365F [V RA:122-139] | captured running (S1b-1); history reconstructed | RBA F1 `rba.cash_rate`: **owner_verified, OD-0116** [V sources.yaml:59-60]. Its earliest date is unrecorded [V specs/factors/cash.aud.overnight.yaml:37]. Pre-2011 coverage is unknown [GK] |
| **Cash USD** | Min 2018 (SOFR). Pref 1983+, with a separate declared pre-SOFR segment [V RA:415] | daily | rate, date, publication instant; NY calendar | §3.2, ACT/360, in arrears | as for AUD | `nyfed.sofr`: **owner_verified** [V sources.yaml:113-114]. Pre-2018: Treasury bills (H2, rec+C, unverified [V T-0002 matrix:50]); EFFR (NY Fed parent unverified [V sources.yaml:47]); **FRB H.15 is not in the register** |
| **FX spot** | Min 1990. Pref Dec 1983 (the float) | daily | quote (USD per AUD), fixing time and venue, valid date | quote inversion [V RA:190-191]; joint calendar [V RA:253-259] | captured from S1b-2; history reconstructed | RBA F11 (parent unverified, blocked OD-0013 [V sources.yaml:18-21]); **no free-history row is drafted for F11**. H.10 (H3, rec+C [V T-0002 matrix:51]; a New York noon timing basis [GK]) |
| **FX carry and hedge** | as cash USD, the binding leg | daily → monthly | both cash legs; forward points if `market_forward` | §4.2 spot + carry + cross; §4.3, h, reset, F source [V RA:198-249] | reconstructed | `cip_implied` from the cash legs (`replicable_with_basis`). Market forward points have no free candidate in the register [J] |
| **Rates AU** | Min 2013-05-20 daily [V T-0002 matrix:52]. Pref monthly 1970s+ | daily; monthly re-strike for history | yields at 2, 3, 5 and 10 years; curve type; coupon dates and day count | §6 CMT: declare curve type, interpolation, pricing and re-strike; F2 yields are benchmark YTMs, an approximation to declare [V RA:303-326] | reconstructed | RBA F2 (H4, rec+C [V T-0002 matrix:52]; V4 open [V :67]). **Check that F2.1 monthly values are end-of-month, not averages.** An averaged yield cannot price a return [J] |
| **Rates US** | Min 1990 daily. Pref 1962+ | daily | par yields by tenor; date; real curve for CMAs | §6 CMT, as for AU | reconstructed | Treasury par curve (H2, rec+C, unverified [V T-0002 matrix:50]; daily from 1990 [GK]). H.15 CMT daily from 1962 [GK]: not registered, **public domain like H.10** [J]. **H.15 monthly values are averages** [GK]: use daily |
| **Equity AU and US in AUD (unhedged, hedged)** | Min: ETF life (US-listed S&P 500 ETF from 1993; ASX 200 ETF from 2001) [GK]. Pref multi-decade monthly index TR for H-0001 | daily EOD | **unadjusted** close; dividends (ex-date, pay date, amount, currency, type incl. special and return of capital); splits and consolidations; franking % (AU, separate); withholding basis | §3.1 TR and the declared reinvestment convention; §5 actions as observations, never `Adj Close` [V RA:99-114,271-286]; §4.1 translation, §4.3 hedge | reconstructed; the vendor's revisions captured as vintages [V RA:283-284] | EODHD (unverified; licence class open [V T-0003:23]); S&P DJI (paid licence [V T-0003:22]); issuer files (triangulation only [V T-0003:34-36]); French (`reference_academic`, rights unknown [V T-0003:25]) |
| **Futures and commodities incl. gold** | Min 10 years daily for a PoC of about 4–6 contracts (ZN, ES, GC; AU: SPI 200, 3- and 10-year bond) [J]. Pref 1985+ | daily | **individual-contract** settlements; contract specification (multiplier, tick, currency, expiry, first notice, last trade); open interest and volume for the roll | §8: same-contract P&L, declared roll, collateral `r^c`, no continuous levels [V RA:357-387]; gold spot, XR and TR kept distinct [V RA:392] | reconstructed (settlements are rarely revised [GK]) | CME DataMine, Databento, Norgate, Barchart: all unverified [V sources.yaml:189-220]. **ASX futures data is not in the register.** Gold spot (LBMA) is licensed [GK] |
| **Trend** | the replicated study's own sample, typically 25+ years daily over 20–60 markets [GK] | daily → monthly | as futures, across rates, equity, FX and commodities | §8 `strategy_return`: signals knowable at t−1, vol scaling, costs [V RA:400-406] | reconstructed for replication; captured for any walk-forward claim | as futures. AQR data (`reference_academic`, unverified [V sources.yaml:186]) |

## 3. Gaps and priorities

**Free cleared sources can meet these needs, subject to the owner's verification under criterion 8 [J]:**
- AUD cash over its RBA coverage;
- USD cash from 2018;
- FX spot (F11 or H.10);
- carry and hedge, via `cip_implied`;
- AU and US CMT (F2, Treasury, and H.15 if registered).

Rates (criterion 7) is therefore free.

**Free sources leave gaps:**

| Gap | Effect | Route |
|---|---|---|
| USD cash before 2018 | caps carry, hedged equity and the futures collateral leg at 2018 | register H.15 and the bills; declare a splice segment (free) |
| F11 history has no rights row | FX history before S1b-2 rests on H.10 alone | add an F11 row to the T-0002 matrix (free) |
| Board downloads being retired "in favour of FRED" [V sources.yaml:162] | H.10 and H.15 history could become reachable only through FRED, which is recommended denied | **time-sensitive:** decide criterion 8 for the Board files soon [J] |
| **Investable equity TR** | no free cleared route [V T-0003:30-33]; blocks the AUD equity factors, H-0001 and H-0002 | **paid**: an EOD feed |
| Multi-decade equity TR (pre-1993) | H-0001's high-inflation regime | a paid index licence, or French as a labelled reference (if rights allow), or confine H-0001 to the 1993+ sample with a stated power loss [J] |
| Futures contracts, ASX futures, trend breadth | the S4 PoC, trend v0 | **paid**; probably beyond AUD 400 a month at full breadth [J] |

**Minimum first purchase [J].** One EOD feed for ASX and US ETFs: unadjusted closes and explicit distributions and
splits, daily since each fund's inception. This agrees with [V docs/base-camp.md:70]. It closes the most binding gap,
equity, which is needed by the factor set, by both hypotheses and by every CMA equity block. Futures are a separate,
later purchase sized to the PoC, unless the same vendor's futures cover individual contracts on equal licence terms.

**The binding factor is the licence class, not the price** [V base-camp.md:66]. Before any purchase, written vendor
answers are needed on:
- personal or non-professional status for SMSF trustee use [V T-0003:50];
- derived storage;
- `post_termination_raw` and `post_termination_derived` [V docs/standards/rights-and-licensing.md:26].

If derived returns must be deleted on cancellation, every factor built from the feed is held hostage to the
subscription. That should count as disqualifying, or at least priced as lock-in [J]. Also check `agent_context`:
licensed rows may not enter agent prompts unless the record allows it [V AGENTS.md "Data rights"].

## 4. What would change the statement

- **N grows** (credit, more markets): the history requirements rise roughly in proportion.
- **The owner relaxes or keeps H-0002's `captured_on_schedule` basis:** this decides whether H-0002 is testable before
  about 2036.
- **The pre-SOFR splice is declined:** the carry, hedged and futures-TR history all stop at 2018.
- **F2.1 or H.15 monthly values prove to be averages:** the long AU and US CMT history becomes daily-only (US 1962+;
  AU 2013+), or AU needs another source.
- **Vendor answers on licence class and post-termination rights.**
- **The trend study chosen:** its sample and breadth set the futures purchase.
- **Rights decisions under criterion 8** (H.10, Treasury, F2 and F11; ALFRED permission, V5).
- **Corrections to any [GK] date above.**

---

**Not approved by this document:** no source, right, splice, hypothesis amendment, rights-matrix row, purchase,
vendor contact or download. Base camp itself, the H-0001 and H-0002 data bases and the ordering of S2/S3 against G2
remain owner decisions. Every [GK] and [J] claim is unverified.
