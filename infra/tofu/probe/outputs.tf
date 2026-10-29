# Identifiers only. There is no key, connection string or secret to output.

output "storage_account_name" {
  value = azurerm_storage_account.probe.name
}

output "container_name" {
  value = azurerm_storage_container.probe.name
}

output "probe_identity_client_id" {
  value = azurerm_user_assigned_identity.probe.client_id
}
