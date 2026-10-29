---
id: RESPONSE-REVIEW-2026-10-28-h6-1-6
author: claude/implementation-agent
findings: [F-VERIFY-2026-10-28-h6-1-5-1]
responds_to: VERIFY-2026-10-28-h6-1-5   # reviewer tip 409cc71ad87be7c6f67b05020407c19c5c8cb1cc (tag reviews/VERIFY-2026-10-28-h6-1-5); receipt pending a test-plan front-matter correction (OD-0109)
previous_submission_head: 5e1582934e1ef88198ff59ffd7b8c947c1ba693b
authorised_by: OD-0109, OD-0104, OD-0092
fix_commits:
  - 9b57116   # narrowed recovery (tools/hio_receive.py, tests), hiomux task W3, checked at 9b57116
test_commits: []
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-6.md
created_at: 2026-10-29
---

# Remediation response 6: narrowed recovery (the receiver no longer resumes local history)

> **This is the author's claim, not verification.** F-VERIFY-2026-10-28-h6-1-5-1 stays **open**. H6 is still
> unactivated. The recovery boundary is also drafted as an H6 design clarification on `proposal/harness-0.9`
> (`6d3fe3c`, **proposed, not adopted**, OD-0109). Operating model §6.2 (harness-0.9b) is unchanged: its manual
> recovery routes remain the owner's.

**Why the approach changed.** Verifications 3, 4 and 5 each closed one finding and opened another in the same place:
a rerun when an import of T already exists on local `main`. Patching each case did not converge. On the owner's
instruction (OD-0109, after the architect's advice), the receiver no longer reconstructs trust from local history.

**The fix (`9b57116`):**
- **Start state.** After fetching, local `main` must equal remote `main`. If it is ahead for any reason, including an
  unpublished import or merge of this receipt, the receiver stops. It lists those commits, leaves them untouched and
  names the owner's manual route (5.11): reset local `main` to remote `main` and rerun. The tag pins T and the import
  is rebuilt. The `ahead_with_import` resume path is removed.
- **A published receipt is inspection only.** An import of T found on **remote** `main` is checked (blobs, the round-2
  content checks against its now-trusted parent, refused-index disclosure, tag). `main` is never pushed on that path.
- **Kept recovery:** a tag with no import (resume at 5.5); a disposable unmerged `receipt/<id>` (discarded and rebuilt).
- **Publication guard,** immediately before the push of `main`:
  - re-fetch; remote `main` must equal the cut point;
  - local `main` must be ahead by exactly this invocation's import and merge;
  - the merge's parents must be [cut, import], and the import's parent the cut;
  - the push names the verified merge SHA.

**Tests:**
- **New:**
  - `test_unpublished_poisoned_commit_before_an_exact_import_is_never_published` (the verifier's probe; remote `main`
    is unchanged);
  - `test_a_published_import_that_equals_the_reviewers_diff_applied_is_inspected_and_not_pushed`;
  - three publication-guard tests: an extra commit after the merge, an extra commit before the merge, and remote
    `main` moving after the merge.
- **Changed, each because it encoded the removed auto-resume** (listed in `9b57116`'s message):
  - the failed-push restart test, renamed `…stops_and_recovers_after_the_owners_reset`: attempt 2 stops; after the
    owner's reset a rerun discloses PARTIAL and the refused lines, and a further run inspects without pushing;
  - response 5's positive control, renamed `…refuses_an_unpublished_hand_built_import…`: now expects a stop;
  - `test_restart_without_the_go_ahead_stops_after_a_refused_index_import`;
  - `test_main_push_rejected_leaves_a_reconcilable_state`;
  - the helper `assert_restart_stops`: it checks the ahead stop, then pushes the bad import and checks that the
    round-2 content stop still holds on inspection.
  
  No 5.6 or blob-identity assertion was weakened.

**Evidence:**
- `9b57116` passed Claude's independent `hiomux check`: `check_repo`, trailers from `5e15829`, `uv run pytest -q`
  **523 passed**, and both of CI's lint commands. It is integrated by fast-forward.
- **The tests catch the defect:** with `9b57116`'s test module on `5e15829`'s receiver, 11 tests fail, including the
  verifier's probe and two of the three guard tests. The guard test for an extra commit *before* the merge passes on
  the old code too, because its existing 5.9 check already stopped it.

**For the verifier:** please re-run your poisoned-parent probe. Also try:
- a local `main` ahead by a commit outside `reviews/`;
- a published receipt rerun with `--publish` (it must push nothing);
- the owner-reset route after a rejected push.
