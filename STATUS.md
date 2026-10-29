---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-29
as_of_revision: "repository elusivenode/hio, branch main; rewritten under OD-0069 from base eb19ef7; updated under OD-0071 from base 16ea0c6; updated under OD-0072/OD-0073 from base 950cce7; updated under OD-0074 to OD-0134"
max_length: 150 lines (move history to handoffs; keep this file current-state only)
---

# HIO status

> **A navigational snapshot with no independent authority.** Authority comes from explicit
> owner actions, evidenced by owner decision records
> ([`docs/decisions/owner/`](docs/decisions/owner/README.md), which is also the decision log).
> Review state lives in [`reviews/README.md`](reviews/README.md). If this file disagrees with
> either, they win; flag the conflict.

## One-line state

**S1a is accepted** (OD-0042); **S1b-1.0 (T-0009)** (OD-0079). **T-0010** (non-live integration: transport, Azure
backend, finality C1–C7, release notices, live path behind `LIVE_AUTHORISATION = None`) **accepted** (OD-0123, `62adccd`,
on `main` as `73f2e40`); **T-0011** (IaC) **accepted** (OD-0125, `c69df9e`, `09d4886`). **H1 met for capture** (five
datasets owner_verified, OD-0116 c1, OD-0118); **H3/H4 decided** (OD-0119); **H5 declined**. **Authorisation B is
staged** (package on `main`): **B-1 done** (OD-0125 c2): `hnf-prod` holds `rg-hio-tfstate` and `rg-hio-evidence`
(empty evidence store, writer identity, logs, disabled alert, budget); state in `~/.hio-state/` on the owner's Mac.
**B-2 ran once** (OD-0132): C5 failed 50/50 as written and a duplicate create returned 403, not 409 (`docs/evidence/b2/`);
**T-0015** (fix and instrumented re-run) is built, not run; the probe account is **held** (OD-0134). **B-3** not started.
**Nothing has been captured.** **Base camp** (`docs/base-camp.md`, proposed) is the procurement-readiness goal (OD-0129 to
OD-0134): **T-0013** accepted; **T-0014** built (verification READY, not received). `main` is protected (PRs only;
OD-0118). Session handoff: `handoffs/s1b1/2026-10-29-base-camp.md`.
**Harness-0.9** (a knowledge layer for Claude and Codex) has its direction adopted (OD-0070); its
**Phase A is approved and applied as harness-0.9a** (OD-0091). **Distil 1 accepted** (46 Settled findings,
OD-0093). Phase B work on H6 then H11 is authorised (OD-0092); activation of either needs Codex review and approval. **hiomux** is a tmux
orchestration pilot (an Opus orchestrator, Sonnet workers, Codex) kept **outside the repository**
(OD-0072). Its residual risks were accepted by the owner (OD-0073); the Codex reviewer has network access (OD-0077). It changes no harness text.
An automated **solution architect** (`gpt-6.1-sol` via the Codex CLI in hiomux, replacing the ChatGPT architect):
direction adopted (OD-0081); **slice 1 implemented** (OD-0082): `hiomux sa`, `docs/agents/solution-architect/`;
boundary probe passed; three regression cases run (results file). **Pilot accepted** (OD-0083); identity
**v0.2 approved** (OD-0084) and in use for new sessions. The orchestrator now runs outside tmux, and the owner
watches a read-only two-pane `view` window (OD-0085; tool hashes recorded there). Each `hio-orch` session runs
the bootstrap and brings hiomux and its view up by itself (OD-0086). A six-case architect **stress test** is
adopted (OD-0087): 12 runs, mechanically clean; ChatGPT's independent grading: all pass, no critical or
major failures. The architect is now in **bounded regular advisory use** (OD-0089; two held-out cases to name). Architect reading view (OD-0088; tool hashes there).
**Option B approved** (OD-0104) and applied as **harness-0.9b** (OD-0106): receipt takes navigation rows only;
finding states change by owner-authorised reconciliation (§6.2 step 5.12). **H6 is parked** (OD-0114): unactivated on
`phase-b/h6` (`655335c`) after seven verifications; one high finding open (F-VERIFY-…-6-1); nothing approved or waived;
**receipts stay manual**. Review environments for Codex (OD-0095); hiomux runner fixed (OD-0111). Handoff:
`handoffs/harness/2026-10-29-h6-parked-orchestration-close.md`.

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Approved | charter, architecture, HIO-ADR-0001…0009, six standards, `AGENTS.md` (OD-0008); HIO-ADR-0010 rev 3 (OD-0011); **HIO-ADR-0012 rev 3** at `d0965cc` (OD-0055); operating model **harness-0.7.1** at `552d4fb` (OD-0056) with correction 1 (OD-0059); **harness-0.9b** (option B amendment at `d26c2fa`, OD-0104; applied OD-0106); **harness-0.9a** (Phase A: `MAP.md`, `knowledge/findings.md`, stream handoffs) at `2df83b4` (OD-0091); OpenTofu as IaC authoring tool and the S1b-1.0 finality staging (OD-0063) | per-file blobs in the OD records |
| Accepted | **S1a** (OD-0042); **T-0009** (OD-0079); **T-0010** at `62adccd` (OD-0123); **T-0011** at `c69df9e` (OD-0125); **T-0012** at `efb6fa1` (OD-0128); **T-0013** at `39747c5` (OD-0134); T-0006, T-0007, T-0008 | [OD-0042](docs/decisions/owner/OD-0042-accept-s1a.md) |
| Authorised, in progress | **hiomux pilot**
use under its protocol, outside the repository (OD-0072, OD-0073). Routine delegated receipt (OD-0061). Harness-0.9: drafting only (OD-0068, OD-0070; done to revision 3). **T-0014**, **T-0015** submitted (OD-0132, OD-0134); base-camp work (OD-0132) | [T-0009 card](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) (`status: accepted`; `accepted_by: OD-0079`) |
| Not authorised | **the B-2 re-run, step 7b and destroy** without a "go"; **any C5 amendment; B-3 go-live** and any capture; S1b-2; setting `LIVE_AUTHORISATION`; any source permission beyond the five S1b-1 datasets (`hio_internal` only) and D7; D4–D6; factor specs (drafts); harness-0.9 Phase B activation (H6 parked, OD-0114), H11, H3, H7, H8; settling any finding without its verification | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Open owner questions | Q-013 (P3 in force), Q-003, Q-004, Q-005b, Q-006, Q-010 (open; H5 declined for S1b-1), Q-014 (harness-0.9) | [`open-decisions.md`](docs/decisions/open-decisions.md) |

## Reviews

| Review | State |
|---|---|
| **REVIEW-2026-10-29-t0013-1** | NOT READY at `caf44da` (OD-0133); **VERIFY-…-t0013-1-1 READY** at `39747c5` (OD-0134): F-1 `verified_closed` |
| **REVIEW-2026-10-29-t0014-1** | NOT READY at `13d2ea5`, one high, one medium (received OD-0134); **VERIFY-…-t0014-1-1 READY** at `e0aaa4d`, **not received** |
| **REVIEW-2026-10-29-t0010-1** | NOT READY at `f345d1e` (OD-0121); **VERIFY-…-t0010-1-1 READY** at `62adccd` (OD-0123): both findings `verified_closed` |
| **REVIEW-2026-10-29-t0011-1** | NOT READY at `2cc7362` (OD-0121); VERIFY-…-1 (OD-0123) and **VERIFY-…-2 READY** at `c69df9e` (OD-0125): all three `verified_closed` |
| **REVIEW-2026-10-28-h6-1** (H6, **parked**) | NOT READY at `9e07b8b` (OD-0096); VERIFY-…-1 to -7 all received (OD-0098, 0101, 0103, 0107, 0110, 0112, 0114). Seven findings `verified_closed`; **F-VERIFY-2026-10-28-h6-1-6-1 (high) open**. VERIFY-…-5's first tip `409cc71` is tagged and not received (OD-0109) |
| **REVIEW-2026-10-25-t0009-1** | **NOT READY** at `ce0c3b5` (merge `9efabbe`, tag `reviews/REVIEW-2026-10-25-t0009-1`, OD-0067); after verification: **all seven `verified_closed`** (OD-0075, OD-0078) |
| **VERIFY-2026-10-28-t0009-1-3** | **READY** at `76539b5..846974b`: F-5 verified_closed (RBA pages read live); **received** (merge `72908c5`, tag `reviews/VERIFY-2026-10-28-t0009-1-3`, OD-0078) |
| VERIFY-2026-10-28-t0009-1-2 | READY (offline) but **not received; superseded** by `-3` (OD-0077) |
| **VERIFY-2026-10-28-t0009-1-1** | **NOT READY** at `ce0c3b5..76539b5`; six verified_closed, F-5 open; **received** (merge `5330307`, tag `reviews/VERIFY-2026-10-28-t0009-1-1`, OD-0075) |
| REVIEW-2026-10-25-adr0012 | F-2 `verified_closed`. F-1 and F-3: **technically verified closed as proposed design corrections** (OD-0054), but their index rows still read `remediation_claimed` because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived (OD-0057). Read OD-0054 before relying on either |
| harness-0.7.1 review findings 1…4 | technically verified closed (OD-0054); not yet in the index finding table |
| REVIEW-2026-10-24-s1a-1, REVIEW-2026-10-18-a01, REVIEW-2026-10-18-t0004 | all findings `verified_closed`; t0004 READY, received across lineages (OD-0040) |
| Receipt sweep (2026-10-25) | 17 `review/*` branches on origin, each received or disposed by an OD |

No finding is waived.

## Phase and gate

| Item | State |
|---|---|
| Phase | S1b-1 Authorisation B, staged ([package](docs/evidence/S1B1-authorisation-B-package.md)): **B-1 done**; B-2 ran, re-run pending; then B-3. Base camp: `docs/base-camp.md` (proposed) |
| B-2 (storage probe) | run `40853094503`: create, refusals and one-version pass; duplicate create gives 403 `UnauthorizedBlobOverwrite`; **C5 0/50** (`s` floored to whole seconds; the probe measured `completed_at` after the write, unlike the ADR). Next: merge T-0015, re-run (R-1), 7b, C5 decision, destroy ≥24 h after the last write (re-run plan `docs/evidence/S1B1-B2-rerun-plan.md` on `feat/t0015`) |
| B-3 (go-live) | five data-source URLs approved; `LIVE_AUTHORISATION` set; workflow moved to `.github/workflows/`; `alert_enabled = true`; the `capture` reviewer rule removed (C-4); one watched dispatch; then schedule and the 10-business-day soak (incl. a failing **scheduled** run's email, I-5) |
| Deadlines | **2027 RITS/NSW calendars** before 2027-01-01 (RBA page unpublished at 2026-10-29; recheck by 2026-12-01) |
| Next permissible actions | **Owner:** receive VERIFY-…-t0014-1-1 and accept T-0014; accept or review T-0015; then the re-run "go"; distil 2 (proposed); rights V1–V5; back up `~/.hio-state/`. Architect review: material assembled (OD-0128). Older items stand: held-out stress cases (OD-0089); H7 timing; observations v0.3; Q-013. **Claude:** nothing beyond what an OD authorises |

## Branches holding work not on `main`

| Branch | Head | Holds |
|---|---|---|
| `feat/t0014` | `e0aaa4d` (pushed) | T-0014 base-camp completion build; verified READY, **not received, not accepted** (PR #43) |
| `feat/t0015` | `3d259d3` (pushed) | T-0015 B-2 follow-up (403 mapping, probe instrumentation, re-run plan); **submitted** (PR #53) |
| `phase-b/h6` | `655335c` (pushed) | H6 tools and tests, responses 1 to 7; **parked, unactivated** (OD-0114) |
| `proposal/h6-option-b` | `d26c2fa` (pushed) | the option B amendment, **approved** (OD-0104) and applied to `main` (OD-0106) |
| `proposal/harness-0.9` | `c711f51` (pushed) | harness-0.9 revision 4 (design record for Phase B and H7; Fable dry-run report); H6 design wording per option B (OD-0106); the H6 recovery clarification (**proposed**, OD-0109, OD-0112). Phase A is applied on `main` (OD-0091) |

## Work cards

| Work | Card | Status |
|---|---|---|
| A01 decisions review | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (criteria met by OD-0008, OD-0011; acceptance not recorded) |
| S1 source rights | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: the five S1b-1 datasets owner_verified (OD-0116 c1, OD-0118); the rest unverified |
| Equity total-return source | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted; vendor questions need owner approval |
| HIO-001 boundary (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review; review READY, received (OD-0040); **not accepted, not merged** |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | S1a stage **accepted** (OD-0042); S1b staged under HIO-ADR-0012 |
| S1b-1.0 cash capture | [T-0009](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) | **accepted** (OD-0079) at `846974b`, integrated `7eba3f9`; finality staging and Authorisation B remain |
| S1b-1 non-live integration | [T-0010](registers/tasks/T-0010-s1b1-non-live-integration.md) | **accepted** (OD-0123) at `62adccd`; W-5 calendars a gap |
| S1b-1 IaC | [T-0011](registers/tasks/T-0011-s1b1-infrastructure-as-code.md) | **accepted** (OD-0125) at `c69df9e`; applied as B-1 |
| B-2 storage probe | [T-0012](registers/tasks/T-0012-b2-storage-probe.md) | **accepted** (OD-0128) at `efb6fa1`, merged `01edfe9`; ran once (B-2) |
| Soak monitoring fix | [T-0013](registers/tasks/T-0013-soak-alert-and-completeness.md) | **accepted** (OD-0134) at `39747c5`, merged `ae84ac6`; alert still disabled |
| Base-camp completion build | T-0014 (on `feat/t0014`) | submitted; verification READY, not received |
| B-2 follow-up | T-0015 (on `feat/t0015`) | submitted (OD-0134) |
| T-0006, T-0007, T-0008 | in `registers/tasks/` | **accepted** (OD-0007, OD-0004, OD-0006) |
| ETF diagnostic (lives in `macsmsf`) | `macsmsf` branch `docs/etf-diagnostic-card` | proposed; not authorised (OD-0018); not an HIO dependency |

## Verified

- **Migration** (OD-0017): `macsmsf@dc4fd02:hio` split with history into this repository; tree
  identical, ids and states unchanged ([`MIGRATION-MAP.md`](MIGRATION-MAP.md)). Commit ids in
  older documents refer to `macsmsf` history.
- **S1a**, on synthetic fixtures (OD-0042), with its limitations: no CI egress firewall (Q-008);
  Hatchling not hash-locked; release ids revision-dependent.
- **B-1 read-back** (OD-0125 c2): evidence account shared key off, no public access, ZRS, immutability Unlocked 3,650 days, 0 blobs, alert disabled.
- **B-2 first run** (`docs/evidence/b2/`): writer RBAC refuses overwrite and delete; one version per key; C5 as written fails on Azure.
- **No live capture or publication timing has been validated**; immutability against a privileged actor is untested (7b).

## Unverified and external

**Every** vendor, licence, coverage, price and publication-timing claim is `unverified`
([`registers/sources.yaml`](registers/sources.yaml)).

## Do not

- fetch any real source, write to the evidence store, run `tofu plan/apply` or any Azure write, or dispatch a workflow,
  outside an OD that authorises it (B-2 and B-3 each need their own yes);
- commit any subscription, tenant or object id, email address, GitHub numeric id, state or backend file;
- mark any further source permission verified, or declare S1b-1 complete;
- change HIO-001, or `macsmsf`; treat a branch, a merge or a handoff as approval;
- commit data whose rights do not allow public redistribution (the repository is public, OD-0019).
