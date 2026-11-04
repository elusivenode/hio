---
id: OD-0151
title: "Owner assigns one Codex review of T-0019 at b4929f7"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-assign-t0019-review.md (owner's message, verbatim, with Claude's question put)
  sha256: fde6113be520d49c4305d854feb03738bc537156029b6cd006637c329f02deff
  date: 2026-11-04
  quote: "yes, assign the Codex review"
applies_to:
  - path: feat/t0019
    revision: b4929f721d9772f64d5904685ccc741a5ae10224
base_revision: cbd6c8c7b421a8fecf9d4eee03a4ef82463b933f
related: {adrs: [], tasks: [T-0019], findings: [], ods: [OD-0150]}
---

# OD-0151: review of T-0019

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-11-04-t0019-1` |
| Target | T-0019, rows C-1 to C-3 of `registers/tasks/T-0019-cmt-construction-synthetic.md` at the head |
| Base SHA | `cbd6c8c7b421a8fecf9d4eee03a4ef82463b933f` |
| Head SHA | `b4929f721d9772f64d5904685ccc741a5ae10224` (`feat/t0019`, PR #83) |
| Scope | the construction against RA §6 and the proposed spec: full revaluation, coupon cash and re-strike, RA-INV-013, interpolation, street-convention pricing, date arithmetic, the decomposition, and whether the tests would catch errors in them; whether the spec is sound enough to build on; the H2 reading pack's accuracy against the matrix. No Azure access; no request to any data URL; no real yields; publishers' documentation pages may be read |
| Review branch | `review/t0019-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0151-assign-t0019-review.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

**Index row.** The row in `docs/decisions/owner/README.md` is added once #83 merges: adding it now would conflict with that PR and change its reviewed head.

## Not authorised

Accepting or merging T-0019; adopting the spec; any real data.

## Corrections (append-only)
