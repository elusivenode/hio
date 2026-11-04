---
id: VERIFY-2026-11-04-t0019-1-1-TEST-PLAN
title: T-0019 first remediation verification test plan
status: in_review
---

# Test plan fixed before author response

Role: Codex, independent reviewer. T-0019 is `in_review`. OD-0152 correction 1 and the Assigned reviews row on local `main` at `9482189c0b58b9fbd82b7af2066f702e61df0ac8` assign `VERIFY-2026-11-04-t0019-1-1`, base `b4929f721d9772f64d5904685ccc741a5ae10224`, head `fa6370dc3f55c4d9e6537d502ab4a4727ca85fbd`, branch `review/t0019-1-verify-1-codex`. The checked-out head agrees and the base is an ancestor. The original [review](../records/REVIEW-2026-11-04-t0019-1.md) found three open items. Return accounting §6 and RA-INV-013 govern the calculations; the factor spec is still proposed. No H2 right has been granted.

1. Inventory the base-to-head changes, separating remediation from the merge of `main`. Check for another owner assignment. Examine the changed implementation, tests, proposed spec, and H2 pack, with the original findings as the acceptance criteria.
2. For F-1, derive maturity-anchored coupon dates independently for invented leap-day and month-end strikes. Check the declared first-stub/par convention against dirty-price arithmetic, coupon cash on both sides of the boundary, and subsequent re-strike. Probe invalid dates and gaps so the fix does not weaken C-1 or RA-INV-013.
3. For F-2, determine whether the spec now distinguishes the Taylor decomposition residual from flat-yield pricing-basis uncertainty. Check any proposed sensitivity or reference against the actual model and test what the residual can and cannot bound, using invented curves only.
4. For F-3, compare the H2 pack's retention duration question or proposal with the owner-verification matrix's requirement. Confirm that no draft recommendation became a permission or a data retrieval action.
5. Recheck C-1 through C-3: full revaluation, cash-inclusive return, interpolation, decomposition, RA §14.6 worked case, RA-INV-013, spec consistency, and test power. Run focused tests, the full suite, lint/format, `tools/check_repo.py`, and `git diff --check`. State exact outcomes and any tools added. Read the author response only after this plan is written. Record each finding outcome and any new finding; write only under `reviews/`.

No Azure access, data-URL request, real yields, authentication, publisher contact, or external write is in scope. Publishers' documentation pages may be read if needed.
