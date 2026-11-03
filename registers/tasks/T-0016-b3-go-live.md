---
id: T-0016
title: "B-3 go-live PR: set LIVE_AUTHORISATION, configure the four approved URLs, move the capture workflow into .github/workflows, and update the tests that pin the disabled state"
status: authorised
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex (REVIEW-2026-11-03-t0016-1)"
created_at: 2026-11-03
updated_at: 2026-11-03
authorised_by: OD-0143
base_revision: 5c68d6c529d946009172cee3bf30c06a1481dd07
review_required: Codex (OD-0143 item 4), then owner acceptance
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0010 (accepted), T-0013 (accepted), T-0015 (accepted)]
  blocks: ["Authorisation B stage B-3: the steps on the day"]
---

# T-0016: the go-live PR

> **Authorised by OD-0143 item 4**, under `docs/evidence/S1B1-go-live-package.md` at `3cee431`. Merging this PR arms the schedule; the `capture` reviewer rule holds it until the package's step 8.

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| G-1 | `LIVE_AUTHORISATION = "OD-0143"` in `src/hio/jobs/s1b1_capture.py` | a test pins the value, and that the OD file exists |
| G-2 | the four approved URLs on `PUBLICATIONS`, exactly as in the package | a test pins all four and the publication set; `_default_urls` returns them |
| G-3 | `infra/workflows/s1b1-capture.yml` moved to `.github/workflows/s1b1-capture.yml`; its name and "disabled" comments corrected; its triggers, permissions, pins and steps unchanged | the schedule test against the moved file; a test that it is the only scheduled workflow |
| G-4 | the tests that pin the disabled state updated; the refusal stays tested, with the constant patched to `None` | full suite; `ruff`; `check_repo` |

## Exclusions

Any other change to the capture path, the completeness check, the schedule or the parsers; any dispatch, Azure or GitHub setting change; any request to a data URL.
