---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-4
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-6]
responds_to: VERIFY-2026-10-24-s1a-1-3   # commit ff0dd813927e0f4c568b17ff4b10ee246afc84de, record sha256 5fef6573502ac9dd0fbf20f8cee127e8a529b6a7bc1ad4742e7aa2d76d34ae1d (checked)
previous_submission_head: 21c81676a574ad57850bf5f78ba93387007bdbd8
authorised_by: OD-0025   # the F6 correction cycle; see "Authority" below
fix_commits: [5fbbd09ff322db53238d1d7723f87e7a7c90a37f]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-4.md
created_at: 2026-10-24
---

# Remediation response 4: F-REVIEW-2026-10-24-s1a-1-6

> **Author's claim, not verification.** F6 stays **open** until a verification record closes
> it. Responses 1–3 are unchanged.

## Authority

- OD-0025 disposed VERIFY-…-1 and -2 by name. It also says: "Do not require me to repeat these
  dispositions for each technical iteration within the same authorised scope."
- I read that as covering this round's record, VERIFY-2026-10-24-s1a-1-3, as preserved,
  owner-disposed evidence for the same F6 cycle. The record is not received into `main`.
- Before use I checked:
  - the record's commit and hash (`ff0dd81`, `5fef6573…ae1d`);
  - that the PR #2 head was `21c8167`.

  The fix is inside OD-0025's scope: the storage transaction only, with no standard, financial
  or scope change.
- If the owner reads OD-0025 more narrowly, this round awaits a one-line disposition. Nothing
  here is merged.

## The counterexample (VERIFY-2026-10-24-s1a-1-3)

- `_journal_claim` called `os.write` once and ignored a short count.
- In a child process, Codex's wrapper wrote half of `b`'s claim and returned that honest short
  count. The child was then killed after `os.link(b)`.
- The live store exposed `b`. Recovery skipped the truncated final line and deleted the journal,
  so `b` stayed visible after reopening, uncommitted, permanently.

I reproduced it as a test before fixing.

## The fix (`5fbbd09`, `src/hio/storage/objectstore.py`)

1. **A claim is complete and durable before its link.** `_journal_claim` keeps writing until the
   whole line is on disk, raises on zero progress, then fsyncs. Any failure raises before
   `os.link`, so the object is never linked, and the commit rolls back.
2. **A truncated final claim is checked, not assumed.** The journal header now names the intended
   keys (format 3).
   - A truncated final line is accepted only if no intended key holds an object the journal does
     not claim. That covers a crash while a claim was being written, before its link.
   - Otherwise `get`, `exists`, `list`, `snapshot` and opening the store all **raise**. Nothing is
     deleted, and the journal stays for inspection: the store fails closed.
3. **Earlier formats stay refused.** Journals in formats 1 (intended keys only) and 2 (format-3
   claims without intended keys) cannot support that check.

## Evidence

**Regression tests:** `tests/test_remediation_s1a_1_f6_round4.py`.

| Test | Before (`21c8167`) | After (`5fbbd09`) |
|---|---|---|
| Codex: short write of `b`'s claim, then a crash after `os.link(b)`; `b` invisible live and after reopen; every claim line complete | FAILED (`exists('catalogue/b')` true) | passed |
| A claim that cannot be completed fails before the link (`b` never linked) | FAILED (`b` linked; the child reached the crash point) | passed |
| Truncated journal plus an unclaimed object at an intended key: reads and open raise, nothing deleted, journal kept | FAILED | passed |
| Truncated journal with no unclaimed object: recovered | FAILED | passed |

- **Before:** 4 failed, `pytest` exit 1. The run used a worktree at `21c8167`, and I confirmed it
  imported that tree's module.
- **The injection is real.** The child writes a `.short-injected` marker when it shortens the
  write, and both child tests assert that marker exists.
  - I added the marker because the first draft's wrapper never matched. The fix passes a
    `memoryview` to `os.write`, and `bytes in memoryview` is element-wise, so it is always false.

**Retained, and passing:**
- the round-2 visibility, ownership and recovery-failure tests;
- the round-3 crash, torn-journal, legacy-journal, write-while-unresolved and normal-commit tests;
- the round-1 tests. The round-1 crash test now passes the intended keys to `_journal_begin`.

**Whole suite at `5fbbd09`:**
- `pytest`: 217 passed, exit 0;
- `ruff check`: 0;
- `ruff format --check`: 0;
- `tools/check_repo.py`: 0;
- `git diff --check`: 0.

**F1, F2, F3 and F5:** no change to their code; their tests pass.

**Financial output:** Codex's comparison probe is byte-identical between `21c8167` and `5fbbd09`,
and with the round-2 baseline (`cmp` exit 0).

## Residual limits

These are unchanged from response 3: a single writer only, and ownership by POSIX
`(st_dev, st_ino)` on one local filesystem. The fail-closed state (a truncated claim plus an
unclaimed object) needs a person to inspect it. With complete claims written before every link,
it should arise only if the filesystem misreports a write.
