---
id: OD-0125
title: "Owner go-ahead to receive VERIFY-2026-10-29-t0011-1-2 (READY) with §5.12; acceptance of T-0011 at c69df9e; Authorisation B stage B-1 (infrastructure in hnf-prod, each apply after the owner's go on its plan); no capture"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-receive-verify-2-accept-t0011-b1.md (owner's message AY, verbatim, with Claude's decisions put)
  sha256: 59f4971ef658153b6e802947fce7ea8a5ffb078e6adb6456b02108ba0568e839
  date: 2026-10-29
  quote: "Yes to all"
applies_to:
  - path: review/t0011-1-verify-2-codex
    revision: f504833144a5d8c24f3792270b21113ed2bb955c
  - path: infra/t0011
    revision: c69df9e982a81e87a8fdb208ba4c66771b9664d5
related: {adrs: [HIO-ADR-0012], tasks: [T-0011, T-0009], findings: [F-REVIEW-2026-10-29-t0011-1-2], ods: [OD-0117, OD-0119, OD-0123, OD-0124]}
---

# OD-0125: second verification received; T-0011 accepted; B-1 authorised

## 1. Receipt

`VERIFY-2026-10-29-t0011-1-2`, reviewer tip `f504833144a5d8c24f3792270b21113ed2bb955c`, verdict READY. Receipt by
§6.2 step 5 through a pull request; §5.12: F-REVIEW-2026-10-29-t0011-1-2 open → verified_closed. Results appended below.

## 2. Acceptance of T-0011

**T-0011 is accepted at `c69df9e982a81e87a8fdb208ba4c66771b9664d5`**, effective once receipt (1) is complete; PR #8
(`infra/t0011`) is then merged into `main`. Limits: I-7 applied separately (OD-0118); I-8 (second copy) not built;
live scheduled-email delivery and the alert query's behaviour are verified only in the soak.

## 3. Authorisation B, stage B-1 (infrastructure)

As put in the decision, in the owner's terminal session with the owner's `az` login, `--subscription hnf-prod` on every
command, at the merged revision of T-0011:
1. register `Microsoft.Insights`, `Microsoft.OperationalInsights`, `Microsoft.AlertsManagement`;
2. `infra/tofu/bootstrap`: `init`, `plan` shown to the owner, `apply` only on the owner's "go"; state outside the
   repository;
3. `infra/tofu`: backend configuration outside the repository; `init`, `plan` shown to the owner, `apply` only on
   the owner's "go";
4. set the `capture` Environment variables `HIO_STORAGE_ACCOUNT_URL`, `HIO_STORAGE_CONTAINER`, `AZURE_TENANT_ID`,
   `AZURE_CLIENT_ID`.

Values that identify the tenant, subscription, principals, the GitHub numeric ids or the owner's email are supplied by the
owner at the prompt or in files outside the repository, and are never committed.

## Not authorised

Any data capture or write to the evidence store; B-2; B-3; setting `LIVE_AUTHORISATION`; moving the workflow; removing
the `capture` Environment's reviewer rule; locking the immutability policy.

## Corrections (append-only)
