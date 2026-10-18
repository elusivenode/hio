---
id: T-0006
title: Refine the HIO collaboration harness before the Codex A01 review (documentation only)
status: submitted_for_review
owner: owner
assignee_role: documentation agent (Claude)
created_at: 2026-10-18
updated_at: 2026-10-18
authorised_by: OD-0001    # PROPOSED, not confirmed by the owner (see the OD record)
base_revision: 85ef0fa8821e5f538b739c5fe000f3f63d3bfac1
accepted_by: null
review_required: independent (Codex), as part of the A01 review
links: {adrs_governing_approved: [], adrs_context_proposed: [HIO-ADR-0008], specs: [], standards: [], findings: [], depends_on: [], blocks: [Codex A01 review]}
---

# T-0006: harness refinement

## Purpose and rationale
Prevent three failure modes before independent review starts:
- **authority laundering:** an unconfirmed statement treated as approved;
- **review laundering:** an author closing its own findings, or a reviewer accepting the
  author's summary;
- **migration amnesia:** losing provenance when `hio/` moves to its own repository.

Brief: [`../../docs/history/2026-10-18-directive-harness-refinement.md`](../../docs/history/2026-10-18-directive-harness-refinement.md).

## Owner-authorised scope (per OD-0001, pending confirmation)
Minimal edits to HIO planning, harness and reviewer documentation within `hio/`.

## Exclusions
- code; infrastructure;
- `macsmsf` application changes;
- HIO-001 or HIO-S1 activation;
- roadmap changes;
- ADR status changes;
- claims of Codex endorsement.

## Governing documents
**None is approved.** HIO-ADR-0008 (proposed) is context only.

## Acceptance evidence
| ID | Test | Evidence expected |
|---|---|---|
| H1 | the authority rules (git ≠ approval; OD records; stop on conflict; self-declaration) are in AGENTS.md, with detail in the operating model | AGENTS.md "Authority rules"; operating model §1.1 |
| H2 | lifecycles for OD, work card, finding and handoff, with waiver rules | operating model §3; templates |
| H3 | a single review index exists, linked from AGENTS and STATUS | `reviews/README.md` |
| H4 | role-specific bootstrap for Claude and Codex | AGENTS.md; operating model §2.1–2.2 |
| H5 | the advice → owner → Claude → Codex → owner chain | operating model §5.1; task-card template |
| H6 | a migration continuity checklist | operating model §8.1 |
| H7 | cold-start test prompts, with an honest record of what was and was not run | operating model §10; handoff |
| H8 | no ADR status, roadmap or `macsmsf` file changed | `git diff --stat 85ef0fa..HEAD` |

## Submission
See [`../../handoffs/2026-10-18-harness-refinement.md`](../../handoffs/2026-10-18-harness-refinement.md).

## Review and acceptance
Pending:
- owner confirmation of OD-0001;
- the Codex A01 review (which includes this change);
- an acceptance OD.
