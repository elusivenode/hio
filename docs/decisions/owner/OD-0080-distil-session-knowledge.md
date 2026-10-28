---
id: OD-0080
title: "Owner instructs that this session's learnings and context be distilled, and that mechanisms be developed to track long-run context and let agents access it; Claude drafts harness-0.9 revision 4 (seeds refreshed, session findings, gaps) and writes the session handoff; nothing approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-distil-session.md (typed by the owner, verbatim)
  sha256: 4bc5efe640d5b6c6eba478fdaa351530bcb5c4fa84c1969bf54eaca49417854e
  date: 2026-10-28
  quote: "distill learnings and context from this session.  this is the long run context we need to develop.  we need mechanisms to track it and allow agents to access it."
applies_to:
  - path: proposal/harness-0.9 (docs/decisions/harness-0.9-proposal.md, MAP.md, knowledge/findings.md)
    revision: 2df83b427896cf5ce413e8cee76f809a267687f6   # revision 4, drafted; not approved
  - path: handoffs/2026-10-28-t0009-acceptance-and-knowledge.md
    revision: self
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], open_decisions: [Q-014], ods: [OD-0068, OD-0070, OD-0072 to OD-0079]}
---

# OD-0080: distil the session; mechanisms for long-run context

## Owner instruction (verbatim in the source file)

"distill learnings and context from this session. this is the long run context we need to develop. we need
mechanisms to track it and allow agents to access it."

## How Claude read it, and what was done

The mechanism the owner describes already exists as a design: harness-0.9 Phase A. It provides:
- `MAP.md`, the orientation map;
- `knowledge/findings.md`, one line per finding, appended to an Inbox and settled by the owner at a distil;
- the per-stream handoff sections *Didn't work* and *For the index*;
- the read-path wiring in `AGENTS.md` and the `hio-session` skill.

The owner adopted its direction (OD-0070), but its text was never approved. Building a second mechanism would
duplicate it. So this instruction is read as authorising **drafting** within that design. It does not approve
anything.

1. **Revision 4 of the harness-0.9 package** on `proposal/harness-0.9` at `2df83b4`. `main` (`e16a47f`) was merged
   in first, keeping `main`'s index rows.
   - **Seeds refreshed.** Four stale findings lines are marked superseded or updated, never deleted. `MAP.md` is
     updated for T-0009's acceptance and the D7 data.
   - **22 Inbox lines added** from this session, each citing its evidence.
   - **Gaps G1 to G5** recorded in §14: Codex has no access to the findings; operational knowledge lives outside
     the repository; nothing checks out-of-repository tools against their recorded hashes; distil has no owner
     moment; every receipt needed an owner question.
   - §12 updated: Phase A can apply now, and Phase B's gate is met.
2. **The session handoff**, `handoffs/2026-10-28-t0009-acceptance-and-knowledge.md`. It follows the current
   template, plus the proposed *Didn't work* and *For the index* sections.
3. **STATUS** updated to point to revision 4.

## Not approved or changed

- **No harness text approved.** Phase A, Phase B, H7 and branch protection remain the owner's decisions (Q-014;
  proposal §12).
- **No Settled findings.** Inbox lines are claims (rank 6).
- **No changes** to `AGENTS.md`, the operating model, the templates, the skills, `tools/`, CI or hiomux.
- **Auto-memory** holds only a pointer and the owner's stated preferences. It is never a record (`CLAUDE.md`).

## Corrections (append-only)

None.
