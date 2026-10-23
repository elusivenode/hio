---
id: HANDOFF-2026-10-24-further-stale-lines
date: 2026-10-24
actor: claude/documentation-agent (Claude Opus 5.5, Claude Code session)
work_status: authorised (OD-0015)
base_revision: 73512cf
head_revision: self       # resolve: git log -n1 --format=%H -- hio/handoffs/2026-10-24-further-stale-lines.md
work_commits: [73512cf]   # the OD-0014 work, committed on the owner's "yes"
work_card: T-0006, T-0007 (text corrections only)
---

# Handoff: further stale-line fixes (OD-0015)

> A dated snapshot. **Not a decision.**

## Done

- **Owner message archived** verbatim and recorded as **OD-0015**. The OD and history indexes
  and the STATUS row are updated.
- **T-0007:**
  - line 29 now records that HIO-ADR-0008 and the protocol were approved after acceptance;
  - criterion 3 now cites Codex's use of §6.2 (T0007-PILOT `e36dd08` → `385389d`;
    VERIFY-2026-10-18-a01-1 → `a82aa0d`);
  - the front-matter `links` field now lists HIO-ADR-0008 under `adrs_context_approved`.
- **T-0006:** the *Governing documents* line, plus the same `links` change. The front-matter
  field was not listed separately in the earlier handoff; it is included because it makes the
  same claim, and OD-0015 says so.
- Every edit appears in the card's *Later edits* table with the accepted text. Acceptance is
  unchanged (T-0006: OD-0007 at `35c9821`; T-0007: OD-0004 at `b48f83c`).

## Still stale (NOT fixed; outside scope)

- **T-0008 front matter:** `adrs_context_proposed: [HIO-ADR-0004 … 0007]`. Those ADRs were
  approved by OD-0008. This is the same class of issue as above, on another accepted card.

## NOT approved by this session

Nothing is approved, accepted, authorised, waived or closed. No status changes. No S1a, no live
data, no vendor contact, no merges, nothing outside `hio/`.

## Next authorised action

None is pending under OD-0015. The owner decisions in `STATUS.md` are unchanged.
