---
id: OD-0117
title: "Owner authorises a read-only az assessment of hnf-prod, tofu init -backend=false and validate, drafting T-0011 (IaC), and the Azure SDKs (azure-storage-blob, azure-identity) for T-0010; nothing provisioned"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-azure-assessment-and-u7.md (owner's messages AM and AN, verbatim, with Claude's decisions put)
  sha256: 68d8e6eadfbd4a76086d35ff9cbca50ce13efbdc543755f545e9472a5c351c1b
  date: 2026-10-29
  quote: "yes to all."
applies_to:
  - path: infra/tofu/
    revision: "main at 150f81387"
  - path: registers/tasks/T-0010-s1b1-non-live-integration.md
    revision: "main at 150f81387"
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0010, T-0011], findings: [], ods: [OD-0038, OD-0063, OD-0066, OD-0115, OD-0116]}
---

# OD-0117: Azure assessment, tofu validation, T-0011, Azure SDKs

Message AN ("yes to all.") answered five decisions put by Claude after message AM. Question 5 (U7) is recorded as
OD-0116 correction 1. Questions 1 to 4 are recorded here, each as put.

## Authorised

1. **Read-only `az` assessment of `hnf-prod`**, with the owner's existing `az` login: list or show the account and
   subscription, resource groups, resources, storage accounts, role assignments, policy assignments, locks, resource
   providers, diagnostic settings, and Entra apps with their federated credentials. Raw output stays outside the
   repository (Claude's scratchpad); only a summary with no ids, tenant details or names beyond `hnf-prod` enters it.
2. **`tofu init -backend=false` and `tofu validate`** in `infra/tofu/`, downloading the azurerm provider from the
   OpenTofu registry; commit `.terraform.lock.hcl` with its provider hashes.
3. **Draft T-0011** (IaC) from the assessment and validation: remote state, the evidence store, identities, Environment
   protection, alerting and the second copy.
4. **Azure SDKs (architect's option A, consultation `20261029T121425-ask-c603`):** add `azure-storage-blob` and
   `azure-identity` as T-0010 runtime dependencies, hash-locked; allow their imports only in the Azure backend and
   authentication modules (`check_repo` enforced); a worker task to build and test the backend against fakes. This is
   the stack decision OD-0038 left open, for these two packages and their resolved dependencies only.

## Not authorised

Any create, update or delete in Azure or Entra; any login change; `tofu plan` or `apply`; a state backend; any
credential committed; provisioning; an enabled schedule; a change to the C5 rule (HIO-ADR-0012 §4.3.3); Authorisation B.
Azure's own immutability enforcement and C5's suitability for Azure's whole-second timestamps stay open until H4.

## Corrections (append-only)
