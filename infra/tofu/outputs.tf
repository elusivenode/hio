# Identifiers only. There is no key, connection string or secret to output.

output "storage_account_name" {
  value = azurerm_storage_account.evidence.name
}

output "container_name" {
  value = azurerm_storage_container.evidence.name
}

output "capture_identity_client_id" {
  value = azurerm_user_assigned_identity.capture.client_id
}

output "tenant_id" {
  value = azurerm_user_assigned_identity.capture.tenant_id
}
