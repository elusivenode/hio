---
id: OD-0015
title: "Owner instruction: fix the further stale lines in the accepted T-0006 and T-0007 cards"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-24-owner-further-stale-lines.md (the owner's chat message, verbatim)
  sha256: 84743d2e1f33e9556ebcd6de09a7a3e0cbc349adb98496512d3fe04f1b9b57cb
  date: 2026-10-24
  quote: "yes, fix the stale lines and then advise best next step to advance"
applies_to:
  - path: hio/
    revision: 73512cf
related: {adrs: [HIO-ADR-0008], tasks: [T-0006, T-0007], findings: []}
---

# OD-0015: fix the further stale lines

## Owner action

Fix the four stale lines listed in `handoffs/2026-10-24-stale-line-fixes.md`, and advise the
best next step. The same message also answered "yes" to committing the OD-0014 work as one
commit (`73512cf`).

## Scope and exclusions

- T-0007: line 29 (HIO-ADR-0008 and the protocol's status), criterion 3 (Codex exercise of
  §6.2) and the front-matter `links` field.
- T-0006: the *Governing documents* line, and its front-matter `links` field, which makes the
  same claim ("HIO-ADR-0008 proposed"). The handoff did not list that field separately; it is
  included so the card does not contradict itself.
- Each is recorded as a later edit on the accepted card, quoting the accepted text. Acceptance
  stays at the original revisions (T-0006: OD-0007 at `35c9821`; T-0007: OD-0004 at `b48f83c`).
- Bookkeeping: this record, the OD and history indexes, and a handoff.

## What this record does NOT do

- It does not re-accept T-0006 or T-0007.
- It does not change any approval, verification or task status.
- It does not authorise S1a, live data operations, vendor contact or merges.
