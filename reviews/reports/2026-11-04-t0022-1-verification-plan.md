---
id: VERIFY-2026-11-04-t0022-1-1-PLAN
title: Narrow verification plan for T-0022 findings 1 to 5
status: in_review
reviewed_head: bb58f859888d4b7f3b6ebc3a071157642de2f0a3
assignment: docs/decisions/owner/OD-0167-history-verify-aud-variant.md item 2
created_at: 2026-11-04
---

# Verification plan fixed before author material

Role: Codex independent reviewer. T-0022 remains in review. OD-0167 item 2 assigns only the five remediation claims in `tools/eodhd_eval.py`, its tests, and `docs/evidence/e0002/assessment-1.md`. The assigned head resolves from the OD-0167 file to the checked-out `bb58f859888d4b7f3b6ebc3a071157642de2f0a3`. No licensed bytes or values, source retrieval, or local evaluation workspace will be used.

Basis read before the author response: OD-0167, T-0022, E-0002 pre-registration, rights standard, return accounting standard, and REVIEW-2026-11-04-t0022-1. The original findings define the tests below. The task card's base revision and original review head are context, not a substitute for the assigned verification head.

1. F-1: inspect how quote currency is established and how Q1 gates the three sleeves. Use invented USD, wrong-currency, and unknown-currency cases; a wrong or unknown quote currency must refuse Q1 and the comparison gate. Do not conflate distribution currency with quote currency.
2. F-2: inspect Q3's denominator and missing adjusted closes. Use invented complete, partial and absent adjusted-close sequences; missing comparisons must count against the pre-registered 99% requirement, and a mostly unassessable sleeve must not open the comparison gate.
3. F-3: inspect snapshot validation before fetch or write. Exercise absolute paths, traversal, unsafe components and a normal name in a temporary invented workspace. Confirm raw writes cannot resolve outside `raw/`, including through path links if the implementation permits them. No network call.
4. F-4: inspect and exercise private-workspace checks and creation modes. A permissive pre-existing root must be refused. Directories and files holding raw, store and report content must be private with a permissive process umask. Use only invented content in temporary paths.
5. F-5: inspect the current assessment for a source-derived direction, magnitude or interpretation while avoiding the earlier licensed-derived bound in Git history. The public assessment may carry counts and qualification states; detailed values belong only in the local owner report under the rights record.

After the plan is fixed, read the author's response and scoped diff as unverified claims. Run the relevant existing tests and independent invented probes as needed. Record per-finding evidence, verdict and limits in a verification record. Write only `.md` under `reviews/`; do not edit the submitted work, commit, push or access the licensed workspace. Include a reviewer handoff and report the added-file hashes for the runner's receipt.
