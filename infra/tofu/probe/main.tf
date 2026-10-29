# The B-2 storage-validation probe (T-0012). A separate, short-lived root module: its own resource group,
# account, container, identity and role. Nothing here is shared with the evidence store (infra/tofu/).

resource "azurerm_resource_group" "probe" {
  name     = "rg-hio-probe"
  location = var.location
}

resource "azurerm_storage_account" "probe" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.probe.name
  location                 = azurerm_resource_group.probe.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "ZRS"

  # Same settings as the evidence account, so the probe observes the same behaviour.
  is_hns_enabled                  = false
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true

  # Versioning on, and deliberately NO blob or container soft-delete retention: retained soft-deleted
  # items would outlive the one-day period and block the destroy.
  blob_properties {
    versioning_enabled = true
  }

  # The only difference from the evidence account: a one-day period, Unlocked, so objects become
  # deletable one day after creation and the account can be destroyed.
  immutability_policy {
    allow_protected_append_writes = false
    state                         = "Unlocked"
    period_since_creation_in_days = 1
  }

  network_rules {
    default_action = "Allow"
    bypass         = ["AzureServices"]
  }
}

resource "azurerm_storage_container" "probe" {
  name                  = "probe"
  storage_account_id    = azurerm_storage_account.probe.id
  container_access_type = "private"
}
