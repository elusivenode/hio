# Audit logging and the soak alert (T-0011 I-4, I-5). Everything lives in the HIO resource group.
# Needs Microsoft.OperationalInsights, Microsoft.Insights and Microsoft.AlertsManagement registered on
# the subscription first: registration is a separate owner authorisation, not done here.
#
# GitHub workflow-failure notification is configured in GitHub (repository or account notification
# settings), not here: this file alerts on the *absence* of evidence writes in Azure.

resource "azurerm_log_analytics_workspace" "hio" {
  name                = "log-hio-evidence"
  resource_group_name = azurerm_resource_group.hio.name
  location            = azurerm_resource_group.hio.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
}

# Blob service operations of the evidence account, for the C5/C6 audit (HIO-ADR-0012 section 4.3.3).
resource "azurerm_monitor_diagnostic_setting" "evidence_blob" {
  name                       = "diag-hio-evidence-blob"
  target_resource_id         = "${azurerm_storage_account.evidence.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.hio.id

  # Resource-specific tables: logs land in StorageBlobLogs, which the soak alert queries.
  log_analytics_destination_type = "Dedicated"

  enabled_log {
    category = "StorageRead"
  }

  enabled_log {
    category = "StorageWrite"
  }

  enabled_log {
    category = "StorageDelete"
  }

  enabled_metric {
    category = "Transaction"
  }
}

resource "azurerm_monitor_action_group" "owner" {
  name                = "ag-hio-owner"
  resource_group_name = azurerm_resource_group.hio.name
  short_name          = "hio-owner"

  email_receiver {
    name                    = "hio-owner-email"
    email_address           = var.owner_email
    use_common_alert_schema = true
  }
}

locals {
  # One row with WriteCount = 0 when the table exists and nothing was written. StorageBlobLogs is
  # named directly (no union, no placeholder datatable): if the table is missing, because the
  # diagnostic setting is not in resource-specific mode or logs never arrived, the query errors and
  # the rule shows a failure instead of reading as zero writes.
  no_attempt_write_query = <<-QUERY
    StorageBlobLogs
    | where TimeGenerated > ago(${var.missing_write_window_hours}h)
    | where Category == "StorageWrite" and OperationName == "PutBlob" and StatusText == "Success"
    | where ObjectKey contains "/catalogue/attempts/"
    | summarize WriteCount = count()
  QUERY
}

# Fires when no successful write to the attempts prefix occurs in the window: a missed capture, a
# broken identity or a stopped workflow. The window is in the query; the rule looks back two days.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "no_attempt_write" {
  name                    = "alert-hio-no-attempt-write"
  resource_group_name     = azurerm_resource_group.hio.name
  location                = azurerm_resource_group.hio.location
  display_name            = "HIO: no capture attempt record written"
  description             = "No successful StorageWrite to catalogue/attempts/ in the configured window."
  scopes                  = [azurerm_log_analytics_workspace.hio.id]
  severity                = 2
  evaluation_frequency    = "PT1H"
  window_duration         = "P2D"
  enabled                 = true
  auto_mitigation_enabled = false
  skip_query_validation   = true

  criteria {
    query                   = local.no_attempt_write_query
    time_aggregation_method = "Total"
    metric_measure_column   = "WriteCount"
    operator                = "LessThan"
    threshold               = 1

    failing_periods {
      number_of_evaluation_periods             = 1
      minimum_failing_periods_to_trigger_alert = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.owner.id]
  }
}
