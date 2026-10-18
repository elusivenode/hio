---
id: T-0008
title: Correct the A01 baseline for the eight open REVIEW-2026-10-18-a01 findings (documentation and fixtures)
status: in_progress
owner: owner
assignee_role: documentation agent / quantitative researcher (Claude)
created_at: 2026-10-18
updated_at: 2026-10-18
authorised_by: OD-0005
base_revision: e99fae104908c79fc800222b9c2eb1c82fec388d
accepted_by: null
review_required: independent (Codex) verification at the submission head, assigned by the owner
links: {adrs_governing_approved: [], adrs_context_proposed: [HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006, HIO-ADR-0007], specs: [cash.aud.overnight, cash.usd.overnight, fx.usd_cash_vs_aud.excess], standards: [observations-and-point-in-time, return-accounting-and-factor-construction, datasets-releases-and-artefacts, rights-and-licensing], findings: [F-REVIEW-2026-10-18-a01-1, F-REVIEW-2026-10-18-a01-2, F-REVIEW-2026-10-18-a01-3, F-REVIEW-2026-10-18-a01-4, F-REVIEW-2026-10-18-a01-5, F-REVIEW-2026-10-18-a01-6, F-REVIEW-2026-10-18-a01-7, F-REVIEW-2026-10-18-a01-8], depends_on: [], blocks: [G1, S1 authorisation]}
---

# T-0008: A01 correction slice

## Purpose and rationale

Fix the defects Codex found in the PIT, cash, release, CMT, rights, triangulation and FX
contracts, so the A01 baseline can be re-reviewed for G1. It follows each finding's corrective
direction and adds synthetic numeric fixtures that the reviewer can reproduce.

## Owner-instructed scope (OD-0005)

Documentation, standards, specs and plans within `hio/`. Then one remediation response
(`reviews/responses/RESPONSE-REVIEW-2026-10-18-a01-1.md`) and the *Remediation claim* cells.

## Exclusions

As OD-0005.

## Acceptance evidence

- Per finding: the corrected text, plus fixtures whose arithmetic is reproducible (listed in
  the response).
- No ADR status change; no review-record edit; nothing outside `hio/`.

## Submission

Fix commit(s), then a submission-head commit adding the response. Both are named in the latest
T-0008 handoff.
