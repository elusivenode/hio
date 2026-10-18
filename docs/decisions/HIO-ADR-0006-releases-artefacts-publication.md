---
id: HIO-ADR-0006
title: Immutable releases, artefact envelope, status lifecycle, consumer pinning
status: proposed
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [HIO-S1]
review_record: null
---

# HIO-ADR-0006: immutable releases, artefact envelope, status lifecycle, pinning

## Decision (proposed)

- **Receipts, releases and artefacts are immutable and content-addressed** (SHA-256). A
  correction is a new object that `supersedes` the old one. Nothing is edited in place.
- **Status lifecycle:** `draft → exploratory → validated → approved_for_consumer`, plus
  `superseded`, `withdrawn` and `deprecated`.
  - `validated` requires an independent review record.
  - `approved_for_consumer` requires owner approval for a named consumer class.
- **Consumers pin `artefact_id` + `content_hash`.** No consumer resolves "latest".
- **Every artefact carries:**
  - lineage (run ids, release ids, spec versions, code revision, image or lock digest);
  - `knowledge_mode` and the weakest `knowable_basis`;
  - the rights record;
  - uncertainty fields;
  - a human-readable summary.

Detail: the [datasets, releases and artefacts standard](../standards/datasets-releases-and-artefacts.md).

## Consequences

- A trustee pack can be regenerated years later with identical HIO figures.
- Status, not location, distinguishes exploratory from approved work.

## Approval

_Unapproved._
