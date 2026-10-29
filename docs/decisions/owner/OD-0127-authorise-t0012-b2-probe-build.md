---
id: OD-0127
title: "Owner authorises T-0012: building the B-2 storage-validation probe (OpenTofu for a separate short-lived account, a manually dispatched probe workflow and script, offline validation and tests), and the session handoff with a STATUS update; nothing created or run in Azure"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-build-b2-probe.md (owner's message BA, verbatim, with Claude's decision put)
  sha256: dcd4b524d70868238464f4ad07cc9a10a4920e596e8bf9e17a0265340fa45f5e
  date: 2026-10-29
  quote: "Yes, please do that"
applies_to:
  - path: registers/tasks/T-0012-b2-storage-probe.md
    revision: "main at d3ae240"
related: {adrs: [HIO-ADR-0012], tasks: [T-0010, T-0011, T-0012], findings: [], ods: [OD-0117, OD-0119, OD-0125]}
---

# OD-0127: build the B-2 probe; session handoff

1. **T-0012** (card drafted with this record): the probe's OpenTofu root module (`infra/tofu/probe/`, a separate
   short-lived account with a one-day immutability period, its own identity and create-only role, local state outside
   the repository); a `workflow_dispatch`-only probe workflow in the `capture` Environment; a probe script using the
   accepted Azure backend; offline validation (`tofu validate` with `-backend=false`) and tests; hiomux worker(s).
2. **Session close:** the session handoff and the `STATUS.md` update, once the probe code is in hand.

## Not authorised

Creating the probe account or any Azure resource; running the probe workflow; any write to the evidence store; B-2
itself (comes back with a plan); B-3.

## Corrections (append-only)
