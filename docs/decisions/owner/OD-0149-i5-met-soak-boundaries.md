---
id: OD-0149
title: "Owner accepts scheduled run 41741724257 as meeting I-5 and drops the deliberate failure test; soak boundaries declared"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-i5-accepted.md (owner's messages, verbatim, with Claude's decision put)
  sha256: a808d84ae1e2a75d3965869453f538d60ea5b9f3c5ccfd0a862b83d1d7d2eb63
  date: 2026-11-04
  quote: "yes, accept it as I-5 and drop the test"
base_revision: a88188211b252d7496656f520f63a211ad8f85a6
related: {adrs: [HIO-ADR-0012], tasks: [T-0013, T-0016], findings: [], ods: [OD-0143, OD-0148]}
---

# OD-0149: I-5 met; the soak's boundaries

1. **I-5 is met by evidence from a real scheduled failure.** Run `41741724257` (event `schedule`, at `ac36cbf`) failed on the expected startup gaps, and the owner confirms the GitHub failure email reached their account. `infra/tofu/README.md` asks for a run made to fail on purpose; the owner accepts this run in its place, because it shows the same thing. The check must be repeated if anyone else edits the `schedule:` lines or re-enables the workflow.
2. **The deliberate test in the package is dropped.** No `capture` variable is changed.
3. **The soak's boundaries** are in `docs/evidence/b3/soak-1.md`, under the package's bar as adopted by OD-0143.

## Not authorised

The dead-man exercise, still owed after the soak, whose method comes to the owner first; any change in GitHub or Azure.

## Corrections (append-only)
