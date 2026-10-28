# HIO-only resources: a dedicated resource group, one storage account, one container. Nothing here
# is shared with macsmsf or any other system (HIO-ADR-0002).

resource "azurerm_resource_group" "hio" {
  name     = "rg-hio-evidence"
  location = var.location
}

resource "azurerm_storage_account" "evidence" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.hio.name
  location                 = azurerm_resource_group.hio.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  # Flat namespace: version-level immutability is not supported with a hierarchical namespace.
  is_hns_enabled = false

  # No static credentials of any kind: identity-only access.
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }
  }

  # The account default for every object. Unlocked on purpose: a Locked policy cannot be removed and
  # its period can only grow, so it is locked by a deliberate owner action after the first captures.
  immutability_policy {
    allow_protected_append_writes = false
    state                         = "Unlocked"
    period_since_creation_in_days = var.immutability_period_days
  }

  network_rules {
    default_action = var.network_default_action
    bypass         = ["AzureServices"]
  }
}

resource "azurerm_storage_container" "evidence" {
  name                  = "hio-evidence"
  storage_account_id    = azurerm_storage_account.evidence.id
  container_access_type = "private"
}
