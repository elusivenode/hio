# OpenTofu remote state for infra/tofu. A separate root module with its own resource group: the
# evidence store (rg-hio-evidence) never holds state, and this module is applied once with local state
# kept outside the repository (see README.md). Nothing here is shared with macsmsf (HIO-ADR-0002).

resource "azurerm_resource_group" "state" {
  name     = "rg-hio-tfstate"
  location = var.location
}

resource "azurerm_storage_account" "state" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.state.name
  location                 = azurerm_resource_group.state.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  is_hns_enabled = false

  # No static credentials of any kind: Entra-only access.
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true

  # Versioning and soft delete make an overwritten or deleted state file recoverable.
  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

# Owner-only access, scoped to the state container and nothing wider.
resource "azurerm_role_assignment" "state_admin" {
  scope                = azurerm_storage_container.tfstate.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.state_admin_principal_object_id
}
