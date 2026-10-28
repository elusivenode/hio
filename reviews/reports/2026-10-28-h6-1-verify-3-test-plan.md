---
id: VERIFY-2026-10-28-h6-1-3-TEST-PLAN
status: fixed_before_author_response
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0102-assign-h6-verification-3.md on local main
reviewed_base: 5b9e49cae02da18fd019cbf4486760306bab098e
reviewed_head: cd87bc0478e37620c776b200d7834b241f5c8ff6
review_branch: review/h6-1-verify-3-codex
---

# Test plan: H6 verification round 3

Fixed before reading the author's response or handoff. The owner statement in
`docs/history/2026-10-28-owner-assign-h6-verify-3.md`, OD-0102 and the local `main`
Assigned reviews row agree. Public HTTPS `ls-remote` returned the assigned head for
`phase-b/h6` and `d26c2faca78fc40dc409ff53c872cb172e918d7e` for
`proposal/h6-option-b`; the base is an ancestor of the head. No competing owner assignment
was found in the index or the owner records inspected. The approved operating model on
`main` is the current contract; the option B amendment at the fixed proposal SHA is a
draft consistency target under OD-0100, not approved or activated.

1. Compare the fixed base and head. Inspect the receiver's option B changes and tests,
   then the response as an unverified claim. Confirm that receipt never writes an existing
   finding state; Class N navigation rows are checked against imported immutable records;
   duplicate ids, non-open added findings, forbidden status cells and arbitrary changes stop.
   Independently probe a contradictory VERIFY outcome and an attempted Class S closure in
   dry run and publish fixtures.
2. Compare implementation with the draft's full §5.6, `--without-index`, §5.12 and
   verification-row wording. A refused diff must stop by default; with the flag it must be
   omitted wholly, listed verbatim in the summary, and produce the required import trailer.
   A valid diff must still apply. Reporting must identify every stated VERIFY outcome that
   the `main` index does not show, including a missing row or conflicting outcome, without
   changing state. Probe partial receipt and restart.
3. Recheck the original review's nine failure classes using independent disposable Git
   fixtures: moved tip, wrong head, extra and missing files, disallowed path, hash mismatch,
   duplicate or conflicting receipt, incorrect index change, stale target and partial failure.
   Check dry run leaves remote refs unchanged; `main` requires `--publish`; the tool uses
   `main`'s scope, assignment and repository checks; final recheck and recovery still hold.
   Recheck previously verified F-1, F-3 and F-4 for regression, without reopening them by
   inference.
4. Run `uv sync --frozen` and the full `uv run pytest -q` suite against the 509-test
   baseline; run CI's exact `uv run ruff check .` and
   `uv run ruff format --check .`, plus `git diff --check` on the assigned range. Record
   versions, counts, failures and fixture limitations. Do not read source datasets or write
   to a real remote.
5. Write a verification record with an exact bold per-finding outcome token, scope evidence,
   verdict and limits; a reviewer handoff and index navigation row. Do not change any existing
   finding state, approve the draft, activate H6, commit, push or open a PR in this runner.
