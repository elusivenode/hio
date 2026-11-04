<!-- The solution architect's answer to the OD-0175 brief, verbatim. Consultation 20261104T182348-ask-fdd7, checkout 6e4a455, with E-0003 V1 read separately on feat/e0003-v1 at 59429c5. Advice only: nothing in it is adopted. Link targets are repointed from its temporary clone to repository paths; no other change. The original is at ~/.hio-runs/20261103T065037Z-3d12/sa/20261104T182348-ask-fdd7/out/answer.md. -->

## 1. Executive verdict

**Judgement: HIO has crossed into useful exploratory quantitative research. Its direction remains sound.** The change is substantive: it can now connect reconstructed investment returns, currency translation, fixed allocations, path-dependent risk measures and uncertainty estimates around a coherent investment question.

That is a meaningful beginning of the charter’s research capability. It does not yet establish a validated factor library, reliable strategic risk estimates, predictive models or implementable allocation recommendations.

My assessment uses two explicit evidence baselines:

- **Verified:** the supplied checkout at `6e4a455831a30701ae2e5e7979d45aeea9198927`.
- **Verified separately:** E-0003 V1’s registration, authority and reported result on local branch `feat/e0003-v1`, at `59429c541390d8df7a9e0900e0ad9d7be33658e2`.

I did not substitute that branch for the checkout or verify current remote state. Throughout, **verified** means repository content or behaviour I checked; **reported** means an outcome recorded by another agent; **owner-decided** means a named OD; **judgement** means my interpretation; **unknown** means the evidence does not establish it.

I accessed no licensed observations, owner-only numerical reports, credentials or private financial information. I inspected methods, implementation, tests and review records, but did not rerun the research or full test suite. One small probe used invented inputs only.

**The central recalibration:** my earlier criticism that HIO had not connected its foundations to a useful portfolio question is now materially outdated. The principal constraint has shifted from missing analytical capability to the evidential strength and permitted use of the data feeding that capability.

## 2. Progress since the previous assessment

**Verified:** the previous assessment, at `bde61d74f8b97e7e7c6d50c15a76939a9e77a26e`, identified missing aligned panels, portfolio analytics and empirical results. It recommended a few fixed allocations connecting equity, duration, currency and cash, with uncertainty. E-0002 and E-0003 directly address that recommendation. [Previous assessment](../../docs/history/2026-11-04-architect-strategic-assessment.md)

**Verified engineering progress:** the tree now contains:

- Explicit ETF market-price total-return construction from unadjusted closes, distributions and splits.
- A release reader checking identity, current rights, knowledge declarations, currency and return class.
- Common-period alignment, monthly rebalancing, wealth reconciliation, covariance, drawdown and recovery calculations.
- Joint block resampling and AUD translation with currency cross terms.
- Source qualification and issuer-return comparison tools.

These capabilities appear in `vehicle_return.py`, `fixed_allocation.py` and the research tools. NumPy is now present; dedicated `models`, `taa` and `implementation` packages remain absent. [Implementation](../../src/hio/portfolio/fixed_allocation.py), [reader](../../tools/research_reader.py)

**Judgement:** the earlier panel-and-analysis capability gap is substantially addressed. The reader also addresses the earlier concern that callers might fail to enforce knowledge mode and cutoff. Neither conclusion validates the underlying observations.

**Reported economic progress:** E-0001 rejected the adequacy of its flat-yield approximation under its registered rules. Its zero-curve variant investigated an alternative without reversing that result or claiming market validation. This is useful negative research, although the traded-return reference remains missing. [E-0001 records](../../docs/evidence/e0001/result-1.md)

**Owner-decided:** OD-0171 accepts T-0022 tooling at `888c493`, explicitly accepting no EODHD data as valid. Four findings were verified closed; one fix’s further verification was waived under OD-0169. The original NOT READY verdicts remain unchanged. E-0002 and E-0003 are not accepted as validated experiments. [OD-0171](../../docs/decisions/owner/OD-0171-accept-t0022-rba-pack.md)

**Verified state distinction:** E-0002 remains registered as running; E-0003 is marked complete, with `reviewed_by: null`. V1 is owner-authorised by OD-0173 on the separate branch; its record says it was not reviewed by Codex. Completion, report receipt and technical acceptance remain separate.

## 3. Research assessment

**Judgement: the experiments ask the right early questions.** Fixing equity exposure while changing the defensive sleeve makes interpretation much easier than optimising weights or fitting a complicated model immediately.

The comparisons need precise economic names:

| Comparison | What it examines |
|---|---|
| USD bills versus AUD cash | Foreign-currency exposure, the cash-return differential and bill-ETF characteristics |
| US Treasuries versus USD bills | Incremental duration exposure, including differences between the vehicles |
| US Treasuries versus AUD cash | Their combined effect |

**Verified:** these distinctions are registered explicitly. BIL is described as a funded bill-ETF sleeve, not overnight cash; IEF does not validate the synthetic CMT construction. [Experiment register](../../registers/experiments.yaml)

**Judgement:** “incremental Treasury-duration effect” is reasonable shorthand when accompanied by the vehicle qualification. It is not a pure duration factor: maturity composition, fees, distributions, valuation and rebalancing remain embedded.

Currency deserves explicit treatment independently of any reported significance. In E-0003’s design, replacing domestic cash with a USD sleeve changes total foreign-currency exposure. Comparing IEF with BIL holds that broad currency allocation constant, but currency still interacts multiplicatively with their different local returns. This is accounting and exposure analysis, not proof that USD will reliably protect an Australian portfolio.

**Verified:** the return construction follows the declared market-price, ex-date reinvestment convention; simple returns compound, split accounting is explicit, and AUD translation includes the cross term. Fund expenses are embedded rather than deducted twice. These choices are appropriate for the stated descriptive study under the approved return standard. They do not reproduce actual payment-date reinvestment, execution or investor taxation. [Return standard](../../docs/standards/return-accounting-and-factor-construction.md)

**Judgement:** volatility, maximum drawdown, recovery and underwater duration are suitable initial measures. Monthly AUD drawdowns describe losses at monthly observation points; they cannot establish intramonth liquidity needs or worst experienced losses. These studies also do not yet measure the charter’s real-return shortfall objective.

The bootstrap design is proportionate. **Verified:** it jointly resamples constituent returns in circular monthly blocks, preserves contemporaneous cross-asset relationships, compares allocations on the same sampled paths and examines several block lengths.

**Judgement:** this is considerably more defensible than independently resampling assets. Nevertheless:

- Resampling cannot add independent crises.
- Circular blocks join historical endpoints and can create artificial transitions.
- Pooled resampling does not establish stable regime probabilities.
- Drawdown intervals depend on path length and block structure.
- Multiple windows, metrics and variants provide several opportunities to find an apparent distinction.

These are sensitivity intervals conditional on this history, not calibrated probabilities for future outcomes. An interval containing zero establishes neither equivalence nor absence of an economically consequential effect.

There is also a concrete reporting limitation. **Verified:** `intervals_span_zero` asks whether *all* block-length intervals contain zero. The conclusion maps a false answer to “distinguished at every block length.” With invented mixed intervals, the function returns false even though some intervals contain zero. **Unknown:** whether any recorded research result was actually misclassified. The all-block claim therefore needs checking against the individual intervals. This calls for a narrow correction, not a new statistical framework. [E-0003 reporting logic](../../tools/e0003_aud_cash.py)

**Reported:** E-0003 and V1 describe distinctions in volatility while leaving the duration comparison inconclusive. I cannot authenticate those conclusions or their economic size. **Judgement:** they justify further investigation; they establish neither a stable currency hedge nor regime-dependent duration behaviour.

## 4. Architecture assessment

**Judgement: the recent work supports the approved architecture without establishing a need for structural change.**

Several choices have acquired practical support:

- **Explicit constructions:** adjusted-close agreement is correctly separated from independent validation.
- **Retained receipts:** snapshots permit revision detection and reconstruction.
- **Versioned specifications:** reinvestment, numeraire and funding conventions remain inspectable.
- **Released-data readers:** analysis can enforce provenance and temporal declarations.
- **Lightweight local analysis:** useful research fits within ordinary modules and scripts.
- **Separate publication authority:** exploratory computation does not silently become a governed consumer output.

These are the boundaries envisaged by the approved architecture. [Architecture](../../docs/architecture.md)

**Verified:** common-boundary compounding and explicit staleness rules make historical alignment feasible. **Judgement:** noon-New-York FX and ETF closing prices still represent different valuation instants. Monthly aggregation reduces the prominence of that mismatch; it does not remove it.

Retaining bytes and hashes supports reproducibility, but does not establish that the source was correct. The findings index already records this distinction and the need for independently accessible evidence.

The rights model has exposed a real research constraint. **Owner-decided:** OD-0163 permits a narrow personal evaluation while denying agent access to values, external processing and consumer distribution; post-termination rights remain unknown. [OD-0163](../../docs/decisions/owner/OD-0163-eodhd-rights-zero-curve-variant.md)

**Judgement:** this creates material friction for independent empirical assessment. It is evidence about source suitability, not a reason to weaken the rights standard. Synthetic review can validate implementation behaviour while leaving actual-data accuracy unauthenticated. A permitted human verification or a source with suitable verification rights can address that gap.

The corrections needed are local: accurate summary logic, current evidence classifications and dependable execution from pinned inputs. No observed workload requires another service, database, orchestration platform or agent layer.

## 5. Critical gaps

The following priorities are **judgement**, distinguished by when they matter.

1. **Historical ETF accuracy — material now and before crisis-dependent inference.**  
   **Reported:** issuer comparisons passed for SPY, IEF and BIL, but reach back only to 2016. Those checks are useful aggregate corroboration, not validation of each distribution or closing price. The issuer references are not independently readable here; I cannot authenticate their transcription or comparisons. The 2008 inputs remain particularly consequential. [Evaluation evidence](../../docs/evidence/e0002/assessment-1.md)

2. **Cash construction and alignment — material to V1 interpretation.**  
   **Reported at `59429c5`:** V1 extends the sample into 2008 and passes its later-period accrual comparison. **Verified:** the registered check compares the method with the post-2011 index because the historical file does not overlap it. It cannot authenticate the older rates, and benchmark accrual is not an investable deposit return.

3. **Sparse episodes and descriptive conditioning — prerequisites for the next conditional study.**  
   Adding 2008 adds an important episode, not many independent crises. Inflation, policy, rate and liquidity states overlap. Small cells, retrospective labels and outcome-selected windows can create persuasive but unstable explanations.

4. **Reporting and end-to-end reproduction — material before stronger reliance.**  
   Correct the block-length wording and retain explicit unavailable or unperformed checks. **Reported by Codex:** V3 initially mishandled truncated windows and overstated reconciliation; the two corrections were subsequently verified READY at `c294e7f`. This validates those scoped corrections, not E-0003 or its licensed results. [Verification](../../reviews/records/VERIFY-2026-11-04-e0002-v3-1.md)

5. **Rights and validation for dissemination — prerequisites for consumer output.**  
   Current personal-use permissions do not support a consumer report. Publication also needs appropriate validation, approval and a defined consumer contract. Source retention after cancellation remains an owner decision.

6. **Broader implementation and prediction — later-stage requirements.**  
   Trading costs, tax, hedge execution, ETF liquidity and factor-to-vehicle basis matter before implementation conclusions. Validated expected-return and predictive models remain absent. Australian distribution completeness matters before expanding into affected ETFs; the BGBL discrepancy does not directly invalidate the current US-only comparison.

## 6. Next milestone

**Judgement: prefer Option 3, with a small descriptive component from Option 1.**

The bounded milestone should be:

> **Make the existing AUD defensive-sleeve comparison independently challengeable, then determine whether its historical stress contrast warrants one conditional-diversification experiment.**

This offers the highest marginal value because the next model would otherwise lean heavily on precisely the older observations that remain least corroborated. Broader asset comparisons would multiply unresolved data and economic bases. A full regime model would add explanatory flexibility before establishing a dependable benchmark.

The milestone should produce:

- A frozen panel identity and reproducible execution from retained inputs under current rights.
- Targeted corroboration of the three existing sleeves over the historical periods carrying the interpretation, especially 2008.
- An explicit cash-splice account separating method agreement from historical-source accuracy.
- Correct per-block uncertainty classifications and a concise record of remaining timing and vehicle basis.
- One comparison of already identified stress episodes, expressly treated as retrospective description, not independent confirmation or a predictive regime model.

**Acceptance evidence:** a rights-permitted verifier can trace the decisive reference facts to underlying bytes or an independent read; rebuild evidence identifies exactly what ran; discrepancies are accounted for; and the conclusion remains defensible under the declared sensitivities—or is narrowed.

A hash or author transcription alone does not close the external-evidence gap. If suitable corroboration is unavailable, the owner chooses between obtaining it and accepting a narrower claim. **I recommend obtaining targeted corroboration before relying on 2008 to motivate a general conditional relationship.** Other exploratory work need not stop.

The next actor is the owner to adopt a bounded instruction, then Claude within that scope. A usable instruction would be: “Prepare the qualified AUD comparison described above, using only authorised sources and operations; retain all limits; obtain no new source or publication rights implicitly; return a recommendation on the next conditional question.” This advice changes no reviewer assignment.

## 7. Medium-term outlook

**Judgement:** HIO is in an early research phase within Year 1 foundations. Some analytical functions anticipated later have arrived; the validation obligations have not thereby disappeared. The charter’s trajectory remains a sequencing hypothesis. [Charter](../../docs/charter.md)

| Capability | Present maturity and next boundary |
|---|---|
| Acquisition and provenance | Working capture and retained-history tooling; source coverage and operational reliability remain bounded |
| Economic factor construction | Explicit ETF and cash constructions demonstrated; theoretical duration remains unreferenced |
| Reproducible historical research | Strong pins and synthetic checks; independent actual-data reproduction constrained |
| Multi-factor risk analysis | Joint portfolio comparisons exist; exposure estimation and robust conditional covariance remain ahead |
| Portfolio construction | Ready for qualified fixed-allocation comparisons; risk budgets need better-supported risk estimates |
| Expected returns | No validated capability; economic building blocks and uncertainty come first |
| Factor dynamics and mean reversion | Hypotheses exist; long state histories, vintage evidence and disciplined inference remain missing |
| Tactical allocation | No demonstrated predictive capability; requires timestamped inputs, benchmarks, costs and out-of-sample evaluation |
| ETF implementation | Return reconstruction exists; liquidity, execution, tax and exposure mapping remain incomplete |
| Consumer publication | Contracts and gates exist; source permissions, validation and explicit approvals remain unresolved |

If new infrastructure development stopped, **judgement:** six to twelve months could reasonably deliver a small qualified multi-asset panel, one disciplined conditional-diversification study, covariance-estimator comparisons, historical scenarios, marginal-risk analysis and a modest set of strategic allocation comparisons. A limited vehicle comparison and building-block expected-return ranges are plausible once their data and rights prerequisites are met.

That does not require a mature investment-management platform. Existing capture and required operational obligations would still need maintenance.

**Judgement on assurance:** collaboration has contributed meaningfully. **Verified records show** independent review identified substantive qualification, boundary and reporting failures. Those were not cosmetic findings. Research output now demonstrates the foundations’ practical value.

**Unknown:** net developer productivity, owner time saved and cost per useful result. Neither rapid commits nor review counts establishes efficiency. Some recordkeeping is visibly stale, and repeated permission exchanges can burden iteration, but the record does not quantify that burden.

A bounded standing authority for preregistered local analyses on named, cleared inputs would be reasonable. New sources, changed economic conventions, predictive claims and consumer use should remain separate decisions. This would preserve scrutiny while avoiding a new approval for every routine execution.

The greatest risk of moving too quickly is **fitting an elaborate explanation to a few crises, imperfectly corroborated returns and hindsight-defined states, then mistaking resampled precision for predictive evidence**.

## 8. Owner decisions

**Judgement:** no architecture amendment or standards relaxation is warranted.

Only two decisions need follow this calibration:

1. **Yes/no:** authorise the single consolidation milestone in §6, including routine local iterations within its named sources and descriptive scope; any additional acquisition requires its own explicit scope.
2. **Before subscription termination:** decide retention only on evidenced permissions, or choose a source arrangement that supports the intended research and independent verification.

This assessment accepts no experiment, validates no series and authorises no implementation.