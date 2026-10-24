---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-5
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-6]
responds_to: VERIFY-2026-10-24-s1a-1-4   # commit 873fc691ca61a2c3f96ef417e9202e3d59762d5a, record sha256 7d291a03941c4b4de1ae5eb93c102051d9611bbb6828a9166aa5c6d9df56ede2 (checked)
previous_submission_head: 4c1b565220218d9aa7cf799e0268b03a00e77bdb
authorised_by: OD-0025   # F6 correction cycle; record treated as owner-disposed as in response 4
fix_commits: [7cf2c01e2b1cdf4509f9170b980a332bd07553a8]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-5.md
created_at: 2026-10-24
---

# Remediation response 5: F-REVIEW-2026-10-24-s1a-1-6

> **Author's claim, not verification.** F6 stays **open** until a verification record closes
> it. Responses 1–4 are unchanged.
>
> - The record was checked before use: `873fc69`, hash `7d291a03…ede2`, and the PR #2 head was
>   `4c1b565`.
> - It is treated as owner-disposed evidence under OD-0025's per-iteration clause, as stated in
>   response 4. It is not received into `main`.

## The counterexample (VERIFY-2026-10-24-s1a-1-4)

- `get` checked the journal (`_unresolved()`) and only then opened the object.
- One reader paused between those two steps. Meanwhile the sole writer linked `b` and stayed
  unresolved. The reader then returned `b'b'`.
- `list` and `snapshot` had the same check-then-access shape.

## The fix (`7cf2c01`, `src/hio/storage/objectstore.py`)

**Publication point.** A journalled object is committed when its journal is removed after a
successful commit.

**Validate after opening, not before.** `get`, `exists`, `list` and `snapshot` follow these steps:
1. Open the object and `fstat` it.
2. For `get`, read the bytes.
3. While still holding the file open, check two things. If either fails, the object is not
   committed (`get` raises `FileNotFoundError`; the others omit it):
   - no unresolved journal claims that exact `(key, dev, ino)`;
   - the key still names that inode.

**Why this is enough.** The writer's ordering is already fixed: claim before link, and a
rolled-back object is removed before its journal is deleted. So a file the reader holds open is
in one of three states:
- **claimed and unresolved**, which the reader rejects;
- **committed**: no claim remains and the file is still at the key;
- **rolled back**: it is no longer at the key.

Holding the descriptor open keeps the inode allocated, so a later object cannot reuse it during
the check.

**Snapshot** skips an object that is rolled back after it was listed. **Fail-closed journals**
(a truncated claim with an unclaimed object) still make reads raise.

**No new concurrency contract.** There are no locks and no reader registration, and the
single-writer model is unchanged. This is the read side of the existing claim/journal protocol,
inside OD-0025's scope, so no escalation was needed.

## Evidence

**Regression tests:** `tests/test_remediation_s1a_1_f6_round5.py`. Each test runs one writer
thread and one reader thread on separate store instances. Events force the interleaving: the
reader is paused just before it first touches `catalogue/b`, the writer links `b` and pauses
with its journal unresolved, and then the reader finishes.

| Test | Before (`4c1b565`) | After (`7cf2c01`) |
|---|---|---|
| Codex: `get` paused before its read cannot return the uncommitted `b` | FAILED: returned `b'b'` | passed |
| `list` paused before enumerating | FAILED: listed `catalogue/b` | passed |
| `snapshot` paused before enumerating | FAILED: included `catalogue/b` (`3e23e816…`) | passed |
| `exists` paused before its check | passed (the old `exists` checked the file before the journal) | passed |
| A read overlapping a rollback: the reader holds `b` open, the writer rolls back and resolves, then the reader validates | FAILED (no such path) | passed |

- **Before:** 4 failed and 1 passed, `pytest` exit 1, in a worktree at `4c1b565` that imported
  its own module.
- **After:** 5 passed. **Stable:** 25 repeated runs, no failures.
- Each test asserts that its pause actually happened. For example, the rollback test's writer
  waits until the reader holds `b` open.

**Retained and passing:** the round-1 to round-4 tests (crash, short write, torn journal,
failed rollback, ownership, write while unresolved, normal commit).

**Whole suite at `7cf2c01`:**
- `pytest`: 222 passed, exit 0;
- `ruff check`: 0;
- `ruff format --check`: 0;
- `tools/check_repo.py`: 0;
- `git diff --check`: 0.

**F1, F2, F3 and F5:** no change to their code; their tests pass.

**Financial output:** Codex's comparison probe is byte-identical to `4c1b565` and to the round-2
baseline (`cmp` exit 0).

## Residual limits

- **Cost:** reads now open the object and list the journal directory. That directory is empty
  outside a commit, so the cost is negligible at S1a scale.
- **Unchanged:** a single writer; POSIX file identity on one local filesystem; manual inspection
  for the fail-closed journal state.
- **Direct filesystem access** bypasses the publication point. It is not a supported interface.
