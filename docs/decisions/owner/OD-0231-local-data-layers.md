---
id: OD-0231
title: "Owner authorises local bronze, silver and gold data layers, immutable and reconstructable, in files or DuckDB at Claude's choice"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-data-layers.md (owner's message, verbatim)
  sha256: b8141fb95d9570fcc163f60c436b54edfccfe0efd9dcc5815db96e01bd4b7331
  date: 2026-11-22
  quote: "I am happy to produce our layers using custom data structures and leverage files or duckdb. The choice is yours and I favour an immutable, reconstruct able approach."
base_revision: 0f2a008d111ed619a5ac054774959e98661fd191
related: {adrs: [HIO-ADR-0009], tasks: [T-0024], findings: [], ods: [OD-0163, OD-0176, OD-0199, OD-0210, OD-0213, OD-0230]}
---

# OD-0231: local data layers

## Owner action

**Authorised:** building HIO's local research data as three layers (bronze, silver, gold), immutable and reconstructable, using files or DuckDB as Claude chooses. Claude's choice and the contract the tools are built to are in `docs/decisions/local-data-layers-proposal.md`.

**Read as included:**

1. Worker-built tools, tested on invented data: a silver builder, a factor build that reads silver, a catalogue rebuilt from manifests, and a backup with a restore test.
2. Claude's runs of them on the real local stores, with real-data checks.
3. Proposed observation specs, and a factor spec version where a correction moves from a factor spec to silver.

## Owner direction on the vendor data

The owner states: "The data will not be used by any third parties, only locally for personal financial research. This is well within the terms of use and I want you to stop raising it." Claude records this as the owner's reading and stops raising the subject. Local storage, local databases and local backups of the research data are within it.

## What this record does NOT do

It authorises no hosted database, no cloud storage and no publication. It accepts no series, adopts no spec and approves no design: the proposal stays `proposed`. The approved storage design (`docs/architecture.md` §2, HIO-ADR-0009) is not amended.

## Corrections (append-only)

**1 (2026-11-22).** The owner named the backup target: "Can you access to folder level in which the hio repo is situated? Create the backup folder there". Claude created `hio-backup` beside the repository, outside it, and ran the first backup there (`docs/evidence/factors/data-layers-1.md`).
