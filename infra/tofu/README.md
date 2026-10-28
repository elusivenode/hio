---
id: HIO-INFRA-TOFU
title: HIO evidence store OpenTofu definitions (authored, never applied)
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
---

# HIO evidence store: OpenTofu definitions (authored, never applied)

**Status: definitions only.** Nothing here has been planned, validated against the provider, or
applied. No subscription, credential, state file or account exists. `tofu fmt` is the only command
run (offline). `tofu init`, `validate`, `plan` and `apply` download providers or touch Azure and need
the owner's network and credential-control decision and provisioning go-ahead (T-0009 section 8, H3/H4).

Tool: OpenTofu (OD-0063). Resources are HIO-only (HIO-ADR-0002): one resource group, one storage account
with one container, one managed identity, two role assignments. The `hnf-dev` subscription is not used.

## Never in git

State, variable files and plans: `*.tfstate*`, `*.tfvars`, `.terraform/`, `*.tfplan`. State lives in a
separate container or account, **not** in the evidence store. `tools/check_repo.py` refuses them.

## Controls (each is tested by `tests/test_s1b1_infra.py`)

| Control | Definition | Documentation read 2026-10-25 |
|---|---|---|
| Flat namespace | `is_hns_enabled = false` | Microsoft Learn: version-level WORM "isn't yet supported" with a hierarchical namespace |
| Versioning | `versioning_enabled = true` | version-level WORM needs versioning |
| Immutability | account `immutability_policy`, **Unlocked** | Locked cannot be removed and its period only grows; created only as Disabled or Unlocked |
| No static credentials | `shared_access_key_enabled = false`, OIDC federation | azurerm `storage_account`: argument exists, default true |
| Create-only writer | custom role: `blobs/read` and `blobs/add/action` | Put Blob: new blob needs `add/action`; overwrite needs `write` |
| Conditional create | the backend contract is create-if-absent | Put Blob supports `If-None-Match: *`; an unmet condition returns 412 |
| No public access | `allow_nested_items_to_be_public = false`, private container | azurerm argument exists |

## Not confirmed (do not rely on until `tofu validate`/`plan` after authorisation)

- `azurerm_storage_container` argument `storage_account_id` and attribute `resource_manager_id` (older
  provider releases use `storage_account_name`);
- `azurerm_role_definition.role_definition_resource_id`;
- the GitHub issuer, audience and subject strings (`token.actions.githubusercontent.com`,
  `api://AzureADTokenExchange`, `repo:<owner>/<repo>:environment:<env>`): not re-read this session;
- per-container version-level immutability is **not** exposed by the azurerm docs read; the account-level
  default policy is used instead;
- whether a create-only identity can use every operation the client library issues (listing versions,
  large uploads via Put Block List). The objects are small and written with Put Blob.

## Decisions before apply

Immutability period (default 3650 days) and the moment to Lock it; replication (ZRS default);
network default action (GitHub-hosted runner addresses are not stable); the subscription; the
off-provider second copy; the Environment protection on `main`.
