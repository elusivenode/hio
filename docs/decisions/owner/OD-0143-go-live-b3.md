---
id: OD-0143
title: "Owner authorises go-live (Authorisation B, stage B-3) under the go-live package at 3cee431"
decision: authorise_work
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-go-live-yes.md (owner's message, verbatim, with Claude's decision put)
  sha256: 52ab78bf6130f71dcff0b860409d99a21e2622db81b156c89db0961abe7ed14a
  date: 2026-11-03
  quote: "yes, go live under the package at 3cee431"
applies_to:
  - path: docs/evidence/S1B1-go-live-package.md
    revision: 3cee4310114610bc8f12a8cbb3a6ddf10638f765
base_revision: 5c68d6c529d946009172cee3bf30c06a1481dd07
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0016], findings: [], ods: [OD-0063, OD-0116, OD-0119, OD-0139, OD-0140, OD-0142]}
---

# OD-0143: go live under the package at `3cee431`

This is the Authorisation B yes for stage B-3, and the id `LIVE_AUTHORISATION` takes.

1. **The package is adopted at `3cee431`:** its four URLs, its punctuality bar and its order of steps.
2. **The staging statement is in force for live capture:**
   > Live S1b-1 capture runs under the OD-0063 staging until finality is met: every vintage is `schedule_only`; every release is `exploratory`, states its knowledge
   > cutoff and is never labelled final; C5 is unresolved. C1–C7 evaluations, when recorded, are reported as they fall, and a failure is never overridden. Nothing
   > here discharges a finality obligation.
3. **Its decisions:**
   - D-2 option A: startup failures are accepted only for the slots on the step 3 list, until each expires.
   - D-3: up to six requests per file on a bad day is accepted within the RBA reading.
   - D-4: no `~/.hio-state/` backup is required at go-live. This settles the conflict with revision 1's prerequisite 3.
   - D-5 option B: one Codex review of the go-live PR.
4. **Authorised:**
   - T-0016, the go-live PR, built by Claude;
   - one Codex review of it, `REVIEW-2026-11-03-t0016-1`, whose head is recorded here by correction once the PR exists;
   - the package's steps on the day and the I-5 test, confirming the exact variable change with the owner first;
   - the soak.

## Not authorised

Accepting T-0016, which stays a separate owner act after the review, so the go-live PR is not merged before it; waiving any finding; any URL, dataset or operation beyond the package;
any C5 amendment or final label; S1b-2; destroying the probe account; the dead-man exercise, whose method comes to the owner first. A failure at step 4 or 6 stops the sequence and returns to the owner.

## Corrections (append-only)
