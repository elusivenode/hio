---
id: VERIFY-2026-10-28-h6-1-6-TEST-PLAN
status: fixed_before_author_response
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0111-assign-h6-verification-6-and-hiomux-fix.md on main
reviewed_base: 5e1582934e1ef88198ff59ffd7b8c947c1ba693b
reviewed_head: 3d376ba11519a87dc5d802d96d3d75570c69c917
---

# Fixed test plan: H6 verification 6

Fixed before reading the author's response or handoff. Role: independent reviewer; H6 status: in_review, unactivated. OD-0111, its owner-message source, and the Assigned reviews row agree; the checkout is the assigned branch at the assigned head, the base is its ancestor, and public HTTPS `ls-remote` confirms both pinned branch heads. The proposed clarification is a consistency target, not an adopted rule. Governing rule: approved operating model §6.2 on `main`, amended by harness-0.9b.

1. **Finding F-VERIFY-2026-10-28-h6-1-5-1.** Inspect the assigned diff and trace all restart and publish paths. In a disposable local Git origin, recreate an unrelated local `main` commit before an otherwise plausible import, including a false finding closure. A `--publish` restart must stop without advancing remote `main`, and report the local commits. Repeat with a legitimate local unpublished import or merge. Test a tag-only recovery and a disposable unmerged receipt branch: the receiver must build its own import from freshly fetched remote `main`. Test a receipt already on remote `main`: it must inspect required content and state and make no new `main` push. Test rejected or altered import metadata and mismatched blobs as applicable. Test the final publication guard by moving remote `main` between construction and push: the receiver must stop without publishing its local commits. Check the exact set of commits it is willing to push.
2. **Earlier findings.** Compare the assigned diff with the verified closure evidence for F-REVIEW-2026-10-28-h6-1-1 through -4, F-VERIFY-2026-10-28-h6-1-3-1, and F-VERIFY-2026-10-28-h6-1-4-1. Re-run focused tests or independent probes for assignment status, duplicate assignment, index parsing and state-change refusal, refused-index disclosure, and existing-import content integrity. Judge these against approved §6.2, including option B's navigation-only import and step 5.12 reconciliation boundary.
3. **Proposed consistency target.** Compare behavior to `proposal/harness-0.9` at `6d3fe3c8916d7595e837f7097a722fc48cd65fe5`, §6.1: same-invocation construction from fetched remote `main`; automatic recovery only for pushed tag/no import and disposable unmerged receipt branch; stop on any local-ahead `main`; inspect-only remote-published imports; re-fetch and exact cut-point/commit-set guard before push.
4. **Baseline and hygiene.** Run `uv run pytest` for the assigned 523-test baseline; run CI's exact `uv run ruff check .` and `uv run ruff format --check .`; run `uv run python tools/check_repo.py` after adding review files. Record exact outcomes and any environment additions. Check the assigned diff for whitespace errors.
5. **Reporting.** Write a per-finding outcome table with exact bold tokens, identify new findings and limits, a verification record and reviewer handoff under `reviews/`. Do not edit author files, commit, push, open a PR, or change the finding index's state. Report sha256 for every added file so the runner can commit exactly those bytes.
