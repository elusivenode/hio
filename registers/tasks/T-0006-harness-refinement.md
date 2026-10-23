---
id: T-0006
title: Refine the HIO collaboration harness before the Codex A01 review (documentation only)
status: accepted
owner: owner
assignee_role: documentation agent (Claude)
created_at: 2026-10-18
updated_at: 2026-10-24
authorised_by: [OD-0001, OD-0002]   # owner instructions: the original (ambiguity recorded) and the final correction
base_revision: 85ef0fa8821e5f538b739c5fe000f3f63d3bfac1
accepted_by: OD-0007                 # accepted as completed work at 35c9821f805955914b05991c1c075b8cb3e082b5
review_required: independent (Codex), within the A01 review, once the owner assigns it
links: {adrs_governing_approved: [], adrs_context_proposed: [], adrs_context_approved: [HIO-ADR-0008], specs: [], standards: [], findings: [], depends_on: [], blocks: [Codex A01 review assignment]}
---

# T-0006: harness refinement

## State history (truthful; append-only)

| Date | State | Revision | Basis |
|---|---|---|---|
| 2026-10-18 | authorised, then in_progress | from `85ef0fa` | OD-0001: the owner sent the brief by file path. **Whether that was an explicit instruction was ambiguous** (see OD-0001) |
| 2026-10-18 | submitted_for_review | `72d1e56`, `23ad27f` | harness-0.2; Claude dry-run cold-start tests (unverified) |
| 2026-10-18 | changes requested by the owner, then in_progress | from `23ad27f` | OD-0002: the owner directive, based on a Codex focused analysis that Claude has not seen. That analysis was **not** the A01 review and granted no approval |
| 2026-10-18 | **submitted_for_review** | the head named in the latest handoff | harness-0.3 corrections 1–6 |
| 2026-10-18 | **accepted** as completed work | `35c9821` | OD-0007: the owner's statement (the harness was later revised under T-0007) |

**Statement of state as at `35c9821`** (historical; superseded on 2026-10-18 by OD-0007, which accepts T-0006, and by OD-0008, which approves HIO-ADR-0008):
- **not accepted**;
- **HIO-ADR-0008 and all A01 ADRs remain proposed**;
- **no Codex review is assigned.**

## Purpose and rationale

Prevent four failure modes, without enlarging the harness:
- **authority laundering:** an unconfirmed statement treated as approved;
- **review laundering:** an author closing its own findings, or a reviewer accepting the
  author's summary;
- **migration amnesia:** losing provenance when `hio/` moves to its own repository;
- **gate confusion:** treating authorisation, acceptance and approval as one step.

Briefs:
- [`../../docs/history/2026-10-18-directive-harness-refinement.md`](../../docs/history/2026-10-18-directive-harness-refinement.md);
- [`../../docs/history/2026-10-18-directive-t0006-final-correction.md`](../../docs/history/2026-10-18-directive-t0006-final-correction.md).

## Owner-instructed scope
Documentation-only edits to the HIO harness, task and decision records, and the review index,
within `hio/`.

## Exclusions
- code; infrastructure;
- `macsmsf`;
- HIO-001 and HIO-S1;
- roadmap or architecture rewrites;
- ADR status changes;
- accepting T-0006;
- closing or waiving findings;
- claims of Codex endorsement.

## Governing documents
At acceptance, none was approved: the provisional working protocol (operating model §1.1)
applied, and HIO-ADR-0008 was context only. HIO-ADR-0008 and the protocol have since been approved (OD-0008 at `a82aa0d`; harness-0.6 by OD-0012). _(Later edit, OD-0015; see below)_

## Acceptance evidence (for the owner and the reviewer, not self-certified)

| ID | Test | Where |
|---|---|---|
| H1 | instruct, accept, approve and waive are distinct owner actions; transcription is audit only | AGENTS.md rules 2–3; operating model §1.1 |
| H2 | the OD, work card, finding and handoff lifecycles; waivers preserve findings | operating model §3; templates |
| H3 | one review index, with *Assigned* and *Candidate* tables kept separate | `reviews/README.md` |
| H4 | role-specific bootstrap; the reviewer answers "No review target has been assigned" when none is | AGENTS.md; operating model §2.2 |
| H5 | advice → adoption → authorisation chain | operating model §1.1, §5.1 |
| H6 | migration continuity checklist | operating model §8.1 |
| H7 | the state-aware cold-start test; the fresh Codex run remains **pending** | operating model §10; latest handoff |
| H8 | `HIO-Actor` is metadata only; the provenance classes are distinguished | operating model §6.1 |
| H9 | no ADR status, roadmap or `macsmsf` file changed | `git diff --stat 85ef0fa..<head>` |

## Submission
See the latest handoff in `hio/handoffs/` for this task.

## Later edits (after acceptance)

Acceptance (OD-0007) applies to this card as it stood at `35c9821`. These edits are not part of
the accepted version.

| Date | Authority | Edit | Accepted text |
|---|---|---|---|
| 2026-10-24 | OD-0015 | *Governing documents*: records that HIO-ADR-0008 and the protocol were approved after acceptance | "**None is approved.** The provisional working protocol (operating model §1.1) applies. HIO-ADR-0008 is context only." |
| 2026-10-24 | OD-0015 | Front matter `links`: HIO-ADR-0008 moved from `adrs_context_proposed` to `adrs_context_approved` | `adrs_context_proposed: [HIO-ADR-0008]` |
