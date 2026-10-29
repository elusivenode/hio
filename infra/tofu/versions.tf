terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote state in the separate state account (T-0011 I-2; OD-0126). Empty on purpose: every value,
  # including use_azuread_auth = true, comes from a -backend-config file kept outside the repository.
  backend "azurerm" {}
}

provider "azurerm" {
  # The subscription is a variable with no default: it is chosen by the owner at apply time and is
  # never written into this repository (public). The hnf-dev subscription is not used for HIO.
  subscription_id     = var.subscription_id
  storage_use_azuread = true

  features {}
}
