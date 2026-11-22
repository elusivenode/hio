---
id: OD-0211
title: "Assignment of the final Codex verification of F-2, scoped to the relocation of EODHD-dependent results (OD-0210; OD-0184 A2)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-relocate-results.md (owner's messages, verbatim, with Claude's questions; OD-0210), under docs/decisions/owner/OD-0184-standing-delegation.md (A2)
  sha256: 63f0f373b649f9904e50348a28eb64d9a08dfcc3334d60728fef3b0336a3245e
  date: 2026-11-22
  quote: "Y"
applies_to:
  - path: main
    revision: 144d39a51ebd17ddf61a0cf329816aae2706ba28
base_revision: 2f1251b3252955aa609a4618e159b254a7083a1e
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0176, OD-0184, OD-0196, OD-0206, OD-0209, OD-0210]}
---

# OD-0211: final verification of F-2, scoped to the relocation

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-11-22-e0004-1-4` |
| Target | "Response 4" in `reviews/responses/RESPONSE-REVIEW-2026-11-22-e0004-1.md` |
| Base SHA | `2f1251b3252955aa609a4618e159b254a7083a1e` (the head of VERIFY-2026-11-22-e0004-1-3) |
| Head SHA | `144d39a51ebd17ddf61a0cf329816aae2706ba28` (`main`) |
| Question 1: was the relocation done as OD-0210 defines it? | (a) Each of the ten named evidence files at the head is a stub that states no result, reading, sign, count or measure that depends on EODHD data: only what the record is, its standing, where its content is, and public reference identifiers. (b) The named summaries (`registers/experiments.yaml`, `knowledge/findings.md`, the three handoffs OD-0210 means, `STATUS.md`, the T-0003 vendor assessment) no longer state such a result. (c) `tools/results_store.py` and its tests do what Response 4 says, on invented data |
| Question 2: what result-bearing content remains in current tracked files? | An inventory for the owner, by file and line, without repeating any value: anything that still depends on EODHD data **outside** what OD-0210 relocated. OD-0210 deliberately leaves owner decision records, `docs/history/` and review records untouched, and keeps preregistrations public; list what those and any other file still hold, and say which items the reviewer thinks matter. **This inventory does not by itself decide the verdict:** the verdict on F-2 is the reviewer's own judgement of whether the finding is remediated at the head, with its reasons, given OD-0210's stated boundary |
| Regression | the relocation changed no acceptance, verdict or finding state; links and checks still pass |
| Not available to the reviewer | the local results store itself: it holds the relocated content, which the reviewer does not need to answer either question. **No licensed data:** nothing under `~/.hio-research/`, no EODHD bytes or values, no Azure, no vendor URL. Public reads only. Git history is outside the question (OD-0196) |
| Review branch | `review/e0004-1-verify-4-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0211-assign-e0004-verification-4.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

## Not authorised

Accepting any work; closing or waiving a finding.

## Corrections (append-only)
