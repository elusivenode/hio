---
id: T-0004
title: Decide the HIO-001 boundary and, if approved, amend macsmsf ADR 0003 (documentation only)
status: proposed
owner: owner
assignee_role: architecture agent (drafting) + owner (decision)
created: 2026-10-18
approved: null
links: {adrs: [HIO-ADR-0003], depends_on: [], blocks: [HIO-001 activation (SMSF programme), HIO reference context design]}
---

# T-0004: decide the HIO-001 boundary

## Objective
Owner decision on option C1 in [HIO-ADR-0003](../../docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md).
If approved, add the staged amendment text to `macsmsf` `docs/adr/0003-*`, with a pointer from
`docs/hio-001-review-record.md`.

## Approved scope (if approved)
One `macsmsf` documentation commit, on its own branch, merged with `--no-ff` per SMSF
conventions.

## Non-goals
- any HIO-001 code, migration, registry, test or activation change;
- A17.

## Acceptance tests
| ID | Test | Evidence |
|---|---|---|
| B1 | the `macsmsf` diff touches only the two documentation files | `git diff --stat` |
| B2 | HIO-001's activation prerequisites read the same before and after | diff review |
| B3 | HIO-ADR-0003 status updated | ADR |
