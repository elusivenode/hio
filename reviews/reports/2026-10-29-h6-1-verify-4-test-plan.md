---
id: VERIFY-2026-10-28-h6-1-4-TEST-PLAN
status: fixed_before_author_response
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0105-assign-h6-verification-4.md on main
reviewed_base: cd87bc0478e37620c776b200d7834b241f5c8ff6
reviewed_head: 41e0840224fa60b0c68f6db9860bc6facfe104ce
review_branch: review/h6-1-verify-4-codex
---

# Test plan: H6 verification round 4

Fixed before reading response 4 or an author handoff. OD-0105 and the `main` Assigned reviews row agree with the direct assignment. Public HTTPS `ls-remote` returned the assigned `phase-b/h6` head and the fixed `proposal/h6-option-b` revision; the base is an ancestor of the head. OD-0104 approves the amendment at that revision, but its application to the operating model and H6 activation are separate actions.

1. Inspect the base-to-head diff and receiver control flow. Reproduce F-VERIFY-2026-10-28-h6-1-3-1 in disposable local Git fixtures: refuse an index rewrite, interrupt after import/tag and before the `main` push, restart, and rerun idempotently. The successful output must disclose the partial index and list the refused lines verbatim. Check a dry run of the same restart state, the `Index-Diff: refused` trailer, and unchanged remote index. Probe inconsistent or forged recovery state and require a stop before `main` advances.
2. Check approved option B §5.6, `--without-index` and §5.12 against the head. Default refusal stops; an authorised flag permits a wholly omitted refused diff, while a valid Class N diff applies. Receipt never rewrites a finding state. Pending reconciliation reports exact bold verification outcomes. Recheck F-REVIEW-2026-10-28-h6-1-1 to -4: unsupported owner-status navigation, negated finding closure, duplicate assignment target, and blank-separated index parsing.
3. Recheck the original H6 safety paths where affected: fixed tip, inventory and hashes, assignment and `main` check tools, tag and `main` consistency stops, dry run without remote writes, and `main` publish only under `--publish`. Use local fixtures only; no real remote receipt.
4. Run `uv sync --frozen`, the full `uv run pytest -q` suite against the 512-test baseline, CI's exact `uv run ruff check .` and `uv run ruff format --check .`, and `git diff --check` on the assigned range. Record independent results and limitations.
5. After these checks, write a verification record with an exact bold per-finding outcome token, verdict, evidence and limits; add a reviewer handoff and index navigation row. Only `reviews/*.md` paths may be written. This runner leaves files uncommitted and unpushed for the hash-checked hiomux receipt.
