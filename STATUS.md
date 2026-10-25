---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-25
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

**G1 is complete** (OD-0008, OD-0011). **S1a is accepted** (OD-0042, 2026-10-25): the
synthetic-fixture foundation, in this repository, `elusivenode/hio` (**public** since 2026-10-24,
OD-0019). The acceptance covers the implementation at the reviewed head `084154c` (integrated as
`773a557`) and the evidence in
[`docs/evidence/S1A-acceptance-package.md`](docs/evidence/S1A-acceptance-package.md): all seven
findings verified closed and S1-A16 satisfied (OD-0041). It is accepted with its limitations:
synthetic data only; no CI egress firewall (Q-008); Hatchling not hash-locked; release ids
revision-dependent. **S1b is not authorised.** HIO has no cloud storage, no real data and no
credentials.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | OD-0001…0045, OD-0046…0054 (the HIO-ADR-0012 proposal and remediation, the harness-0.7.1 proposal, the review dispositions and the closure of seven findings), plus **OD-0060** (**B2 received under the corrected harness-0.7.1; evidence and CI clean**; local agent-exchange convention; routine delegated receipt **not yet enabled**, owner decision), **OD-0055** (**HIO-ADR-0012 rev 3 approved**), **OD-0056** (**harness-0.7.1 approved**; first receipt supervised, routine receipt not authorised) **OD-0059** (**bounded harness-0.7.1 trailer/CI-reporting correction approved**, regression-tested; routine receipt still **not enabled**), **OD-0058** (first supervised receipt: A2 received, CI trailer mismatch, adoption **not** validated) and **OD-0057** (D0: `e1f60f9` and `9c51a6b` disposed, unreceived; supervised first receipt of A2, completed under OD-0058) (before them: **OD-0050**, REVIEW-2026-10-25-adr0012 received by byte-identical import; earlier:  **OD-0045, readiness assessment integrated; T-0002 RBA/NY Fed evidence** (no permission verified); OD-0044, S1b readiness assessment (a report only; not authorisation); OD-0043, S1-A16 evidence relocated (correction note); **OD-0042, S1a accepted**; OD-0041, S1-A16 accepted as PASS; OD-0040, T-0004 review received across lineages and the S1-A16 two-revision basis; OD-0039, record S1-A16 run 1, pending; OD-0038, Q-007 ratified, Q-008 accepted for S1a only, Q-005a confirmed, Q-010 deferred to S1b; not acceptance); OD-0037 (integrate PR #2 and receive the S1a evidence); the latest are OD-0016 (S1a preparation), OD-0017 (**S1a authorised**; migration) OD-0018 (T-0004 mechanics confirmed; parallel work; ETF card; roadmap corrections) OD-0019 (repository public), OD-0020 (proceed with S1a implementation) OD-0021 (harness-0.7 approved) OD-0022 (S1a review received at `e55cc89`; harness-0.7 adoption condition met), OD-0023 (S1a remediation slice), OD-0024 (F6 round 2 before receipt; harness-0.8 stopped) and OD-0025 (VERIFY-…-1 and -2 disposed as preserved evidence; F6 correction cycle) OD-0026 (Q-001/Q-002 drafts refined), OD-0027/0028 (draft revisions), OD-0029 (**Q-001 revision 4 approved**; Q-002 A′ selected) OD-0030 (**Q-002 revision 5 approved**; F4/F7 implementation authorised) OD-0031, OD-0032 and OD-0033 (exceptions for VERIFY-2026-10-24-s1a-1-6, -7 and -8), OD-0034 and OD-0035 (**Q-002-R1 `quality_digest` approved**; exception for VERIFY-2026-10-24-s1a-1-9), OD-0036 (exception for VERIFY-2026-10-24-s1a-1-10) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Approved | at `a82aa0d` (OD-0008): charter, architecture, HIO-ADR-0001…0009 (C1; projection fund-level), six standards, `AGENTS.md`. HIO-ADR-0010 rev 3 at `760f73e` (OD-0011). Operating model **harness-0.7.1** at `552d4fb`, blob `a74a41453d10`, plus the OD-0059 correction to §6.2 steps 5.7, 5.8 and 5.10, with `AGENTS.md` and `reviews/README.md` at `8461e99` (OD-0056; supersedes §6.2's harness-0.7 delivery and receipt text; adoption conditional on a supervised first receipt). **HIO-ADR-0012 rev 3** at `d0965cc`, blob `eb110ee394af` (OD-0055; supersedes only HIO-ADR-0010 rev 3's S10-B2, S10-B5 and conditionally the wording of S10-B8(ii)). Earlier items are `macsmsf` commit ids | per-file blobs in the OD records |
| Accepted | **S1a** (OD-0042): implementation at `084154c` (integrated as `773a557`); evidence in the [acceptance package](docs/evidence/S1A-acceptance-package.md) (integrated by `8140edb`). Also T-0006, T-0007, T-0008 | [OD-0042](docs/decisions/owner/OD-0042-accept-s1a.md) |
| Not approved / not authorised | factor specs (drafts); roadmap and plan (recommendations); **S1b**; all T-0002 source permissions **unverified and blocked** (OD-0013); the ETF diagnostic workstream; any `macsmsf` pointer change or merge | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Independent reviews | REVIEW-2026-10-18-a01 → VERIFY-2026-10-18-a01-1: 8/8 verified_closed. T0007-PILOT READY. **REVIEW-2026-10-24-s1a-1** (REQUEST CHANGES, received `e55cc89`) → **VERIFY-2026-10-24-s1a-1-1…-11**, all **received** (OD-0037; V1 = PR #3 at `3015c5b`, V11 at `95c2e82`); V11 READY at `084154c`; **REVIEW-2026-10-18-t0004** READY, received across lineages (OD-0040); **REVIEW-2026-10-25-adr0012** (HIO-ADR-0012 proposal, REQUEST CHANGES, 3 findings **open**) received by import, not merge (OD-0050); §10 run 1 HARNESS-2026-10-25-s1a16-1 pending. **Unreceived Codex records** (pushed branches, none merged): `e1f60f9` and `9c51a6b` **disposed, unreceived** (OD-0057, limitations recorded); `dac54f5` (A2) **received** by byte-identical import (merge `347da95`, tag `reviews/VERIFY-2026-10-25-adr0012-2`, OD-0058; CI failed on a missing `HIO-Actor` trailer, a procedure/CI mismatch, corrected by OD-0059 (approved, regression-tested); `4682c98` (B2) **received** by byte-identical import (merge `c3905d7`, tag `reviews/VERIFY-2026-10-25-harness-0.7.1-1`, CI run `40177539871` green, OD-0060): the first full receipt under the corrected text; first-use outcome reported in OD-0060, routine receipt **not enabled** until the owner records it. Index finding rows for harness-0.7.1-1…-4 not yet updated. Seven findings technically verified closed (OD-0054), none waived | [`reviews/README.md`](reviews/README.md) |
| Open findings | **none for S1a**: F1, F2, F3, F5 verified closed at `18c80f2` (V1); F6 at `d9fa276` (V5); F4 at `f00db8c` (V7, held through V11); F7 at `084154c` (V11). Technical verification, not acceptance | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | S1a accepted (OD-0042); S1b not authorised |
| Current gate | **S1b authorisation** (owner). Per HIO-ADR-0010 rev 3 it needs: S1a accepted (**done**, OD-0042); T-0002 `owner_verified` rights for every S1b operation, per source; publication timing, calendars and the AUD rate regime evidenced; a separate network and credential-control decision (OD-0038); Q-010 in S1b design; and the owner's authorisation of S1b's scope and infrastructure. Observations v0.3 (blob `61ddd58e`) awaits separate approval. Readiness: [S1b readiness assessment](docs/evidence/S1B-readiness-assessment.md) (OD-0044); staged by [HIO-ADR-0012](docs/decisions/HIO-ADR-0012-staged-s1b.md) (**approved**, revision 3, OD-0055; its three findings technically verified closed, OD-0054; **S1b-1 and S1b-2 not authorised**; Q-013, the release-manifest schema, publisher header semantics and every source right still open); rights proposals in the [verification matrix](docs/research/T-0002-owner-verification-matrix.md) |
| Next permissible actions | **Owner:** approve or defer observations v0.3; decide the run-1 stale-line candidates; continue T-0002/T-0003 under OD-0013; decide when to prepare S1b. **Agents:** no S1a change without a new material finding; S1b not authorised; no real fetch, bucket, credential or schedule |
| Next implementation slice | S1b: needs T-0002 `owner_verified` rights, the network and credential-control decision, and its own authorisation (S1a acceptance is done) |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (its acceptance criteria are met by OD-0008 and OD-0011; owner acceptance not recorded) |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: findings drafted ([research](docs/research/T-0002-source-rights-and-timing.md); [2026-10-25 RBA/NY Fed evidence](docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md): RBA AUD/USD is WM/Reuters and the BAB is ASX, both third party); awaiting owner verification |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted ([research](docs/research/T-0003-equity-total-return-sources.md)); vendor questions need owner approval |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review: `fe3fdc7` on `docs/hio-001-boundary-c1`; review REVIEW-2026-10-18-t0004 (OD-0010, OD-0018) **received**: READY, copied byte-for-byte from `macsmsf@db305a3` (OD-0040); **not accepted, not merged** |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | **S1a accepted** (OD-0042). S1b **not authorised** |
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
- treat a branch, a merge or a handoff as approval;
- commit secrets, or any source data whose rights do not allow public redistribution (the repository is public, OD-0019).
