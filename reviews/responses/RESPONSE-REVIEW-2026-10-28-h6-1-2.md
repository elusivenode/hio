---
id: RESPONSE-REVIEW-2026-10-28-h6-1-2
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-28-h6-1-2, F-REVIEW-2026-10-28-h6-1-3, F-REVIEW-2026-10-28-h6-1-4]
responds_to: VERIFY-2026-10-28-h6-1-1   # reviewer tip 505d498b801e9896efe6c2971bda9b666a72d68c (tag reviews/VERIFY-2026-10-28-h6-1-1); record blob d54590dcaa5bd6aeb62d9892956c431091423a98; received by OD-0098
previous_submission_head: ab0288fe57fb2ae9100c989142102445e5046bc5
authorised_by: OD-0092
fix_commits:
  - fb9b456   # F-3 and the ruff format fix (tools/hio_assign.py, tests), hiomux task H6A3, checked at dbb3dbd
  - e4fff98   # F-2, F-4 and the F-1-fix regression (tools/hio_receive.py, tests), hiomux task H6R3, checked at 56b3ca3
test_commits: []
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-2.md
created_at: 2026-10-28
---

# Remediation response 2: H6

> **This is the author's claim, not verification.** F-2, F-3 and F-4 stay **open**. F-1 was `verified_closed` by
> VERIFY-2026-10-28-h6-1-1. H6 is still unactivated.

**The principle this round** (from the verifier's three rejections): parse the structure exactly, and never search a
cell or a line for a word.

**Evidence:**
- Each fix commit passed Claude's independent `hiomux check`, and the integrated files are blob-identical to the
  checked commits.
- On the integrated head: **501 tests passed**; `ruff check .` and `ruff format --check .` pass (CI's exact
  commands); `check_repo` and the trailer check pass.
- Run against the round-1 tools (`ab0288f`), **exactly the 8 new tests fail** and the other 77 pass.
- No test was removed or renamed.

| Finding | Claimed fix | Tests (the verifier's counterexamples) |
|---|---|---|
| F-2 | An outcome cell supports a state only if it begins with exactly the bold token `**<state>.**` or `**<state>**`. A cell beginning with the bare word supports nothing ("verified_closed was NOT reached …") | `test_outcome_cell_counts_only_with_the_exact_bold_state_token` |
| F-3 | An assignment is inactive only if its status cell's **leading state token** is `received`, `withdrawn` or `superseded`. "assigned; not received" is active | `test_cli_status_with_inactive_word_but_active_leading_token_still_blocks` (four cases, through the CLI with `--apply`); `test_leading_inactive_token_with_suffix_does_not_block` |
| F-4 | A header-less run after blank lines continues the findings table when its rows have the table's cell count **or** the six-cell shape of the ADR-0012 rows | `test_header_less_run_after_blank_lines_continues_the_findings_table_with_six_cell_rows`; `test_real_index_adr0012_six_cell_row_accepts_a_class_s_transition` |
| F-1-fix regression | The accepted/waived/approved guard reads only state-bearing cells, never scope or prose. "Review whether the work was accepted by the owner" passes; an `accepted` status still fails | `test_forbidden_state_guard_reads_state_cells_never_scope_or_prose` |

**For the verifier (F-2):** requiring the exact bold token binds outcome tables to the existing record convention.
A plain-text `verified_closed` no longer supports a transition.
