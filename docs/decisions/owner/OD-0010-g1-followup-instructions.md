---
id: OD-0010
title: "Owner follow-up instructions: correct the ADR-0010 S1a gate; present harness-0.6 for approval; begin T-0002/T-0003; assign the T-0004 review"
decision: authorise_work
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-18-owner-g1-followup.md (the owner's chat message, verbatim)
  sha256: 16fa7d3f1332eb83be2eb60df0b61b104e1503b9a02679826f705646045f8715
  date: 2026-10-18
  quote: "Clarify ADR-0010’s S1a entry gate: OD-0009 requires a future, separate authorization; it is not that authorization. Return the corrected ADR for my revision-specific G1 decision. I want approval to cover the harness-0.6 amendment explicitly. Present its changed text and exact revision for that separate approval. Begin the already-authorised T-0002 and T-0003 research now. Assign a separate review of T-0004 at fe3fdc78cb2d2b9f147122528cc5cf97db976397 before proposing its merge. Do not start S1a or live data operations."
applies_to:
  - path: hio/
    revision: f2275e274e2cc69cb9219fcf62184ce65e8e257c
related: {adrs: [HIO-ADR-0010, HIO-ADR-0008], tasks: [T-0002, T-0003, T-0004], findings: []}
---

# OD-0010: G1 follow-up instructions

## Owner action

1. **Correct ADR-0010's S1a entry gate:** OD-0009 requires a future, separate authorisation of S1a;
   it is not that authorisation. Return the corrected ADR for a revision-specific G1 decision.
2. **Present harness-0.6** (operating model §6.2, the `reviews/reports/` path) with its changed
   text and exact revision, for a separate, explicit approval.
3. **Begin T-0002 and T-0003** (research, authorised by OD-0009) now.
4. **Assign a separate review of T-0004** at `fe3fdc78cb2d2b9f147122528cc5cf97db976397`, before
   any merge is proposed.
5. **Do not start S1a. No live data operations.**

## Transcription of item 4 into the review index

The assignment is recorded as an *Assigned reviews* row (`reviews/README.md`). That table is
owner-written, so the row is a transcription of this instruction.

**Mechanics the owner should confirm.** The target is on branch `docs/hio-001-boundary-c1`
(from `macsmsf` `main`), which contains no `hio/` directory. §6.2 assumes a review branch cut
from the target. In this case the reviewer instead:
- inspects `fe3fdc7` in a separate, read-only worktree;
- commits its record on `review/t0004-codex`, cut from the staging-branch commit that adds this
  record (resolve: `git log -n1 --format=%H -- hio/docs/decisions/owner/OD-0010-g1-followup-instructions.md`);
- passes the scope check against that base.

This adapts how §6.2 is applied; it does not change §6.2's text.

## What this record does NOT do

- It does not approve ADR-0010 revision 3 or harness-0.6.
- It does not authorise S1a, or any live data operation.
- It does not authorise merging T-0004.
