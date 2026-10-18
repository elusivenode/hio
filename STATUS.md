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

> **A navigational snapshot with no independent authority.** Authority comes from explicit
> owner actions, evidenced by owner decision records
> ([`docs/decisions/owner/`](docs/decisions/owner/README.md)). Review state lives in
> [`reviews/README.md`](reviews/README.md). If this file disagrees with either, they win; flag
> the conflict.

## One-line state

**Nothing is approved or accepted; nothing is implemented.** HIO has no code, no repository
of its own, no storage, no data and no credentials. The planning baseline is staged in
`macsmsf/hio/`, on the unmerged branch `docs/hio-a01-baseline`.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | two `authorise_work` records (OD-0001, corrected; OD-0002), both for T-0006 documentation. **No accept, approve or waive record exists** | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Working protocol | `AGENTS.md` and the operating model operate **provisionally** (HIO-ADR-0008 is proposed) | operating model §1.1 |
| HIO-ADR-0001 to 0010 | all `proposed` | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Standards and specs | all `proposed` or `draft` | front matter |
| Independent reviews | A01 at `1502ab8..35c9821`: **REQUEST CHANGES**; no A01 approval. T0007-PILOT at `46ea6a5..b48f83c`: **READY** (a readiness opinion; received by merge `385389d`, under §6.2; **not acceptance**) | [`reviews/README.md`](reviews/README.md) |
| Open findings | eight A01 findings (one critical, five high, two medium); the T0007-PILOT review opened none | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | A01: architecture and research charter |
| Current gate | **G1: owner approval of the A01 baseline** ([roadmap](docs/roadmap.md#4-decision-gates)); the first independent review requested changes |
| Next permissible actions | the owner considers the [A01 findings](reviews/records/REVIEW-2026-10-18-a01.md) and directs a correction slice; the owner accepts or returns T-0006 and T-0007 (separate actions) |
| Next implementation slice | **HIO-S1 walking skeleton**: recommended, **not authorised** ([implementation plan](docs/implementation-plan.md#hio-s1-walking-skeleton-recommended)) |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | proposed |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | proposed |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | proposed |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | proposed; **not authorised** |
| Harness refinement (harness-0.3) | [T-0006](registers/tasks/T-0006-harness-refinement.md) | submitted_for_review; **not accepted** (authorised by OD-0001/OD-0002) |
| Review branch and worktree protocol (harness-0.4) | [T-0007](registers/tasks/T-0007-review-worktree-protocol.md) | submitted_for_review at `b48f83c`; Codex T0007-PILOT **READY** (received at `385389d`); **not accepted** (OD-0003) |

## Verified

The A01 planning baseline has received an independent design review at `35c9821`; its verdict
is **REQUEST CHANGES**. No HIO implementation, release or source claim has been validated.

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
