---
id: HANDOFF-2026-10-24-s1a-remediation-1
date: 2026-10-24
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code session)
work_status: in_review (remediation submitted; verification not yet assigned)
base_revision: 6fe35cf6f85ec421ec6f8d67acc04134f2bdbd39   # main; receipt e55cc89 is an ancestor
head_revision: self       # resolve: git log -n1 --format=%H -- handoffs/2026-10-24-s1a-remediation-1.md
work_commits: [b9f7f50, 1c117e6, 3185443, 7076452, 6bbf562, 39d37da, d1edf1e]
work_card: T-0005 (S1a), OD-0023
---

# Handoff: S1a remediation of REVIEW-2026-10-24-s1a-1

> A dated snapshot. **Not a decision.** The claims are in
> [`reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md`](../reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md).

## Done

- **OD-0023 recorded** (`b9f7f50`).
- **Fix commits:**

  | Finding | Commit | Fix |
  |---|---|---|
  | 6 | `1c117e6` | atomic commits |
  | 3 | `3185443` | receipt integrity |
  | 5 | `7076452` | rebuild verifies the stored bytes |
  | 2 | `6bbf562` | class-specific approval |
  | 1 | `39d37da` | lineage-derived sources |

  Each finding's counterexample failed before its fix and passes after.
- **Drafts:** OBS-AMEND-Q001 and OBS-AMEND-Q002 (`d1edf1e`), proposed and not implemented.
- **This commit (the submission head):** the remediation response, the index's
  remediation-claim cells (state still `open`), T-0005, STATUS and this handoff.

## Tests and evidence

- **Checks at this commit:** `pytest` 199 passed (exit 0); `ruff check` 0;
  `ruff format --check` 0; `tools/check_repo.py` 0.
- **CI:** the run id and attempt are in the PR description.
- **Financial outputs:** `data.csv` bytes are identical to the reviewed head for all four
  datasets.

## Known limitations

See the response's "Residual risk" column:
- the API change (`source_ids` removed);
- the class-status representation (Q-005b);
- integrity is checked at selection time;
- the journal path assumes a single writer.

## NOT approved by this session

- No finding is closed or verified.
- S1a is not accepted.
- No standards change is approved.
- S1b is not authorised.
- The implementation is not merged.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `remediation/s1a-1` @ this commit (resolve as above; also stated in the PR description) |
| Pushed? PR link | yes; the author PR states `Submission-Head` |
| Received into `main`? | not received (an author PR merges only on the owner's instruction) |
| Next actor | **owner**: assign the Codex verification at the submission head; decide Q-001/Q-002 |
| Prompt for the next actor | Codex: "Verify REVIEW-2026-10-24-s1a-1 findings 1, 2, 3, 5 and 6 at submission head `<sha>` on `elusivenode/hio` (author PR #<n>). Stop if that SHA is not the PR head. Use a fresh worktree and branch `review/s1a-1-verify-1-codex` from that head; reproduce each original counterexample and the response's evidence; write VERIFY-2026-10-24-s1a-1-1 under `reviews/`; open a reviewer PR stating `Reviewed-Head: <sha>`. Findings 4 and 7 are policy questions, not remediation claims." |
