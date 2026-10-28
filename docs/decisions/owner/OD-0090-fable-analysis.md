---
id: OD-0090
title: "Owner allows Claude to engage Fable for analysis of challenging questions or decisions it has reservations about; advice only"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-fable-analysis.md (typed by the owner, verbatim)
  sha256: 796350c1321e6bae9276ddb58aa76101d69a60743104b49c4f717480de06a758
  date: 2026-10-28
  quote: "whenever you have a challenging question or have reservations about a decision or option, you are free to engage Fable for analysis."
base_revision: cf40cee
applies_to: []
related: {adrs: [], tasks: [], findings: [], ods: [OD-0081, OD-0089]}
---

# OD-0090: Fable for analysis

## What is authorised

Claude may engage **Fable** (Claude Fable 5.1, as a Claude Code subagent) to analyse a challenging question, or a
decision or option Claude has reservations about. This is a standing permission, at Claude's judgement.

## Conditions (Claude's reading; the existing rules apply unchanged)

- **Advice only.** Fable's analysis is collaborator advice (AGENTS.md rule 4). It approves, authorises and
  widens nothing, and never directs Codex.
- **Read-only.** Fable analyses; it does not edit the repository, run live operations, push, or touch MACSMSF.
  Licensed data and secrets never enter its brief.
- **Independence.** Fable is not an independent reviewer in the Codex sense, because it shares a vendor with
  Claude. It never replaces Codex's review or the solution architect's consultation (OD-0089).
- **Reported.** Claude tells the owner when Fable was engaged, what it was asked, and where its view differs
  from Claude's or the architect's.

## Not authorised

Any change to roles, standards, the harness or tooling.

## Corrections (append-only)
