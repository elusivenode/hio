---
id: T-0001
title: Owner review of the A01 baseline decisions
status: proposed
owner: owner
assignee_role: owner (with an independent reviewer for ADRs that gate implementation)
created: 2026-10-18
authorised_by: null       # OD record id; none exists, so this card is not authorised
base_revision: null
links: {adrs: [HIO-ADR-0001, HIO-ADR-0002, HIO-ADR-0003, HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007, HIO-ADR-0008, HIO-ADR-0009, HIO-ADR-0010], depends_on: [], blocks: [T-0005]}
---

# T-0001: owner review of the A01 baseline decisions

## Objective
Approve, amend or reject each proposed ADR and the charter, so that HIO has a binding baseline
before any implementation.

## Approved scope
- review of the ADRs, the charter and the return standard;
- an optional independent review of the standards (Codex) before approval.

## Non-goals
- implementation;
- repository or cloud creation.

## Acceptance tests
| ID | Test | Evidence |
|---|---|---|
| A1 | every ADR carries `approved`, `rejected` or `deferred`, with an approval line | ADR files |
| A2 | the return standard is `approved` at a version, or has review findings logged | standard front matter; review record |
| A3 | `STATUS.md` gate G1 updated | STATUS |

## Open issues
See [`../../docs/risks-and-open-decisions.md`](../../docs/risks-and-open-decisions.md) §1.

## Review status
_Not reviewed._
