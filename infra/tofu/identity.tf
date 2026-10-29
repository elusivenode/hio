# The capture workflow writes through a federated managed identity: no key, secret or token is stored
# in GitHub or in this repository. The owner reads through a separate, read-only assignment.

resource "azurerm_user_assigned_identity" "capture" {
  name                = "id-hio-capture"
  resource_group_name = azurerm_resource_group.hio.name
  location            = azurerm_resource_group.hio.location
}

# The subject is GitHub's immutable form (numeric owner and repository ids), supplied at apply time
# through var.github_oidc_subject and never committed.
resource "azurerm_federated_identity_credential" "capture" {
  name                      = "github-capture"
  user_assigned_identity_id = azurerm_user_assigned_identity.capture.id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = var.github_oidc_subject
}

# Create-only. `blobs/add/action` creates a new blob; overwriting needs `blobs/write`, which this role
# does not grant, and there is no delete, move or super-user action. The store layer also has no
# overwrite or delete call (src/hio/storage/blobstore.py), and the immutability policy is a third layer.
resource "azurerm_role_definition" "capture_writer" {
  name        = "HIO capture writer (create-only)"
  scope       = azurerm_storage_account.evidence.id
  description = "Create and read evidence blobs in the HIO container. No overwrite, no delete."

  permissions {
    actions = []
    data_actions = [
      "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
      "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action",
    ]
  }

  assignable_scopes = [azurerm_storage_account.evidence.id]
}

resource "azurerm_role_assignment" "capture_writer" {
  scope              = azurerm_storage_container.evidence.id
  role_definition_id = azurerm_role_definition.capture_writer.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.capture.principal_id
}

resource "azurerm_role_assignment" "owner_reader" {
  scope                = azurerm_storage_container.evidence.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = var.reader_principal_object_id
}
