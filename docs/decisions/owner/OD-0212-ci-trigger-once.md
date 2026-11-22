---
id: OD-0212
title: "Owner authorises drafting one CI workflow edit: run once per change; a local pre-push gate is installed. Merging the workflow change needs the owner's approval at its exact head"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-ci-trigger.md (owner's messages, verbatim, with Claude's report and question)
  sha256: ec5ee061a5935fcbeedfbf6477e6d8a9c2bf5995b34c38c37da6f9d5031536c3
  date: 2026-11-22
  quote: "Y"
base_revision: a63cb354328d66390b48ade5bf83a9c8798691f6
related: {adrs: [], tasks: [], findings: [], ods: [OD-0017, OD-0020, OD-0118, OD-0184]}
---

# OD-0212: CI runs once per change

**What the investigation found.** No flaky test and no CI fault; `main` has never failed. In the last 200 runs: 115 succeeded; 8 failed, from 5 commits, each a real mistake caught before merge (one broken test, three lint or format failures, one front-matter failure); 22 were cancelled as superseded; 49 skipped by design. Three things made it look worse:

| Cause | Effect |
|---|---|
| The workflow ran on both `push` and `pull_request` | every push to a pull-request branch ran twice, and each failure was reported twice |
| A newer commit cancels the run in progress, on every ref | 22 cancelled runs, shown as failures, three of them on `main` |
| No local check before a push | lint, format and tests first ran in CI |

**Authorised: drafting one edit to `.github/workflows/ci.yml`.**
- **Triggers:** `pull_request`; and `push` only for `main`, `review/**` branches and `reviews/**` tags, which have no pull request.
- **Cancellation:** a newer commit still cancels an older run on a branch or pull request; runs on `main` are never cancelled.
- The jobs, their steps, permissions and pinned actions are unchanged.

**Not delegated:** `.github/workflows/` is excluded from Claude's own merges (OD-0184 C). **The owner approves this PR at its exact head before it merges.**

**Also done, outside the repository:** a pre-push hook in this clone (`.git/hooks/pre-push`) runs ruff check, ruff format, the repository checks, the trailer check and the full suite when the checked-out commit is pushed. It is local, reversible, and can be skipped once with `HIO_SKIP_PREPUSH=1`.

**A consequence to know:** a branch pushed without a pull request, other than a reviewer's branch, no longer gets a CI run. Draft branches are checked by the local gate and by CI when their pull request opens.

## Not authorised

Any other workflow change; merging this change without the owner's approval at its head.

## Corrections (append-only)
