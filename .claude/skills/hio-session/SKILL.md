---
name: hio-session
description: "Starting or ending any HIO work session (the investment research system staged in hio/). Use BEFORE doing HIO work in a fresh session, and BEFORE ending a session that changed anything. Covers the bootstrap read order, the context budget, document precedence, what you may change, and writing the handoff. Triggers: HIO, hio/, start session, bootstrap, handoff, task card, what's next, status."
---

# HIO session procedure

The canonical rules are in `hio/AGENTS.md` and `hio/docs/harness/operating-model.md`. This
skill is a checklist, not a restatement.

## Start
1. `git rev-parse HEAD`: record it.
2. Read `hio/AGENTS.md`, then `hio/STATUS.md`.
3. Find your task card in `hio/registers/tasks/` and its authorising OD record in
   `hio/docs/decisions/owner/`. If the card is not `authorised` or `in_progress`, or the OD is
   not `approved`, you may only read, propose or draft. State your role and the work status.
   - **Reviewer:** set the target revision and test plan *before* reading the author's handoff
     (operating model §2.2).
4. Read only the ADRs, standards sections and specs the card links. Budget about 25k tokens.
5. Read the latest `hio/handoffs/*` that names the task.

## During
- Git state is not approval. Approved OD records govern; proposed ADRs only recommend; STATUS
  and handoffs carry no authority. On a conflict or a missing approved revision: **stop and
  flag**.
- Open findings: `hio/reviews/README.md`. An author may only record `remediation_claimed`.
- Never set `approved`, `validated` or `approved_for_consumer`.
- No `macsmsf` code, database or credential access from HIO work.
- Licensed data never goes into prompts or handoffs unless its rights record allows.

## End
Write `hio/handoffs/YYYY-MM-DD-<slug>.md` from `hio/templates/handoff.md`, including what was
**not** approved. Commit with an `HIO-Actor:` trailer. Update `hio/STATUS.md`
if the current state changed, keeping it to 150 lines or fewer.
