---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-24
as_of_revision: "repository elusivenode/hio, branch main; see the latest handoff for the exact commit"
max_length: 150 lines (move history to handoffs; keep this file current-state only)
---

# HIO status

> **A navigational snapshot with no independent authority.** Authority comes from explicit
> owner actions, evidenced by owner decision records
> ([`docs/decisions/owner/`](docs/decisions/owner/README.md)). Review state lives in
> [`reviews/README.md`](reviews/README.md). If this file disagrees with either, they win; flag
> the conflict.

## One-line state

**G1 is complete** (OD-0008, OD-0011). **S1a is authorised** (OD-0017): synthetic-fixture-only,
in this repository, `elusivenode/hio` (private), migrated with history from
`macsmsf@dc4fd02` on 2026-10-24. **No S1a code exists yet.** S1b is not authorised. HIO has no
storage, no data and no credentials. The `macsmsf` staging branch `docs/hio-a01-baseline` is
frozen at `dc4fd02` and stays unmerged.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | OD-0001…0018; the latest are OD-0016 (S1a preparation), OD-0017 (**S1a authorised**; migration) and OD-0018 (T-0004 mechanics confirmed; parallel work; ETF card; roadmap corrections) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Approved | at `a82aa0d` (OD-0008): charter, architecture, HIO-ADR-0001…0009 (C1; projection fund-level), six standards, `AGENTS.md`. HIO-ADR-0010 rev 3 at `760f73e` (OD-0011). Operating model harness-0.6 at `f2275e2` (OD-0012). All of these are `macsmsf` commit ids | per-file blobs in the OD records |
| Authorised, not accepted | **S1a** (OD-0017) | [OD-0017](docs/decisions/owner/OD-0017-authorise-s1a.md) |
| Not approved / not authorised | factor specs (drafts); roadmap and plan (recommendations); **S1b**; all T-0002 source permissions **unverified and blocked** (OD-0013); the ETF diagnostic workstream; any `macsmsf` pointer change or merge | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Independent reviews | REVIEW-2026-10-18-a01 (REQUEST CHANGES), then VERIFY-2026-10-18-a01-1: **8/8 verified_closed**. T0007-PILOT READY. REVIEW-2026-10-18-t0004 **assigned, not received** | [`reviews/README.md`](reviews/README.md) |
| Open findings | **none** | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | S1a (synthetic-fixture foundation) |
| Current gate | S1a acceptance, after an independent Codex review at a fixed revision |
| Next permissible actions | **Agents:** S1a within OD-0017 (harness CI, contracts, observation model, constructions, gates; fixtures only); T-0002 evidence from published pages; T-0003 research (no vendor contact). **Owner:** run the Codex T-0004 review (a fresh session with the neutral §10 prompt, if it is also to count as the fresh-session test); decide how the T-0004 review record is received now that the staging branch is frozen; T-0002 evidence; the vendor drafts (**not sent**) |
| Next implementation slice | S1a: authorised. S1b: needs S1a accepted, T-0002 `owner_verified` rights, and its own authorisation |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (its acceptance criteria are met by OD-0008 and OD-0011; owner acceptance not recorded) |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: findings drafted ([research](docs/research/T-0002-source-rights-and-timing.md)); awaiting owner verification |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted ([research](docs/research/T-0003-equity-total-return-sources.md)); vendor questions need owner approval |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review: `fe3fdc7` on `docs/hio-001-boundary-c1`; **review REVIEW-2026-10-18-t0004 assigned** (OD-0010); mechanics **confirmed** (OD-0018); not merged |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | **S1a authorised** (OD-0017); not started beyond migration. S1b **not authorised** |
| Harness refinement (harness-0.3) | [T-0006](registers/tasks/T-0006-harness-refinement.md) | **accepted** at `35c9821` (OD-0007) |
| Review branch and worktree protocol (harness-0.5) | [T-0007](registers/tasks/T-0007-review-worktree-protocol.md) | **accepted** at `b48f83c` (OD-0004) |
| A01 correction slice (8 findings) | [T-0008](registers/tasks/T-0008-a01-correction-slice.md) | **accepted** at `0c74686` (OD-0006) |
| ETF diagnostic (SMSF-owned; lives in `macsmsf`) | `macsmsf` branch `docs/etf-diagnostic-card` | proposed; **not authorised** (OD-0018). Not an HIO dependency |

## Verified

**Migration** (OD-0017): `macsmsf@dc4fd02:hio` split with history into this repository. The tree
is identical, 23/23 commits mapped, ids and states unchanged, 15/15 approved targets equal, and
175/175 links resolve ([`MIGRATION-MAP.md`](MIGRATION-MAP.md)). Commit ids in older documents
refer to `macsmsf` history.


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

- start S1b, fetch any real source, or create any bucket, credential or schedule;
- change HIO-001, or `macsmsf` (a pointer change needs a separate reviewed change);
- contract or contact a vendor;
- treat a branch, a merge or a handoff as approval.
