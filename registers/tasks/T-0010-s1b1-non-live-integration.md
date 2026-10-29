---
id: T-0010
title: "S1b-1 non-live integration: real transport confined to the adapters, Azure blob backend, OIDC and disabled workflow wiring, C1–C7 finality on synthetic inputs, 2027 calendars, draft H3/H4 evidence"
status: authorised
owner: owner
assignee_role: "implementation engineer (Claude orchestrator with hiomux Sonnet workers; independent reviewer: Codex, when assigned)"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0115
base_revision: a56462cb60a002324f90097da28168396c8ae918
accepted_by: null
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

## Review and acceptance
