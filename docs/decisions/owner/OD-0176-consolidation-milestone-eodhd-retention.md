---
id: OD-0176
title: "Owner adopts the consolidation milestone; retains EODHD data for research in the project; all agents may review it"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-milestone-and-retention.md (owner's message, verbatim)
  sha256: f9305ba32bdb36af7b37d951a1a1b62f921f456f80b099f0b459de6daaed1100
  date: 2026-11-04
  quote: "all agents can review it."
base_revision: 569f338956ae02840207da977e1df2bc6cbde5e2
related: {adrs: [], tasks: [T-0022, T-0023], findings: [], ods: [OD-0163, OD-0170, OD-0174, OD-0175]}
---

# OD-0176: consolidation milestone and EODHD retention

## 1. The milestone

The owner adopts the architect's §6 milestone: T-0023, including routine local iterations within its named sources and descriptive scope. Any new data source needs its own yes.

## 2. Retention and agent review

- **Retention:** the owner retains the EODHD data for research use in the project. The subscription will likely continue, which is the owner's to confirm.
- **Agent review:** on the owner's own reading of EODHD's terms, all HIO agents, including Codex and the solution architect, may review the data and results. This replaces OD-0174's limit, and OD-0170's instruction not to send such values to agents.

## How Claude read it

"It" is read as **the retained data, raw and derived, and what is built on it**, because the sentence follows the retention and answers the architect's point that a verifier must be able to read the evidence. The owner can narrow this. Agents may now see values when a task or review needs them; none has been sent by this record.

## Unchanged

- **Nothing goes in the repository:** `quotation_in_documents` stays denied, and the repository is public, so reviews and records hold no values.
- **No consumers:** SMSF uses and third parties stay denied.
- **Local computation:** `external_processing` stays denied, so CI and cloud hosts still refuse.
- **Rights after termination** stay unknown in the record, because the vendor's position is unknown.
- **Acceptance:** no data or experiment is accepted, and the architect's other advice, including standing authority, isn't adopted.

## Corrections (append-only)
