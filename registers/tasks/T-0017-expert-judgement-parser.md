---
id: T-0017
title: "Fix the expert-judgement parser's header detection after the first live run"
status: accepted   # OD-0146 at 4576ae5, merged into main
accepted_by: OD-0146
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex (REVIEW-2026-11-04-t0017-1)"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0145
base_revision: 0a2c0a12925fecae3c7de69e8d2e74d12411f98c
review_required: Codex (OD-0145), then owner acceptance
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0016 (accepted)]
  blocks: ["Authorisation B stage B-3: resuming the steps on the day"]
---

# T-0017: expert-judgement parser

> **Authorised by OD-0145.** The first live run (`41733292506`) failed `rba.expert_judgement` as `schema`: the live file opens with prose, and one prose cell holds both "date" and "type", so it was taken for the header.

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| P-1 | `parse_rba_expert_judgement`: the date column's cell must be exactly `date`, and the type column must be a different cell | the new test fails on the old code and passes on the new |
| P-2 | a synthetic fixture with the live layout: invented words and dates, no publisher text or values | `check_repo`; the existing fixture and tests unchanged |

## Exclusions

Any other parser, any URL, the schedule or the completeness check; the workflow; any dispatch or setting; committing the downloaded file or its values.

## Submission (filled by the implementer)

Branch `feat/t0017`, built by the orchestrator. The local copy of the live file parses to 466 flags, and no row is dropped. That count is the only thing kept from it. Submitting approves nothing.
