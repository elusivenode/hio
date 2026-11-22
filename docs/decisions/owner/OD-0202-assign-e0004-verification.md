---
id: OD-0202
title: "Assignment of one Codex verification of the E-0004 review's two findings, under the standing delegation (OD-0184 A2) and OD-0201"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-e0004-deviation.md (owner's message, verbatim, with Claude's question; OD-0201), under docs/decisions/owner/OD-0184-standing-delegation.md (A2)
  sha256: 68f37d96e21403e44f7eee11eb74cbc3d4f81d4ac8e1e9c0278236c5d3e885ee
  date: 2026-11-22
  quote: "Y"
applies_to:
  - path: main
    revision: f349efeaaf1cd3540e8b206d5f79e511ee1f2410
base_revision: 6720c5c34a130db8ae0a6196fa530e10f3888e91
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0184, OD-0192, OD-0195, OD-0196, OD-0197, OD-0198, OD-0200, OD-0201]}
---

# OD-0202: verification of the E-0004 review's findings

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-11-22-e0004-1-1` |
| Target | the remediation claims in `reviews/responses/RESPONSE-REVIEW-2026-11-22-e0004-1.md` for F-REVIEW-2026-11-22-e0004-1-1 and -2 |
| Base SHA | `6720c5c34a130db8ae0a6196fa530e10f3888e91` (the reviewed head) |
| Head SHA | `f349efeaaf1cd3540e8b206d5f79e511ee1f2410` (`main`) |
| Scope | **F-1:** whether the claim is true as stated and sufficient: that every CPI level the state reads has a retained first release; that exactly four first-published levels differ from the flat file; that the states recomputed from first-release levels equal the run's in all 233 periods under the primary rule and the equality sensitivity; that the addenda say this and no more, and leave the adopted preregistration text unchanged; whether `tools/bls_cpi_releases.py` and `tools/e0004_first_release_states.py` and their tests would catch an error in any of it. The claim is a recorded deviation with no rerun (OD-0201): say whether that closes the finding, narrows it, or leaves it open. **F-2:** whether the current files at the head hold any measurement derived from EODHD returns. The git history is kept by the owner's decision (OD-0196) and is outside the question. **Regression:** nothing else in the E-0004 tools, tests and records changed in a way that breaks the original review's conclusions |
| Local reads allowed | **BLS-derived files only:** `~/.hio-research/E-0004/raw/`, `~/.hio-research/E-0004/releases/`, `~/.hio-research/E-0004/releases-2005/`, `~/.hio-research/E-0004/first-release-states/`, and the one file `~/.hio-research/E-0004/runs/20261121T230030Z-6745c1fd/states.csv`. The reviewer may run the committed tools on them, writing only under its own temporary directory |
| Excluded | **No licensed data:** nothing else under `~/.hio-research/` (in particular no other file under `E-0004/runs/`, and nothing under `T-0023/`, `E-0001/`, `E-0002/`), no EODHD bytes or values, no Azure, no vendor URL. Public reads only; BLS public pages may be read, sparingly, to spot-check a release |
| Limit stated up front | the reviewer can't reproduce the estimation run; it verifies the CPI side from the retained bytes, the code, the tests and the records |
| Review branch | `review/e0004-1-verify-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0202-assign-e0004-verification.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

## Not authorised

Accepting E-0004 or any result; a rerun; closing or waiving a finding (the verification's verdict is received, and finding states change only by owner-authorised reconciliation).

## Corrections (append-only)
