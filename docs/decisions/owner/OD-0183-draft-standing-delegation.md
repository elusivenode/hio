---
id: OD-0183
title: "Owner authorises drafting a standing delegation to Claude (OD-0184) and the harness-0.10 amendment that permits it, in one PR"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-y-standing-delegation.md (owner's message, verbatim, with Claude's question)
  sha256: ddac93d2d4e756f166c0c86d2f6f69bc12b6b6928e1cf8298ec5026e678eb18e
  date: 2026-11-22
  quote: "y"
base_revision: 05f2dcd4782874d60f9f4bda4eb9eb07e0397bb9
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0061, OD-0076, OD-0089, OD-0139, OD-0181, OD-0184]}
---

# OD-0183: draft the standing delegation

The owner asked for autonomy for Claude as the trusted orchestrator, to maximise efficiency. The architect was consulted once (`20261122T074842-ask-e4cd`). It found that merging and Codex assignment can't be delegated by an OD alone, because operating model §1.1, §2.2 and §6.2 steps 0 and 1 require the owner's statement at the exact revision. It named self-merging as the riskiest delegated power and proposed the guard adopted in OD-0184.

**Authorised:** drafting, as `proposed`, OD-0184 (the delegation) and the harness-0.10 text in `docs/harness/operating-model.md` and `AGENTS.md`, in one PR.

## Not authorised

Either taking effect. Both take effect only when the owner approves the PR's exact head in a statement recorded by OD-0184's corrections.

## Corrections (append-only)
