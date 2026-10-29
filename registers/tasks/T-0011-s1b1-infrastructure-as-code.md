---
id: T-0011
title: "S1b-1 infrastructure as code: state bootstrap, evidence store, identities, GitHub Environment and branch protection, alerting, budget and the second copy, authored and validated for hnf-prod; never applied without Authorisation B"
status: proposed   # drafting authorised by OD-0117 decision 3; the IaC work itself needs an owner instruction
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers); independent reviewer: Codex, when assigned"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: null       # OD-0117 authorises drafting this card only
base_revision: e829c83
accepted_by: null
review_required: independent (Codex), assigned separately by the owner
links:
  adrs_governing_approved: [HIO-ADR-0012, HIO-ADR-0002]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0009 (accepted, OD-0079), T-0010 (authorised, OD-0115, OD-0117)]
  blocks: ["Authorisation B (T-0009 §8: H3, H4)"]
---

# T-0011: S1b-1 infrastructure as code

> **Proposed.** OD-0117 authorises drafting this card. Authoring the IaC beyond the existing definitions needs an owner
> instruction; `tofu plan` against Azure, `apply`, provider registration and any GitHub setting change each need their
> own explicit authority (Authorisation B or a narrower yes). Role: implementation agent.

## What exists (assessed 2026-10-29 under OD-0117)

**`infra/tofu/`** (T-0009): one resource group, one storage account (flat namespace, versioning, account-level
immutability Unlocked, shared key off, no public access), one container, one user-assigned identity with a GitHub
federated credential, a create-only custom role and two role assignments. `tofu init -backend=false` and
`tofu validate` (OpenTofu 1.12.5, azurerm 4.81.0, lock file committed): **valid**, one deprecation warning
(`azurerm_storage_container.resource_manager_id`, removed in azurerm 5.0; use `id`).

**`hnf-prod`, read-only `az` assessment** (raw output kept outside the repository; no ids recorded here):

| Area | Finding |
|---|---|
| Resources | **None.** No resource groups, resources, storage accounts, identities, custom roles, locks or budgets |
| Access | Two `Owner` assignments to user principals: one at subscription scope, one inherited from a management group |
| Policy and security | Only the default Microsoft Defender for Cloud policy assignment; Defender plans `Discovery` and `FoundationalCspm` |
| Logging | No subscription diagnostic settings |
| Resource providers | `Microsoft.Storage`, `Microsoft.ManagedIdentity`, `Microsoft.Security`, `Microsoft.Consumption` registered; **`Microsoft.AlertsManagement` not registered** |
| Entra | No app registrations owned by the signed-in user |
| CLI context | The `az` default subscription is `hnf-dev`; every HIO command must name `hnf-prod` explicitly |

**GitHub** (`gh api`, read-only): the repository is public, created 2026-10-23; **`main` is not protected**; **no
Environments exist** (the identity expects `capture`); the OIDC subject uses GitHub's **immutable subject format**
(`use_immutable_subject: true`), so `identity.tf`'s `repo:<owner>/<repo>:environment:<env>` subject **will not match**.
The correct subject carries numeric owner and repository ids and must be supplied as a variable, not committed.

## Proposed scope

| # | Work | Acceptance evidence |
|---|---|---|
| I-1 | **Fix the definitions:** immutable-subject federated credential (subject from a variable); `id` for the container scope; reader identity separate from the writer | `tofu fmt -check`, `tofu validate` clean; `tests/test_s1b1_infra.py` extended |
| I-2 | **State bootstrap:** a separate resource group and storage account for OpenTofu state (versioning, soft delete, Entra-only auth, owner-only access), applied once with local state and then migrated; the evidence store never holds state | separate config under `infra/tofu/bootstrap/`; validate clean; the runbook for the one-time migration |
| I-3 | **Evidence store decisions** wired as variables: immutability period and the moment to lock; replication (ZRS or GZRS); network default action (GitHub-hosted runner addresses are not stable) | owner decision pack (H4) with each item a yes/no |
| I-4 | **Audit logging:** storage account diagnostic settings for blob write and read operations to a Log Analytics workspace (supports the C5/C6 audit, HIO-ADR-0012 §4.3.3) | validate clean; retention stated |
| I-5 | **Alerting for the soak:** an action group to the owner, an alert when no attempt record is written in a capture window, and GitHub workflow failure notification; needs `Microsoft.AlertsManagement` (and `Microsoft.Insights`, `Microsoft.OperationalInsights`) registered | validate clean; the deliberate-failure test of S1-A13 planned |
| I-6 | **Budget:** a subscription or resource-group consumption budget with an alert | validate clean |
| I-7 | **GitHub:** a `capture` Environment limited to `main`, with the owner as required reviewer for any manual dispatch; branch protection on `main` (also an open STATUS item) | applied by the owner or by `gh` under its own yes; recorded |
| I-8 | **Second copy (off-provider):** a destination and copy job for receipts and records | owner decision: destination and rights (`external_processing` applies to any new host) |

## Exclusions

`tofu plan` or `apply`; any Azure or Entra write, including provider registration; any GitHub setting change; any
credential or id committed; an enabled schedule.

## Decision dependencies

H3 (controls; the OD-0038 successor) and H4 (storage), each as an owner decision pack; then Authorisation B, which
should name the exact apply steps: bootstrap, evidence store, identities, alerting, GitHub settings.

## Submission (filled by the implementer)

## Review and acceptance
