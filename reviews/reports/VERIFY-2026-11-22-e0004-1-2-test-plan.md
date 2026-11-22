---
id: VERIFY-2026-11-22-e0004-1-2-TEST-PLAN
status: in_review
owner: codex/reviewer
---

# Test plan: VERIFY-2026-11-22-e0004-1-2

Fixed before reading Response 2 or any author handoff. Authority: OD-0204 and its Assigned reviews row on public `main`; base `f349efeaaf1cd3540e8b206d5f79e511ee1f2410`, head `3528e8e537a7505d4de3af469f9de0a4dcba4183`, branch `review/e0004-1-verify-2-codex`. The checkout matches. Prior records are REVIEW-2026-11-22-e0004-1 and VERIFY-2026-11-22-e0004-1-1. Work is in review.

1. **F-2, current files:** Inspect the full current tracked tree, especially OD-0190 correction 2 and E-0004 evidence, for any numerical measurement derived from EODHD returns. Trace suspect fields through code and the source rights record. Exclude git history as OD-0196 directs. Do not read licensed inputs or quote any restricted value.
2. **PDF dependency finding:** Build a fresh environment from `uv.lock` with `uv sync --frozen`; verify `pypdf` is installed from the lock. Run the PDF tests, and the focused E-0004 suite, checking that no tests skip. Run the first-release check on retained BLS PDF releases using only the allowed local paths and write any generated files to a temporary directory. Record the command and result.
3. **256-month wording only:** Independently enumerate the distinct CPI months actually read by the 233 state calculations from the permitted run states and first-release ledger, and compare the corrected text in the preregistration addendum and `cpi-first-release-states-1.md`. Do not re-verify F-1's substantive disposition or close it.
4. **Regression:** Inspect the base-to-head diff and run focused relevant tests for changed behavior or broken evidence claims. Check that changes outside the three narrow corrections do not alter the prior review conclusions.

Limits: local research reads only under the OD-0204 paths, no EODHD bytes or values, no other licensed data, no Azure or vendor URL, and no real-input experiment rerun. Only `reviews/` may be written in the repository. The author response is an unverified claim until checked.
