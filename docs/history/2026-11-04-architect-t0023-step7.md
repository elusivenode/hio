<!-- The solution architect's answer on T-0023 step 7, verbatim. Consultation 20261104T202100-ask-df98, checkout 52ffed8. Advice only: nothing in it is adopted. It holds no licensed value; it had none. The original is at ~/.hio-runs/20261103T065037Z-3d12/sa/20261104T202100-ask-df98/out/answer.md. Link targets are repointed from its temporary clone to repository paths; no other change. -->

**Judgement: yes to designing one bounded experiment; the evidence does not yet justify running it or asserting a conditional relationship.** I agree with your direction, but would sharpen the question and avoid making a particular historical start date or IEF NAV file an absolute prerequisite.

**Verified baseline:** checkout `52ffed8cfc362c33d540c60196ca1adbfb7988ef`. I inspected the requested records and code, but accessed no numerical reports or underlying source bytes and ran no research calculations. Consequently, empirical outcomes below are **reported**, not independently verified. The findings index supplied no additional T-0023 corroboration.

**A. Row 1 is an honest classification, conditional on the reported results.**

**Verified:** the preregistration requires opposite robust signs on compounded return, and the tool implements that rule. “May be warranted” leaves room for rejecting an inadequately supported next experiment. [Rule and implementation](../../tools/t0023_episodes.py#L135)

**Reported:** Treasury duration meets that rule. The failures do not retrospectively change the rule, but materially narrow its interpretation:

- **BIL C1:** a consequential month-end discrepancy remains unresolved.
- **IEF C4:** disagreement with a different, itself unreferenced construction establishes neither that IEF is wrong nor that maturity differences explain the gap.
- **SPY C5:** the audited-return bar failed. The subsequent NAV diagnostic offers a plausible explanation; it does not erase the failure.
- **Missing IEF NAV:** the sleeve carrying the duration interpretation still lacks that corroboration. Fiscal-year agreement cannot establish calendar-2008 accuracy.

These qualifications are correctly retained in [corroboration-1.md](../../docs/evidence/t0023/corroboration-1.md).

**Judgement:** say “the author reports a sign reversal that survives the declared substitutions,” rather than “Treasury diversification is robust.” Unknown sizes and sensitivity margins prevent me from judging how comfortably the result survives plausible data errors.

**B. Your question needs a defined measure of diversification benefit.**

A positive Treasury-versus-bills return difference during an equity crisis does not itself establish an equity–Treasury dependence relationship. Bond performance, carry and portfolio compounding all contribute.

**Judgement:** my preferred first question is:

> Does replacing the bills sleeve with Treasuries reduce monthly downside losses differently across a predeclared, observable inflation state, in otherwise identical USD portfolios?

Retain the existing 60/40 weights and monthly rebalancing. One primary outcome could be the difference between portfolios’ mean monthly downside losses, using \(L(R)=\max(0,-R)\), compared across states. This directly measures the portfolio consequence. It would not establish inflation’s causal role.

For **one candidate state**, I would choose **inflation acceleration**:

> At the preceding month-end, is the latest published year-on-year headline CPI rate greater than the rate published twelve months earlier?

Use original release values and publication timestamps; carry the state forward between releases; assign equality to the non-accelerating state. Missing publication evidence means unavailable, rather than assumed knowledge.

**Judgement:** this gives a reproducible binary definition without fitting a threshold to the three episodes. It may classify those episodes inconveniently—that must be allowed. Choosing between inflation and policy after comparing their results would spend another hypothesis. I would leave policy for later.

I agree with USD first, with one correction. **Verified from the accounting:** both duration-comparison portfolios are fully USD investments. Under the declared translation identity,

\[
W_T^{AUD}-W_B^{AUD}
= W_{FX}\bigl(W_T^{USD}-W_B^{USD}\bigr).
\]

Since \(W_{FX}>0\), translation preserves the compounded-return difference’s sign. Thus the reported sign reversal already implies a USD reversal. Currency still changes its size and drawdown behaviour.

**C. The smallest requirement is adequate independent information, not a prescribed start year.**

**Judgement:** the design needs:

1. **Aligned monthly USD total returns** for equity, Treasury duration and bills, with explicit income, valuation and splice conventions.
2. **One state history with evidenced availability**, appropriate rights and retained underlying evidence.
3. **A frozen primary outcome, state definition, sample rule and economic relevance threshold**, declared before inspecting conditional results.
4. **An information assessment:** observations, distinct state runs and separate equity-stress clusters in each state. Numerous adjacent months cannot substitute for multiple independent episodes.
5. **Independent empirical corroboration** of the consequential inputs and reproducible calculations from retained bytes.

I disagree with requiring pre-2007 history *before* assessing those counts. Longer history is likely valuable, but neither “1990” nor “before SPY” is intrinsically sufficient. Extending the sample with an unreferenced construction can increase length without increasing trustworthy information. E-0001 should therefore remain a sensitivity unless its construction obtains a suitable independent reference.

For uncertainty, dependence must be preserved. A useful fragility diagnostic is whether omitting one contiguous stress episode reverses the conclusion. Older history already familiar to the researcher remains retrospective evidence; it does not become an untouched validation sample merely because it was newly acquired.

**Judgement:** I recommend independent verification before stronger reliance on T-0023; the owner controls any assignment. IEF NAV is the smallest obvious additional corroboration, **but a comparably independent return reference could serve instead**. Its absence need not prevent drafting the experiment.

I would recommend **not running the inferential study** if:

- one stress episode supplies essentially the entire state contrast;
- publication timing or permitted data use cannot be established;
- unresolved return discrepancies could plausibly determine the conclusion;
- the state or threshold needs adjustment to recover the desired episode separation; or
- feasible uncertainty is too wide to distinguish an economically useful effect.

The owner can choose additional evidence or a narrower descriptive claim. I recommend closing material evidence gaps rather than accepting them for a general conditional conclusion.

**D. Step 6 has limitations that materially constrain the interpretation.**

**Verified:** the code computes weighted monthly portfolio returns, compounds their paths, subtracts portfolio measures and applies the declared decision rule. That inspection does not authenticate the reported run.

Four points matter:

- **“Robust” has a narrow definition.** The two-point threshold applies only to the frozen result. Sensitivities need preserve sign, so an arbitrarily small surviving effect can qualify. This matches the preregistration but does not establish robust economic size.
- **Nine sensitivities provide less independent challenge than their count suggests.** S6/S7 alter AUD cash, absent from both duration portfolios. S8/S9 cannot change the duration compounded-return difference’s sign under common FX translation. None substitutes IEF NAV.
- **Episode drawdowns reset wealth at each window’s start.** They describe losses from peaks inside that window, excluding an earlier portfolio peak and intramonth losses. Three-month and twelve-month windows also offer different opportunities to accumulate losses.
- **The step-6 evidence does not fully pin its sensitivities.** The tool reads current local reference files and discards some returned provenance. Its summary retains robustness classifications but not each sensitivity’s numerical effect. The frozen baseline panel ID therefore does not identify every sensitivity input. [Sensitivity loading](../../tools/t0023_episodes.py#L221), [summary construction](../../tools/t0023_episodes.py#L427)

**Judgement:** retaining a private manifest of sensitivity-input hashes and their numerical outcomes is the smallest remedy for the last point. None of these observations establishes that row 1 is wrong; they constrain what can be claimed from it.

Your step-7 recommendation should therefore support **one proposed design and feasibility assessment**, with USD downside-loss benefit, one fixed observable state, and explicit evidence requirements. Running it, acquiring additional sources and assigning review remain separate owner decisions under OD-0180.