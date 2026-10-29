---
id: HIO-INFRA-TOFU
title: HIO evidence store OpenTofu definitions (authored, never applied)
status: proposed
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
---

# HIO evidence store: OpenTofu definitions (authored, never applied)

**Status: definitions only.** Nothing here has been planned or applied, and no subscription,
credential, state file or account exists. `tofu fmt` is the offline check run by the test suite.
`tofu init -backend=false` and `tofu validate` are run by the orchestrator under T-0011 (OD-0118
decision 1). `tofu plan` and `apply` touch Azure and need the owner's network and credential-control
decision and provisioning go-ahead (T-0009 section 8, H3/H4; Authorisation B).

Tool: OpenTofu (OD-0063). Resources are HIO-only (HIO-ADR-0002), all in `rg-hio-evidence`: the
storage account with one container, a Log Analytics workspace, a diagnostic setting, an action group,
a scheduled-query alert, a resource-group budget, one managed identity, and two role assignments
(a create-only writer and a separate read-only reader). The `hnf-dev` subscription is not used.

## Never in git

State, variable files and plans: `*.tfstate*`, `*.tfvars`, `.terraform/`, `*.tfplan`. State lives in a
separate container or account, **not** in the evidence store. `tools/check_repo.py` refuses them.
No subscription id, tenant id, object id, email address or GitHub numeric id is committed: each is a
variable with no default (`subscription_id`, `reader_principal_object_id`, `github_oidc_subject`,
`owner_email`, `budget_start_date`) supplied at apply time.

## Controls (each is tested by `tests/test_s1b1_infra.py`)

| Control | Definition | Documentation read 2026-10-25 |
|---|---|---|
| Flat namespace | `is_hns_enabled = false` | Microsoft Learn: version-level WORM "isn't yet supported" with a hierarchical namespace |
| Versioning | `versioning_enabled = true` | version-level WORM needs versioning |
| Immutability | account `immutability_policy`, **Unlocked**; period `immutability_period_days` (default 3650, validated 1 to 146000) | Locked cannot be removed and its period only grows; created only as Disabled or Unlocked |
| Replication | `account_replication_type`, default `ZRS`, validated to `ZRS` or `GZRS` | owner decision H4 |
| Network | `network_default_action`, default `Allow`, validated to `Allow` or `Deny` | GitHub-hosted runner addresses are not stable; `Deny` needs a self-hosted runner or private path |
| No static credentials | `shared_access_key_enabled = false`, OIDC federation | azurerm `storage_account`: argument exists, default true |
| Immutable OIDC subject | `subject = var.github_oidc_subject`, no default, validated to the immutable format `repo:<owner>@<owner_id>/<repo>@<repo_id>:environment:<env>` | GitHub's repository setting `use_immutable_subject` is on: the plain `repo:<owner>/<repo>` form does not match |
| Create-only writer | custom role: `blobs/read` and `blobs/add/action` | Put Blob: new blob needs `add/action`; overwrite needs `write` |
| Separate reader | `Storage Blob Data Reader` on the container, for `reader_principal_object_id` only | the writer identity never reads as the owner and the owner never writes |
| Conditional create | the backend contract is create-if-absent | Put Blob supports `If-None-Match: *`; an unmet condition returns 412 |
| No public access | `allow_nested_items_to_be_public = false`, private container | azurerm argument exists |
| Audit logging | `azurerm_monitor_diagnostic_setting` on the blob service: `StorageRead`, `StorageWrite`, `StorageDelete` logs and `Transaction` metrics, to a Log Analytics workspace (`log_retention_days`, default 90), `log_analytics_destination_type = "Dedicated"` so logs land in `StorageBlobLogs` | supports the C5/C6 audit (HIO-ADR-0012 section 4.3.3) |
| Soak alert | `azurerm_monitor_scheduled_query_rules_alert_v2`, a weekend-aware dead-man: fires when no successful `StorageWrite` `PutBlob` to `catalogue/attempts/` occurs in `missing_write_window_hours` (default 26), except in the quiet window Sat 00:00 UTC to Mon 18:00 UTC, when the query returns no row and the rule cannot breach; `auto_mitigation_enabled = true`; off until B-3 (`alert_enabled = false`); action group emails `owner_email` | proves only the **absence of writes**, not that capture is healthy or complete (see below) |
| Budget | `azurerm_consumption_budget_resource_group` on `rg-hio-evidence`, `budget_amount` (default 20) per month; notifications at 80% and 100% of actual spend to `owner_email` | cost guard |

### What the soak alert does and does not prove (T-0013 A-2)

- **It proves the absence of writes, nothing more.** Captures run on business days only, across
  publications, so the alert counts writes to `catalogue/attempts/` over all publications together. It
  cannot see one publication going silent while another still writes, and it says nothing about the health
  of capture. Per-slot completeness is checked by the capture job, and the soak's gap record is the
  reconciliation report (T-0013 A-1, A-3).
- **Quiet window:** Saturday 00:00 UTC to Monday 18:00 UTC (end exclusive). The legitimate weekend gap is
  about 50 hours, and the New York winter first slot is Monday 13:30 UTC, plus 3 h `LATENESS`, plus an
  ingestion allowance. In the window the query returns no row, so the rule does not breach.
- **A resolution inside the quiet window is a suppression, not a recovery.** With
  `auto_mitigation_enabled = true` a fired alert resolves when a later evaluation no longer breaches, and
  that includes the evaluation that merely entered the quiet window. Treat the silence as recovered only
  after an attempt record is seen written, not because the alert resolved.
- The window variable `missing_write_window_hours` keeps its bounds (1 to 48, Azure's two-day query limit).

### GitHub workflow-failure notification (T-0011 I-5; not narrowed)

The Azure alert covers a workflow that never ran or never wrote. It does **not** replace the GitHub
notification for a workflow that ran and failed. That notification is configured in GitHub, not in this
directory, and is specified here so it is not left to memory:

- **Setting:** in GitHub, go to *Settings > Notifications > System > Actions* (the dropdown), choose
  **Email**, tick **Only notify for failed workflows**, and **Save**. It is an account setting, not a
  repository setting. Procedure per GitHub:
  <https://docs.github.com/en/subscriptions-and-notifications/how-tos/managing-github-actions-notifications>.
- **Whose account (GitHub's recipient rule):** GitHub sends notifications for *scheduled* workflow runs to
  the user who **created or last modified the cron schedule**, or who **re-enabled a disabled workflow**,
  not to the repository owner by default. Rule per GitHub:
  <https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs>.
  The owner's account must therefore be that user, with the setting above on for that account. Any change
  of who last edits the `schedule:` line, or who re-enables the workflow, moves the notice to another
  account and **requires the verification below to be repeated**.
- **Verification before the soak counts:** the deliberate-failure test in the soak (S1-A13) must make a
  **scheduled** run fail on purpose, and the owner's account must receive the GitHub failure email. This
  must happen before the soak counts. A `workflow_dispatch` failure may be run as supplementary evidence
  but is never sufficient, because a manual run notifies whoever triggered it, not the schedule's user.
  Until the scheduled-run failure email is received, the soak does not count and this notification is
  **unverified**. The same test proves the Azure alert fires (see "Not confirmed" below).

## Not confirmed (do not rely on until `tofu validate`/`plan` after authorisation)

- `azurerm_storage_container` argument `storage_account_id` (older provider releases use
  `storage_account_name`); the deprecated `resource_manager_id` is replaced by `id`;
- `azurerm_role_definition.role_definition_resource_id`;
- the GitHub issuer and audience strings (`token.actions.githubusercontent.com`,
  `api://AzureADTokenExchange`) and the immutable subject format: not re-read this session. The subject
  must be read from GitHub (the numeric owner and repository ids) and supplied as a variable;
- per-container version-level immutability is **not** exposed by the azurerm docs read; the account-level
  default policy is used instead;
- whether a create-only identity can use every operation the client library issues (listing versions,
  large uploads via Put Block List). The objects are small and written with Put Blob;
- the log fields of the soak alert: the query reads `StorageBlobLogs` directly and assumes the columns
  `Category`, `OperationName` (`PutBlob`), `StatusText` (`Success` for a created blob) and `ObjectKey`
  containing `/catalogue/attempts/`. The diagnostic setting uses `log_analytics_destination_type =
  "Dedicated"` so logs land in `StorageBlobLogs`. Not checked against a live log record. The query has no
  placeholder for a missing table: if `StorageBlobLogs` does not exist the query errors rather than
  reading as zero writes, which is intended; `skip_query_validation = true` only lets the rule be
  created before the table exists. The deliberate-failure test (S1-A13) must prove the alert fires and
  must also show that a query error is visible to the owner;
- the diagnostic setting's `enabled_log` and `enabled_metric` categories on `blobServices/default`
  (`StorageRead`, `StorageWrite`, `StorageDelete`, `Transaction`), and the alert `window_duration`
  value `P2D` with `evaluation_frequency` `PT1H`;
- the budget's `GreaterThanOrEqualTo` operator on actual spend, and that the budget start date must be
  the first day of a month.

## Before apply: resource providers

The alert, diagnostic and budget resources need `Microsoft.AlertsManagement`, `Microsoft.Insights` and
`Microsoft.OperationalInsights` registered on the target subscription (`Microsoft.AlertsManagement` is
not registered on `hnf-prod` at the 2026-10-29 assessment). **Registration is an Azure write and a
separate owner authorisation**; this directory does not register providers.

## Decisions before apply

- Immutability period (default 3650 days) and the moment to Lock it;
- replication (`ZRS` default; `GZRS` allowed);
- network default action (`Allow` default; GitHub-hosted runner addresses are not stable);
- the subscription;
- the owner email for alerts and the budget (supplied at apply time);
- the Log Analytics retention (default 90 days), the missing-write window (default 26 hours) and the
  budget amount (default 20 per month) and start month;
- the immutable GitHub OIDC subject value, read from GitHub and supplied at apply time;
- provider registration (separate authorisation);
- the off-provider second copy;
- the Environment protection on `main`.
