---
id: OD-0161
title: "Owner confirms reading the three Treasury pages, lifting the E-0001 download hold; decides no vendor letters need be sent; accepts T-0021 at 59d03ab without a Codex review"
decision: accept
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-pages-letters-t0021.md (owner's message, verbatim)
  sha256: f28a796ac6f791fd1f178077f1c2d6caeecdfda863349e91203b7c10b77b03e4
  date: 2026-11-04
  quote: "1. yes. we do not need to send any vendor letters. 4. yes"
base_revision: 2662e1d36f959532b7892df0c9de9d94d7715d50
related: {adrs: [], tasks: [T-0003, T-0020, T-0021], findings: [], ods: [OD-0155, OD-0156, OD-0157, OD-0159, OD-0160]}
---

# OD-0161: pages read, no letters, T-0021 accepted

1. **The owner has read the three live Treasury pages.** This answers OD-0156 and lifts OD-0157's hold, so the one-off download may run. `us_treasury.par_yield_curve` no longer says the reading is unconfirmed.
2. **No vendor letters need be sent.** OD-0155's permission and the drafts stay unused. Neither the Tiingo letter nor any other goes out.
3. **T-0021 is accepted at `59d03ab`** (merged as `6c1699b`), without a Codex review, on synthetic data only. Acceptance covers the code. It establishes no investment result.

## How Claude read it

**The letters decision doesn't clear any vendor.** The assessment found no candidate cleared on published terms, and unknown means deny (`docs/research/T-0003-vendor-assessment-2026-11-04.md`). Without written answers, E-0002 Stage B has no written rights, so its test V9 can't pass as written. No vendor is chosen, no permission is marked and T-0003 Q2 stays open. **What replaces the letters is the owner's to say;** Claude has asked. Stage A's acceptance doesn't carry a Stage C run.

## Rights conditions recorded (OD-0157 item 4)

On `us_treasury.par_yield_curve`, with this OD as evidence:
- `automated_retrieval`: one one-off download, at most 40 requests, declared User-Agent, on the owner's Mac (`tools/treasury_par_fetch.py`).
- `raw_retention`: the bytes stay outside the repository, with a manifest citing Treasury and stating no implied endorsement.
- `agent_context`: Claude reads the retained file to build the parser, on the same notice. No value goes into the repository.

The compute, derivation, derived storage and `hio_internal` conditions wait for the release, which must carry the notice.

## Not authorised

Any purchase, account, or retrieval from any vendor; a second Treasury download; scheduled capture; any value in the repository.

## Corrections (append-only)
