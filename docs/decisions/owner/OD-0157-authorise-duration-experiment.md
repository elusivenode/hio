---
id: OD-0157
title: "Owner authorises one bounded, pre-registered construction experiment on the Treasury par yield curve (T-0020, E-0001), ending in a local exploratory release labelled UNREFERENCED; the download waits for the owner's confirmation of the page reading"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-authorise-duration-experiment.md (owner's message, verbatim)
  sha256: ec5714417707def20b56a62e3fa6eea98d08c1f474c8ad05250ee53ba712061f
  date: 2026-11-04
  quote: "yes, authorise the duration experiment"
base_revision: bde61d74f8b97e7e7c6d50c15a76939a9e77a26e
related: {adrs: [], tasks: [T-0019, T-0020], findings: [], ods: [OD-0139, OD-0150, OD-0153, OD-0155, OD-0156]}
---

# OD-0157: the duration experiment

Claude's question was whether the owner authorises one bounded, pre-registered construction experiment on the Treasury par yield curve, ending in a local `exploratory` release labelled UNREFERENCED. The solution architect advised yes (`20261104T122134-ask-11b6`, the fifteenth consultation), which grants nothing.

## Authorised, in this order

1. Task card T-0020 and spec 0.1.3, repointed to `us_treasury.par_yield_curve`.
2. Pre-registration E-0001, **merged before any data is downloaded**: sample start, conditional on checking coverage from 1990; handling of missing, duplicate or conflicting rows; the zero-curve method; pass and fail bars; separate diagnostics before and after the December 2021 method change, keeping the crossing period in the sample.
3. One one-off download with a declared User-Agent, at most 40 requests, on the owner's Mac; not CI, not the evidence store; labelled `reconstructed(T)`.
4. Claude records the rights conditions as met, in an OD, with evidence.
5. A parser, the 10-year funded total return using the T-0019 calculation, the per-period decomposition and the zero-curve repricing sensitivity; a local `exploratory` release.
6. A Codex review, on an assignment Claude drafts and the owner approves.

The strongest result allowed is **"construction diagnostics completed; UNREFERENCED"**, never "factor validated".

## Held

**The download waits for the owner's confirmation that the three live pages were read.** Claude asked for it as a limit on this experiment, and this message didn't answer it. Steps 1 and 2, and code on synthetic inputs, can proceed.

## Not authorised

- Use by any consumer; any `as_known_by_market` claim; approving the spec; accepting the result.
- Scheduled capture; bills, H.15, GSW or AU data; any other tenor as a factor.
- Any change to capture code, workflows or infrastructure. Research pauses if capture needs attention during the soak.
- **Values in the repository.** `quotation_in_documents` is `unknown`, so raw data and return values stay outside it. The repository gets only counts, hashes and pass or fail results.

## Corrections (append-only)
