---
id: HIO-STD-REL
title: Dataset releases, runs and artefacts
status: approved
approved_by: OD-0008   # at a82aa0d, blob 8539be643e9d
owner: HIO architecture lead (owner)
version: 0.2
last_reviewed: 2026-10-18
decisions: [HIO-ADR-0006, HIO-ADR-0009]
---

# Dataset releases, runs and artefacts (v0.2)

## 1. Object layout (HIO bucket)

```
receipts/<source_id>/<yyyy>/<mm>/<receipt_sha256>          # raw bytes, write-once
releases/<dataset_id>/<content_sha256>/data.parquet        # + manifest.json (the manifest core, §2)
artefacts/<artefact_kind>/<artefact_id>/<content_sha256>/  # envelope.json + payload
catalogue/<record_type>/<yyyy>/<mm>/<record_id>.json       # append-only records (runs, receipts index, vintages, rights)
catalogue/status/<content_sha256>/<seq>.json               # append-only status events (§5)
```

**Content addressing.** An object's key contains the SHA-256 of its canonical bytes. Canonical
bytes are defined as follows:
- **Parquet:** written with a pinned library version, sorted rows, a fixed schema order, and no
  writer-time metadata, **or** hashed over a canonical CSV rendering. The choice is fixed in S1
  and recorded in the manifest.
- **JSON:** UTF-8, sorted keys, no insignificant whitespace.

## 2. Content identity: what is hashed, and what is not

Each release or artefact has **three kinds of data**, kept in different objects:

| Kind | Object | Mutable? | In the content hash? |
|---|---|---|---|
| **Content**: the data files, plus the deterministic manifest *core* | `releases/<dataset_id>/<content_sha256>/` or `artefacts/<kind>/<artefact_id>/<content_sha256>/` | never | yes: this *is* the hash domain |
| **Run metadata**: `created_at`, `run_id`, host, durations | the run record (`catalogue/runs/`) | append-only | **no** |
| **Lifecycle status** | status events (`catalogue/status/<content_sha256>/<seq>.json`) | append-only | **no** |

**The manifest core** (canonical JSON, UTF-8, sorted keys, no insignificant whitespace) contains
exactly:
- `dataset_id` (or `artefact_kind` + `artefact_id`), `version`;
- `spec_ref` (`factor_id@version`);
- `code_ref` (commit + lock or image digest);
- `inputs`: receipt hashes with vintage cuts (`series_id`, `knowledge_mode`, `knowledge_cutoff`),
  or upstream content hashes, sorted;
- `knowledge_mode`, `knowledge_cutoff`, `weakest_knowable_basis`;
- `rights` (the propagated record **as of build**, a snapshot; current rights are re-checked at use, §7);
- `invariant_results`; `quality_summary`;
- `files`: each data file's path and sha256, computed over the declared canonical rendering;
- `supersedes` (content hash, or null).

**`content_sha256` = sha256(canonical manifest core).** It never contains itself, `created_at`
or any status. `release_id` = `rel-` + `content_sha256`; `artefact_id` is stable across versions,
and each version is addressed by its content hash.

## 3. Runs

Every job writes a run record:
- `run_id`, `job`, `trigger` (schedule or manual), `started_at`, `ended_at`;
- `code_ref`, inputs and outputs (content hashes);
- `outcome` (`ok | failed | partial`), and a message.

## 4. Artefact envelope (consumer contract)

The envelope is the artefact's **manifest core** (§2) plus:
- `as_of`;
- `lineage` (run ids are *not* included, because they are non-deterministic; lineage is spec
  versions, input content hashes and code ref);
- `uncertainty`;
- `limitations`;
- `summary`.

For an artefact, **the hash domain is the whole canonical envelope**: `content_sha256 =
sha256(canonical envelope)`. All its fields are deterministic. **The envelope carries no
status.** It is a birth record and is never rewritten.

## 5. Status lifecycle (append-only events)

```
draft → exploratory → validated → approved_for_consumer(<class>)
            ↘ withdrawn       ↘ superseded / deprecated
```

- **A status event** is `{content_sha256, seq, status, consumer_class?, actor, evidence, at}`.
  It is written once, under `catalogue/status/<content_sha256>/`.
- **`seq`** starts at 1 and increases by 1 per object. Status changes are made only by the
  publish job or the owner's runbook, never concurrently. A gap or a duplicate `seq` fails
  catalogue validation.
- **Effective status** = the event with the highest `seq`.
- **Precedence:** `withdrawn` is terminal. No later event may revive the object; a correction is
  a new release.

| Transition | Who | Requires |
|---|---|---|
| → `exploratory` | producing job | invariants pass |
| → `validated` | independent reviewer + owner acknowledgement | review record: method, invariants, triangulation, reproducibility rebuild |
| → `approved_for_consumer(C)` | owner | rights gate for C passes; a named decision or use |
| → `withdrawn` | owner | reason recorded |

## 6. Reproducibility

A release or artefact is reproducible when a clean checkout of `code_ref`, given the same input
receipts and cuts, produces the same `content_sha256`. CI tests this for every new release kind,
and periodically for existing ones.

## 6.1 Fixtures (F-REVIEW-2026-10-18-a01-3)

1. **Determinism.** Build twice from the same inputs, code ref and spec, at different times. The
   `content_sha256` is identical; only the run records differ.
2. **Status does not change identity.** Append `validated`, then `withdrawn`. A rebuild still
   gives the same `content_sha256`, and the content bytes are unchanged.
3. **Withdrawal reaches a pinned consumer.** A consumer pinned to that hash resolves effective
   status `withdrawn` and refuses use. Its pinned bytes still verify against the hash.
4. **Self-reference is impossible.** The manifest core has no field holding its own hash.
   Adding a `content_sha256` field to the core fails the schema check.

## 7. Consumers

- A consumer pins `artefact_id` + `content_sha256`.
- It validates the envelope against the published contract schema version.
- **At each use, it resolves the effective status from the status events.** It refuses if the
  status is below its required level or `withdrawn`, or if the **current** rights record
  (not the build-time snapshot) excludes its class.

## Changelog

- 0.1 (2026-10-18): initial.
- 0.2 (2026-10-18): precise hash domain (manifest core); run metadata and status moved out of
  content objects; append-only status events with withdrawal precedence; §6.1 fixtures
  (T-0008, F-REVIEW-2026-10-18-a01-3).
