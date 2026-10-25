variable "subscription_id" {
  description = "Azure subscription that will hold the HIO evidence store. No default, never committed."
  type        = string
}

variable "location" {
  description = "Azure region for the HIO evidence store."
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
  description = "Replication for the evidence account. The off-provider second copy is a separate control."
  type        = string
  default     = "ZRS"
}

variable "immutability_period_days" {
  description = "Account-level default immutability period for objects, in days. Owner decision before apply."
  type        = number
  default     = 3650
}

variable "github_repository" {
  description = "The repository whose capture workflow may write evidence."
  type        = string
  default     = "elusivenode/hio"
}

variable "github_environment" {
  description = "The GitHub Environment the capture workflow runs in. It is limited to the main branch."
  type        = string
  default     = "capture"
}

variable "reader_principal_object_id" {
  description = "Object id of the owner's user, who gets read-only access. No default."
  type        = string
}

variable "network_default_action" {
  description = "Allow or Deny. GitHub-hosted runner addresses are not stable, so Allow relies on identity alone; Deny needs a self-hosted runner or a private path (a control decision)."
  type        = string
  default     = "Allow"
}
