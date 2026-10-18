---
id: OD-NNNN
title: <the owner action, in one line>
decision: <authorise_work | accept_work | approve | reject | waive_finding | supersede>
record_status: draft      # draft (text awaiting an owner statement; no authority) | recorded | corrected | superseded
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
recorded_by: <owner | claude/<role> | ...>
owner_statement:          # required for record_status: recorded. The authority is the statement, not this file.
  source: <path to the verbatim owner message or directive under docs/history/, or an owner-authored commit>
  sha256: <hash of the source file, if a file>
  date: YYYY-MM-DD
  quote: <the operative words>
applies_to:               # exact documents and revision(s)
  - path: <path>
    revision: <commit sha>
related: {adrs: [], tasks: [], findings: []}
---

# OD-NNNN: <title>

## Owner action
What the owner explicitly instructed, accepted, approved or waived. Use the owner's words; do
not upgrade them.

## Scope and exclusions

## For a waiver only
The original finding id (preserved), rationale, risk accepted, affected revision, expiry or
revisit condition, and the accountable owner.

## What this record does NOT do
For example: authorising work does not accept its result or approve any ADR.

## Corrections (append-only)
Date, what the earlier record said, and what is corrected and why.
