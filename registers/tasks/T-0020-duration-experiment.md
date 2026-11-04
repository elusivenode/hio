---
id: T-0020
title: "US duration construction experiment E-0001, UNREFERENCED, on the Treasury par yield curve"
status: authorised
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex, once the owner approves the assignment"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0157
base_revision: bde61d74f8b97e7e7c6d50c15a76939a9e77a26e
review_required: owner and Codex
links:
  adrs_governing_approved: []
  adrs_context_proposed: []
  specs: [specs/factors/rates.us.cmt_10y.total_return.yaml]
  standards: [docs/standards/return-accounting-and-factor-construction.md, docs/standards/factor-specification.md, docs/standards/rights-and-licensing.md]
  findings: []
  depends_on: [T-0019]
  blocks: ["the analytical reader card (factor-first proposal, question 4)"]
---

# T-0020: the duration experiment

> **Authorised by OD-0157.** It shows whether the construction works, not whether the factor is valid. The spec stays proposed. **No download until E-0001 is merged and the owner has confirmed reading the live pages.**

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| X-1 | Spec 0.1.3; hypothesis H-0005 and experiment E-0001, pre-registered | merged before any download |
| X-2 | `src/hio/library/zero_curve.py`: the bootstrap and repricing in the spec, on invented inputs | `tests/test_t0020_zero_curve.py`, including ZC-INV-1 to 3 |
| X-3 | A parser and a one-off fetch tool, on synthetic fixtures first; fetch refuses without the rights gate | tests; at most 40 requests, stops on any surprise |
| X-4 | Rights conditions recorded as met, with evidence, in an OD | the gate allows the operations named, and still refuses the parent row |
| X-5 | A driver: fetch once, then build, diagnose and release locally, with `reconstructed(T)` and the notices | two runs byte-identical |
| X-6 | `docs/evidence/e0001/` with counts, hashes and pass or fail only; E-0001's results | `check_repo`; no value in the repository |

## Where the data lives

Outside the repository, in `~/.hio-research/E-0001/`: raw bytes, the manifest, the local store and all values. `data/` and `.hio-store/` aren't used, because the reviewer's sandbox blocks both. **Codex must read the actual bytes, not Claude's hashes.** Its read access to this path is to be tested before the assignment is drafted; if it fails, the assignment says how the bytes reach it.

## Exclusions

As OD-0157 lists. Also: no change to `src/hio/sources/` capture paths, `src/hio/jobs/s1b1*`, workflows or `infra/`; no new dependency (numpy waits for its own decision).

## Submission (filled by the implementer)

X-1 merged in `de834d8`. X-2 on branch `feat/t0020-zero-curve`, on invented yields only. X-3 to X-6 not started: the parser waits for the real file's format, because a parser built on an assumed layout failed live in T-0017. No data downloaded.
