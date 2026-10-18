---
id: OD-NNNN
title: <the decision, in one line>
kind: <approve | reject | supersede | authorise_work | accept_work | waive_finding>
status: proposed          # proposed | approved | rejected | superseded. Only the owner sets anything other than proposed.
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
drafted_by: <owner | claude/<role> | ...>
decided_by: null          # the owner's name or role; set only by the owner
decided_at: null
source: <direct owner commit | transcription of chat/meeting on YYYY-MM-DD (quote or file ref)>
applies_to:               # exact documents and revisions; a decision without a revision is invalid
  - path: <path>
    revision: <commit sha>
related: {adrs: [], tasks: [], findings: []}
---

# OD-NNNN: <title>

## Decision
What is approved, rejected, authorised, accepted or waived, stated so that it can be tested.

## Scope and exclusions
What it covers. What it explicitly does not cover.

## For a waiver only
Rationale; risk accepted; affected revision; expiry or revisit condition.

## Evidence considered
Review records, test evidence, documents.

## Next action

## Owner confirmation
_Pending._ The owner replaces this line with their confirmation (name, date) and commits with
`HIO-Actor: owner`. Until then the record is `proposed` and has no authority.
