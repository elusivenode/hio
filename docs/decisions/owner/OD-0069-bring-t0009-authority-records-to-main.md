---
id: OD-0069
title: "Bring the T-0009 authority records (OD-0062 to OD-0065, the T-0009 card, the S1b-1 readiness package) to main by byte-identical import, and rewrite STATUS.md; documentation only, nothing approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-decision-0-authority-to-main.md
  sha256: 32cbbcd23da061ff38726004a8b2ec2462b511f1751a2e6060f3be5e7e3cc9ac
  date: 2026-10-28
  quote: "do decision 0 first"
applies_to:
  - path: STATUS.md
    revision: eb19ef760fe3f03d47882e4a1aa8ab46df01486e   # base: origin/main
  - path: (records listed below)
    revision: ce0c3b534ac98eb89663cf15c439f5ccad93b969   # source: impl/t0009-shared-receipt-and-storage
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: []}
---

# OD-0069: bring the T-0009 authority records to `main`

## Owner action

"do decision 0 first". Decision 0 is item 0 of `docs/decisions/harness-0.9-proposal.md` §9 at
`f5ce1b8`: bring OD-0062 to OD-0065 and the T-0009 card to `main`, and rewrite `STATUS.md`, so
that `main` alone answers "what is authorised now?". The owner selected it ahead of the rest of
harness-0.9, and it does not depend on harness-0.9.

## What was done

On `docs/od0069-t0009-authority-to-main`, cut from `origin/main` at `eb19ef7`:

1. **Byte-identical import** from `ce0c3b5` (`git checkout ce0c3b5 -- <path>`). The blob ids
   equal the source's:

   | Path | Blob |
   |---|---|
   | `docs/decisions/owner/OD-0062-authorise-s1b1-development-and-staging-direction.md` | `216835de5c8d` |
   | `docs/decisions/owner/OD-0063-approve-opentofu-and-s1b1-0-finality-staging.md` | `5bf72f470196` |
   | `docs/decisions/owner/OD-0064-f1-file-retention-direction.md` | `81bd8cd5135f` |
   | `docs/decisions/owner/OD-0065-authorise-shared-receipt-correction-and-storage.md` | `24820bf33a21` |
   | `docs/history/2026-10-25-owner-s1b1-authorisation-a-and-staging.md` | `de416f818f82` |
   | `docs/history/2026-10-25-owner-opentofu-and-staging-approval.md` | `d3ca044fd31b` |
   | `docs/history/2026-10-25-owner-f1-file-direction.md` | `562eb6ff9b70` |
   | `docs/history/2026-10-25-owner-shared-receipt-and-storage-authorisation.md` | `c2db3953ebb4` |
   | `registers/tasks/T-0009-s1b1-cash-capture-and-research.md` | `8d909f7ff04c` |
   | `docs/evidence/S1B1-readiness-package.md` | `175bd0fc0d49` |

   The readiness package goes beyond the literal wording of decision 0. It is included because
   OD-0062 and the T-0009 card cite it as their evidence, and they should be readable from `main`.
2. **Index rows:**
   - the four OD-index rows for OD-0062 to OD-0065, taken verbatim from the source branch;
   - history-index rows for the four transcripts, which the source branch had not added;
   - this record and its transcript.
3. **`STATUS.md` rewritten** as current state, with T-0009 in it. The packed OD history was
   removed; the OD index is that log.

## Scope and exclusions

No code, test, spec, infrastructure or `reviews/` file moves to `main`. The implementation stays
on `impl/t0009-shared-receipt-and-storage` (`ce0c3b5`), unmerged and unaccepted. The handoff and
the review-assignment draft of that branch stay there.

The T-0009 card keeps its own front matter (`status: proposed`, `authorised_by: OD-0062`), so on
`main` it reads exactly as it was recorded. Authorisation A covers synthetic-fixture development
only.

## What this record does NOT do

- It approves, accepts or waives nothing.
- It does not authorise S1b-1 or any live operation, verify any source right, or decide Q-013.
- It does not adopt any part of harness-0.9: decision 0 was chosen as a stand-alone fix.
- It does not start T-0009 remediation (OD-0067).

## Corrections (append-only)

None.
