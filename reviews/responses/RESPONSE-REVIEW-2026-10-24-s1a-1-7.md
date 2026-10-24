---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-7
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]
responds_to: VERIFY-2026-10-24-s1a-1-6   # commit 3cb3dd073f832f2cb9d49a1d2690a131b14e7f37, record sha256 87ff2b82c8779cb73015468bb59447022a2af838f272df656786c16c33bab9d1 (checked; OD-0031)
previous_submission_head: 191ac0f0461b59c61c8b11c60befd6f7f04da6b6
authorised_by: OD-0031   # within OD-0030
fix_commits: [36e5f13, c3be820]
test_commits: [b3aa3c7]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-7.md
created_at: 2026-10-24
---

# Remediation response 7: F4/F7 round 2

> **Author's claim, not verification.** F4 and F7 stay **open**. Response 6 is unchanged. The
> approved contract blobs are unchanged (Q-001 `419992f2`, Q-002 `d0a25b3b`).

## Finding 1: completeness (`36e5f13`)

**Root cause.** A same-value row was treated as a no-op by value equality alone. Response 6 listed
this as a residual limit, but it violated OBS-INV-019, and Codex's rejection was correct.

**Fix.**
- **A processing outcome per capture event.** Ingest now writes one outcome per receipt, in the
  receipt's own transaction, distinct from the capture evidence: the capture mode, and per row the
  disposition (`vintage` with its seq, or `redundant`), `knowable_at` and basis.
- **What completeness now requires.** Every receipt captured by Q has an outcome, or a quarantine
  record, that verifies:
  - its rows equal the receipt's rows, by identity and content;
  - each `vintage` row names a stored vintage exactly;
  - each stored vintage of the capture event (`receipt_id`, `captured_at`) is accounted for;
  - each `redundant` row is re-derived from the recorded capture mode, and justified by an earlier
    capture with equal or stronger evidence knowable no later.
- **The evidence digest** pins the capture mode.
- **A receipt cannot be processed twice.**

## Finding 2: admissibility (`c3be820`)

**Fix.** `build_releases` calls `require_predictive_pit` on every input view of a point-in-time
build, before rights, computation or any release exists.
- There is no override, and no new descriptive-publication path.
- Reconstructed builds keep their existing labelled-reconstruction path.

## Evidence

| Check | Result |
|---|---|
| `tests/test_f4_f7_round2.py`, run against `191ac0f` | 5 failed, 1 passed (exit 1). Codex's case was served, then changed under the same digest; the Q > T build was published |
| The same tests now | 6 passed |
| Whole suite | `pytest` 248 passed, exit 0. That includes the F1, F2, F3, F5 and F6 regressions with unchanged test code, and the original F4/F7 acceptance tests |
| `ruff check`, `ruff format --check`, `tools/check_repo.py` | 0, 0, 0 |
| Financial output versus `191ac0f` (Codex's probe) | all four `data.csv` byte-identical. Release ids change, because the `evidence_digest` recorded in the manifest's `inputs` now includes the capture mode. Verified: there is no other manifest difference apart from the resulting FX upstream hashes |

## Changed test expectation

`test_fx_period_waits_for_the_in_arrears_usd_leg_under_market_knowledge` built point-in-time market
releases with Q > T. It now:
- asserts that such a build is refused;
- checks the same knowability placement on views, which are labelled and not admissible;
- builds admissible releases at Q = T, where the Friday→Monday period appears once its inputs are
  captured at 14:00Z.
