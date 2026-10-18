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

> **A navigational snapshot with no independent authority.** Authority lives in owner decision
> records ([`docs/decisions/owner/`](docs/decisions/owner/README.md)). Review state lives in
> [`reviews/README.md`](reviews/README.md). If this file disagrees with either, they win; flag
> the conflict.

## One-line state

**Nothing is approved or authorised; nothing is implemented.** HIO has no code, no repository
of its own, no storage, no data and no credentials. The planning baseline is staged in
`macsmsf/hio/`, on the unmerged branch `docs/hio-a01-baseline`.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | **none approved**; OD-0001 is `proposed` (unconfirmed transcription) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| HIO-ADR-0001 to 0010 | all `proposed` | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Standards and specs | all `proposed` or `draft` | front matter |
| Independent reviews | none yet; the A01 review is proposed | [`reviews/README.md`](reviews/README.md) |
| Open findings | none recorded | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | A01: architecture and research charter |
| Current gate | **G1: owner approval of the A01 baseline** ([roadmap](docs/roadmap.md#4-decision-gates)), expected after the Codex A01 review |
| Next implementation slice | **HIO-S1 walking skeleton**: recommended, **not authorised** ([implementation plan](docs/implementation-plan.md#hio-s1-walking-skeleton-recommended)) |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | proposed |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | proposed |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | proposed |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | proposed; **not authorised** |
| Harness refinement (harness-0.2) | [T-0006](registers/tasks/T-0006-harness-refinement.md) | submitted_for_review; its authorisation (OD-0001) is unconfirmed |

## Verified

Nothing in HIO has been verified by an independent reviewer.

The `macsmsf` repository facts relied on (HIO-001 state, registry scope, loader coupling) were
checked by the author on 2026-10-18 at `1502ab8`. See
[`handoffs/2026-10-18-a01-baseline.md`](handoffs/2026-10-18-a01-baseline.md). They are author
claims, not reviewed evidence.

## Unverified and external

**Every** vendor, licence, coverage, price and publication-timing claim is `unverified`
([`registers/sources.yaml`](registers/sources.yaml)).

## Do not

- start S1;
- create the `hio` repository or any cloud resource;
- change HIO-001;
- contract a vendor;
- treat this branch, or any handoff, as approval.
