---
id: HIO-ADR-0006
title: Immutable releases, artefact envelope, status lifecycle, consumer pinning
status: approved
approved_by: OD-0008   # at a82aa0d, blob 595e6b4f829c
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [HIO-S1]
review_record: null
---

# HIO-ADR-0006: immutable releases, artefact envelope, status lifecycle, pinning

## Decision (proposed)

- **Receipts, releases and artefacts are immutable and content-addressed** (SHA-256). A
  correction is a new object that `supersedes` the old one. Nothing is edited in place.
- **The content hash covers deterministic content only:** the manifest core, or the artefact
  envelope. Run metadata (`created_at`, run ids) and lifecycle status are kept **outside**
  content objects, so a rebuild reproduces the hash and a status change never rewrites bytes.
- **Status lifecycle** (append-only status events; effective status = the latest event;
  `withdrawn` is terminal): `draft → exploratory → validated → approved_for_consumer`, plus
  `superseded`, `withdrawn` and `deprecated`.
  - `validated` requires an independent review record.
  - `approved_for_consumer` requires owner approval for a named consumer class.
- **Consumers pin `artefact_id` + `content_sha256`.** No consumer resolves "latest". At use,
  a consumer resolves the effective status and current rights, and refuses a withdrawn
  artefact while its pinned bytes stay verifiable.
- **Every artefact carries:**
  - lineage (input content hashes, spec versions, code revision, image or lock digest; run ids
    stay in run records, outside the hash);
  - `knowledge_mode` and the weakest `knowable_basis`;
  - the rights record;
  - uncertainty fields;
  - a human-readable summary.

Detail: the [datasets, releases and artefacts standard](../standards/datasets-releases-and-artefacts.md).

## Consequences

- A trustee pack can be regenerated years later with identical HIO figures.
- Status, not location, distinguishes exploratory from approved work.

## Changelog

- 2026-10-18: created (85ef0fa).
- 2026-10-18: hash domain excludes run metadata and status; status as append-only events (T-0008, F-REVIEW-2026-10-18-a01-3). Status unchanged: proposed.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `595e6b4f829c`). Edits after that commit record status only.
