---
id: HIO-ADR-0008
title: Canonical knowledge, precedence and agentic harness
status: approved
approved_by: OD-0008   # at a82aa0d, blob fffb4be30556
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [all HIO work]
review_record: null
---

# HIO-ADR-0008: canonical knowledge, precedence and agentic harness

## Context

[OBS] Evidence from `macsmsf` (detail in [operating model §0](../harness/operating-model.md#0-evidence-from-macsmsf-what-to-keep-and-what-to-fix)):
- **What worked:**
  - a short rules file;
  - trigger-described skills;
  - ADRs;
  - review records with an explicit evidence method;
  - evidence tags.
- **What drifted:**
  - a 3,958-line append-only progress log whose status summary went stale;
  - several competing planning essays;
  - project status held in model memory;
  - a blocker recorded as real after it stopped being true (whole-fund MWR, per `CLAUDE.md`).

## Decision (proposed)

- **Precedence:** owner approvals > approved standards > approved specs > charter, architecture,
  roadmap and plan > STATUS and task cards > handoffs > everything else (never authoritative).
  See `AGENTS.md`.
- **Bounded current-state files.** `STATUS.md` holds current state only (≤150 lines). History
  goes into dated handoffs. The register is in the ADRs.
- **Every canonical file has front matter:** `id`, `status`, `owner`, `version`, `last_reviewed`,
  and supersession links.
- **Work happens through task cards; sessions end with handoffs.** Both are templated.
- **Research memory is a versioned register** (hypotheses, experiments), including failures and
  variant counts.
- **Owner decision records** (`docs/decisions/owner/`) evidence explicit owner actions:
  instruct (authorise work), accept, approve, waive. These are distinct actions, and git state
  is not approval. An explicit owner instruction authorises bounded work immediately; recording
  it is audit (harness-0.3). Findings follow
  `open → remediation_claimed → verified_closed | waived`: reviewer-closed, owner-waived only.
  There is one review index (`reviews/README.md`). See operating model §1.1, §3 and §6.1
  (harness-0.2).
- **Roles have separated duties.** No agent sets an approved or validated status, or certifies
  its own work.
- **The minimum viable harness** is defined in [operating model §9](../harness/operating-model.md#9-minimum-viable-harness-and-deferred-behaviours).
  Advanced agent behaviour is deferred.

## Consequences

- Chat-only decisions do not exist. A decision not in the repository is not a decision.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `fffb4be30556`). Edits after that commit record status only.

## Changelog

- 2026-10-18: created (85ef0fa).
- 2026-10-18: added OD records, finding lifecycle and the review index (T-0006). Status unchanged: proposed.
- 2026-10-18: separated instruct, accept, approve and waive; trailers are metadata only (T-0006 final correction). Status unchanged: proposed.
