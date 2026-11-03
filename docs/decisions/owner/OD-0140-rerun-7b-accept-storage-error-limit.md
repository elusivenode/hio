---
id: OD-0140
title: "Owner gives the go for the B-2 re-run (R-1) and step 7b, once the ~/.hio-state backup is confirmed, and accepts the storage-error limit for the soak"
decision: authorise_work
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-rerun-7b-storage-limit.md (owner's message, verbatim, with Claude's decisions put)
  sha256: f8c81d27afc2c561a517c3902ae3c49617d385490e2aa5afb909aa746db43140
  date: 2026-11-03
  quote: "yes to both"
applies_to:
  - path: docs/evidence/S1B1-B2-rerun-plan.md
    revision: dfc2e99febd25a24606a240fb471814893078670
base_revision: dfc2e99febd25a24606a240fb471814893078670
related: {adrs: [HIO-ADR-0012], tasks: [T-0015], findings: [], ods: [OD-0134, OD-0138, OD-0139]}
---

# OD-0140: re-run and 7b go; storage-error limit accepted

1. **The go for R-1 and 7b, conditional on the owner confirming the `~/.hio-state/` backup.**
   - R-1: dispatch `storage-probe.yml` on `main` with `repeats=50`, which the owner approves in GitHub, and retain the report (R-2).
   - 7b, on a key from R-1, within its one-day retention: with the owner's `az` login, `--subscription hnf-prod` named on every command, a
     temporary `Storage Blob Data Contributor` role on container `probe` only, removed and read back afterwards.
   - Only the probe account is touched. The evidence account is never touched.
   - **Stop rule (the plan's):** if deleting the retained version succeeds, stop; a storage design review comes before B-3.
2. **The storage-error limit is accepted for the soak**, as stated in Authorisation B revision 1: a storage error during capture can leave
   partial writes and skip that run's remaining slots. The run fails loudly, and the completeness check flags the gap on the next run. Any
   occurrence is recorded and may prompt a fix. This accepts the behaviour for the soak, not as a permanent design. It waives no finding,
   because none is open on it.

## Not authorised

The destroy; any C5 amendment; B-3 go-live; any write to the evidence account; running before the backup is confirmed. Adopting the re-run
plan as a standing document is not implied: only these steps are authorised.

## Corrections (append-only)

### Correction 1 (2026-11-03): backup condition dropped; 7b role changed; both run

**Owner's words:** `docs/history/2026-11-03-owner-backup-and-7b-role.md`, sha256 `9961974836968621dafd532d5d59cf9104ba11db9d6e2d7bb9edc891db8ae918`.

1. **The backup condition is dropped for R-1 and 7b.** The owner: "rebuilding state from deployed resources isn't that difficult. we can back
   up state if you really want." Claude reads this as: no backup is required for these steps. Authorisation B revision 1 lists a backup as a
   B-3 prerequisite. Claude treats the same words as making it optional there too, **open to the owner's correction at the go-live yes**.
   `~/.hio-state/` remains a single copy. Its `probe*` files were set to owner-only on the owner's "yes to all".
2. **The 7b role changed** from `Storage Blob Data Contributor` to `Storage Blob Data Owner`, on the owner's yes, on container `probe` only:
   the first role cannot delete a version, so its refusal would have proved nothing. That was an error in the plan Claude wrote.
3. **The auto-mode classifier refused Claude's role grant** ("Permission Grant"). The owner ran it with their own login, as the plan had
   said. Claude ran the removal and the read-back.
4. **Claude's first delete attempt never reached Azure**: `az storage blob delete` has no `--version-id` (exit 2), an error in the same plan.
   That was found by reading the output, before any result was reported. The delete then ran through the SDK, after the overwrite, so the
   order was not the plan's. The refusal is unaffected.

**Results:** `docs/evidence/b2/rerun-1.md`. R-1 run `41590213489`: C5 as written 45 of 50 violations, candidate 0 of 50. 7b: the retained version's
delete refused, 409 `BlobImmutableDueToPolicy`; bytes identical; the role removed. **The stop rule did not fire.** Last write 2026-11-03T06:36:50Z.
No C5 change, destroy or go-live follows from this record.
