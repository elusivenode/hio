---
id: OD-0131
title: "Owner instructs merging PRs #37 (B-2 plan), #38 (base-camp definition) and #39 (free-source rights rows) into main as proposals; nothing approved; the owner asks Claude to set the pace"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-merge-proposals.md (owner's message 5, verbatim, with Claude's decision put)
  sha256: aa78ed9d4a8d26140ad525e4e871e5ed9c5e7a5aba5e72cd0d6c4d8c47905796
  date: 2026-10-29
  quote: "yes.  pick the pace here.  we can make any adjustments going forward as needed."
applies_to:
  - path: plan/b2-probe
    revision: b825551
  - path: proposal/base-camp
    revision: 034f60b
  - path: research/free-history-rights
    revision: f59b797
related: {adrs: [], tasks: [T-0012, T-0013], findings: [], ods: [OD-0130]}
---

# OD-0131: merge the base-camp proposals

1. **Merge** PRs #37, #38 and #39 at the heads above into `main`. Each document keeps its `proposed` or `draft` status.
   Merging approves nothing (AGENTS.md rule 1).
2. **Pace.** The owner asks Claude to set the pace. Claude reads this as permission to sequence the authorised work
   and put decisions as they come due, without waiting to be asked. It grants no new authority: each approval,
   acceptance, apply, dispatch or purchase is still a separate owner yes.

The owner added the local permission rule `Bash(gh pr merge *)` (`/permissions`, project local settings, not
committed), so Claude can merge PRs the owner has instructed.

## Not authorised

Merging #40 (T-0013) before its acceptance or review decision; B-2; adopting the base-camp definition; any rights
verification.

## Corrections (append-only)
