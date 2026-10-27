---
id: OD-0062
title: "Owner approves Authorisation A (S1b-1.0 development without live operations) and directs a simplified, staged scope for proposed T-0009; the staging of the finality obligations is proposed, not decided"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-s1b1-authorisation-a-and-staging.md (two chat messages, verbatim)
  sha256: 1319eea3809be81995f79444ae8999121fba015033261d27b6bda6c5e2bf2da0
  date: 2026-10-25
  quote: "Authorisation A approved."
applies_to:
  - path: docs/evidence/S1B1-readiness-package.md
    revision: 1e5b7e808e995f8989ead582aa6edf03904adf30   # branch docs/s1b1-readiness-package; parent origin/main 0665b66b1af4aa51ceda89d9e95451e365b2670d
  - path: registers/tasks/T-0009-s1b1-cash-capture-and-research.md
    revision: proposed   # drafted by this change
related: {adrs: [HIO-ADR-0012, HIO-ADR-0010], tasks: [T-0009, T-0002, T-0005], findings: []}
---

# OD-0062: Authorisation A and the staging direction

## Owner action

1. **"Authorisation A approved."** That is Authorisation A of the readiness package §6.2, as scoped there:
   S1b-1.0 development **on synthetic fixtures only**, plus a documentation-only storage check and the
   drafting of T-0009. It is bounded, reversible work (operating model §1.1).
2. A **scope direction for proposed T-0009** (the second message): a simplified first slice, the
   deferral of P2, Q-013 and P1, a lighter capture record, and eight numbered points, all transcribed in
   the history file. The owner asks that it be recorded as **a bounded owner-directed staging proposal**.
3. The owner notes an **Azure account is available**, and that infrastructure will be **open-source
   Terraform**, with "some rework necessary".

## What this authorises

Only what the readiness package §6.2 lists for Authorisation A, reshaped by the direction above and by
T-0009's scope. It authorises **no** network call outside documentation reads, no credential, no
provisioning, no real source, no live ingestion and no change to S1a semantics.

## What this does not do

- It does **not** authorise S1b-1 (ADR-0012 §4.2 gates (b) to (g) are unmet), S1b-2 or any live operation.
- It does **not** verify any source right; every T-0002 permission stays `unverified`.
- It does **not** decide Q-013 (it stays open), the storage provider, the network and credential
  controls, or the Terraform distribution.
- It does **not** change an approved ADR-0012 obligation. The staging of the finality-specific
  obligations is a **proposal**, with the exact decision requested in T-0009 §Staging decision. Until
  the owner records it, T-0009's capture-record scope is a draft that stays within ADR-0012 §5 as
  written, and any code that omits C1–C7 is held back.
- It accepts, approves and waives nothing.

## Corrections (append-only)

None.
