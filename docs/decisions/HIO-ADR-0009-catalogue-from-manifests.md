---
id: HIO-ADR-0009
title: Catalogue derived from immutable manifests; no hosted database initially
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [HIO-S1 infrastructure]
review_record: null
supersedes_proposal: "18 Oct proposal §4.1 (small hosted Postgres catalogue)"
---

# HIO-ADR-0009: catalogue from manifests, no hosted database initially

## Context

- The 18 October proposal included a hosted Postgres catalogue from the start.
- In S1 the catalogue holds a few hundred records:
  - sources;
  - receipts;
  - vintages;
  - releases;
  - runs;
  - rights.
- These records are written append-only, by jobs that never write concurrently.

## Options

| Option | For | Against |
|---|---|---|
| Hosted Postgres from S1 | online query; familiar | a second system of record beside the object store; a credential; backup; running cost; drift between database and bytes |
| **Append-only manifest records in the object store + a DuckDB index rebuilt locally or in CI** | one system of record; trivially recoverable; zero running cost; portable | no concurrent writers; rebuild latency grows with volume |
| Lakehouse table format | time travel; concurrency | premature |

## Decision (proposed)

Option 2. The adoption triggers for a hosted catalogue are in
[`architecture.md` §5](../architecture.md#5-measurable-evolution-triggers).

## Consequences

- The manifest schema becomes a contract from S1 (`src/hio/contracts`).
- Migrating to a hosted catalogue later is a load from manifests. No data is at risk.

## Approval

_Unapproved._
