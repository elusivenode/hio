---
id: T-0019
title: "CMT synthetic bond return in the library, on invented inputs only"
status: accepted   # OD-0153 at fa6370d, merged into main as 29dab6f; invented inputs only
accepted_by: OD-0153
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex, if the owner assigns one"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0150
base_revision: cbd6c8c7b421a8fecf9d4eee03a4ef82463b933f
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: []
  adrs_context_proposed: []
  specs: [specs/factors/rates.us.cmt_10y.total_return.yaml]
  standards: [docs/standards/return-accounting-and-factor-construction.md]
  findings: []
  depends_on: []
  blocks: ["the US duration experiment, with the H2 rights decision and its own yes"]
---

# T-0019: CMT construction, synthetic

> **Authorised by OD-0150.** Code on invented numbers. The spec it follows is **proposed, not approved**: the standard wants a spec before construction code, and this one exists but has no approval. So nothing here can produce a release, and no job, source or store touches it.

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| C-1 | `src/hio/library/cmt.py`: full revaluation, coupon cash, interpolation, decomposition; decimal arithmetic; no new dependency | `tests/test_t0019_cmt.py` |
| C-2 | RA-INV-013's two fixtures; RA §14.6's worked case, including duration and convexity; CMT-INV-1 to 5 | the same |
| C-3 | spec 0.1.1: the coupon wording, still proposed | `check_repo` |

## Exclusions

Any real yield; a parser, source, job or release; excess return; any other tenor or market; approving the spec.

## Submission (filled by the implementer)

Branch `feat/t0019`, built by the orchestrator. Full suite 1146 passed; `ruff` and `check_repo` clean. **A defect found while building:** the first version's convexity term was 100 times too small, and the worked-example test's tolerance hid it. The residual test failed, and the formula and tolerance were corrected. The return itself never used that term. Worst residual on invented curves: about 0.26 bp. Submitting approves nothing.
