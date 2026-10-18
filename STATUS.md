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

**G1 is complete** (OD-0008, OD-0011). **S1a is not authorised.** It needs a future, separate
owner authorisation (HIO-ADR-0010 rev 3). Nothing is implemented. HIO has no code, no repository
of its own, no storage, no data and no credentials. The baseline is staged in `macsmsf/hio/`, on
the unmerged branch `docs/hio-a01-baseline`.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | OD-0001…0009; the latest are OD-0006/0007 (T-0008/T-0006 accepted), OD-0008 (G1 decisions) and OD-0009 (follow-on instructions) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Approved | at `a82aa0d` (OD-0008): charter, architecture, HIO-ADR-0001…0009 (C1; projection fund-level), six standards, `AGENTS.md`. HIO-ADR-0010 rev 3 at `760f73e` (OD-0011). Operating model harness-0.6 at `f2275e2` (OD-0012) | per-file blobs in the OD records |
| Not approved / not authorised | factor specs (drafts); roadmap and plan (recommendations); **S1a and S1b not authorised**; all T-0002 source permissions **unverified and blocked** (OD-0013) | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Independent reviews | REVIEW-2026-10-18-a01 (REQUEST CHANGES), then VERIFY-2026-10-18-a01-1: **8/8 verified_closed** (received at `a82aa0d`). T0007-PILOT READY (received at `385389d`) | [`reviews/README.md`](reviews/README.md) |
| Open findings | **none** | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | A01 → G1 |
| Current gate | **G1 complete.** Next: the owner's separate decision whether, and in what scope, to authorise S1a |
| Next permissible actions | **Owner:** consider S1a authorisation; answer the T-0002 open questions (evidence); review the [vendor question drafts](docs/research/T-0003-vendor-questions-draft.md) (**not sent**); run Codex REVIEW-2026-10-18-t0004. **Agents:** T-0002 evidence-gathering from published pages; no S1a; no live data; no vendor contact |
| Next implementation slice | S1a (synthetic-fixture-only), per approved HIO-ADR-0010 rev 3: **not authorised** |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (its acceptance criteria are met by OD-0008 and OD-0011; owner acceptance not recorded) |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: findings drafted ([research](docs/research/T-0002-source-rights-and-timing.md)); awaiting owner verification |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted ([research](docs/research/T-0003-equity-total-return-sources.md)); vendor questions need owner approval |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review: `fe3fdc7` on `docs/hio-001-boundary-c1`; **review REVIEW-2026-10-18-t0004 assigned** (OD-0010); not merged |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | proposed; **not authorised** |
| Harness refinement (harness-0.3) | [T-0006](registers/tasks/T-0006-harness-refinement.md) | **accepted** at `35c9821` (OD-0007) |
| Review branch and worktree protocol (harness-0.5) | [T-0007](registers/tasks/T-0007-review-worktree-protocol.md) | **accepted** at `b48f83c` (OD-0004) |
| A01 correction slice (8 findings) | [T-0008](registers/tasks/T-0008-a01-correction-slice.md) | **accepted** at `0c74686` (OD-0006) |

## Verified

The A01 design contracts and fixture arithmetic were independently reviewed (`35c9821`) and
verified (`0c74686`) by Codex. **No HIO implementation, release, source licence or publication
timing has been validated.**

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
