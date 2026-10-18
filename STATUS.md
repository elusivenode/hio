---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-18
as_of_revision: "branch docs/hio-a01-baseline (macsmsf repository); see the latest handoff for the exact commit"
max_length: 150 lines (move history to handoffs; keep this file current-state only)
---

# HIO status

## One-line state

**Planning baseline drafted; nothing approved; nothing implemented.** HIO has no code, no
repository of its own, no storage, no data and no credentials.

## Phase and gate

| Item | State |
|---|---|
| Phase | A01: architecture and research charter |
| Current gate | **G1: owner approval of the A01 baseline** ([roadmap](docs/roadmap.md#decision-gates)) |
| Next implementation slice | **HIO-S1 walking skeleton**, *recommended, awaiting approval* ([implementation plan](docs/implementation-plan.md#hio-s1-walking-skeleton-recommended)) |

## Under construction

| Work | Task card | State |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | ready for owner |
| Rights verification for the S1 sources (RBA, NY Fed, US Treasury, Federal Reserve Board) | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | ready; not started |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | ready; not started |
| HIO-001 boundary amendment proposal (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | proposal drafted in HIO-ADR-0003; awaiting owner |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | **not approved**; blocked on G1 and T-0002 |

## Verified

Nothing in HIO has been verified, because nothing has been built.

Repository facts that HIO documents rely on were verified on 2026-10-18 against `macsmsf`
`main` at `1502ab8` (handoff [2026-10-18](handoffs/2026-10-18-a01-baseline.md)):
- HIO-001 is not applied to the authoritative SMSF database;
- its registry holds exactly the 11 held instruments;
- its loader requires both `sql/048` and `sql/049` and full classification coverage.

## Unverified and external

**Every** vendor, licence, coverage, price and publication-timing claim in HIO documents is
`unverified` until [`registers/sources.yaml`](registers/sources.yaml) records owner
verification.

## Decisions awaiting the owner

See [`docs/decisions/README.md`](docs/decisions/README.md). All of HIO-ADR-0001 to HIO-ADR-0010
are `proposed`.

## Do not

- start S1 implementation;
- create the `hio` repository or any cloud resource;
- change HIO-001;
- contract a vendor.

Each of these needs the gate above.
