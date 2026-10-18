---
id: OD-0003
title: Owner instruction to implement the review branch and worktree protocol (T-0007)
decision: authorise_work
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: >-
    Claude Code chat, 2026-10-18. The owner asked "in terms of agentic workflow, where would you
    suggest Codex commits?", and after Claude's answer wrote "please implement ... I will advise
    Codex", attaching hio/docs/history/2026-10-18-directive-review-worktree-protocol.md.
  sha256: d191ab38ab88fc0a8b234d20102178fcb703d757a7c2039e827aefe02f037a78   # of the attached directive
  date: 2026-10-18
  quote: "please implement ... I will advise Codex"
applies_to:
  - path: hio/
    revision: bada9526342d62fc2776e8f71aedf26097ab65ac
related: {adrs: [HIO-ADR-0008], tasks: [T-0007], findings: []}
---

# OD-0003: implement the review worktree protocol

## Owner action

The owner explicitly instructed Claude to implement the attached directive's §9 harness
amendment, starting from `bada952`. The directive is marked "Proposed harness amendment for
owner adoption". It names ChatGPT among its roles, but its authorship is not stated. The
owner's instruction is the adoption.

## Scope and exclusions

**Scope:**
- minimal documentation in the operating model (§2.2, §6.1), the review index ("Who writes
  what"), and a short pointer in `AGENTS.md`;
- the templates the protocol needs;
- one lightweight validation script, `hio/tools/check_review_branch.sh` (directive §10.4).

**Excluded:**
- ADR statuses;
- application, financial or infrastructure code;
- HIO-S1;
- Codex's review record and its findings;
- performing a review.

## What this record does NOT do

- It does not approve HIO-ADR-0008 or the protocol as architecture. The protocol joins the
  *provisional* working protocol.
- It does not accept T-0006 or T-0007.
- It does not act on any A01 finding.
