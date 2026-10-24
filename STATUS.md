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
in this repository, `elusivenode/hio` (**public** since 2026-10-24, OD-0019), migrated with history from
`macsmsf@dc4fd02` on 2026-10-24. **S1a is implemented and submitted for review** (OD-0020;
[evidence package](docs/evidence/S1A-evidence-package.md)): synthetic fixtures only, 150 tests,
CI green. **Not accepted**: reviewed (REQUEST CHANGES), remediated on PR #2, verification in progress (see below). S1b is not
authorised. HIO has no cloud storage, no real data and no credentials. The `macsmsf` staging branch `docs/hio-a01-baseline` is
frozen at `dc4fd02` and stays unmerged.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Owner decision records | OD-0001…0023; the latest are OD-0016 (S1a preparation), OD-0017 (**S1a authorised**; migration) OD-0018 (T-0004 mechanics confirmed; parallel work; ETF card; roadmap corrections) OD-0019 (repository public), OD-0020 (proceed with S1a implementation) OD-0021 (harness-0.7 approved) OD-0022 (S1a review received at `e55cc89`; harness-0.7 adoption condition met), OD-0023 (S1a remediation slice), OD-0024 (F6 round 2 before receipt; harness-0.8 stopped) and OD-0025 (VERIFY-…-1 and -2 disposed as preserved evidence; F6 correction cycle) OD-0026 (Q-001/Q-002 drafts refined), OD-0027/0028 (draft revisions), OD-0029 (**Q-001 revision 4 approved**; Q-002 A′ selected) OD-0030 (**Q-002 revision 5 approved**; F4/F7 implementation authorised) OD-0031, OD-0032 and OD-0033 (exceptions for VERIFY-2026-10-24-s1a-1-6, -7 and -8) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| Approved | at `a82aa0d` (OD-0008): charter, architecture, HIO-ADR-0001…0009 (C1; projection fund-level), six standards, `AGENTS.md`. HIO-ADR-0010 rev 3 at `760f73e` (OD-0011). Operating model **harness-0.7** at `9b58811` (OD-0021; supersedes harness-0.6, OD-0012). All of these are `macsmsf` commit ids | per-file blobs in the OD records |
| Authorised, not accepted | **S1a** (OD-0017, OD-0020): implemented, **submitted for review** | [evidence package](docs/evidence/S1A-evidence-package.md) |
| Not approved / not authorised | factor specs (drafts); roadmap and plan (recommendations); **S1b**; all T-0002 source permissions **unverified and blocked** (OD-0013); the ETF diagnostic workstream; any `macsmsf` pointer change or merge | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Independent reviews | REVIEW-2026-10-18-a01 → VERIFY-2026-10-18-a01-1: 8/8 verified_closed. T0007-PILOT READY. **REVIEW-2026-10-24-s1a-1: REQUEST CHANGES** (Codex, at `98e6a8e`), **received** at `e55cc89` (PR #1, OD-0022). **VERIFY-2026-10-24-s1a-1-1** (Codex, at `18c80f2`; REQUEST CHANGES: F1, F2, F3, F5 verified_closed, F6 remediation_rejected) is committed at `0255cb2` (PR #3); **VERIFY-2026-10-24-s1a-1-2** (Codex, at `759ddf7`; REQUEST CHANGES: F6 round 2 rejected) at `9a94c3a`; **VERIFY-2026-10-24-s1a-1-3** (Codex, at `21c8167`; REQUEST CHANGES: F6 round 3 rejected) at `ff0dd81`; **VERIFY-2026-10-24-s1a-1-4** (Codex, at `4c1b565`; REQUEST CHANGES: F6 round 4 rejected) at `873fc69`; **VERIFY-2026-10-24-s1a-1-5** (Codex, at `d9fa276`; **READY: F6 verified_closed** within the S1a local single-writer storage contract) at `6d8b60d`. None is received; all are owner-disposed evidence for the F6 cycle (OD-0025) | [`reviews/README.md`](reviews/README.md) |
| Open findings | **seven, all open in this index**: -1, -2, -3, -5 verified_closed by VERIFY-2026-10-24-s1a-1-1 (index states change at its receipt); -6 **verified_closed by VERIFY-2026-10-24-s1a-1-5** at `d9fa276` (index state changes at receipt; rounds 1–4 rejected); -4 **remediation_claimed** (round 2, response 7) and -7 **remediation_claimed, round 4** (fix `7b267f5`, RESPONSE-REVIEW-2026-10-24-s1a-1-9; rounds 1–3 rejected by VERIFY-2026-10-24-s1a-1-6/-7/-8); not verified | [`reviews/README.md`](reviews/README.md) |

## Phase and gate

| Item | State |
|---|---|
| Phase | S1a (synthetic-fixture foundation) |
| Current gate | Codex verification of F4/F7 at PR #2's new submission head, with regression checks of F1, F2, F3, F5 and F6; owner approval of observations v0.3 (candidate); receipt or disposition of the preserved review records; the §10 fresh-session test (S1-A16; **not run**); then S1a acceptance |
| Next permissible actions | **Codex:** verify PR #2's submission head (the commit adding RESPONSE-REVIEW-2026-10-24-s1a-1-9). **Owner:** decide the archive-on-capture-clock question (response 6); approve or amend the v0.3 candidate; decide receipt of the preserved review records; run the §10 test. **Agents:** no further S1a change until verification findings or decisions exist; T-0002 evidence; T-0003 research (no vendor contact). |
| Next implementation slice | S1a: authorised. S1b: needs S1a accepted, T-0002 `owner_verified` rights, and its own authorisation |

## Work cards

| Work | Card | Status |
|---|---|---|
| Owner review of the A01 decisions | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (its acceptance criteria are met by OD-0008 and OD-0011; owner acceptance not recorded) |
| Rights verification for the S1 sources | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: findings drafted ([research](docs/research/T-0002-source-rights-and-timing.md)); awaiting owner verification |
| Equity total-return source decision | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted ([research](docs/research/T-0003-equity-total-return-sources.md)); vendor questions need owner approval |
| HIO-001 boundary amendment (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review: `fe3fdc7` on `docs/hio-001-boundary-c1`; **review REVIEW-2026-10-18-t0004 assigned** (OD-0010); mechanics **confirmed** (OD-0018); not merged |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | **S1a submitted for review** (OD-0017, OD-0020); not accepted. S1b **not authorised** |
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
