---
id: HIO-ENG-RECOVERY
title: Second copy and restore exercise (runbook)
status: proposed   # authorised build (OD-0132 item 3, T-0014 P-3); NOT approved; not yet run on a real store
owner: HIO architecture lead (owner)
version: 0.1
authorised_by: [OD-0132]
---

# Second copy and restore exercise

This runbook is for base-camp criterion 5 (`docs/base-camp.md`, proposed): a second copy of the evidence
store exists, and HIO can be restored from it without the primary. The tools were built and tested on
synthetic receipts and fake stores only (T-0014 P-3). **Building them does not establish criterion 5.** It
is established only when the steps below are run on the real store and the real state backup, which needs
the owner's choice of destination and its own authority (T-0014 execution checklist, item 2).

## What is covered, and what is not

| Covered | Not covered |
|---|---|
| Copy every object of a store into a second store; a sealed hash inventory | Choosing or provisioning the destination (the owner's decision) |
| Restore into an **empty** store without any access to the primary | Restoring real infrastructure state (the owner does this; see §6) |
| Rebuild the S1b-1 releases from pinned code, specs, lockfile and cutoff; byte comparison | Any change to return mathematics, a spec, a manifest schema or a lifecycle status |
| Canonical catalogue rows compared (never DuckDB file bytes) | Approval of anything: these tools report and decide nothing |
| Original provider metadata and audit references preserved | Treating a copy's timestamps as a C5 witness (they never are) |

## Roles and rules

- The **owner** chooses the destination, holds it separately from the primary, and runs or authorises each
  real run. An implementation agent does not read real store contents: licensed data never enters an agent
  prompt, an external service or a published artefact unless its rights record allows it. The reports hold
  keys, hashes, sizes and counts, not content.
- The destination and the inventory are written once. Nothing in these tools deletes or overwrites; the
  store layer has no such operation (`BlobBackend` has none), and an existing object with different bytes
  refuses.
- Secrets never appear in an inventory, a report or a command line. The tools take directories, not
  credentials.

## 1. Prepare

1. Check out the **pinned** code: the commit and `uv.lock` recorded in the manifests' `code_ref`. Run
   `uv sync --frozen`. A rebuild from other code is not a rebuild from pinned code, and the report says so
   (`running_code_matches_pin`).
2. Have the primary store available **read-only**, an empty destination, and a path for the inventory file
   that does not yet exist.

## 2. Copy

```
uv run python tools/second_copy.py copy --source <primary-dir> --dest <second-dir> \
    --inventory <inventory.json> --label <name-for-this-copy>
```

The tool reads every object through the store (so content addresses and single-version checks run), writes
them to the destination in commit order (data, manifests, catalogue records, attempt records last), and
verifies the destination against the inventory before it succeeds. Rerun the same command after an
interruption: it resumes, because identical objects are skipped and different bytes refuse.

The **inventory** (`hio-second-copy-inventory/1`, canonical JSON, self-hashed) holds, per object: key,
sha256, size, the **original provider metadata** (blob version id and provider write time, or a local file's
mtime, which is not a provider witness) and, separately, the copy's own metadata. It also holds the totals
by prefix and the digest of the canonical catalogue rows. Keep the inventory with the second copy **and** in
a third place: it is the key to proving the copy complete.

Read the output: `objects` and `bytes` must equal what you expect of the primary.

## 3. Verify the second copy at any time

```
uv run python tools/second_copy.py verify --store <second-dir> --inventory <inventory.json>
```

Exit 0 means every listed object is present with the listed hash and size, and nothing unlisted is present.
Exit 1 prints `missing` (listed, absent), `tampered` (different bytes, unreadable, or more than one version)
and `unlisted` (present but not in the inventory). Any non-empty list is a finding to report to the owner;
do not repair a copy by hand. An edited inventory is refused (exit 2) before any object is read.

## 4. Restore exercise: without the primary

Make the primary unavailable to the shell doing the restore (unmount it, or run on a machine that has only
the second copy and the inventory). Then:

```
uv run python tools/restore_exercise.py restore --second <second-dir> \
    --inventory <inventory.json> --target <empty-dir>
```

The restore verifies the second copy against the inventory **first** and writes nothing if it does not
match. It refuses a target that is not empty. It then writes every object in commit order, verifies the
target against the inventory, and compares the canonical catalogue rows (rebuilt from the restored records)
with the digest in the inventory. The command has no parameter for the primary.

## 5. Rebuild and compare

```
uv run python tools/restore_exercise.py rebuild --store <restored-dir> --cutoff <knowledge cutoff> \
    --rits-calendar <rits calendar files> --nsw-calendar <nsw calendar files> --check-running-code
```

The cutoff is the `knowledge_cutoff` string in the manifests. The pins (code reference, spec references,
release hashes) are read from the stored manifests and the releases are rebuilt with them from the restored
receipts, records and vintages. The comparison is the manifest bytes and every payload file, per release.
The calendars are the cited reference calendars used for the original build; the rights register is
`registers/sources.yaml`.

**Reading the report.** `identical: true` for every release, `running_code_matches_pin: true`, the catalogue
`identical: true` and an empty `missing`/`tampered`/`unlisted` are what a successful exercise shows. Anything
else is reported, not corrected: a difference may mean a changed calendar file, a different register, other
code or a damaged copy, and finding which is part of the exercise.

## 6. State restoration rehearsal (dummy state only)

Real infrastructure state can hold secrets and is not handled by these tools. To rehearse the procedure:

```
uv run python tools/restore_exercise.py dummy-state --out <backup.json>        # prints its sha256
uv run python tools/restore_exercise.py state --backup <backup.json> --sha256 <hash> --into <empty-dir>
```

The rehearsal accepts only a file marked as dummy state, checks its hash, refuses a directory that is
inside this repository or not empty, writes one file (`terraform.tfstate`, mode 0600) and runs no
infrastructure command. It reports `infrastructure_applied: false`. It proves the backup-to-isolated-
directory path works; it does not test any provider or apply anything. Restoring the **real** state is a
separate owner action with its own authority, performed by the owner against an isolated directory first.

## 7. After a real run

Record the inventory hash, the object and byte totals, the destination description (not its credentials),
and the three reports in a handoff. Adopting criterion 5 as met is the owner's decision, tied to the exact
revision of this runbook and the tools that ran. Until then this document is `proposed`.
