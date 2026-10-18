---
name: hio-session
description: "Starting or ending any HIO work session (the investment research system staged in hio/). Use BEFORE doing HIO work in a fresh session, and BEFORE ending a session that changed anything. Covers the bootstrap read order, the context budget, document precedence, what you may change, and writing the handoff. Triggers: HIO, hio/, start session, bootstrap, handoff, task card, what's next, status."
---

# HIO session procedure

A checklist that points to the canonical rules: `hio/AGENTS.md` (short) and
`hio/docs/harness/operating-model.md` (detail). It restates nothing, so it cannot drift.

## Start
1. `git rev-parse HEAD`: record it.
2. Read `hio/AGENTS.md` (the authority rules and the bootstrap by role), then `hio/STATUS.md`.
3. Find your task card and the recorded owner instruction behind it. If there is none, read and
   draft only. **Reviewer:** check *Assigned reviews* in `hio/reviews/README.md`. If it is
   empty, your answer is "No review target has been assigned."
4. Read only what the card or assignment links. Budget about 25k tokens.

## End
Write a handoff from `hio/templates/handoff.md`, including what was **not** approved.
- **Non-reviewers:** put it in `hio/handoffs/`; update `hio/STATUS.md` if the state changed (150
  lines or fewer).
- **Reviewer on a review branch:** put it in `hio/reviews/handoffs/`; never touch
  `hio/handoffs/` or `STATUS.md` (operating model §6.2).
