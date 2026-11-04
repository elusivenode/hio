<!-- The brief the owner pasted to Claude Code, 2026-11-04, verbatim as to substance, with no words of the owner's own around it. Recorded by OD-0162. Headings and sections kept; the section numbers are the owner's. -->

# HIO — EODHD Personal Plan: Owner Decision and Evaluation Assignment

**To:** Claude, HIO implementation agent. **From:** HIO Owner. **Subject:** Authorised one-month EODHD evaluation — setup, integration, data validation and suitability assessment

## 1. Owner decision

I have decided to proceed with a **one-month evaluation of the EODHD Personal EOD Historical All-World plan**, currently advertised at approximately US$19.99 per month.

This is a deliberate decision to invest a small amount in obtaining direct evidence about the data, rather than continuing extended vendor research.

**EODHD is the selected candidate for this evaluation. Do not reopen the vendor-selection exercise.**

The goal is to determine whether EODHD can supply sufficiently complete, economically valid and operationally suitable equity and ETF data to underpin HIO's quantitative research programme.

I am authorising Claude to assist with setup, implement the bounded evaluation and produce an evidence-based recommendation.

**Expenditure authority is limited:** I will personally approve and complete the subscription. Claude must not independently purchase, upgrade, renew or commit to additional products.

This decision does not approve the data for downstream consumer use, alter HIO's source-rights standard or constitute an acceptance of EODHD's data quality.

## 2. Operating instructions

Data qualification, not an architecture or governance project. Claude undertakes as much technical work as possible. Use the approved modular monolith, existing rights and provenance mechanisms, and established testing. No new infrastructure unless necessary. A local, segregated evaluation workspace. Do not modify production capture, existing source observations or MACSMSF. Independent of the Treasury experiment and the capture soak. Routine implementation, test correction and Codex verification may proceed within scope. Escalate only genuine changes to standards, rights, financial commitments, approved boundaries or acceptance.

## 3. Phase A — Subscription and environment setup

Identify the official pages; confirm plan name, price, payment frequency and recurring billing; explain the owner's minimum steps; guide generating an API key without placing credentials in chat, Git or repository evidence; configure secret handling; a segregated local workspace; confirm the plan exposes EOD, dividends, splits and FX; identify cancellation or renewal controls. **Stop before any payment or account action requiring my authorisation.** Do not ask me to paste an API key into the conversation or a tracked file. No new Azure service, production scheduler or GitHub Actions secrets unless separately authorised.

## 4. Phase B — Data acquisition and profiling

Subject to the applicable rights gate, a bounded historical sample for SPY.US, VTI.US, IEF.US, VAS.AU, IVV.AU, BGBL.AU, and AUD/USD using the confirmed identifier. Profile first and last observations; currency and exchange; observation count; duplicate or missing dates; raw and adjusted closes; distributions; splits and other corporate actions; corrections and revisions where detectable; source and methodology information. Retain original response bytes and record retrieval time, request parameters, payload hashes and software revision. **Do not assume that a successful API response establishes data quality.** Do not insert these data into the production evidence store or commit licensed observations or derived return values to the public repository. If documented personal-use permissions do not cover an operation, limit the evaluation to permitted data and record the restriction rather than bypassing it.

## 5. Phase C — Economic return validation

The most important part. For each ETF, construct total return from unadjusted prices, cash distributions, split events and explicit corporate-action conventions. Compare with adjusted-close-derived returns, and investigate differences. Attend to: ex-dates and payment dates; split-adjusted against unadjusted dividend amounts; Australian managed-fund distributions including non-income components; currency and implicit FX; missing or revised records; rounding and provider method; incomplete histories and inception dates. Where independently permitted, reconcile against issuer or other authoritative material. A comparison between two EODHD fields is **an internal consistency check**, not independent validation. Record material unexplained discrepancies as unresolved findings. Do not label any series as economically validated simply because code tests pass.

## 6. Phase D — First portfolio research demonstration

If sufficient data passes qualification: SPY, IEF and USD cash, subject to common-period availability and consistent conventions. Three illustrative fixed allocations: 100% equity; 60% equity / 40% cash; 60% equity / 40% Treasury ETF. Specify rebalancing before calculating. Analyse compounded wealth, annualised volatility, maximum drawdown, drawdown duration and recovery, equity-Treasury covariance and correlation, subperiods, and sensitivity to frequency and sample. **Primary question: what additional risk and diversification effect resulted from replacing cash with Treasury exposure while holding equity weight constant?** Not portfolio recommendations or evidence of forecasting skill. IEF is an observed vehicle, not validation of the synthetic factor. AUD translation may be added if FX is trustworthy, and must not delay the USD comparison. No optimisation engine or tactical system.

## 7. Phase E — Technical and operational suitability

Endpoint reliability; limits and actual usage; backfill efficiency; corrections and reproducibility across snapshots; stable identifiers and symbol changes; incremental updates; Python simplicity; compatibility with HIO contracts; maintenance effort; whether an additional independent source is required; suitability for future research. A functioning prototype is sufficient, not a production service.

## 8. Evaluation and reporting requirements

A single consolidated assessment: A. subscription and cost; B. coverage matrix; C. economic validity; D. technical suitability; E. portfolio demonstration; F. recommendation (continue, continue conditionally, or do not continue), distinguishing internal exploratory research from governed releases or SMSF-facing outputs; G. next decision: retain or cancel after the first month, with the smallest follow-up.

## 9. Evidence and review discipline

Current head as baseline; read relevant standards, rights, decisions and Treasury work first; a dedicated evaluation branch with exact-revision provenance. Tests cover event handling, return accounting, incomplete observations, date alignment and refusal of prohibited operations. One focused Codex review of the completed implementation and its claimed evidence, under the approved process; remediate material findings within scope. No repeated general architecture reviews. Don't confuse qualification with approval for publication.

## 10. Boundaries and stop conditions

Authorised to prepare and implement the bounded evaluation, subject to the owner completing the subscription and the existing rights requirements. Not authorised to: purchase or upgrade; exceed the selected plan; share credentials or licensed raw data with an unapproved external service; change the rights or return-accounting standards; publish for an SMSF or other consumer; modify MACSMSF; modify production capture or Azure; begin permanent scheduled ingestion; commit licensed observations or derived return series to the public repository; represent an unvalidated ETF return as a validated factor; silently extend into other vendors.

**Stop on a material rights mismatch, missing credentials, unexpected charge, evidence-integrity failure or required change to approved scope.** Report the precise issue and the smallest owner decision needed. Do not stop for routine implementation questions already covered.

## 11. Immediate instruction

Begin by inspecting the current repository evidence and preparing the minimum EODHD account, credential and local evaluation setup. Return the exact subscription link, the required owner actions and the proposed isolated workspace. Then help me proceed through those actions and execute the authorised technical evaluation.

**The objective is to obtain empirical evidence about EODHD's suitability, not to generate another extended series of planning documents.**
