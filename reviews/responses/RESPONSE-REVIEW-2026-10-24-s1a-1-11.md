---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-11
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-7]
responds_to: VERIFY-2026-10-24-s1a-1-10   # commit 586b35e6dfe1226b8b139a5deee13a211faa84ba, record sha256 35685f04a2368616258032bba044093b45a7ddb7c9c4b28d76d653a925a1ca4b (checked; OD-0036)
previous_submission_head: 21e4a0777f2f6bcece0b2dd691a552b6a7020e39
authorised_by: OD-0036
fix_commits: [6b0c0b3]
test_commits: [b996e48]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-11.md
created_at: 2026-10-25
---

# Remediation response 11: F7, stored quality events obey the decision clock

> **Author's claim, not verification.** F7 stays **open** (and so does F4). The approved contract
> blobs are unchanged (Q-001 `419992f2`, Q-002 `d0a25b3b`, Q-002-R1 `cb7a937d`).

## Root cause

- `quality_digest` excludes `recorded_at` because Q-001's no-backdating rule holds.
- But only `set_quality` enforced that rule; `_load` trusted stored events.
- So an event altered to `recorded_at > decided_at` was applied on reopen, with all four pins
  unchanged.

## Fix (`6b0c0b3`)

**One shared rule,** `_check_decision_clock`, now governs both writing (`set_quality`) and loading
(`_load`). A decision must be:
- not earlier than its own recording;
- strictly after the vintage's capture;
- strictly after the previous decision.

A missing `recorded_at` refuses.

**Where it bites.** An invalid stored event refuses (`DecisionRefused`) when the store is opened.
So it can't reach a view, a digest, pin verification or a release: all of them start from an open
store. Valid differing `recorded_at` values stay digest-neutral, as Q-002-R1 specifies.

## Evidence

| Check | Result |
|---|---|
| `tests/test_f7_round6.py`, run against `21e4a07` | 4 failed, 1 passed (exit 1): `recorded_at` after `decided_at`, `decided_at` at the capture, `decided_at` before the capture, and a missing `recorded_at` were all accepted. The faithful-copy baseline passed |
| The same tests now | 5 passed. Each invalid case refuses on reopen, both at store construction and through `verify_pins`. Faithful copies with valid, differing `recorded_at` keep identical views and pins, across independent stores and after reopening |
| Whole suite | `pytest` 278 passed, exit 0. That includes F1–F6, the original F4/F7 cases, rounds 6–9 and AT-Q2R1-1..7. AT-Q1-4's message match was updated to the now-precise "not after the vintage's capture"; the refusal itself is unchanged |
| `ruff check`, `ruff format --check`, `tools/check_repo.py` | 0, 0, 0 |
| Financial output versus `21e4a07` (Codex's probe) | **fully identical** (`cmp` exit 0): `data.csv` and the release ids alike. Only load validation changed |
