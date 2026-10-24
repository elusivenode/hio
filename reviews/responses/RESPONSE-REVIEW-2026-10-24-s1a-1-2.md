---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-2
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-6]
responds_to: VERIFY-2026-10-24-s1a-1-1   # commit 0255cb2a3966f87a6c41af6020d0fd621a4fc2f1, record sha256 03dbf7197f9a0ee99902698aa265b86ad8ef4ba24f44a06dcc9fdff13fc55e5e (checked)
previous_submission_head: 18c80f27a64c8cbba653f347a3bc3401f536d0aa
authorised_by: OD-0024   # harness-0.7 §6.2 step 6, remediation before receipt
fix_commits: [45dd5386f87637b5d7ef61f6a4b0e2e969dee70d]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-2.md
created_at: 2026-10-24
---

# Remediation response 2: F-REVIEW-2026-10-24-s1a-1-6

> **Author's claim, not verification.** F6 stays **open** until a verification record closes
> it.
>
> - Response 1 (`RESPONSE-REVIEW-2026-10-24-s1a-1-1`) is unchanged; this response adds the
>   round-2 claim for F6 only.
> - The record was read with `git show 0255cb2:<path>` and is not received into this branch
>   (PR #3 is open).

## The counterexample (from VERIFY-2026-10-24-s1a-1-1)

The setup:
- `catalogue/` already exists, so the commit takes the journalled path;
- `catalogue/a` and `catalogue/b` are staged;
- `os.chmod` raises for `catalogue/b`, after `os.link` has made it visible.

At round 1 (`18c80f2`), `_commit_journalled` added a key to `written` only after `put()`
returned, and then deleted the journal. So `catalogue/b` stayed visible (SHA-256 `3e23e816…`),
and it survived a reopen.

## The fix (`45dd538`, `src/hio/storage/objectstore.py`)

1. `put()` removes its own object if anything fails after `os.link` (chmod, or removing the
   temporary file), then re-raises.
2. The journalled rollback removes the key in flight as well as the keys already written. The
   exception is a `WriteOnceViolation`, which means another writer's object holds that key; the
   rollback never removes that object.
3. `_remove()` no longer depends on `chmod`: POSIX unlink needs no write permission on the file.
4. The journal is deleted only if every rollback removal succeeded. Otherwise it stays, and the
   next `LocalObjectStore` open rolls the commit back.

## Evidence

**Regression tests:** `tests/test_remediation_s1a_1_f6_round2.py`.

| Test | Before (`18c80f2`, src unchanged) | After (`45dd538`) |
|---|---|---|
| Codex's counterexample, persistent injection | FAILED: `{'catalogue/b': '3e23e816…'}` left | passed |
| Codex's counterexample, single injection | FAILED (same object left) | passed |
| A rollback that cannot finish keeps its journal; reopen recovers | FAILED | passed |
| A failed single `put()` removes its own object | FAILED | passed |
| Rollback never removes another writer's object (guard) | passed | passed |

- **Before:** `pytest` exit 1, 4 failed and 1 passed. The run was at `HEAD` `18c80f2`, with an
  empty `git diff --stat HEAD -- src`.
- **After:** the five tests plus `tests/test_remediation_s1a_1.py` give 26 passed, exit 0.

**Whole suite at `45dd538`:**
- `pytest`: 204 passed, exit 0;
- `ruff check`: exit 0;
- `ruff format --check`: exit 0;
- `tools/check_repo.py`: exit 0.

**The four corrections verified closed (F1, F2, F3, F5).** Their regression tests in
`tests/test_remediation_s1a_1.py` are unchanged and pass. The F6 round-1 tests in that file
also pass.

**Financial output:**
- I ran Codex's comparison probe from both the `18c80f2` and `45dd538` trees, with the same
  fixtures, cutoff `2026-01-29T00:00:00Z` and a fixed code reference. The outputs are
  byte-identical (`cmp` exit 0): the same four release IDs, and the same `data.csv` SHA-256 and
  lengths:
  - AUD cash `9e3a03e9…` (2506 bytes);
  - USD cash `97faf4e8…` (2466 bytes);
  - FX decomposition `6e628493…` (2640 bytes);
  - FX excess `b8ea0d6f…` (2834 bytes).
- With each tree's real code reference, the `data.csv` bytes are identical too. The release IDs
  differ only because the code reference is a release-identity input (releases standard §6).

## Residual risk

- The journal still assumes a single writer, as stated in response 1.
- If the process dies after a failed rollback, the object stays visible until the store is
  next opened. The journal is kept so that the open removes it.
- The directory-group path (`_commit_group`) is unchanged by this round.
