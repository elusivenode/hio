---
id: OD-0068
title: "Draft harness-0.9 (context, knowledge and collaboration) as a proposal, with seed drafts of MAP.md and the findings index, and obtain a same-vendor dry-run review; nothing applied or approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-harness-0.9-instruction.md
  sha256: fcdbf8d11e9e893cc81d70a7d9fee72b80972db7dfdaabfea915f46d34a18f4d
  date: 2026-10-28
  quote: "yes, draft it.  then have fable perform and review"
applies_to:
  - path: docs/harness/operating-model.md
    revision: eb19ef760fe3f03d47882e4a1aa8ab46df01486e   # base: origin/main; harness-0.7.1 with correction 1
related: {adrs: [HIO-ADR-0008], tasks: [], findings: []}
---

# OD-0068: draft harness-0.9 as a proposal

## Owner action

The owner asked for an assessment of the agentic workflow, with long-term context and alignment
for Claude and Codex as the goal ("I am open to trying different patterns to maximised context,
knowledge gaining and sharing and collaboration"). After the assessment the owner instructed:
"yes, draft it. then have fable perform and review".

## Scope and exclusions

Authorised, documentation only, on branch `proposal/harness-0.9` cut from `eb19ef7`:
- the decision package `docs/decisions/harness-0.9-proposal.md` (`proposed`);
- seed drafts `MAP.md` and `knowledge/findings.md` (`proposed`; navigation only, no authority);
- an open-decisions entry and index rows;
- a review by a Claude Fable 5.1 sub-agent. Under operating model §10 it is a same-vendor
  **unverified dry run**: advice, not an independent review.

Excluded: any edit to `AGENTS.md`, `STATUS.md`, `operating-model.md`, templates, tools, hooks or
CI; any merge to `main`; any Codex assignment.

## What this record does NOT do

It approves no part of harness-0.9 and no seed file. It does not change the approved harness
(harness-0.7.1 with correction 1). The Fable review does not satisfy any independent-review gate.
T-0009 remediation (OD-0067) is unaffected and has not started.
