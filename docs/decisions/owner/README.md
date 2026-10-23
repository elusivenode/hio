---
id: HIO-OD-INDEX
title: Owner decision records
status: current
owner: owner
last_reviewed: 2026-10-24
---

# Owner decision records (OD)

These records evidence explicit owner actions: instruct (authorise work), accept, approve and
waive. The authority is the **owner's statement**, which each record cites verbatim. The rules
are in operating model §1.1; the template is
[`../../../templates/owner-decision.md`](../../../templates/owner-decision.md).

| ID | Decision | What | Applies to | Record status |
|---|---|---|---|---|
| [OD-0001](OD-0001-authorise-harness-refinement.md) | authorise_work | T-0006 harness refinement (the original ambiguity is preserved) | `hio/` from `85ef0fa` | corrected |
| [OD-0002](OD-0002-authorise-t0006-final-correction.md) | authorise_work | T-0006 final harness correction | `hio/` from `23ad27f` | recorded |
| [OD-0003](OD-0003-adopt-review-worktree-protocol.md) | authorise_work | T-0007 review branch and worktree protocol | `hio/` from `bada952` | recorded |
| [OD-0004](OD-0004-accept-t0007.md) | accept_work | T-0007 accepted | T-0007 at `b48f83c` | recorded |
| [OD-0005](OD-0005-authorise-a01-correction-slice.md) | authorise_work | T-0008 A01 correction slice | `hio/` from `e99fae1` | recorded |
| [OD-0006](OD-0006-accept-t0008.md) | accept_work | T-0008 accepted | T-0008 at `0c74686` | recorded |
| [OD-0007](OD-0007-accept-t0006.md) | accept_work | T-0006 accepted as completed work | T-0006 at `35c9821` | recorded |
| [OD-0008](OD-0008-g1-decisions-a82aa0d.md) | approve | G1: items 1–11 and 13–20 approved (C1 chosen; projection fund-level); item 12 (ADR-0010) returned | each file at `a82aa0d` | recorded |
| [OD-0009](OD-0009-g1-follow-on-instructions.md) | authorise_work | §6.2 `reports/` path; T-0002 and T-0003 authorised; prepare T-0004; S1a limits | `hio/` from `f7a9ec9` | recorded |
| [OD-0010](OD-0010-g1-followup-instructions.md) | authorise_work | ADR-0010 S1a gate corrected; harness-0.6 presented for approval; begin T-0002/T-0003; T-0004 review assigned | `hio/` from `f2275e2` | recorded |
| [OD-0011](OD-0011-approve-adr-0010-rev3.md) | approve | HIO-ADR-0010 rev 3; **G1 complete**; S1a not authorised | ADR-0010 at `760f73e` (blob `8ade1962cf28`) | recorded |
| [OD-0012](OD-0012-approve-harness-0.6.md) | approve | harness-0.6, including the `reviews/reports/` rule | operating model at `f2275e2` (blob `e3114bd188ad`) | recorded |
| [OD-0013](OD-0013-t0002-hold-t0003-drafts.md) | authorise_work | keep T-0002 permissions unverified and blocked; draft (do not send) vendor questions | `hio/` from `8e11581` | recorded |
| [OD-0014](OD-0014-fix-stale-lines.md) | authorise_work | fix the stale lines (STATUS authority row; T-0002/T-0003 front matter; T-0007 line 60 as a later edit) | `hio/` from `4a994d3` | recorded |
| [OD-0015](OD-0015-fix-further-stale-lines.md) | authorise_work | fix the further stale lines in the accepted T-0006 and T-0007 cards (later edits); commit the OD-0014 work | `hio/` from `73512cf` | recorded |
| [OD-0016](OD-0016-s1a-preparation.md) | authorise_work | adopt the S1a-preparation advice: align roadmap, plan, T-0005, §8.1 and README to ADR-0010 rev 3; draft (not grant) S1a; push the staging branch | `hio/` from `81793f7` | recorded |
| [OD-0017](OD-0017-authorise-s1a-DRAFT.md) | authorise_work | **DRAFT** S1a authorisation, awaiting the owner's decision | — | **draft (no authority)** |

**Current position:**
- **Approved:**
  - charter, architecture, HIO-ADR-0001…0009, six standards and `AGENTS.md`, at `a82aa0d`
    (OD-0008);
  - HIO-ADR-0010 rev 3 at `760f73e` (OD-0011);
  - the operating model, harness-0.6, at `f2275e2` (OD-0012).
- **G1 is complete.**
- **Not approved:** the factor specs (drafts); the roadmap and plan (recommendations).
- **Not authorised:** S1a; S1b.
- **Accepted:** T-0006, T-0007 and T-0008.
- **No finding is waived.**
