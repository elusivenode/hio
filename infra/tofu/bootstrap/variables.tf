variable "subscription_id" {
  description = "Azure subscription that will hold the HIO OpenTofu state. No default, never committed."
  type        = string
}

variable "location" {
  description = "Azure region for the HIO state store."
  type        = string
  default     = "australiaeast"
}

variable "storage_account_name" {
  description = "Globally unique storage account name (3-24 lowercase letters and digits), chosen at apply time."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "The storage account name must be 3-24 lowercase letters and digits."
  }
}

variable "account_replication_type" {
  description = "Replication for the state account."
  type        = string
  default     = "ZRS"
}

variable "state_admin_principal_object_id" {
  description = "Object id of the owner's user, who gets Storage Blob Data Contributor on the state container only. No default."
  type        = string
}
