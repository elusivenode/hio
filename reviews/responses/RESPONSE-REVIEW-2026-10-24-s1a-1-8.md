---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-8
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-7]
responds_to: VERIFY-2026-10-24-s1a-1-7   # commit 35526b539186ca31b1c944dbb93b46ac7531360d, record sha256 5cfc9bc3e138afb4e60d7f205668c0abc9ea115448b888c538efadc60147e00c (checked; OD-0032)
previous_submission_head: f00db8c46a8462eab73a39117e866990160d5c57
authorised_by: OD-0032   # within OD-0030/OD-0031
fix_commits: [6ac9ef7]
test_commits: [655f22c]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-8.md
created_at: 2026-10-24
---

# Remediation response 8: F7 round 3

> **Author's claim, not verification.** F7 stays **open** (and so does F4). Responses 6 and 7 are
> unchanged. The approved contract blobs are unchanged (Q-001 `419992f2`, Q-002 `d0a25b3b`).

## Root cause

- Response 7's outcome verification used its own, looser rules. It accepted a `redundant` row
  wherever *any* earlier vintage held the same value.
- Ingest's rule (`_redundant`) also requires the *latest* capture-order value to match.
- So the true revert 3.60, 3.61, 3.60 could be forged as "redundant" and serve 3.61.

## Fix (`6ac9ef7`)

**One rule set, not two.** Ingest's per-row decision is now a single function, `_derive`.
- It sees only the vintages captured before the receipt, plus those it decides itself.
- It produces the outcome rows and the new vintages: latest-value and evidence-strength
  redundancy, reverts, knowability from the capture mode, and the jump gate.

**Who uses it.**
- **Ingest** uses it to decide.
- **Completeness** uses it to verify. It re-derives every receipt with the recorded capture mode
  and requires an exact match:
  - the outcome rows;
  - each derived vintage, stored exactly;
  - no other stored vintage from that capture event (`receipt_id`, `captured_at`).

  Any difference refuses queries and resolutions.

## Evidence

| Check | Result |
|---|---|
| `tests/test_f7_round3.py`, run against `f00db8c` | 2 failed, 1 passed (exit 1). The forged revert and the mirror forgery were both accepted; the honest-replay baseline passed |
| The same tests now | 3 passed. The forged state is refused by `as_known_by_market`, `as_captured_by_hio`, `conflicts` and `resolve_conflict`, also after reopening. The honest replay returns 3.60 (vintage 3), and the view and evidence digest are identical after reopening and in an independent replay |
| Whole suite | `pytest` 251 passed, exit 0. That includes the F1–F6 regressions, the original F4/F7 acceptance tests and the round-6 regressions, with unchanged test code |
| `ruff check`, `ruff format --check`, `tools/check_repo.py` | 0, 0, 0 |
| Financial output versus `f00db8c` (Codex's probe) | **fully identical** (`cmp` exit 0): `data.csv` and the release ids alike. Only verification changed |

No further defect was found within the F7 contract.
