---
id: HIO-EVIDENCE-B3-PLAN-DIFFERENCES
title: "The two differences a full OpenTofu plan shows after the targeted alert apply"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0147
---

# Plan differences

Read-only. Nothing was applied. A full plan at `ac36cbf` shows these two beyond the alert, which is now applied (OD-0146).

| Resource | Plan adds | Live, read with the owner's login | Effect if applied | Reading |
|---|---|---|---|---|
| `azurerm_storage_account.evidence` | `network_rules`: default `Allow`, bypass `AzureServices` | default `Allow`, bypass `AzureServices` | none expected: the values are the same | the code declares a block that state doesn't hold. Why state lacks it isn't established |
| `azurerm_monitor_diagnostic_setting.evidence_blob` | `log_analytics_destination_type = "Dedicated"` | the API returns `null` | not established | **The purpose of the setting holds regardless:** `StorageBlobLogs`, which the alert reads, held 5 of 5 successful `PutBlob` writes to `catalogue/attempts/` over the first runs |

**Recommendation.** Leave both. Neither affects capture or the alert, and the evidence account is the last thing to touch during the soak. Every full plan will keep showing them. Look again when a change to `infra/tofu` next needs a full apply.
