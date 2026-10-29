# The probe workflow writes through its own federated managed identity: no key, secret or token is
# stored in GitHub or in this repository.

resource "azurerm_user_assigned_identity" "probe" {
  name                = "id-hio-probe"
  resource_group_name = azurerm_resource_group.probe.name
  location            = azurerm_resource_group.probe.location
}

# The subject is GitHub's immutable form, supplied at apply time through var.github_oidc_subject.
resource "azurerm_federated_identity_credential" "probe" {
  name                      = "github-probe"
  user_assigned_identity_id = azurerm_user_assigned_identity.probe.id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = var.github_oidc_subject
}

# Create-only, as the evidence writer: `blobs/add/action` creates a new blob; overwriting needs
# `blobs/write`, which this role does not grant, and there is no delete, move or super-user action.
resource "azurerm_role_definition" "probe_writer" {
  name        = "HIO probe writer (create-only)"
  scope       = azurerm_storage_account.probe.id
  description = "Create and read blobs in the HIO probe container. No overwrite, no delete."

  permissions {
    actions = []
    data_actions = [
      "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
      "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action",
    ]
  }

  assignable_scopes = [azurerm_storage_account.probe.id]
}

resource "azurerm_role_assignment" "probe_writer" {
  scope              = azurerm_storage_container.probe.id
  role_definition_id = azurerm_role_definition.probe_writer.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.probe.principal_id
}
