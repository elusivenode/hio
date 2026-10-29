# Cost guard for the HIO resource group only (T-0011 I-6). Needs Microsoft.Consumption, which is
# already registered on the target subscription.

resource "azurerm_consumption_budget_resource_group" "hio" {
  name              = "budget-hio-evidence"
  resource_group_id = azurerm_resource_group.hio.id
  amount            = var.budget_amount
  time_grain        = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = [var.owner_email]
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Actual"
    contact_emails = [var.owner_email]
  }
}
