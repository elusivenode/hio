---
id: HANDOFF-2026-10-25-adr0012-remediation
date: 2026-10-25
actor: claude/implementation-agent (Claude Sonnet 5.5)
work_status: in_review   # ADR-0012 proposed, revision 2; remediation claimed; harness-0.7.1 pushed for review; nothing approved
base_revision: 6fbec1aa064551d7aa505cf3008a677acfd68e73
head_revision: self       # = the PR #4 submission head; resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md
work_commits: [a3976bf30e7d69a2dae183aa9aec8a1f891492f6, bc939f778066d96ebafc2364640f9ebf0457d09e]
work_card: T-0005
---

# Handoff: ADR-0012 remediation (revision 2) and harness-0.7.1 push

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Done
- **B:** harness-0.7.1 revision 2 verified (full id, descends from `main`, documentation-only,
  operating model identical to `main`, checks pass in a clean worktree) and **pushed** at
  `9878dd0bad6fa61a0ef8519a6d47da7198b08526`. No PR opened.
- **A:** `main` (receipt `6fbec1a`) merged into PR #4's branch (`a3976bf`); the fix is
  `bc939f7` (ADR-0012 revision 2); the response, OD-0051, Q-013 and the indexes are in the
  submission commit.

## Remediation in one paragraph
A documented schedule is an expectation, not evidence. A vintage is placed by an evidenced
instant, else by the first capture that contains it (the reading accepted S1a code already
applies to revisions), else by the fail-closed `schedule_only`. Finality needs a verified
post-window check recorded in an additive attempt record, because `capture()` writes nothing for
an unchanged re-fetch. SOFR and the SOFR Index, and AONIA and the TRI, are checked independently.

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| S1a code, tests, tools, specs, `.github`, lockfile unchanged | `git diff --stat 084154c HEAD -- …` | empty |
| Standards, harness-0.7, ADR-0010, `registers/`, imported review records unchanged | `git diff --stat main -- …` | empty |
| §1, §2, §4.1, §4.4–§4.6, §7 and *Approval* identical to the reviewed head | section-by-section comparison against `1d68da3` | identical |
| Repository checks | `check_repo`, `ruff check`, `ruff format --check`, `pytest` | PASS (0 problems); clean; 63 files formatted; 278 passed |

## Known limitations and not verified
- Written, not built: the attempt records are specified in a proposal.
- Not evidenced: NY Fed header semantics; the SOFR Index correction rule (taken from the review
  record, not re-read). Both need an owner-approved fetch, so they are S1b-1 gate items.
- A commit authored before the attribution update (`8d63b99`, in the harness branch) carries the
  earlier co-author line. It is left as committed.

## Escalated, not decided
- **Q-013:** the capture-instant reading of `captured_on_schedule` for a first capture.
- The release-manifest schema, if finality evidence ids cannot be release inputs without
  amending the releases standard.

## NOT approved by this session
- HIO-ADR-0012; harness-0.7.1; the push-only pilot; any finding closure; any right; S1b; the
  merge of PR #4.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/adr0012-staged-s1b-proposal` @ the submission head (stated in the report); `docs/harness-0.7.1-review-receipt` @ `9878dd0bad6fa61a0ef8519a6d47da7198b08526` |
| Pushed? PR link | both pushed; PR #4 (https://github.com/elusivenode/hio/pull/4) carries the new `Submission-Head` in a comment. No PR for the harness branch |
| Received into `main`? | no |
| Next actor | **owner**, to confirm and issue the two assignments (OD-0051 Packages A and B) |
| Prompt for Codex | per the owner's issued assignment. Prerequisite: the branch tip equals the head named in the assignment; stop otherwise |
