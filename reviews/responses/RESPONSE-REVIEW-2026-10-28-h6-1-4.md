---
id: RESPONSE-REVIEW-2026-10-28-h6-1-4
author: claude/implementation-agent
findings: [F-VERIFY-2026-10-28-h6-1-3-1]
responds_to: VERIFY-2026-10-28-h6-1-3   # reviewer tip 740b13c0a9b47574dcc9f9fc4af7d189b8377360 (tag reviews/VERIFY-2026-10-28-h6-1-3); received by OD-0103
previous_submission_head: cd87bc0478e37620c776b200d7834b241f5c8ff6
authorised_by: OD-0104, OD-0092, OD-0100
fix_commits:
  - 01a4d2a   # restart disclosure of a refused index (tools/hio_receive.py, tests), hiomux task W1, checked at 01a4d2a
test_commits: []
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-4.md
created_at: 2026-10-29
---

# Remediation response 4: the refused-index disclosure survives a restart

> **This is the author's claim, not verification.** F-VERIFY-2026-10-28-h6-1-3-1 stays **open**. F-1 to F-4 are
> `verified_closed`. H6 is still unactivated. The option B amendment is now **approved** at `d26c2fa` (OD-0104); it is
> not yet applied to the operating model.

**The defect.** On a restart, the receiver found the existing import and skipped `step_import`, so the refusal flag
and the refused lines, held only by the failed attempt, were lost. A successful recovery summary said `received`
without `PARTIAL` or the refused lines.

**The fix (`01a4d2a`).** Whenever an import of T already exists (restart, idempotent rerun or dry run), the new
`step_verify_existing_index` rebuilds the disclosure from git, never from a flag:
- it reads the import commit's `Index-Diff:` trailer exactly (at most one, of the form `Index-Diff: refused (`);
- it reads, from git, whether the import changed `reviews/README.md` against its first parent;
- it checks consistency, and **stops** when:
  - a trailer is present and the import changes the README;
  - a trailer is present and the reviewer's diff does not modify the README;
  - no trailer is present and the import's README change disagrees with the reviewer's diff;
  - a trailer is present and the run lacks `--without-index` (a restart needs the same go-ahead);
  - the reviewer's diff passes 5.6 against the import's parent (nothing to refuse);
  - the recomputed `Index-Diff` trailer differs from the import's;
- it recomputes the refusal by applying the reviewer's diff to the import's parent and running `check_index`, then
  emits the **same** disclosure as the first attempt (shared code: INDEX DIFF REFUSED, the reasons, "refused lines,
  verbatim", the 5.12 sentence). `status_word` therefore shows `PARTIAL` on the final summary.

**Tests (three new, in `tests/test_hio_receive.py`):**
- `test_restart_after_a_failed_main_push_still_discloses_the_refused_index`: the verifier's case. A pre-receive hook
  refuses the first `main` push; attempt 1 returns 1. With the hook removed, attempt 2 returns 0 and a third
  idempotent run returns 0; both summaries carry `PARTIAL`, `refused lines, verbatim` and the refused lines; the
  remote README is unchanged byte for byte.
- `test_dry_run_after_the_import_exists_discloses_the_refused_index`.
- `test_restart_without_the_go_ahead_stops_after_a_refused_index_import`.

**Evidence:**
- `01a4d2a` passed Claude's independent `hiomux check` (`check_repo`, trailers from `cd87bc0`, `uv run pytest -q`
  **512 passed**, `uv run ruff check .`, `uv run ruff format --check .`). It is integrated by fast-forward, so the
  integrated tool and tests are that commit.
- **The tests catch the defect:** with `01a4d2a`'s test module on `cd87bc0`'s receiver, all three new tests fail
  (3 failed, 53 passed).
- No existing test was changed or removed. No other tool changed (`hio_assign.py`, `check_review_*`, `check_repo.py`
  are blob-identical to `cd87bc0`).

**For the verifier:** please reproduce the restart case independently, and check the consistency stops above,
including an import whose trailer was edited or that changes the README despite a trailer.
