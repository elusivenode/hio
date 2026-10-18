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
3. Find your task card in `hio/registers/tasks/`. If its `status` is not `approved`, you may
   only read, propose or draft.
4. Read only the ADRs, standards sections and specs the card links. Budget about 25k tokens.
5. Read the latest `hio/handoffs/*` that names the task.

## During
- Precedence on conflict: approvals > standards > specs > plans > STATUS and cards > handoffs >
  anything else. Record conflicts; never resolve them silently.
- Never set `approved`, `validated` or `approved_for_consumer`.
- No `macsmsf` code, database or credential access from HIO work.
- Licensed data never goes into prompts or handoffs unless its rights record allows.

## End
Write `hio/handoffs/YYYY-MM-DD-<slug>.md` from `hio/templates/handoff.md`. Update `hio/STATUS.md`
if the current state changed, keeping it to 150 lines or fewer.
