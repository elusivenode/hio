---
id: OD-0066
title: "Owner assigns REVIEW-2026-10-25-t0009-1 (T-0009 S1b-1.0 at a fixed head) to Codex via the local exchange, and names the hnf-prod subscription as HIO's intended subscription; nothing provisioned"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-subscription-and-review-assignment.md (typed by the owner, verbatim)
  sha256: f331e308e3ace3060f879801eb408beacf156bd6248c294b95eadf4e28a89557
  date: 2026-10-25
  quote: "issue the review assignment via the communication channel"
applies_to:
  - path: impl/t0009-shared-receipt-and-storage
    revision: ce0c3b534ac98eb89663cf15c439f5ccad93b969   # the fixed head under review
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: []}
---

# OD-0066: the T-0009 review assignment, and the subscription

## Owner action

1. **Review assignment.** The owner instructs that the review assignment drafted for OD-0065
   (`docs/decisions/T-0009-review-assignment-draft.md` on branch `impl/t0009-shared-receipt-and-storage`)
   be issued to Codex through the local agent exchange. This record is the owner-authored assignment
   source (operating model section 6.2 step 1); the exchange message is only the delivery.

   | Field | Value |
   |---|---|
   | Review id | `REVIEW-2026-10-25-t0009-1` |
   | Repository | `elusivenode/hio` |
   | Base SHA | `0665b66b1af4aa51ceda89d9e95451e365b2670d` |
   | Head SHA | `ce0c3b534ac98eb89663cf15c439f5ccad93b969` (branch `impl/t0009-shared-receipt-and-storage`; fixed, never rebased or force-pushed during the review) |
   | Review branch | `review/t0009-1-codex`, cut at the head |
   | Scope | the six questions in the draft assignment at the head; reviewer writes only under `reviews/`; no PR |

2. **Subscription.** "hnf-prd": read as the `hnf-prod` subscription (the owner's earlier screenshot named `hnf-dev`
   and `hnf-prod`; `hnf-dev` was excluded). Recorded as HIO's **intended** subscription **by name only**. The
   subscription id is not recorded here (public repository) and is supplied at apply time as a variable.
   Claude's earlier caution stands as a recorded observation, not a condition: `hnf-prod` is a production
   subscription in the business tenant, so HIO resources must stay in their own resource group with
   container-scoped role assignments, and a dedicated subscription remains the cleaner separation.

## What this does not do

Provision anything, create a credential, authorise `tofu init/validate/plan/apply`, approve any source right,
decide Q-013 or the network and credential controls, authorise S1b deployment, or accept or approve the work under
review. The exchange message grants no assignment by itself.

## Corrections (append-only)

None.
