---
id: HIO-STATUS
title: Current status
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-28
as_of_revision: "repository elusivenode/hio, branch main; rewritten under OD-0069 from base eb19ef7; updated under OD-0071 from base 16ea0c6; updated under OD-0072/OD-0073 from base 950cce7; updated under OD-0074 to OD-0093"
max_length: 150 lines (move history to handoffs; keep this file current-state only)
---

# HIO status

> **A navigational snapshot with no independent authority.** Authority comes from explicit
> owner actions, evidenced by owner decision records
> ([`docs/decisions/owner/`](docs/decisions/owner/README.md), which is also the decision log).
> Review state lives in [`reviews/README.md`](reviews/README.md). If this file disagrees with
> either, they win; flag the conflict.

## One-line state

**S1a is accepted** (OD-0042). **S1b-1.0 (T-0009) is accepted** (OD-0079) at `846974b` and integrated into
`main` as `7eba3f9` (PR #6): the synthetic-fixture slice of Authorisation A (OD-0062). All seven findings of
`REVIEW-2026-10-25-t0009-1` are `verified_closed` (OD-0075, OD-0078). Still owed before S1b-1 completion: the
finality staging (C1–C7, finality, the soak; T-0009 §7) and **Authorisation B**. No live operation is authorised:
HIO has no cloud storage, no real data beyond the D7 calendars (OD-0076) and no credentials, so the
point-in-time capture clock has not started.
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

## Authority snapshot

| Item | State | Record |
|---|---|---|
| Approved | charter, architecture, HIO-ADR-0001…0009, six standards, `AGENTS.md` (OD-0008); HIO-ADR-0010 rev 3 (OD-0011); **HIO-ADR-0012 rev 3** at `d0965cc` (OD-0055); operating model **harness-0.7.1** at `552d4fb` (OD-0056) with correction 1 (OD-0059); **harness-0.9a** (Phase A: `MAP.md`, `knowledge/findings.md`, stream handoffs) at `2df83b4` (OD-0091); OpenTofu as IaC authoring tool and the S1b-1.0 finality staging (OD-0063) | per-file blobs in the OD records |
| Accepted | **S1a** at `084154c`, integrated as `773a557` (OD-0042); **T-0009 S1b-1.0** at `846974b`, integrated as `7eba3f9` (OD-0079); T-0006, T-0007, T-0008 | [OD-0042](docs/decisions/owner/OD-0042-accept-s1a.md) |
| Authorised, in progress | **hiomux pilot**
use under its protocol, outside the repository (OD-0072, OD-0073). Routine delegated receipt (OD-0061). Harness-0.9: drafting only (OD-0068, OD-0070; done to revision 3) | [T-0009 card](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) (`status: accepted`; `accepted_by: OD-0079`) |
| Not authorised | S1b-1 live operation (Authorisation B), S1b-2; provisioning, credentials, real fetches, enabled schedules; every source permission except D7 (unverified, OD-0013; OD-0064 is a design direction, not a verification; D7 `rba_calendar_pages` is owner_verified for retain-and-cite only, OD-0076); factor specs (drafts); harness-0.9 Phase B **activation** (H6, H11 need Codex review and approval), H3, H7, H8; settling any finding (the first distil needs owner acceptance) | [`docs/decisions/README.md`](docs/decisions/README.md) |
| Open owner questions | Q-013 (capture-time knowability), Q-003, Q-004, Q-005b, Q-006, Q-010, Q-014 (harness-0.9) | [`open-decisions.md`](docs/decisions/open-decisions.md) |

## Reviews

| Review | State |
|---|---|
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
| Phase | S1b-1.0 **accepted** (OD-0079); next stage: finality staging and Authorisation B, staged by HIO-ADR-0012 (approved rev 3) |
| Current gate | T-0009 **accepted** and integrated (OD-0079, `7eba3f9`); the next gate is Authorisation B (below) |
| Gate to live S1b-1 (Authorisation B) | T-0002 `owner_verified` rights per dataset and operation; the network and credential-control decision (OD-0038 successor); storage selection and verification; Q-013 decided or P3 in force; an explicit live authorisation (T-0009 card, `depends_on`) |
| Next permissible actions | **Claude (OD-0092):** Phase B implementation work on H6, then H11, on branches (distil 1 accepted and manifest v0.2 approved, OD-0093). **Owner:** name the two held-out stress cases (OD-0089); optionally, a held-out external-data case for the architect (OD-0084); the Authorisation B prerequisites (below); optionally an OD assigning a Codex smoke review to test hiomux end to end. Also harness-0.9: H7 timing; branch protection on `main`; whether OD-0061 covers hiomux-delivered reports (§14 G5); the unrecorded hiomux change (OD-0077 finding 1). Also: the T-0002 rights reading (U1 to U7); the controls decision; observations v0.3 (blob `61ddd58e`) approve or defer; the run-1 stale-line candidates |

## Branches holding work not on `main`

| Branch | Head | Holds |
|---|---|---|
| `proposal/harness-0.9` | `2df83b4` (pushed) | harness-0.9 revision 4: the design record for Phase B (§6) and H7 (§7), and the Fable dry-run report. Phase A is applied on `main` (OD-0091) |

## Work cards

| Work | Card | Status |
|---|---|---|
| A01 decisions review | [T-0001](registers/tasks/T-0001-owner-review-a01-decisions.md) | proposed (criteria met by OD-0008, OD-0011; acceptance not recorded) |
| S1 source rights | [T-0002](registers/tasks/T-0002-verify-s1-source-rights.md) | **in_progress**: evidence drafted ([matrix](docs/research/T-0002-owner-verification-matrix.md)); awaiting the owner's verification |
| Equity total-return source | [T-0003](registers/tasks/T-0003-equity-total-return-source.md) | **in_progress**: scorecard drafted; vendor questions need owner approval |
| HIO-001 boundary (SMSF side) | [T-0004](registers/tasks/T-0004-hio-001-boundary-amendment.md) | submitted_for_review; review READY, received (OD-0040); **not accepted, not merged** |
| HIO-S1 walking skeleton | [T-0005](registers/tasks/T-0005-hio-s1-walking-skeleton.md) | S1a stage **accepted** (OD-0042); S1b staged under HIO-ADR-0012 |
| S1b-1.0 cash capture | [T-0009](registers/tasks/T-0009-s1b1-cash-capture-and-research.md) | **accepted** (OD-0079) at `846974b`, integrated `7eba3f9`; finality staging and Authorisation B remain |
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
- mark any source permission verified (D7 was the owner's act, OD-0076), or declare S1b accepted;
- change HIO-001, or `macsmsf`;
- treat a branch, a merge or a handoff as approval;
- commit secrets, or any data whose rights do not allow public redistribution (the repository
  is public, OD-0019).
