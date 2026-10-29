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
  # One row with the raw WriteCount (0 when the table exists and nothing was written) outside the quiet
  # window, and no row inside it. StorageBlobLogs is named directly (no union, no placeholder
  # datatable): if the table is missing, because the diagnostic setting is not in resource-specific
  # mode or logs never arrived, the query errors and the rule shows a failure instead of reading as
  # zero writes.
  #
  # Quiet window: Saturday 00:00 UTC to Monday 18:00 UTC (end exclusive). Captures run on business
  # days only (src/hio/sources/schedule.py), so a weekend gap of about 50 hours is legitimate. Monday
  # 18:00 UTC is the New York winter first slot (13:30 UTC) + 3 h LATENESS + an ingestion allowance.
  # dayofweek() is a timespan: 0d Sunday, 1d Monday, ..., 6d Saturday. now() is the evaluation time
  # in UTC. Inside the window the query returns no row, so the rule cannot breach.
  no_attempt_write_query = <<-QUERY
    StorageBlobLogs
    | where TimeGenerated > ago(${var.missing_write_window_hours}h)
    | where Category == "StorageWrite" and OperationName == "PutBlob" and StatusText == "Success"
    | where ObjectKey contains "/catalogue/attempts/"
    | summarize WriteCount = count()
    | extend DayOfWeek = toint(dayofweek(now()) / 1d), HourOfDay = hourofday(now())
    | where not(DayOfWeek == 6 or DayOfWeek == 0 or (DayOfWeek == 1 and HourOfDay < 18))
  QUERY
}

# Dead-man alarm: fires when no successful write to the attempts prefix occurs in the window outside
# the weekend quiet window (above): a stopped workflow, a broken identity or a deleted schedule. It
# proves only the ABSENCE of writes; it says nothing about whether capture is healthy or complete
# (per-slot completeness is the capture job's check, and the soak reconciliation report is the gap
# record). auto_mitigation_enabled resolves the alert once a later evaluation no longer breaches, but a
# resolution inside the quiet window is a suppression, not a recovery: treat the silence as over only
# after a write is seen. The window is in the query; the rule looks back two days.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "no_attempt_write" {
  name                 = "alert-hio-no-attempt-write"
  resource_group_name  = azurerm_resource_group.hio.name
  location             = azurerm_resource_group.hio.location
  display_name         = "HIO: no capture attempt record written"
  description          = "No successful StorageWrite to catalogue/attempts/ in the configured window, outside Sat 00:00 to Mon 18:00 UTC. Proves absence of writes only."
  scopes               = [azurerm_log_analytics_workspace.hio.id]
  severity             = 2
  evaluation_frequency = "PT1H"
  window_duration      = "P2D"
  # Off until capture is live (OD-0126 correction 1): before B-3 nothing is written, so an enabled rule
  # would fire on every hourly evaluation. B-3 sets alert_enabled = true.
  enabled                 = var.alert_enabled
  auto_mitigation_enabled = true
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
