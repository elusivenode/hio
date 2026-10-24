---
id: T-0004
title: Decide the HIO-001 boundary and, if approved, amend macsmsf ADR 0003 (documentation only)
status: submitted_for_review
owner: owner
assignee_role: architecture agent (drafting) + owner (decision)
created: 2026-10-18
authorised_by: [OD-0008, OD-0009]   # C1 chosen (OD-0008); prepare the amendment for separate review (OD-0009)
base_revision: 1502ab8804c5968a8bf91fa36275c44e6e84f575   # macsmsf main; the amendment goes on its own branch
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

## Submission (2026-10-18)

- **Branch** `docs/hio-001-boundary-c1`, from `macsmsf` `main` at `1502ab8`. **Commit `fe3fdc78cb2d2b9f147122528cc5cf97db976397`. Not merged.**
- **Diff:** `docs/adr/0003-instrument-identity-and-economic-classification.md` (+16) and `docs/hio-001-review-record.md` (+3). Documentation only (B1).
- **The activation prerequisites read the same** (B2); the amendment says so explicitly.
- **Next:** separate review, then an owner decision to merge to `main` with `--no-ff` (SMSF convention).
- **Review received (2026-10-25, OD-0040):** REVIEW-2026-10-18-t0004, verdict **READY**, no finding, copied byte-for-byte from `macsmsf@db305a3` into [`reviews/records/`](../../reviews/records/REVIEW-2026-10-18-t0004.md). **Not accepted; not merged** into `macsmsf` `main`. That needs a separate owner decision.
- **Note:** the informational note at the top of ADR 0003 on the HIO staging branch (`85ef0fa`) still says "awaiting owner decision". It is reconciled when the two branches meet.
