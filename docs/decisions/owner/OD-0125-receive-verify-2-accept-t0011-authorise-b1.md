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

### Correction 1 (2026-10-29): receipt completed; §5.12; T-0011 accepted and merged

**Receipt:** T `f504833144a5d8c24f3792270b21113ed2bb955c` (tip = fetch = report); 3 added files, sha256 reconciled both
ways; README unchanged; assignment check passed as written; tag `reviews/VERIFY-2026-10-29-t0011-1-2` peels to T; import
`912bdbc`; merged as `0a47384` (PR #25); 5.10 verified (remote `main` = local; blobs equal T). **Received.**

The receipt was interrupted once by the owner after the tag was pushed and before the import (5.11, "tag pushed, no
import"); on the owner's "please continue where you got to" it resumed at 5.5 with the same T.

**§5.12 (this commit):** the *Assigned reviews* row set to received; a *Verification rounds* row;
F-REVIEW-2026-10-29-t0011-1-2: open → **verified_closed** at `c69df9e`. All five findings of REVIEW-2026-10-29-t0010-1 and
-t0011-1 are now verified_closed.

**Decision 2 effective:** T-0011 accepted at `c69df9e`; PR #8 merged into `main` as `09d4886`; `infra/tofu` on `main` is
identical to `c69df9e`. The T-0011 card is set to accepted in this commit. **B-1 may now proceed** as authorised.
