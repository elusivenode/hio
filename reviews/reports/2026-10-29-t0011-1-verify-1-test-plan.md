---
id: VERIFY-2026-10-29-t0011-1-1-TEST-PLAN
subject: Independent T-0011 remediation verification plan
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0122-assign-t0010-t0011-verifications.md
reviewed_base: 2cc7362b962a76b76a3100fbc241a7b204957619
reviewed_head: 0c44b185c130d25e142f8ada6fd7177136a6a18f
created_at: 2026-10-29
---

# Test plan fixed before the author response

I am Codex, independent reviewer; T-0011 is in review. OD-0122 Assignment 2 on `main` assigns `VERIFY-2026-10-29-t0011-1-1` in `elusivenode/hio` at the base and head above, on `review/t0011-1-verify-1-codex`. The checked-out head and public `infra/t0011` tip match; the base is an ancestor. OD-0120 Assignment 2, the received original review, T-0011 I-1 to I-6, and OD-0119's adopted H3/H4 settings fix the criteria below. No author response or handoff was read when this plan was written.

1. **F-REVIEW-2026-10-29-t0011-1-1:** Inspect the exact diagnostic destination and alert query together. Confirm that blob write logs land in the table queried, and that the query counts an actual write while producing zero when no write exists. Check a focused regression test that fails at the original head.
2. **F-REVIEW-2026-10-29-t0011-1-2:** Check that the runbook identifies the GitHub Actions failure notification setting, an owner-side verification step, and its distinction from the missing-attempt Azure alert. No GitHub settings are changed in this review.
3. **F-REVIEW-2026-10-29-t0011-1-3:** Trace the bootstrap state path through `plan`, `apply`, and `output`; confirm all read or write the same external state and that a regression test fails at the original head.
4. **Regression:** Inspect the assigned diff and unchanged I-1 to I-6 contracts against OD-0120's original scope: evidence and state role scoping, adopted H3/H4 settings, no committed subscription, tenant, object, email or GitHub numeric id, and offline OpenTofu syntax/validation where possible. Run the assigned 442-test baseline and CI's exact `uv run ruff check .` and `uv run ruff format --check .` commands. Run `tools/check_repo.py` after reviewer files are written.
5. **Limits:** No Azure plan/apply, provider registration, GitHub setting changes, live data read, receipt, approval, or waiver. Treat the author response and tests as claims until independently checked.
