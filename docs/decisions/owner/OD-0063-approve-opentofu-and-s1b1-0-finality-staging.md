---
id: OD-0063
title: "Owner approves OpenTofu as the infrastructure-as-code tool and the S1b-1.0 staging of the HIO-ADR-0012 finality obligations (T-0009 section 6)"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-opentofu-and-staging-approval.md (typed by the owner, verbatim)
  sha256: 0b31cd5c33aa23755388481968829c2cb1a4e578e8448c69dff393838059dc8c
  date: 2026-10-25
  quote: "Approve OpenTofu and the staging decision; fix and commit"
applies_to:
  - path: registers/tasks/T-0009-s1b1-cash-capture-and-research.md
    revision: c7b51a505bb247bf7b6daed1ae52cc832f86a16e   # section 6 (the staging decision) and section 5 (IaC) as approved; later edits to the card do not change section 6
  - path: docs/decisions/HIO-ADR-0012-staged-s1b.md
    revision: d0965ccfd37a0ddefdbb5ff08a11674c3267792a   # unchanged; blob eb110ee394afa5b3a8abe612cf2e22196acbf51c
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: []}
---

# OD-0063: OpenTofu and the S1b-1.0 finality staging

## Owner action

1. **OpenTofu approved** as the infrastructure-as-code tool, in place of HashiCorp Terraform (proposed
   in T-0009 section 5 because Terraform is under the Business Source Licence).
2. **The staging decision approved**, as worded in T-0009 section 6 at `c7b51a5`. The text is:

> **For S1b-1.0 only:** (a) the section 5 row "Capture-attempt records and finality evidence" is
> discharged **in part**: records are written in full; the **C1-C7 checks, finality (section 4.3.4) and
> the 'final' release label are deferred and remain owed** before any release is called final, and
> before S1b-1 stage completion or G2. (b) ADR-0012 gate (d2) is met by declaring header semantics
> **unavailable**, and gate (d3) by the P3 rule being in force **with Q-013 left open and undecided**.
> (c) Every S1b-1.0 release is `exploratory` and states its knowledge cutoff; none may be labelled final.

3. "Fix and commit": the front-matter fault in T-0009 is corrected, and the work is committed on
   `docs/s1b1-readiness-package` (documentation only).

## Effect, and its limits

- **OpenTofu** joins the stack list as an authoring tool (a separate decision, like Q-007). Only
  `tofu fmt` is permitted under Authorisation A. `init`, `validate` and `plan` download providers
  and wait for the network and credential-control decision. Nothing may be applied, and state never
  enters git or the evidence store.
- **The staging** is a recorded scope decision against ADR-0012. **No ADR text changes.** The
  finality obligations remain owed (to the extent in (a)). The ADR's own wording already covers (b)
  and (c) (section 4.3.1 P3; section 4.3.4 exploratory); only (a) narrows what S1b-1 owes, and only for S1b-1.0.
- It is recorded here, in this OD. If T-0009's section 6 is later changed, this approval does not
  follow the change.

## What this record does NOT do

Authorise any live fetch, credential, provisioning, apply or schedule; verify any source right; decide
Q-013 (it stays open), the storage provider, the network and credential controls or Q-010; accept the
work; or change an approved standard.

## Corrections (append-only)

None.
