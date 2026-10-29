variable "subscription_id" {
  description = "Azure subscription that will hold the short-lived HIO probe account. No default, never committed."
  type        = string
}

variable "location" {
  description = "Azure region for the probe account."
  type        = string
  default     = "australiaeast"
}

variable "storage_account_name" {
  description = "Globally unique probe storage account name (3-24 lowercase letters and digits), chosen at apply time. No default."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "The storage account name must be 3-24 lowercase letters and digits."
  }
}

variable "github_oidc_subject" {
  description = <<-EOT
    The exact OIDC subject GitHub puts in the probe workflow's token. GitHub's immutable subject
    format carries the numeric owner and repository ids:
    'repo:<owner>@<owner_id>/<repo>@<repo_id>:environment:<env>'. No default: the value is read from
    GitHub and supplied at apply time, never committed.
  EOT
  type        = string

  validation {
    condition     = can(regex("^repo:[^/]+@[0-9]+/[^:]+@[0-9]+:environment:.+$", var.github_oidc_subject))
    error_message = "github_oidc_subject must use the immutable format 'repo:<owner>@<owner_id>/<repo>@<repo_id>:environment:<env>'."
  }
}
