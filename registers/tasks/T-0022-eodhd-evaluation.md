---
id: T-0022
title: "One-month EODHD Personal plan evaluation: data qualification and first USD portfolio comparison"
status: submitted_for_review
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex, one focused review"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0162
base_revision: 9b399221684defd643c4d68fbb42b42e80b80b4d
review_required: owner and Codex
links:
  adrs_governing_approved: []
  adrs_context_proposed: []
  specs: []
  standards: [docs/standards/return-accounting-and-factor-construction.md, docs/standards/rights-and-licensing.md]
  findings: []
  depends_on: [T-0021]
  blocks: []
---

# T-0022: the EODHD evaluation

> **Authorised by OD-0162. No retrieval until:** the owner has subscribed and stored the key, the owner's rights decision is recorded, and E-0002 is pre-registered. It qualifies data, and approves nothing for any consumer.

## Workspace

`~/.hio-research/E-0002-eodhd/`, mode 700, outside the repository and separate from E-0001: `raw/` response bytes, `manifest.json`, `store/` local releases, `reports/` for the owner. The key lives in the HIO key vault (OD-0164), and never in a file, argument, log or URL on record.

## Scope

Phases A to E of the brief, then its single consolidated assessment. Tests cover event handling, return accounting, incomplete observations, date alignment and refusal of prohibited operations.

## Exclusions

As OD-0162 lists. No change under `src/hio/sources/`, `src/hio/jobs/`, `.github/` or `infra/`.

## Submission (filled by the implementer)

Branch `feat/t0022-eodhd`. Snapshots `s1` and `s2`; assessment 1 in `docs/evidence/e0002/`: continue conditionally. **REVIEW-2026-11-04-t0022-1: NOT READY at `6f3b1e0`, five high findings, on local branch `review/REVIEW-2026-11-04-t0022-1-codex`, not received.** **VERIFY-2026-11-04-t0022-1-1: NOT READY at `bb58f85`:** F-1, F-2 and F-5 technically verified closed. **VERIFY-...-1-2: NOT READY at `b410b02`:** F-3 technically verified closed; F-4 open. F-4's fix at `75c67a4`: further verification waived (OD-0169). AUD variant V2 run. Not received on `main`; not accepted.
