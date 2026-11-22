---
id: OD-0232
title: "Owner asks for a proposed dimensional model of the silver layer, with the architect consulted as a Kimball expert"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-silver-dimensional-model.md (owner's message, verbatim)
  sha256: bd304a356782b555cc19cd972073c8c1943fdee90e97a543d69982e8a22227fe
  date: 2026-11-22
  quote: "I would like data in silver to be a dimensional model. Propose a set of facts and dimensions and model our source data. Get the architect to act as a kimball expert and suggest a clean, robust silver layer data model"
base_revision: 03b72fe5122c847b1554936ee128104955afc7ff
related: {adrs: [HIO-ADR-0003, HIO-ADR-0009], tasks: [T-0024], findings: [], ods: [OD-0081, OD-0089, OD-0231]}
---

# OD-0232: a dimensional model for silver, proposed

## Owner action

**Authorised:** a proposal. Claude drafts a set of facts and dimensions over HIO's source data, and consults the solution architect, asked to act as a Kimball expert, for its own model. The result is `docs/decisions/silver-dimensional-model-proposal.md` (proposed).

**The owner's direction:** silver is to be a dimensional model.

## What this record does NOT do

It authorises no build of the model, no change to the silver sets or tools built under OD-0231, and no new source. Building it is a later owner decision. The architect's answer is advice (OD-0081).

## Corrections (append-only)

None.
