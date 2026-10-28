---
id: OD-0091
title: "Owner approves harness-0.9 Phase A (Appendix A with its seed files) at 2df83b4 as harness-0.9a, and authorises Claude to apply it verbatim to main"
decision: approve
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-approve-phase-a-and-phase-b.md (owner's message, verbatim, with the questions it answers)
  sha256: a1865264f200f95d96c75984611dde32085633921a709d7fcf4e4301201e624d
  date: 2026-10-28
  quote: "yes to all four"
approves:
  - path: docs/decisions/harness-0.9-proposal.md, Appendix A (revision 4)
    revision: "2df83b427896cf5ce413e8cee76f809a267687f6, blob aa1ee6670556f91d171866cbbd4058e6b5cebec0"
  - path: MAP.md (seed, A1)
    revision: "2df83b4, blob c01c308ccfeecf67f5c09a29de21b8eaa2ffa979"
  - path: knowledge/findings.md (seed, A2)
    revision: "2df83b4, blob 6fe7b139df4654e9239d25a9b1908e6ba8f10cfd"
base_revision: a949875
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0056, OD-0068, OD-0070, OD-0080, OD-0092]}
---

# OD-0091: harness-0.9a approved

## What is approved

Appendix A of `docs/decisions/harness-0.9-proposal.md` at `2df83b4` (revision 4), with the seed files `MAP.md` and
`knowledge/findings.md` at that revision, as the harness amendment **harness-0.9a**. The approval covers the `MAP.md`
text and the §4.1 mechanical-correction rule. Findings Inbox lines are claims and are not approved.

## What is authorised

Claude applies the text verbatim to `main`, as harness-0.7.1 was applied under OD-0056:
- the two seed files byte-identical to `2df83b4`;
- each Appendix A "replace" made only where the quoted old text matches exactly;
- the version bumped to `harness-0.9a` and the changelog line added;
- `approved_by` set to this OD.

Any difference between Appendix A and the applied text is a stop.

## Unchanged

- Codex's bootstrap and the review protocol (operating model §2.2 and §6.2).
- Tools, CI and hooks.
- The 53 existing handoffs, which stay where they are.
- Phase B, which is OD-0092.

## Corrections (append-only)
