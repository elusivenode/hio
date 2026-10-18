---
id: HIO-STD-REL
title: Dataset releases, runs and artefacts
status: proposed
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
decisions: [HIO-ADR-0006, HIO-ADR-0009]
---

# Dataset releases, runs and artefacts (v0.1)

## 1. Object layout (HIO bucket)

```
receipts/<source_id>/<yyyy>/<mm>/<receipt_sha256>          # raw bytes, write-once
releases/<dataset_id>/<release_sha256>/data.parquet        # + manifest.json
artefacts/<artefact_kind>/<artefact_id>/<content_sha256>/  # envelope.json + payload
catalogue/<record_type>/<yyyy>/<mm>/<record_id>.json       # append-only records (runs, receipts index, vintages, releases, rights, status changes)
```

**Content addressing.** An object's key contains the SHA-256 of its canonical bytes. Canonical
bytes are defined as follows:
- **Parquet:** written with a pinned library version, sorted rows, a fixed schema order, and no
  writer-time metadata, **or** hashed over a canonical CSV rendering. The choice is fixed in S1
  and recorded in the manifest.
- **JSON:** UTF-8, sorted keys, no insignificant whitespace.

## 2. Dataset release manifest

Fields:
- `release_id` (hash), `dataset_id`, `version`, `created_at`;
- `inputs`:
  - receipts and vintage cuts as (`series_id`, `knowledge_mode`, `knowledge_cutoff`);
  - or upstream `release_id`s;
- `spec_ref`: for example `factor_id@version`;
- `code_ref`: commit, image or lock digest;
- `knowledge_mode`, `knowledge_cutoff`, `weakest_knowable_basis`;
- `rights` (propagated, per the rights standard);
- `quality_summary`;
- `invariant_results`;
- `supersedes`;
- `status`.

## 3. Runs

Every job writes a run record:
- `run_id`, `job`, `trigger` (schedule or manual), `started_at`, `ended_at`;
- `code_ref`, inputs and outputs (ids);
- `outcome` (`ok | failed | partial`), and a message.

## 4. Artefact envelope (consumer contract)

Fields:
- `artefact_id`, `kind`, `version`, `status`, `as_of`;
- `knowledge_mode`, `knowledge_cutoff`, `weakest_knowable_basis`;
- `lineage` (run and release ids, spec versions, code ref);
- `rights` (as it applies to the consumer class);
- `uncertainty` (methods and fields present);
- `limitations` (proxy and non-market risks);
- `payload` (files and hashes);
- `content_hash`;
- `summary` (human-readable).

## 5. Status lifecycle

```
draft → exploratory → validated → approved_for_consumer(<class>)
            ↘ withdrawn       ↘ superseded / deprecated
```

| Transition | Who | Requires |
|---|---|---|
| → `exploratory` | producing job | invariants pass |
| → `validated` | independent reviewer + owner acknowledgement | review record: method, invariants, triangulation, reproducibility rebuild |
| → `approved_for_consumer(C)` | owner | rights gate for C passes; a named decision or use |
| → `withdrawn` | owner | reason recorded; consumers notified through the handoff and status change record |

## 6. Reproducibility

A release or artefact is reproducible when a clean checkout of `code_ref`, given the same input
receipts and cuts, produces the same `content_hash`. CI tests this for every new release kind,
and periodically for existing ones.

## 7. Consumers

- A consumer pins `artefact_id` + `content_hash`.
- It validates the envelope against the published contract schema version.
- It refuses an artefact whose status is below its required status, or whose rights exclude
  its class.
