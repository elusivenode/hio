---
id: T-NNNN
title: <imperative, one line>
status: proposed          # proposed | authorised | in_progress | submitted_for_review | accepted | changes_required
owner: <who authorises and accepts: the owner>
assignee_role: <implementation engineer | quantitative researcher | documentation agent | ...>
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
authorised_by: null       # OD-NNNN (owner decision record); required before work starts
base_revision: null       # exact starting commit, set in the authorising OD
accepted_by: null         # OD-NNNN, after the required review gates
review_required: <independent (Codex) | owner only>
links: {adrs_governing_approved: [], adrs_context_proposed: [], specs: [], standards: [], findings: [], depends_on: [], blocks: []}
---

# T-NNNN: <title>

## Purpose and rationale
The investment-research or architecture outcome, and why it is needed now.

## Owner-authorised scope
- …

## Exclusions (explicitly out of scope)
- …

## Governing documents
Only *approved* ADRs and standards govern, with versions. List proposed ones separately, as
context.

## Environment and rights constraints
Credentials allowed; data sources allowed and their rights status; no `macsmsf` access unless stated.

## Acceptance evidence
| ID | Test | Evidence expected |
|---|---|---|

## Decision dependencies, open questions, blockers
- …

## Intended outputs and next approval gate
- …

## Submission (filled by the implementer)
Base..head revisions; changed files; evidence paths; handoff id.

## Review and acceptance
Review record ids; findings and their states (from `reviews/README.md`); the acceptance OD id.
