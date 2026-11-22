---
id: HIO-PROPOSAL-LOCAL-DATA-LAYERS
title: "Local data layers (proposed): bronze, silver and gold as immutable files with a rebuildable DuckDB catalogue"
status: proposed            # built under OD-0231; approves nothing and amends no approved document
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
base_revision: 0f2a008d111ed619a5ac054774959e98661fd191
instruction: OD-0231
amends_if_adopted: "nothing: it follows docs/architecture.md §2 and HIO-ADR-0009 (files are the record; the database is a derived index)"
sources: ["architect consultation 20261122T185346-ask-1f88 (advice only)", docs/decisions/owner/OD-0231-local-data-layers.md]
---

# Local data layers

> **Proposed.** The implementation contract for OD-0231. Version 1 of each format below is fixed for the first tools; a change is a new version, never an edit in place.

## Choice

**Files are the record; DuckDB is the index.** Every layer is a set of immutable directories, each with a manifest of sha256 hashes and an identity derived from its inputs. A DuckDB catalogue is rebuilt from the manifests at any time and can be deleted without loss. Nothing is updated in place, and no build reads "latest": each names the exact identity of what it reads.

| Layer | Holds | Identity | State |
|---|---|---|---|
| **Bronze** | bytes as fetched, with a manifest | the manifest's sha256 | exists: the pinned snapshots. Unchanged |
| **Silver** | one instrument's cleaned observations, from one bronze snapshot and the corrections its observation spec declares | `silver_id` | new |
| **Gold** | factor and portfolio series | `build_id` | exists: the factor store. Fund builds move to reading silver |
| Catalogue | tables and lineage over all three | none: disposable | new |
| Backup | a verified copy of all of it | `backup_id` | new |

**Where the architect differed.** It advised deferring silver until several builds need one correction. The owner has asked for the layers (OD-0231), and silver is where a correction is made once for every series built on an instrument, so it is built now. Its other advice is followed: no format migration (CSV stays), no hosted database, recovery proved by a restore test.

## Silver, version 1

**Observation spec** (repository): `specs/observations/<SYMBOL>.<EXCHANGE>.yaml`.

```yaml
identity: {instrument: ZZZ.US, version: 0.1.0, status: proposed}
source: {source_id: some.source, quote_currency: USD}
corrections:            # may be empty
  - action: exclude_distribution      # the only action
    ex_date: "2030-01-09"
    reason: "why"
    evidence: path/to/record.md
changelog: ["0.1.0 (date): ..."]
```

**A silver set** is the directory `<silver_root>/<instrument>/<silver_id>/`, mode 0700, files 0600, LF line ends:

| File | Header | Notes |
|---|---|---|
| `closes.csv` | `date,close,adjusted_close` | every vendor row, in order |
| `distributions.csv` | `ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period` | `amount` is the vendor's unadjusted value; corrections applied |
| `splits.csv` | `date,ratio` | `ratio` as the vendor writes it, new/old |
| `manifest.json` | | below |

- **Values are exact text:** a JSON number becomes `format(Decimal, "f")` of its literal; a null or absent field becomes an empty cell. Nothing is rounded, filled or reordered.
- **Refusals:** the quote currency in the snapshot's listing differs from the spec's; dates not unique and ascending; a close not positive; a correction matching zero or several records; an existing set with different bytes. The same inputs give the same bytes (idempotent).
- **`silver_id`** is the first 16 hex characters of sha256 over the observation spec's sha256, the snapshot manifest's sha256 and the code commit, concatenated.

`manifest.json` (indent 1, sorted keys, trailing newline): `schema` (`"hio.silver/1"`), `instrument`, `quote_currency`, `source_id`, `observation_spec` (`{version, sha256}`), `snapshot`, `snapshot_manifest_sha256`, `inputs` (`[{path, sha256}]`, the bronze files read), `corrections` (`[{action, ex_date, record_sha256}]`), `code_commit`, `files` (`{name: {sha256, rows}}` for the three CSV files), `first`, `last`, `silver_id`.

## Gold from silver

`tools/factor_build.py` gains a silver mode: it reads one silver set by `silver_id`, verifies it against its manifest, and builds exactly as before. **The test of the layer is equivalence:** a series built from silver has the same bytes as the series built from the bronze snapshot with the same corrections. A factor spec that declares `source_corrections` is refused in silver mode: corrections belong to the observation spec. The build record names the silver set, and its `build_id` is derived from the spec, the `silver_id` and the code commit.

Builds that derive from other builds (excess, translation, cash) are unchanged: they already name their parents by `build_id`.

## Catalogue

`tools/lake_catalogue.py` reads the three roots, verifies every file against its manifest, and writes one DuckDB file: snapshots and their files, silver sets and their files, gold builds, every gold series in long form (exact text and a numeric value), and a lineage table from each build to its parents. An incomplete or failing bundle is reported and left out.

## Backup

`tools/lake_backup.py` copies a source tree to `<target>/<backup_id>/` with an inventory of sha256 hashes, verifies the copy, and never writes into an existing backup. A restore goes only into an empty directory and is verified against the inventory.

## Not in this version

Other bronze sources (the H.10 file, the RBA history) as silver; portfolio analytics outputs in the catalogue; Parquet; any hosted or shared store; retiring the bronze mode of the factor build.
