---
id: HANDOFF-YYYY-MM-DD-<slug>
date: YYYY-MM-DD
actor: <claude/<role> | codex/reviewer | owner> (<model/agent or person>)
work_status: <proposed | authorised | in_review | approved>   # status of the work this session touched
base_revision: <git sha>
head_revision: <git sha, or "uncommitted: see changeset">
work_card: T-NNNN
---

# Handoff: <slug>

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

## Changed files
`git diff --stat <base>..<head>`, summarised.

## Done
- …

## Tests and evidence
| Claim | Method (command, test id, query) | Result |
|---|---|---|

## Known limitations and not verified
- …

## Open findings (from `reviews/README.md`)
- … (or "none recorded")

## Assumptions made
- …

## Conflicts found between documents
- … (and what was done about each)

## NOT approved by this session
An explicit list: nothing an agent does approves, authorises, accepts, waives or closes.

## Next authorised action
The single next action, the record that authorises it (OD id), and its preconditions. If
nothing is authorised, say so, and name the decision that is needed.
