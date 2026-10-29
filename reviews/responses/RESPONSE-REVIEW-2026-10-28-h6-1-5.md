---
id: RESPONSE-REVIEW-2026-10-28-h6-1-5
author: claude/implementation-agent
findings: [F-VERIFY-2026-10-28-h6-1-4-1]
responds_to: VERIFY-2026-10-28-h6-1-4   # reviewer tip 1fc82bb0d511980f271c6f648b38e42db5ffb04a (tag reviews/VERIFY-2026-10-28-h6-1-4); receipt pending the owner's go-ahead
previous_submission_head: 41e0840224fa60b0c68f6db9860bc6facfe104ce
authorised_by: OD-0107, OD-0104, OD-0092
fix_commits:
  - a6e449b   # content comparison of an existing import (tools/hio_receive.py, tests), hiomux task W2, checked at a6e449b
test_commits: []
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-5.md
created_at: 2026-10-29
---

# Remediation response 5: a restart compares the existing import's content with the reviewer's evidence

> **This is the author's claim, not verification.** F-VERIFY-2026-10-28-h6-1-4-1 stays **open**. H6 is still
> unactivated. Option B is approved (OD-0104) and applied to `main` as harness-0.9b (OD-0106).

**The defect.** Without an `Index-Diff` trailer, the restart check compared only whether the import and the reviewer
had each changed `reviews/README.md`, not what they changed. A hand-built import with a false finding state passed and
was published.

**The fix (`a6e449b`).** For **every** existing import, with or without a trailer, `step_verify_existing_index` now
derives the expected README from immutable evidence alone. A shared `recompute_readme` applies the reviewer's diff
(`head..T`) at the import's first parent `P` and runs `check_index`. It **stops** when:
- **there is no trailer:**
  - the reviewer's diff fails 5.6 (or does not apply) at `P`;
  - the import's README blob differs from that result, or from `P`'s blob when the reviewer left the README alone;
- **there is a trailer:**
  - the import changes the README;
  - the reviewer did not modify the README;
  - the run lacks `--without-index`;
  - the recomputed refusal is empty or yields a different trailer;
- **in every case:** the import's changed paths (`P..import`) differ from the inventory's added files plus, only when
  applied, the README.

The round-1 disclosure behaviour is unchanged.

**Tests (six new, in `tests/test_hio_receive.py`):**
- `test_restart_stops_on_an_import_with_a_false_state_row_and_no_trailer`: the verifier's case. The run exits
  non-zero and remote `main` does not advance.
- `test_restart_stops_on_an_import_that_applied_the_refused_diff_without_a_trailer`.
- `test_restart_stops_on_an_import_whose_readme_differs_from_the_reviewers_diff`: a valid Class N change that is not
  the reviewer's.
- `test_restart_stops_on_an_import_that_changes_a_file_outside_the_inventory`.
- `test_restart_stops_on_an_import_that_changes_the_readme_the_reviewer_left_alone`.
- `test_restart_accepts_a_hand_built_import_that_equals_the_reviewers_diff_applied`: a positive control.

**Evidence:**
- `a6e449b` passed Claude's independent `hiomux check`: `check_repo`, trailers from `41e0840`, `uv run pytest -q`
  **518 passed**, `uv run ruff check .` and `uv run ruff format --check .`. It is integrated by fast-forward, so the
  integrated tool and tests are that commit.
- **The tests catch the defect:** with `a6e449b`'s test module on `41e0840`'s receiver, four new tests fail (4
  failed, 58 passed). The other two pass on the old code too: `…changes_the_readme_the_reviewer_left_alone` was already
  stopped there, and the positive control should pass.
- No existing test was changed or removed. No other tool changed.

**For the verifier:** please re-run your hand-built import probe, and try an import that differs from the expected
README by a single byte, and one whose parent is not the `main` it was cut from.
