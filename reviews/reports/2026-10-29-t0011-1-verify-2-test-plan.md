---
id: VERIFY-2026-10-29-t0011-1-2-TEST-PLAN
subject: Independent T-0011 second remediation verification plan
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0124-assign-t0011-verification-2.md
reviewed_base: 0c44b185c130d25e142f8ada6fd7177136a6a18f
reviewed_head: c69df9e982a81e87a8fdb208ba4c66771b9664d5
review_branch: review/t0011-1-verify-2-codex
created_at: 2026-10-29
---

# Test plan fixed before reading author material

I am Codex, independent reviewer. T-0011 is in review. OD-0124 on `main` assigns this verification in `elusivenode/hio`, and the owner's direct instruction and `main` review-index row agree. The checked-out head matches the public `infra/t0011` tip; the assigned base is an ancestor. I read the task card, OD-0120 Assignment 2, the original review, the first verification, OD-0123, the H3/H4 decision pack, and CI commands before writing this plan. I have not read the round-2 author response or an author handoff.

1. **F-REVIEW-2026-10-29-t0011-1-2:** Inspect the changed runbook against the first verification's counterexample. Check the current GitHub notification-setting path and require a deliberately failing *scheduled* workflow run whose notice reaches the intended owner account. Confirm the test cannot be satisfied by a manual dispatch alone and addresses who created or last changed the schedule, including re-enabling it. Check that the runbook keeps this notice distinct from the Azure missing-attempt alert and makes no unsupported claim of completed live verification. Check the focused regression test against the previous head.
2. **No regression of F-1 and F-3:** Confirm the diagnostic destination remains Dedicated and its blob-write alert queries the matching `StorageBlobLogs` table; confirm the bootstrap `plan`, `apply`, and `output` commands still use the same external state path.
3. **Original-review scope:** Inspect the entire assigned diff and the I-1 through I-6 definitions against OD-0120 Assignment 2 and adopted H3/H4 settings. Check the writer's create-only container scope, the separate reader and state-admin scopes, no committed subscription, tenant, object, email or GitHub numeric id, and offline OpenTofu formatting and validation where feasible. Do not perform a plan, apply, registration, GitHub setting change or source-data read.
4. **Required checks:** Run the 442-test baseline and CI's exact `uv run ruff check .` and `uv run ruff format --check .` commands. Run `tools/check_repo.py` after all reviewer files are written. Record tool versions, outcomes and any verification limits.

The author response and its tests are claims until independently checked. This verification does not accept T-0011, waive a finding, authorise live operation or receive records into `main`.
