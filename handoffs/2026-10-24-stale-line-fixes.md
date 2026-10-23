---
id: HANDOFF-2026-10-24-stale-line-fixes
date: 2026-10-24
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0014)
base_revision: 4a994d3bc3214bfcc54ce3ac1961da299b114ac5
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-24-stale-line-fixes.md
work_commits: []
work_card: T-0002, T-0003, T-0007 (text corrections only)
---

# Handoff: stale-line fixes (OD-0014)

> A dated snapshot. **Not a decision.**

## Bootstrap check

- `docs/hio-a01-baseline` was at `4a994d3`, as expected.
- `macsmsf` `main` has moved from `1502ab8` to `5f6b8b5` (the year-end close and distribution
  claim fixes). Those commits touch nothing under `hio/`, nothing in the T-0004 files and
  nothing in HIO-001. Both this branch and `docs/hio-001-boundary-c1` still merge cleanly onto
  `main` (`git merge-tree`).
- No `review/t0004-codex` branch exists, so REVIEW-2026-10-18-t0004 has not been received. A
  leftover worktree folder, `/private/tmp/macsmsf-t0004-target`, holds only empty directories
  dated 2026-10-23, and git lists it as `prunable`. I did not touch it.

## Done

- **Owner instruction archived** verbatim (`docs/history/2026-10-24-owner-stale-line-fixes.md`)
  and recorded as **OD-0014**. Indexes updated.
- **`STATUS.md`:** the *Owner decision records* row now covers OD-0001…0014.
- **T-0002 and T-0003:** the front-matter comment "execution not yet started" is replaced.
- **T-0007 line 60 (criteria 1–2):** recorded as a later edit, with a new *Later edits* section
  that quotes the accepted text. The accepted version stays at `b48f83c` (OD-0004).
  - **Correction to the bootstrap report:** on re-checking, "fresh-session test is pending" is
    **still true**. T0007-PILOT and VERIFY-2026-10-18-a01-1 were both assigned directly in the
    Codex chat, not found from the index. What was stale was the missing context. The line now
    gives it, and names REVIEW-2026-10-18-t0004 as the first index-assigned review.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Each replaced string occurred exactly once | assertion in the edit script | passed |
| OD-0014 source hash | `shasum -a 256 docs/history/2026-10-24-owner-stale-line-fixes.md` | `4e237884…4eae8c` |
| Earlier reviews were chat-assigned | `assignment:` front matter of `REVIEW-2026-10-18-t0007-pilot.md` and `VERIFY-2026-10-18-a01-1.md` | both "owner direct assignment/request in Codex chat" |

## Other stale lines found (NOT fixed; outside OD-0014's scope)

- **T-0007 line 29:** "HIO-ADR-0008 remains proposed, and the protocol stays provisional." Both
  have been approved since OD-0008.
- **T-0007 line 61 (criterion 3):** "Not yet exercised by Codex." Codex exercised the worktree
  and review-branch protocol in T0007-PILOT (`e36dd08`, received at `385389d`) and VERIFY-a01-1
  (received at `a82aa0d`).
- **T-0007 front matter:** `adrs_context_proposed: [HIO-ADR-0008]` (now approved).
- **T-0006 line 61:** "**None is approved.** The provisional working protocol … applies."
  T-0006 is an accepted card, so the same later-edit treatment would apply.

## NOT approved by this session

Nothing is approved, accepted, authorised, waived or closed. T-0007's acceptance is unchanged.
No status changes. No S1a, no live data, no vendor contact, no merges, nothing outside `hio/`.

## Next authorised action

None is pending under OD-0014. The owner decisions in `STATUS.md` are unchanged. Also needed:
whether to fix the four further stale lines above.
