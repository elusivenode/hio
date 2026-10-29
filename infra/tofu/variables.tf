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
  description = "Replication for the evidence account: ZRS (default) or GZRS only. Locally redundant and read-access types are not allowed. The off-provider second copy is a separate control."
  type        = string
  default     = "ZRS"

  validation {
    condition     = contains(["ZRS", "GZRS"], var.account_replication_type)
    error_message = "account_replication_type must be ZRS or GZRS."
  }
}

variable "immutability_period_days" {
  description = "Account-level default immutability period for objects, in days (default 3650, about ten years). Owner decision before apply. The policy stays Unlocked; locking is a separate, deliberate owner action."
  type        = number
  default     = 3650

  validation {
    condition     = var.immutability_period_days >= 1 && var.immutability_period_days <= 146000
    error_message = "immutability_period_days must be between 1 and 146000."
  }
}

variable "github_oidc_subject" {
  description = <<-EOT
    The exact OIDC subject GitHub puts in the capture workflow's token. GitHub's immutable subject
    format carries the numeric owner and repository ids:
    'repo:<owner>@<owner_id>/<repo>@<repo_id>:environment:<env>'. The plain 'repo:<owner>/<repo>' form
    does not match. No default: the value is read from GitHub and supplied at apply time, never
    committed.
  EOT
  type        = string

  validation {
    condition     = can(regex("^repo:[^/]+@[0-9]+/[^:]+@[0-9]+:environment:.+$", var.github_oidc_subject))
    error_message = "github_oidc_subject must use the immutable format 'repo:<owner>@<owner_id>/<repo>@<repo_id>:environment:<env>'."
  }
}

variable "reader_principal_object_id" {
  description = "Object id of the owner's user, who gets read-only access. No default."
  type        = string
}

variable "network_default_action" {
  description = "Allow or Deny (default Allow). GitHub-hosted runner addresses are not stable, so Allow relies on identity alone; Deny needs a self-hosted runner or a private path (a control decision)."
  type        = string
  default     = "Allow"

  validation {
    condition     = contains(["Allow", "Deny"], var.network_default_action)
    error_message = "network_default_action must be Allow or Deny."
  }
}

variable "log_retention_days" {
  description = "Retention of the audit logs in the Log Analytics workspace, in days (default 90)."
  type        = number
  default     = 90

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "log_retention_days must be between 30 and 730."
  }
}

variable "owner_email" {
  description = "Owner address for alert and budget notifications. No default, never committed; supplied at apply time."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+$", var.owner_email))
    error_message = "owner_email must look like an email address."
  }
}

variable "alert_enabled" {
  description = "Whether the no-attempt-write alert is enabled. Off until live capture starts (B-3), because before then nothing is written and the rule would fire every hour (OD-0126 correction 1)."
  type        = bool
  default     = false
}

variable "missing_write_window_hours" {
  description = "The soak alert fires when no successful StorageWrite to the attempts prefix catalogue/attempts/ occurs in this many hours (default 26: a daily capture plus margin)."
  type        = number
  default     = 26

  validation {
    condition     = var.missing_write_window_hours >= 1 && var.missing_write_window_hours <= 48 && floor(var.missing_write_window_hours) == var.missing_write_window_hours
    error_message = "missing_write_window_hours must be a whole number of hours between 1 and 48 (the alert query looks back at most two days)."
  }
}

variable "budget_amount" {
  description = "Monthly budget for the HIO resource group, in the subscription's billing currency (default 20)."
  type        = number
  default     = 20

  validation {
    condition     = var.budget_amount > 0
    error_message = "budget_amount must be positive."
  }
}

variable "budget_start_date" {
  description = "Start of the budget period: the first day of a month, as 'YYYY-MM-01T00:00:00Z'. No default: Azure rejects a start date before the current month, so a committed value would go stale."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{4}-[0-9]{2}-01T00:00:00Z$", var.budget_start_date))
    error_message = "budget_start_date must be the first day of a month, as YYYY-MM-01T00:00:00Z."
  }
}
