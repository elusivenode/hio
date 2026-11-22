---
id: OD-0233
title: "Owner authorises building the dimensional silver's first version for the fund path, then the gold-mart foundation"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-approved-silver-and-gold-foundation.md (owner's message, verbatim, with Claude's question)
  sha256: e1f27a56cdb52f92a43ab7ebf4a2277d6d67afd64007a0129bbcb11444b65624
  date: 2026-11-22
  quote: "Approved."
base_revision: 62e7f9ddba78b1fb615fd3cabe330f3a33a15d24
related: {adrs: [HIO-ADR-0003, HIO-ADR-0009], tasks: [T-0024], findings: [], ods: [OD-0199, OD-0231, OD-0232]}
---

# OD-0233: build the dimensional silver, then the gold-mart foundation

## Owner action

**Authorised, in this order:**

1. **Dimensional silver, first version, fund path:** a proposed instrument register with HIO codes for the nine funds; the table contract (`docs/decisions/silver-v2-contract.md`, proposed); worker-built code on invented data; Claude's runs on the real snapshots.
2. **The gold-mart foundation:** a Python API with explicit pins, mart specifications and a build planner, and the first two marts (a monthly factor panel and portfolio returns), tested against today's analytics outputs.
3. Evidence notes for each.

**Tests declared before the build:**

- each version 1 silver file is reproduced byte for byte from version 2, for all nine funds;
- every fund series built through version 2 is byte-identical to its existing build;
- a rebuild from a restored backup gives the same hashes.

**"Approved" is recorded as authorising this work.** It was the answer to a question that said a yes "adopts no design as approved and accepts nothing", so both proposals stay `proposed`.

## Where the build follows the architect and not Claude's first advice

The architect's advice on gold (consultation `20261122T193241-ask-cee5`, advice only) agrees with Claude's on the main lines: Python builders with exact decimal arithmetic for returns, floating point only for statistics, DuckDB for set work and querying, content-addressed builds, a small planner, no dbt and no orchestrator. Claude takes two of its points over its own: new code goes into the existing package contexts under the approved import rules, not one new `hio.lake` package; and today's portfolio outputs, which use floating point, are preserved as they are, with any exact-decimal portfolio accounting a separate later change.

## The owner's later direction, not authorised here

"Once we get to the stage of wanting to orchestrate a daily pipeline, I think a vm hosting prefect in azure could lift the model to an always on , cloud hosted version." Recorded as the owner's intended direction. Nothing here builds, provisions or costs it. `docs/architecture.md` §5 names the measured trigger for a workflow orchestrator and requires an ADR to adopt one.

## What this record does NOT do

It adopts no model, approves no proposal, accepts no series, and authorises no hosted or cloud component, no new source and no change to how any return is calculated.

## Corrections (append-only)

None.
