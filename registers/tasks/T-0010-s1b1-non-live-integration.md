---
id: T-0010
title: "S1b-1 non-live integration: real transport confined to the adapters, Azure blob backend, OIDC and disabled workflow wiring, C1–C7 finality on synthetic inputs, 2027 calendars, draft H3/H4 evidence"
status: accepted   # OD-0123 at 62adccd; W-5 (2027 calendars) an open gap; nothing live
owner: owner
assignee_role: "implementation engineer (Claude orchestrator with hiomux Sonnet workers; independent reviewer: Codex, when assigned)"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0115
base_revision: a56462cb60a002324f90097da28168396c8ae918
accepted_by: OD-0123   # at 62adccd3cc1febff28b491f5564c9cae2f047202, merged into main as 73f2e40
review_required: independent (Codex), assigned separately by the owner
links:
  adrs_governing_approved: [HIO-ADR-0012, HIO-ADR-0010, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0002]
  adrs_context_proposed: []
  specs: [cash.aud.overnight@0.2.0, cash.usd.overnight@0.2.0]
  standards: [docs/standards/return-accounting-and-factor-construction.md]
  findings: []
  depends_on: [T-0009 (accepted, OD-0079)]
  blocks: ["Authorisation B (T-0009 §8)", "S1b-1 stage completion"]
---

# T-0010: S1b-1 non-live integration

> **Authorised by OD-0115.** Nothing here permits a real fetch, a credential, provisioning, an enabled schedule, or
> a right to be treated as verified. Role: implementation agent. Status of the work: `authorised`.

## Purpose and rationale

Live point-in-time capture cannot be reconstructed later (charter §6). T-0009 built the capture components on fixtures;
the deployable code is still missing (`src/hio/sources/transport.py` has no real client; `src/hio/jobs/s1b1_capture.py`
refuses live runs). This card builds everything that does not need live authority, so that Authorisation B can be
given at a concrete deployable revision as soon as H1, H3 and H4 are decided.

## Owner-authorised scope (OD-0115)

| # | Work | Acceptance evidence |
|---|---|---|
| W-1 | Real HTTP transport implementing `Transport`, confined to the adapters; `check_repo` amended to allow a network client only in that module and still refuse one elsewhere | tests against a local server or fake only; a deliberate client elsewhere fails `check_repo`; no test touches the network |
| W-2 | Azure blob backend behind the existing store interface (write-once, verified-on-read) | tests against a local emulator (Azurite) or the existing fake, including immutability: overwrite and delete fail |
| W-3 | OIDC and capture-workflow wiring; live-capture path behind the existing refusal, enabled only by a later Authorisation B change | workflow has no enabled `schedule`; `s1b1_capture` still refuses live runs without an explicit authorisation switch; no secret or identity id committed |
| W-4 | C1–C7 checks and finality (HIO-ADR-0012 §4.3.3–4.3.4) on synthetic inputs | a test per check showing it catches its violation; finality refuses unless every input qualifies |
| W-5 | 2027 RITS and NSW calendars, by a manual documentation read within D7 (OD-0076) | dated, cited files beside the 2026 ones; if unpublished, recorded as a gap |
| W-6 | Draft H3 (controls; OD-0038 successor) and H4 (storage settings) evidence packs, `proposed` | owner decision packs, each item a precise yes/no |

Invariants (as T-0009): S1a semantics and the four S1a `data.csv` sha256; return mathematics; the fail-closed rights gate;
P3 `schedule_only` placement; the `macsmsf` boundary; the full suite, `ruff` and `check_repo` pass.

## Exclusions

Any request to a data source; credentials, federated identities, secrets; `tofu init/validate/plan/apply`; provisioning;
an enabled schedule; P1/P2; FX; WM/Reuters and ASX; S1b-2; any right marked verified; a Codex assignment.

## Environment and rights constraints

No credentials. Workers read only the repository and synthetic fixtures. D7 pages may be read manually by the
orchestrator for W-5 only. Every other source: unknown means deny.

## Decision dependencies

H1 (owner rights reading, T-0002 U1–U7), H3, H4, H5 and Authorisation B, all owner acts (T-0009 §8).

## Intended outputs and next approval gate

A branch `feat/t0010` with W-1 to W-6; a handoff; then the owner may assign a Codex review. Acceptance is a separate act.

## Submission (filled by the implementer)

Branch `feat/t0010`, base `150f813`; head: the commit adding this section. hiomux run `20261029T020010Z-e5b6`, Sonnet
workers W1–W4, W7, each `hiomux check`ed and integrated at its `checked_sha`.

| Item | Delivered | Evidence |
|---|---|---|
| W-1 transport | `src/hio/sources/http_transport.py` (stdlib, https only, no proxy/cookies/credentials, bounded redirects, size and time); `check_repo` network allowance for that file only | `tests/test_t0010_transport*.py` (loopback only) |
| W-2 Azure backend (OD-0117) | `src/hio/storage/azure_blob.py`, `azure_auth.py`; `azure-storage-blob`, `azure-identity` hash-locked; `azure` imports confined by `check_repo` | `tests/test_t0010_azure*.py` (offline fakes). **Unverified until H4 S-6:** Azure immutability enforcement; C5 with whole-second `Last-Modified` |
| W-3 wiring | live path in `src/hio/jobs/s1b1_capture.py` behind `LIVE_AUTHORISATION = None`; `infra/workflows/s1b1-capture.yml` in live shape, still outside `.github/` | `tests/test_t0010_capture_cli.py`; `tests/test_s1b1_remediation_schedule.py` |
| W-4 finality | `src/hio/marketdata/finality.py` (C1–C7, vintage and release finality, fail closed); not called by any build | `tests/test_t0010_finality.py` |
| Notices (OD-0118) | `quality_summary.notices` on every S1b-1 release; register derivation conditions satisfied | `tests/test_t0010_notices.py`; A-2 and build tests updated |
| W-5 calendars | **Gap:** the RBA 2027 holiday page is not published (2026-10-29); review moved to 2026-12-01 | `registers/sources.yaml` `rba_calendar_pages` |
| W-6 packs | `docs/evidence/S1B1-H3-H4-decision-pack.md`, adopted by OD-0119 | — |

Full suite 747 passed; `ruff`, `ruff format`, `check_repo` and trailers PASS. Known issues (low): finality re-reads per key;
an SDK retry can turn a lost create response into `BlobExists` for this caller's own bytes (resolved by the store's
identical-bytes check). **Owed for Authorisation B, not this card:** the five data-source URLs (unset by design;
approved with the rights); `LIVE_AUTHORISATION`; moving the workflow; the 2027 calendars.

## Review and acceptance

- REVIEW-2026-10-29-t0010-1 (OD-0120): NOT READY at `f345d1e`; two high findings; received by OD-0121.
- VERIFY-2026-10-29-t0010-1-1 (OD-0122): READY at `62adccd`; both findings verified_closed; received by OD-0123.
- **Accepted by OD-0123** at `62adccd3cc1febff28b491f5564c9cae2f047202`; merged into `main` as `73f2e40` (PR #21).
