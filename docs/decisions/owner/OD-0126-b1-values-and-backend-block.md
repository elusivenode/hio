---
id: OD-0126
title: "Owner approves the B-1 values (state directory, account names, budget start date) and adding an empty azurerm backend block to infra/tofu/versions.tf; the alert email is still to be named"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-b1-values-and-backend.md (owner's message AZ, verbatim, with Claude's request)
  sha256: 617e1a30567864284d4ad21ef2a5736bd0f4327695cad6d2ee110221e7561cd1
  date: 2026-10-29
  quote: "Approved"
applies_to:
  - path: infra/tofu/versions.tf
    revision: "main at 0d909e5"
related: {adrs: [], tasks: [T-0011], findings: [], ods: [OD-0125]}
---

# OD-0126: B-1 values; the backend block

- **Backend block:** `infra/tofu/versions.tf` gains an empty `backend "azurerm" {}` (bootstrap runbook step 4); every
  value comes from `~/.hio-state/backend.hcl`, never committed. `tofu validate` and the infra tests pass.
- **Values (not committed beyond these names):** state directory `~/.hio-state/` on the owner's Mac (owner keeps a
  copy); state account `hiotfstatek835`; evidence account `hioevidencek835`; budget start date `2026-11-01`.
- **Read, not typed:** subscription id, owner object id, the OIDC subject (immutable format, environment `capture`).
- **Still owed:** the alert email (Claude asked which address; the reply did not name one). The evidence-store plan
  waits for it.

## Corrections (append-only)
