---
id: HANDOFF-2026-10-24-s1a-preparation
date: 2026-10-24
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0016)
base_revision: 81793f7
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-24-s1a-preparation.md
work_commits: [73512cf, 81793f7]   # earlier commits this session (OD-0014, OD-0015)
work_card: T-0005 (proposed; documents aligned), T-0007 (later edit)
---

# Handoff: S1a preparation (OD-0016)

> A dated snapshot. **Not a decision.**

## Done

- **Archived** the owner's message (the pasted advice plus "once done, please push our branch to
  the remote") verbatim, and recorded it as **OD-0016**. The reading of "once done" is stated
  in the record for the owner to correct.
- **Execution documents aligned with HIO-ADR-0010 rev 3:**
  - **Implementation plan:** S1a/S1b slice rows; the stage mapping of S1-A1…A16; the dependency
    list (G1 no longer "authorises the repository and bucket"; T-0002 gates S1b only); the
    infrastructure rows marked by stage; the S1a exclusions; migration "with history, per §8.1".
  - **Roadmap:** G1 completed on 2026-10-18; separate S1a (weeks 1–4) and S1b (weeks 4–8) rows;
    T-0002 runs in parallel and gates S1b only; G2 follows S1b.
  - **T-0005** (still `proposed`): two-stage title, per-stage `depends_on`, a *Stages* table, and
    a pointer to the draft OD-0017.
  - **Operating model §8.1:** the status sentence now records the approvals. A **status-only**
    edit, logged in the changelog; the approved content stays at blob `e3114bd188ad`.
  - **README:** the migration preserves history; it is not a `git mv`.
- **T-0007 criteria 1–2 (later edit):** a review in a continuing chat is not the §10 test.
- **OD-0017 drafted** (`record_status: draft`, **no authority**). It covers the S1a boundary,
  the migration method and local verification, the stack and CI permissions (marked
  **[owner]**), the order of work and the stop conditions.
- STATUS, the OD index and the history index are updated.

## Known limitations and not verified

- The S1a/S1b test mapping in the plan is Claude's reading of ADR-0010. The ADR's own S1a list
  governs.
- The roadmap week estimates are unchanged in spirit, but the S1a/S1b week split (1–4, 4–8) is
  new and is an estimate.

## Decisions needed (owner)

1. OD-0017: grant, change or decline. If granting, fill in the **[owner]** fields: the source
   commit, the repository name, the `macsmsf` option (a) or (b), and the stack.
2. OD-0010's cross-lineage review mechanics: confirm them before Codex commits a T-0004 record.
3. Whether the reading of "once done" in OD-0016 matches the intent.

## Still stale (not touched)

- T-0008 front matter (`adrs_context_proposed` lists ADRs 0004–0007, now approved).
- The ADR-0010 heading "Decision (proposed, revision 3)", which is inside the approved blob.

## NOT approved by this session

Nothing is approved, accepted, authorised, waived or closed. S1a and S1b are **not authorised**.
The roadmap and the plan remain recommendations. No live data, no vendor contact, no merges,
nothing outside `hio/`.

## Next authorised action

Push `docs/hio-a01-baseline` to `origin` (OD-0016 item 4). After that, nothing more is
authorised until the owner decides on OD-0017.
