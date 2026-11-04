---
id: VERIFY-2026-11-04-t0022-1-2-PLAN
title: Narrow independent test plan for T-0022 F-3 and F-4
status: in_review
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0168-verify-2-receipt-exception.md item 1
reviewed_base: bb58f859888d4b7f3b6ebc3a071157642de2f0a3
reviewed_head: b410b02d988d431ed3e723c8a7666f391f3bc345
created_at: 2026-11-04
---

# Verification plan, fixed before author material

I am Codex, independent reviewer. T-0022 is in_review. OD-0168 item 1 assigns only the F-REVIEW-2026-11-04-t0022-1-3 and -4 remediation claims in `tools/eodhd_eval.py` and its tests. The assigned head is the commit adding OD-0168. The previous verification at `bb58f859888d4b7f3b6ebc3a071157642de2f0a3` left both findings open; this is the contextual diff base, not an owner-assigned base. No licensed bytes, values, workspace, credentials, or source requests are in scope.

## Fixed checks

1. Trace every raw response, manifest, store and owner-report write reachable from fetch and run. Confirm that snapshot input, pre-existing `raw/`, `store/`, and `reports/` links, and existing output files cannot redirect writes outside the canonical mode-700 workspace. Exercise absolute and traversal snapshot names, a `raw` symlink, a `reports` symlink, and an existing report file using invented data and temporary directories. Check rejection occurs before any outside write.
2. Check mode enforcement for the root, all private directories, and files written under them. Exercise a permissive existing root, permissive existing report file, and the modes of newly created raw and owner-report files with invented data. A refusal or safe correction must precede any licensed-derived write.
3. Run the focused T-0022 test module from the locked environment, without test artefacts under the worktree. Inspect changed tests for whether they cover the original counterexamples, not merely the chosen implementation. Run independent invented probes where a gap remains.
4. Compare the remediation diff against these two findings and the task-card workspace requirement. Record each outcome separately, with evidence and limits. Do not re-review F-1, F-2, F-5, economics, source rights, or actual vendor data. Do not read the author's handoff or response until this plan is fixed.

Technical verification is an opinion at this head. It is not owner acceptance, a waiver, source approval, or an index-state change. The owner or receiver reconciles finding states after receipt under operating model §6.2 step 5.12.
