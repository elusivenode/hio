---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-28
as_of_revision: "repository elusivenode/hio, branch main; rewritten under OD-0069 from base eb19ef7"
max_length: 150 lines (move history to handoffs; keep this file current-state only)
---

# HIO status

> **A navigational snapshot with no independent authority.** Authority comes from explicit
> owner actions, evidenced by owner decision records
> ([`docs/decisions/owner/`](docs/decisions/owner/README.md), which is also the decision log).
> Review state lives in [`reviews/README.md`](reviews/README.md). If this file disagrees with
> either, they win; flag the conflict.

## One-line state

**S1a is accepted** (OD-0042). **S1b-1.0 (T-0009) is in development on synthetic fixtures only**
(Authorisation A, OD-0062). Its implementation at `ce0c3b5` was reviewed **NOT READY**, with
**seven findings open** (`REVIEW-2026-10-25-t0009-1`, received by OD-0067). Remediation is
authorised (OD-0067) and **not started**. No live operation is authorised: HIO has no cloud
storage, no real data and no credentials, so the point-in-time capture clock has not started.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Approved | charter, architecture, HIO-ADR-0001…0009, six standards, `AGENTS.md` (OD-0008); HIO-ADR-0010 rev 3 (OD-0011); **HIO-ADR-0012 rev 3** at `d0965cc` (OD-0055); operating model **harness-0.7.1** at `552d4fb` (OD-0056) with correction 1 (OD-0059); OpenTofu as IaC authoring tool and the S1b-1.0 finality staging (OD-0063) | per-file blobs in the OD records |
| Accepted | **S1a** at `084154c`, integrated as `773a557` (OD-0042); T-0006, T-0007, T-0008 | [OD-0042](docs/decisions/owner/OD-0042-accept-s1a.md) |
| Authorised, in progress | **T-0009** under Authorisation A only: synthetic-fixture development, a documentation-only storage check, IaC authoring (OD-0062, OD-0063, OD-0065). **Remediation** of the seven findings (OD-0067). Routine delegated receipt (OD-0061) | [T-0009 card](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) (`status: proposed`; `authorised_by: OD-0062`) |
| Not authorised | S1b-1 live operation (Authorisation B), S1b-2; provisioning, credentials, real fetches, enabled schedules; every source permission (unverified, OD-0013; OD-0064 is a design direction, not a verification); factor specs (drafts); harness-0.9 (proposed) | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Open owner questions | Q-013 (capture-time knowability), Q-003, Q-004, Q-005b, Q-006, Q-010, Q-014 (harness-0.9) | [`open-decisions.md`](docs/decisions/open-decisions.md) |

## Reviews

| Review | State |
|---|---|
| **REVIEW-2026-10-25-t0009-1** | **NOT READY** at `ce0c3b5`; F-1, F-2, F-6 high and F-3, F-4, F-5, F-7 medium, all **open** (merge `9efabbe`, tag `reviews/REVIEW-2026-10-25-t0009-1`, OD-0067) |
| REVIEW-2026-10-25-adr0012 | F-2 `verified_closed`. F-1 and F-3: **technically verified closed as proposed design corrections** (OD-0054), but their index rows still read `remediation_claimed` because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived (OD-0057). Read OD-0054 before relying on either |
| harness-0.7.1 review findings 1…4 | technically verified closed (OD-0054); not yet in the index finding table |
| REVIEW-2026-10-24-s1a-1, REVIEW-2026-10-18-a01, REVIEW-2026-10-18-t0004 | all findings `verified_closed`; t0004 READY, received across lineages (OD-0040) |
| Receipt sweep (2026-10-25) | 17 `review/*` branches on origin, each received or disposed by an OD |

No finding is waived.

## Phase and gate

| Item | State |
|---|---|
| Phase | S1b-1.0 under Authorisation A, staged by HIO-ADR-0012 (approved rev 3) |
| Current gate | T-0009 remediation, then a new fixed head assigned to Codex for verification (OD-0067) |
| Gate to live S1b-1 (Authorisation B) | T-0002 `owner_verified` rights per dataset and operation; the network and credential-control decision (OD-0038 successor); storage selection and verification; Q-013 decided or P3 in force; an explicit live authorisation (T-0009 card, `depends_on`) |
| Next permissible actions | **Claude:** T-0009 remediation on `impl/t0009-remediation-1` (local, cut from `ce0c3b5`) within OD-0067. **Owner:** harness-0.9 decisions (Q-014); the T-0002 rights reading (U1 to U7); the controls decision; observations v0.3 (blob `61ddd58e`) approve or defer; the run-1 stale-line candidates |

## Branches holding work not on `main`

| Branch | Head | Holds |
|---|---|---|
| `impl/t0009-shared-receipt-and-storage` | `ce0c3b5` (pushed; reviewed head, never rebase) | T-0009 code, tests, specs, `infra/tofu/`, its handoff; **not accepted, not merged** |
| `impl/t0009-remediation-1` | `ce0c3b5` (local) | remediation, not started |
| `proposal/harness-0.9` | `f5ce1b8` (local) | harness-0.9 rev 2, seed `MAP.md` and findings index, dry-run report (OD-0068) |

## Work cards

| Work | Card | Status |
|---|---|---|
| A01 decisions review | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (criteria met by OD-0008, OD-0011; acceptance not recorded) |
| S1 source rights | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: evidence drafted ([matrix](docs/research/T-0002-owner-verification-matrix.md)); awaiting the owner's verification |
| Equity total-return source | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted; vendor questions need owner approval |
| HIO-001 boundary (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review; review READY, received (OD-0040); **not accepted, not merged** |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | S1a stage **accepted** (OD-0042); S1b staged under HIO-ADR-0012 |
| S1b-1.0 cash capture | [T-0009](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) | Authorisation A; review NOT READY; remediation authorised, not started |
| T-0006, T-0007, T-0008 | in `registers/tasks/` | **accepted** (OD-0007, OD-0004, OD-0006) |
| ETF diagnostic (lives in `macsmsf`) | `macsmsf` branch `docs/etf-diagnostic-card` | proposed; not authorised (OD-0018); not an HIO dependency |

## Verified

- **Migration** (OD-0017): `macsmsf@dc4fd02:hio` split with history into this repository; tree
  identical, ids and states unchanged ([`MIGRATION-MAP.md`](MIGRATION-MAP.md)). Commit ids in
  older documents refer to `macsmsf` history.
- **S1a**, on synthetic fixtures (OD-0042), with its limitations: no CI egress firewall (Q-008);
  Hatchling not hash-locked; release ids revision-dependent.
- **No source licence, publication timing or live capture has been validated.**

## Unverified and external

**Every** vendor, licence, coverage, price and publication-timing claim is `unverified`
([`registers/sources.yaml`](registers/sources.yaml)).

## Do not

- fetch any real source, provision anything, run `tofu init/validate/plan/apply`, or create a
  credential or an enabled schedule;
- mark any source permission verified, or declare S1b accepted;
- change HIO-001, or `macsmsf`;
- treat a branch, a merge or a handoff as approval;
- commit secrets, or any data whose rights do not allow public redistribution (the repository
  is public, OD-0019).
