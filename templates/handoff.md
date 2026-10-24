---
id: HANDOFF-YYYY-MM-DD-<slug>
date: YYYY-MM-DD
actor: <claude/<role> | codex/reviewer | owner> (<model/agent or person>)
work_status: <proposed | authorised | in_review | approved>   # status of the work this session touched
base_revision: <git sha>
head_revision: self       # a file cannot contain its own commit id; resolve with: git log -n1 --format=%H -- <this file>
work_commits: [<sha>, ...]   # earlier commits of this session, by id
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

## Completion block (harness-0.7 proposed, operating model §6.2 step 9)
| Field | Value |
|---|---|
| Branch and full SHA | |
| Pushed? PR link | |
| Received into `main`? | receipt commit, or "not received" |
| Next actor | owner / author / reviewer |
| Prompt for the next actor | include explicit prerequisites, e.g. "stop if commit X is not in `main`" |
