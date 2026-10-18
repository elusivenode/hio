---
id: HIO-OD-INDEX
title: Owner decision records
status: current
owner: owner
last_reviewed: 2026-10-18
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

**There is no `approve` or `waive_finding` record.** The only `accept_work` record is OD-0004 (T-0007). Therefore:
- no HIO ADR, standard or spec is approved;
- T-0007 is accepted at `b48f83c`; T-0006 is not accepted;
- no finding is waived.
