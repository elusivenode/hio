---
id: HIO-INFRA-TOFU-BOOTSTRAP
title: HIO OpenTofu state bootstrap (authored, never applied)
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
---

# HIO OpenTofu state bootstrap (authored, never applied)

**Status: definitions only (T-0011 I-2, OD-0118 decision 1).** Nothing here has been planned or applied.
`tofu init`, `plan` and `apply` touch Azure and need **Authorisation B**; nothing in this directory is
applied without it. The `hnf-dev` subscription is not used.

This is a **separate root module** from `infra/tofu/`. It creates the home of the OpenTofu remote state for
`infra/tofu/`: one resource group (`rg-hio-tfstate`, distinct from `rg-hio-evidence`), one storage account and one
private container (`tfstate`). The evidence store never holds state.

## Controls (each is tested by `tests/test_t0011_bootstrap.py`)

| Control | Definition |
|---|---|
| Entra-only access | `shared_access_key_enabled = false`, `default_to_oauth_authentication = true` |
| No public access | `allow_nested_items_to_be_public = false`, container `private`, TLS 1.2, https only |
| Recoverable state | blob versioning on; blob and container soft delete, 30 days |
| Flat namespace, ZRS default | `is_hns_enabled = false`; `account_replication_type` defaults to `ZRS` |
| Owner-only | `Storage Blob Data Contributor` for `state_admin_principal_object_id`, scoped to the **container** only |

## Never in git

State, variable files, plans and provider caches: `*.tfstate*`, `*.tfvars`, `*.tfplan`, `.terraform/`, and the
`-backend-config` file below. `tools/check_repo.py` refuses most of these. Subscription, tenant and object ids are
supplied at apply time and never written into this repository (public). State never enters the evidence store, a
handoff, a review record or any published artefact.

## One-time runbook (needs Authorisation B; every command names the subscription explicitly)

`<STATE_DIR>` below is a directory **outside** the repository (for example under the owner's home directory, mode
700). The bootstrap's local state lives there and is backed up by the owner.

1. **Apply the bootstrap with local state kept outside the repository.** From a copy of, or with `-chdir` to,
   `infra/tofu/bootstrap`:

   ```
   tofu -chdir=infra/tofu/bootstrap init
   tofu -chdir=infra/tofu/bootstrap plan  -state=<STATE_DIR>/bootstrap.tfstate -out=<STATE_DIR>/bootstrap.tfplan \
        -var subscription_id=<hnf-prod subscription id> \
        -var storage_account_name=<chosen name> \
        -var state_admin_principal_object_id=<owner object id>
   tofu -chdir=infra/tofu/bootstrap apply -state=<STATE_DIR>/bootstrap.tfstate <STATE_DIR>/bootstrap.tfplan
   ```

   The owner reviews the plan before apply. The plan file and the `.terraform/` directory are not committed.
2. **Read the backend values:** `tofu -chdir=infra/tofu/bootstrap output` gives the resource group, account name
   and container name (no secrets).
3. **Write a backend config file outside the repository**, `<STATE_DIR>/backend.hcl`, never committed:

   ```
   resource_group_name  = "rg-hio-tfstate"
   storage_account_name = "<chosen name>"
   container_name       = "tfstate"
   key                  = "hio-evidence.tfstate"
   subscription_id      = "<hnf-prod subscription id>"
   use_azuread_auth     = true
   ```
4. **Add the backend block under a separate, owner-authorised change** to `infra/tofu/versions.tf`
   (`backend "azurerm" {}`, empty: all values come from the config file, and `use_azuread_auth = true` selects
   Entra authentication, not an access key). This module does not add it.
5. **Migrate:** `tofu -chdir=infra/tofu init -migrate-state -backend-config=<STATE_DIR>/backend.hcl`. Confirm the
   state object appears in the `tfstate` container (versioning on), then keep the bootstrap's own local state
   file safe: it is the only record of this module and is not migrated.
6. **Verify:** `tofu -chdir=infra/tofu plan` against the remote backend shows no unexpected change.

## Not confirmed (do not rely on until `tofu validate` and an authorised `plan`)

- Whether `azurerm_storage_container.id` is the ARM resource id in the pinned provider (the card's I-1 note says to
  use `id` rather than the deprecated `resource_manager_id`). If `plan` shows a data-plane URL as the role scope,
  the scope must be corrected before apply.
- The applying principal needs permission to create role assignments (for example Owner) at the resource group.
- Backend `use_azuread_auth` needs `Storage Blob Data Contributor` on the container: that is the one assignment made
  here. A CI identity for state is not provided and would need its own owner decision.
