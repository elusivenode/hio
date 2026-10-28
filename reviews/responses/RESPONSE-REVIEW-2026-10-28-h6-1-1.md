---
id: RESPONSE-REVIEW-2026-10-28-h6-1-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-28-h6-1-1, F-REVIEW-2026-10-28-h6-1-2, F-REVIEW-2026-10-28-h6-1-3, F-REVIEW-2026-10-28-h6-1-4]
responds_to: REVIEW-2026-10-28-h6-1   # reviewer tip 731dfa264e1b15439430e967b4fabc1b4834c917 (tag reviews/REVIEW-2026-10-28-h6-1); record blob fa53f9bab846e88d2cd6d9f55a27234c11f12271, sha256 dbe55d80dd1969f8da06c8de3a0672b81747034aa465615d3d5f69235480f029; received by OD-0096 (merge 61c2a4a)
previous_submission_head: 9e07b8b1493a4b4dca2a7d1eb3cf6e7de3f8f33c
authorised_by: OD-0092
fix_commits:
  - 357556b   # F-3 (tools/hio_assign.py), hiomux task H6A2, checked at 7de2796
  - d975ed7   # F-1, F-2, F-4 (tools/hio_receive.py), hiomux task H6R2, checked at e807e75
test_commits: []   # each fix commit carries its own regression tests
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-1.md
created_at: 2026-10-28
---

# Remediation response 1: H6 (scripted assignment and receipt)

> **This is the author's claim, not verification.** All four findings stay **open** (`remediation_claimed` at most).
> Only Codex may verify closure, at a fixed head the owner assigns. H6 is still unactivated.

**How the fixes were made.** Sonnet workers in hiomux made the fixes under contracts that quote each finding
verbatim. Claude checked each commit independently (`hiomux check`: scope, repository checks, trailers and the
acceptance commands), integrated exactly the checked commits (blob-identical), and ran the full suite on the
integrated head: **490 passed**.

**Proof that the new tests reproduce the defects.** With the new tests at the integrated head and the two tools
reverted to the reviewed head `9e07b8b`, **14 new tests fail**. With the fixed tools they pass:
- 8 tests in `test_hio_receive.py`;
- 6 tests in `test_hio_assign.py`.

## F-REVIEW-2026-10-28-h6-1-1 (high): an unsupported `accepted` row can be received

**Claimed:** an added index row may never carry `accepted`, `waived` or `approved`. Those exist only as owner
ODs, which the receiver cites and never creates, so such rows are refused outright. A review row (Assigned or
received) must match the imported record's front matter: id, base, head, record path, and the status or verdict cell
compared with `verdict`. A word in prose no longer counts as support.

**Tests:**
- `test_check_index_refuses_accepted_waived_approved_rows_whatever_the_record_says`;
- `test_check_index_assigned_row_status_is_bound_to_the_record`;
- `test_check_index_verdict_in_a_rounds_row_is_the_outcome_not_a_substring`;
- `test_receive_publish_refuses_an_unsupported_accepted_assigned_row`: the reviewer's case through `--publish`
  against a bare origin.

## F-REVIEW-2026-10-28-h6-1-2 (high): a negated verification outcome can close a finding

**Claimed:** a Class S transition is allowed only when the imported `VERIFY-*` record states the outcome
affirmatively in its per-finding outcome table: a row whose first cell is exactly the finding id and whose second
cell begins with the state word (bold allowed), as existing verification records do. The transition's target state
must equal that outcome. Negated or quoted state words elsewhere never count.

**Test:** `test_class_s_needs_an_affirmative_outcome_row_for_that_finding` ("remains open; do not mark
verified_closed" is refused).

**For the verifier:** this binds verification records to their existing outcome-table convention. A `VERIFY-*`
record without that table cannot support any Class S transition.

## F-REVIEW-2026-10-28-h6-1-3 (medium): a second assignment for the same target is accepted

**Claimed:** `hio_assign.py` refuses any second **active** assignment for the same repository and head, whatever the
scope wording or review id. An assignment is inactive once its status cell marks it received, withdrawn or
superseded.

**Tests:**
- `test_same_head_same_scope_new_id_is_refused`;
- `test_cli_same_target_and_scope_exits_nonzero_and_leaves_readme`: the reviewer's case;
- `test_same_head_different_scope_is_refused`;
- `test_inactive_assignment_does_not_block_its_head`;
- `test_same_head_in_another_repository_is_not_a_conflict`.

**For the verifier:** "active" is judged from the status cell. This is the author's reading of §6.1, and Codex may
dispute it.

## F-REVIEW-2026-10-28-h6-1-4 (medium): valid transitions for later findings are rejected

**Claimed:** a run of rows with no header, separated from a findings table only by blank lines and with the same
column count, continues that table. A run with its own header stays a separate table.

**Tests:**
- `test_findings_table_continues_across_a_blank_separator_line`;
- `test_blank_separated_table_with_its_own_header_stays_a_separate_table`;
- `test_real_index_shape_accepts_a_class_s_transition_after_its_blank_line`: the real index shape, including a
  valid transition for a finding after the blank line.

## Not done here

- **The index's finding rows** are updated to `remediation_claimed` on `main` in a separate administrative commit.
- **Nothing is activated.** H6 still needs Codex's verification and the owner's approval at an exact revision.
