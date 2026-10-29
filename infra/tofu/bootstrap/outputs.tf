# Backend configuration values for infra/tofu (names only; no secrets, no ids).

output "resource_group_name" {
  description = "Resource group holding the state account (backend: resource_group_name)."
  value       = azurerm_resource_group.state.name
}

output "storage_account_name" {
  description = "State storage account (backend: storage_account_name)."
  value       = azurerm_storage_account.state.name
}

output "container_name" {
  description = "State container (backend: container_name)."
  value       = azurerm_storage_container.tfstate.name
}
