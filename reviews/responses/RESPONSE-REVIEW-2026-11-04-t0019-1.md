---
id: RESPONSE-REVIEW-2026-11-04-t0019-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-11-04-t0019-1-1, F-REVIEW-2026-11-04-t0019-1-2, F-REVIEW-2026-11-04-t0019-1-3]
reviewed_head: b4929f721d9772f64d5904685ccc741a5ae10224
fix_commits: [self]   # the commit adding this file; resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-11-04-t0019-1.md
submission_head: self
created_at: 2026-11-04
---

# Remediation response: REVIEW-2026-11-04-t0019-1

> Written by the author on `feat/t0019` under OD-0152. A claim, not a verification. Each finding stays open until a verification record closes it.

| Finding | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|
| F-1 (medium): a leap-day strike has no defined maturity-based schedule | Spec 0.1.2: coupon dates are anchored to the strike (strike + 6k months, day clamped), and the last is the maturity, so there is no stub and the bond is at par on its strike date (CMT-INV-6). **The code's behaviour is unchanged:** the spec moved to match it. | `test_the_coupon_schedule_is_anchored_to_the_strike`: a leap-day and a clamped month-end strike, covering the day before the coupon, the coupon date, par at the strike and the maturity | A synthetic convention, not real Treasury dates; stated as a limitation. The alternative, maturity-anchored with a first stub, was not chosen because it breaks the simple "par at the strike" |
| F-2 (medium): the spec treats the residual as measuring pricing-basis error | Spec 0.1.2: the residual is stated to test the Taylor decomposition only. Pricing basis is declared **unmeasured**, and the experiment must report a separate zero-curve repricing sensitivity, which needs the curve's other tenors. No code for it yet. | Spec text; the module docstring. No test can measure this on invented data | **The sensitivity isn't built.** It is required of the experiment, which needs its own yes. Agreed with the finding: nothing here shows the size of the error |
| F-3 (low): the H2 pack omits raw-retention duration | `docs/research/T-0002-h2-reading-pack.md`: the owner must state a duration; "indefinite, for audit and rebuild" proposed, following the matrix | The pack's text against `T-0002-owner-verification-matrix.md` | None |
