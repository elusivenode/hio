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

**G1 is open, with one item outstanding.** A01 items 1–11 and 13–20 are approved at `a82aa0d`
(OD-0008). HIO-ADR-0010 revision 2 (the S1a/S1b split) awaits the owner's decision. Nothing is
implemented. HIO has no code, no repository of its own, no storage, no data and no credentials.
The baseline is staged in `macsmsf/hio/` on the unmerged branch `docs/hio-a01-baseline`.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | OD-0001…0009; the latest are OD-0006/0007 (T-0008/T-0006 accepted), OD-0008 (G1 decisions) and OD-0009 (follow-on instructions) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Approved at `a82aa0d` (OD-0008) | charter; architecture; HIO-ADR-0001…0009 (C1 chosen; projection fund-level); six standards; operating model; `AGENTS.md` | per-file blobs in OD-0008 |
| Not approved | HIO-ADR-0010 rev. 2 (proposed); the harness-0.6 change adding `reviews/reports/` (directed by OD-0009); factor specs (drafts); roadmap and plan (recommendations) | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Independent reviews | REVIEW-2026-10-18-a01 (REQUEST CHANGES), then VERIFY-2026-10-18-a01-1: **8/8 verified_closed** (received at `a82aa0d`). T0007-PILOT READY (received at `385389d`) | [`reviews/README.md`](reviews/README.md) |
| Open findings | **none** | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | A01 → G1 |
| Current gate | **G1 open:** the owner decides [HIO-ADR-0010 revision 2](docs/decisions/HIO-ADR-0010-first-slice-scope.md) |
| Next permissible actions | **Owner:** decide ADR-0010 rev. 2; review the T-0004 branch `docs/hio-001-boundary-c1` (`fe3fdc7`); say when T-0002 and T-0003 research should begin. **Agents:** T-0002 and T-0003 are authorised research (not yet started); **no S1a work** until G1 completes and the owner explicitly authorises its scope; **no live data operations under S1a** (OD-0009) |
| Next implementation slice | S1a (synthetic-fixture-only), per ADR-0010 rev. 2: **not authorised** |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (largely discharged by OD-0008; ADR-0010 outstanding) |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **authorised** (OD-0009); not started |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **authorised** (OD-0009); not started |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review: branch `docs/hio-001-boundary-c1` at `fe3fdc7`, not merged |
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
