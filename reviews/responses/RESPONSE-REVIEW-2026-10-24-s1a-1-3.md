---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-3
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-6]
responds_to: VERIFY-2026-10-24-s1a-1-2   # commit 9a94c3a8a68d9627b205c954065a9210db4c6aa3, record sha256 3fda0fd349bac50afc64a3663910aa3d186daeefad17b4bb1f5db1f774882c53 (checked)
previous_submission_head: 759ddf7df599c20675395982e97e7fbd6a6fd3af
authorised_by: OD-0025   # owner disposition of VERIFY-…-1 and -2; F6 correction cycle
fix_commits: [c9644615fe9d62911e36468ea47868efd11dfb57]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-3.md
created_at: 2026-10-24
---

# Remediation response 3: F-REVIEW-2026-10-24-s1a-1-6

> **Author's claim, not verification.** F6 stays **open** until a verification record closes
> it. Responses 1 and 2 are unchanged.
>
> - Both verification records were read with `git show`, and neither is received into this
>   branch.
> - Record hashes were checked before use. The owner corrected a mistranscribed hash for -2
>   (OD-0025) before I relied on it.

## The two counterexamples (VERIFY-2026-10-24-s1a-1-2)

1. **Failed rollback.** The setup:
   - `catalogue/` already exists;
   - `os.chmod(b)` fails after the link;
   - the rollback's `os.unlink(b)` also fails.

   At `759ddf7`, `commit()` raised, but the **live** store still returned `b'b'` from
   `get('catalogue/b')` and listed it. Only a reopen removed it.
2. **Ownership.** Another writer creates `b` before this transaction's `put(b)`, and the rollback
   of `a` fails. Recovery then removed `b`, because the journal held *intended* keys.

I reproduced both, independently, before writing the tests.

## The design (`c964461`, `src/hio/storage/objectstore.py`)

**Claims by file identity.**
- Before each `os.link`, the journal durably appends `{key, dev, ino}` for the temp file.
- `os.link` places that same inode at the key. So the object at a key belongs to the transaction
  only if its `(st_dev, st_ino)` matches the claim.
- Another writer's file at that key has a different inode, because both files exist at once
  when the collision happens.

**The required properties (OD-0025):**

| # | Property | How it holds |
|---|---|---|
| 1 | Unresolved objects are not observable | `get` raises `FileNotFoundError("object not committed")`; `exists` is false; `list` and `snapshot` omit them. This is computed from the journal on disk, so it holds for **every** open store, including one opened before a crash |
| 2 | Never remove another writer's object | rollback and recovery remove a key only if its identity matches a claim. They also remove the claimed temp file a crash leaves, which shares the inode |
| 3 | Durable evidence after a failed rollback | the journal is deleted only after every owned object is removed. Otherwise it stays, and opening the store raises until recovery finishes |
| 4 | Single writer kept | there is no locking and no concurrent transactions. A new journalled commit or `put()` first resolves any unresolved journal, and is refused if that cannot finish |
| 5 | Outputs unchanged | the release path, receipts and F1, F2, F3 and F5 code are untouched; the financial probe is byte-identical (below) |

**Hardening found while testing:**
- **Inode reuse.** On filesystems that reuse freed inode numbers (ext4), a retry written while a
  stale claim stood could receive the claimed inode. It would then be hidden, and removed on
  recovery. The "no write while unresolved" rule closes this.
- **Durability.** The parent directories of new links are fsynced before the journal is removed.
  The journal's removal is fsynced too, so a crash cannot resurrect the journal and roll back a
  committed transaction.
- **Journal integrity.** A claim opens the journal without `O_CREAT`, so it can never re-create a
  vanished journal without its header.
- **Corrupt journals.** A torn final claim line is ignored: claims are durable before their link.
  An intent-only journal (the round-1/2 format) is refused with an error rather than guessed at.

## Evidence

**Regression tests:** `tests/test_remediation_s1a_1_f6_round3.py`.

| Test | Unfixed source (`759ddf7`) | After (`c964461`) |
|---|---|---|
| Codex: failed rollback is invisible before reopen; reopen recovers | FAILED (`exists('catalogue/b')` true) | passed |
| Recovery that still fails: open raises; journal kept; nothing exposed | FAILED | passed |
| Codex: collision plus failed rollback keeps the other writer's `b` across reopen | FAILED (`a` visible) | passed |
| Intent-only journal refused; deletes nothing | FAILED (did not raise) | passed |
| Crash (child `os._exit`) after `b`'s link: invisible to a store opened before; reopen recovers | FAILED (`a` and `b` visible) | passed |
| Crash after `b`'s claim, before its link | FAILED (`a` visible) | passed |
| Torn final journal line ignored | FAILED (`JSONDecodeError`) | passed |
| No write while unresolved; a retry recovers, then commits | FAILED | passed |
| Committed objects stay visible; later commits work (baseline) | passed | passed |

- **Before:** 8 failed and 1 passed, `pytest` exit 1. The run used a worktree at `c0899fd`, whose
  `src/` is identical to `759ddf7` (`git diff --quiet` exit 0). I confirmed it imported that
  tree's unfixed module.

**Earlier tests adapted, without weakening their assertions:**
- `test_f6_an_interrupted_journalled_commit_is_rolled_back_when_the_store_is_reopened`
  (round 1) used the intent-only `_journal_begin(txn, keys)` with an unclaimed `put()`. That is
  exactly the semantics VERIFY-…-2 showed to be unsafe. It now simulates the crash on the claimed
  write path, with the same assertion.
- Both racing-writer tests now create the other writer's file directly. Calling this store's own
  `put()` in the middle of a transaction is concurrent use of one store, outside the single-writer
  model. The round-2 wrapper also passes through the new `claim` keyword.

**Whole suite at `c964461`:**
- `pytest`: 213 passed, exit 0;
- `ruff check`: 0;
- `ruff format --check`: 0;
- `tools/check_repo.py`: 0;
- `git diff --check`: 0.

**F1, F2, F3 and F5:** no change to their code. Their regression tests are unchanged and pass.

**Financial output:** Codex's comparison probe gives byte-identical output between the unfixed
source and `c964461` (`cmp` exit 0): the same four release IDs and `data.csv` SHA-256 and
lengths (2506, 2466, 2640 and 2834 bytes).

## Residual limits (stated, not hidden)

- **Single writer only.** Two live writers on one store are not supported. A second writer's
  write would try to recover the first writer's in-flight journal.
- **Ownership rests on POSIX file identity, `(st_dev, st_ino)`, on one local filesystem.** It
  holds because:
  - the claimed temp file exists until it is linked or rolled back;
  - committed objects are never deleted;
  - no write proceeds while a claim is unresolved.

  An object store without stable inode identity (for example S3) would need a different
  ownership token. That is outside S1a's local store.
- **Hidden objects stay on disk while recovery cannot finish.** They are unobservable through the
  supported interface, but direct filesystem access sees them.
- `_commit_group` (new-directory releases) is unchanged: it uses a hidden staging area and an
  atomic rename.
