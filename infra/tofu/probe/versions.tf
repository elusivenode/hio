terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # No backend block on purpose: the state is local and kept outside the repository, passed with
  # -state=$HOME/.hio-state/probe.tfstate. The probe is short-lived and destroyed after B-2.
}

provider "azurerm" {
  # The subscription is a variable with no default: it is chosen by the owner at apply time and is
  # never written into this repository (public).
  subscription_id     = var.subscription_id
  storage_use_azuread = true

  features {}
}
