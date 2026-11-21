---
id: OD-0192
title: "Assignment of one Codex review of E-0004 and the IEF NAV reader, under the standing delegation (OD-0184 A2)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (A2; approved, correction 1)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
applies_to:
  - path: main
    revision: 6720c5c34a130db8ae0a6196fa530e10f3888e91
base_revision: c6886d9e50d034f3a21cb57fa5d736e2a078592c
related: {adrs: [], tasks: [T-0023], findings: [], ods: [OD-0184, OD-0188, OD-0189, OD-0190, OD-0191]}
---

# OD-0192: review of E-0004

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-11-22-e0004-1` |
| Target | E-0004 steps 1, 1b and 2 and their inputs: `tools/bls_cpi_fetch.py`, `tools/e0004_state.py`, `tools/e0004_info.py`, `tools/e0004_precision.py`, `tools/e0004_estimate.py`, the iShares reader in `tools/t0023_reference.py`, their tests, `docs/evidence/e0004/` and `docs/evidence/t0023/corroboration-2.md` |
| Base SHA | `c6886d9e50d034f3a21cb57fa5d736e2a078592c` |
| Head SHA | `6720c5c34a130db8ae0a6196fa530e10f3888e91` (`main`) |
| Scope | **(a)** whether the tools implement the preregistration as adopted at `067bd7b` (OD-0190), with the two readings recorded before the run (OD-0191 and its correction 1): the state rule and its timing, the information count, the precision check (no real-alignment delta), the bootstrap, the decision rule, the four sensitivities; and whether the tests would catch errors in them. **(b)** Whether each claim in `step1-1.md`, `step1b-1.md`, `result-1.md`, `cpi-first-release-check-1.md` and `corroboration-2.md` is supported, narrowed or overstated by the code and the preregistration. **(c)** Whether anything in the sequence let the result be steered after the fact. |
| Excluded | **No licensed data** (no EODHD bytes or values, nothing under `~/.hio-research/`), no Azure, no vendor URL. Public reads only. BLS public pages may be read |
| Limit stated up front | the reviewer can't reproduce the real-input runs; it reviews code, tests and records |
| Review branch | `review/e0004-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0192-assign-e0004-review.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

## Not authorised

Accepting E-0004 or any result; a second run.

## Corrections (append-only)
