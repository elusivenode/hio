---
id: T-0023
title: "Make the AUD defensive-sleeve comparison independently challengeable"
status: in_review   # steps 1 to 7 done, unreviewed and unaccepted (OD-0177, OD-0178, OD-0179, OD-0180); IEF's NAV not obtained; recommendation proposed
owner: owner
assignee_role: "implementation engineer (Claude orchestrator)"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0176
base_revision: 569f338956ae02840207da977e1df2bc6cbde5e2
review_required: owner; Codex assignment by owner
links:
  adrs_governing_approved: []
  adrs_context_proposed: []
  specs: []
  standards: [docs/standards/return-accounting-and-factor-construction.md, docs/standards/rights-and-licensing.md]
  findings: []
  depends_on: [T-0022]
  blocks: []
---

# T-0023: consolidate, then decide on one conditional experiment

> **Authorised by OD-0176, adopting §6 of `docs/history/2026-11-04-architect-calibration.md`.** Exploratory: not a release, recommendation or acceptance of any data.

## Scope, in order

1. **Fix `intervals_span_zero`:** classify each block length, and say "distinguished at every block length" only when true.
2. **Freeze the panel:** a panel identity, and one command that rebuilds it and the comparison from retained inputs, naming exactly what ran.
3. **Corroborate the three sleeves,** especially 2008, from sources already authorised or publicly readable. Report what can't be corroborated rather than bridging it.
4. **Account for the cash seam,** separating agreement of method from accuracy of the historical rates.
5. **Record what remains:** FX and close timing, vehicle basis, and the SPY gap to the issuer.
6. **Compare the already identified stress episodes,** declared before running, as retrospective description only.
7. **Recommend** whether one conditional-diversification experiment is warranted, and what it needs.

## Out of scope

New data sources without their own yes; regime or predictive models; new assets or hedging; any change to standards or infrastructure; values in the repository.

## Acceptance evidence

A permitted verifier can trace the decisive reference facts to underlying bytes or an independent read; rebuild evidence identifies what ran; discrepancies are accounted for; the conclusion holds under the declared sensitivities, or is narrowed. A hash or author transcription alone doesn't close the external-evidence gap.

## Stop and ask

If corroboration needs a new source, the owner chooses between obtaining it and accepting a narrower claim.
