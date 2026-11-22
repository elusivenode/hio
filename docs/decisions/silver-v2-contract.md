---
id: HIO-PROPOSAL-SILVER-V2-CONTRACT
title: "Silver version 2 contract (proposed): the dimensional tables, keys, releases and selections for the fund path"
status: proposed            # built under OD-0233; approves nothing
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
base_revision: 62e7f9ddba78b1fb615fd3cabe330f3a33a15d24
instruction: OD-0233
amends_if_adopted: "docs/decisions/local-data-layers-proposal.md: silver version 1 becomes a compatibility export"
sources: [docs/decisions/silver-dimensional-model-proposal.md, "architect consultations 20261122T192012-ask-d8f1 and 20261122T193241-ask-cee5 (advice only)"]
---

# Silver version 2 contract, fund path

> **Proposed.** The exact formats the first version is built to. Several workers build to this at once, so every header, key and formula here is literal. A change is a new schema version.

## 1. Encoding rules

- **Canonical JSON** is `hio.contracts.canonical.canonical_json`; **sha256** is lower-case hex of its bytes, 64 characters, never shortened.
- **Tables are CSV:** UTF-8, the `csv` module with `lineterminator="\n"` and minimal quoting, a header row, every cell text. An absent or null source field is an empty cell.
- **A source number is written as its exact text:** the JSON is read with `parse_float=Decimal, parse_int=Decimal` and a number is written as `format(value, "f")`. Nothing is rounded.
- **`record_sha256`** of a source record is sha256 of `json.dumps(record, sort_keys=True, default=str).encode("utf-8")`, the record as parsed above.
- Files are mode 0600 and directories 0700. Nothing is overwritten.

## 2. Keys

```text
sk(dimension, durable_key, version_identity=None) =
  sha256(canonical_json({"key_schema": "hio-dimensional-key/1", "dimension": dimension,
                         "durable_key": durable_key[, "version_identity": version_identity]}))
observation_id = sha256(canonical_json({"schema": "hio-observation/1", "series_id": s, "coordinate": c}))
value_fingerprint = sha256(canonical_json(measures))       # the row's measure cells, by column name
vintage_id = sha256(canonical_json({"schema": "hio-vintage/1", "observation_id": o,
                                    "value_fingerprint": f, "anchor_snapshot_id": a}))
source_record_id = sha256(canonical_json({"file_sha256": h, "row_index": i}))   # i is 0-based, an integer
```

`version_identity` is omitted from the JSON when it is `None`. `attributes_sha256` below is sha256 of the canonical JSON of the row's other attribute cells, by column name.

## 3. Inputs

| Input | Where | Notes |
|---|---|---|
| Release spec | `specs/silver/<name>.yaml` | below |
| Instrument register | `registers/instruments.yaml` | below |
| Observation specs | `specs/observations/<SOURCE_SYMBOL>.yaml` | the version 1 format; one is required for every instrument in the release |
| Bronze | `<bronze_root>/raw/<snapshot>/manifest.json` and the files it lists | `files[]` entries have `path` (relative to the root), `sha256`, `kind` (`eod`, `div`, `splits`, `symbols`), `symbol`, `retrieved_at`. An exchange list has symbol `EXCHANGE.<X>` and serves every `<CODE>.<X>` |

**Release spec:**

```yaml
identity: {release_name: funds, version: 0.1.0, status: proposed}
schema: hio.silver/2
source_id: some.source
snapshots:                       # in capture order; refused unless ascending by earliest retrieved_at
  - {name: s1, manifest_sha256: "<64 hex>"}
instruments: [ZZZ.US]            # source symbols; each must be mapped in the register
selections:
  - name: compat-v1
    members: {ZZZ.US: s1}        # source symbol -> snapshot name
```

**Instrument register:**

```yaml
status: proposed
instruments:
  - instrument_code: example-fund          # slug: lower-case letters, digits and hyphens
    name: "Example Fund"
    issuer_code: example-issuer
    vehicle_type: etf
    domicile: US
    listings:
      - {mic: XXXX, ticker: ZZZ, quote_currency: USD, valid_from: null}
    source_mappings:
      - {source_id: some.source, source_symbol: ZZZ.US, mic: XXXX, ticker: ZZZ}
```

A `valid_from` of null means the start date is not established; it is written as an empty cell and as `""` in the key. A mapping must name exactly one listing of its instrument. Codes, and (source, symbol) pairs, are unique.

## 4. Tables

Each table is `tables/<name>.csv`. Columns are in the order shown. Rows are sorted by the stated key, as text.

**Dimensions**

| Table | Columns | Key formula | Sort |
|---|---|---|---|
| `dim_date` | `date_sk,date,year,month,day,iso_weekday` | `sk("date", {"date": date})`; one sentinel row with every other cell empty and `sk("date", {"sentinel": "not_recorded"})` | `date` |
| `dim_currency` | `currency_sk,code` | `sk("currency", {"code": code})`; one sentinel row, empty code, `sk("currency", {"sentinel": "not_recorded"})` | `code` |
| `dim_source` | `source_sk,source_id` | `sk("source", {"source_id": id})` | `source_id` |
| `dim_instrument` | `instrument_sk,instrument_code,name,issuer_code,vehicle_type,domicile` | `sk("instrument", {"instrument_code": c}, {"attributes_sha256": a})` | `instrument_code` |
| `dim_listing` | `listing_sk,instrument_code,instrument_sk,mic,ticker,valid_from,quote_currency` | `sk("listing", {"instrument_code": c, "mic": m, "ticker": t, "valid_from": v})` | `instrument_code,mic,ticker,valid_from` |
| `dim_source_listing` | `source_listing_sk,source_id,source_symbol,vendor_code,vendor_exchange,name,country,exchange,currency,isin,type` | `sk("source_listing", {"source_id": s, "source_symbol": y}, {"attributes_sha256": a})`; one row for each distinct attribute set seen across the pinned snapshots | `source_symbol,source_listing_sk` |
| `dim_series` | `series_sk,series_id,source_id,source_symbol,quantity` | `series_id` is `<source_symbol>.<quantity>`; quantity is `bar_day`, `adjusted_close_day`, `distribution` or `split`; `sk("series", {"series_id": s}, {"definition": "1"})` | `series_id` |
| `dim_audit` | `audit_sk,schema,code_commit,release_spec_sha256,register_sha256,observation_specs_sha256` | one row; `sk("audit", <the other five cells by column name>)`; `observation_specs_sha256` is sha256 of the canonical JSON of the sorted list of observation-spec sha256 values | — |

`dim_date` holds every date any fact refers to, and the sentinel. `dim_currency` holds every currency any row refers to, and the sentinel. The vendor's listing fields map `Code`→`vendor_code`, `Exchange`→`exchange`, `Name`, `Country`, `Currency`, `Isin`, `Type`; `vendor_exchange` is the part of the source symbol after the last dot.

**Provenance**

| Table | Columns | Notes | Sort |
|---|---|---|---|
| `snapshot` | `snapshot_id,name,source_id,capture_order,first_retrieved_at,last_retrieved_at` | `snapshot_id` is the manifest's sha256; `capture_order` counts from 1 | `capture_order` |
| `snapshot_member` | `snapshot_id,path,file_sha256,kind,source_symbol,retrieved_at` | only the files of the release's instruments and their exchange lists | `snapshot_id,path` |
| `source_record` | `source_record_id,file_sha256,row_index,record_sha256` | every row of every `eod`, `div` and `splits` file in `snapshot_member`; one file held by two snapshots appears once | `file_sha256`, then `row_index` as a number |
| `source_identity_mapping` | `source_id,source_symbol,instrument_code,listing_sk` | from the register | `source_symbol` |
| `bridge_vintage_support` | `vintage_id,source_record_id,snapshot_id` | every (vintage, record, snapshot) that asserts the vintage's value | all three |

**Facts.** Every measurement fact starts with these columns:

`vintage_id,observation_id,series_id,series_sk,source_sk,audit_sk,origin_source_record_id,anchor_snapshot_id,first_captured_at`

`first_captured_at` is the `retrieved_at` of the anchoring snapshot's file. Then:

| Table | Further columns | Coordinate | Measures (the fingerprint) |
|---|---|---|---|
| `fact_listing_bar_day` | `listing_sk,instrument_sk,trade_date_sk,trade_date,quote_currency_sk,open,high,low,close,volume` | `{"trade_date": d}` | `open,high,low,close,volume` |
| `fact_vendor_adjusted_close_day` | `listing_sk,instrument_sk,trade_date_sk,trade_date,quote_currency_sk,adjusted_close` | `{"trade_date": d}` | `adjusted_close` |
| `fact_distribution_event` | `instrument_sk,currency_sk,ex_date_sk,declaration_date_sk,record_date_sk,payment_date_sk,ex_date,occurrence,declaration_date,record_date,payment_date,amount_unadjusted,amount_split_adjusted,currency,period_label,franking` | `{"ex_date": d, "occurrence": n}` | every column from `declaration_date` to `franking` |
| `fact_split_event` | `instrument_sk,effective_date_sk,effective_date,occurrence,ratio,new_units,old_units` | `{"date": d, "occurrence": n}` | `ratio` |

- One `eod` row gives one bar row and one adjusted-close row, the second even when the adjusted close is absent (an empty cell).
- Vendor fields: `date`, `open`, `high`, `low`, `close`, `volume`, `adjusted_close`; distributions `date`→`ex_date`, `unadjustedValue`→`amount_unadjusted`, `value`→`amount_split_adjusted`, `currency`, `declarationDate`, `recordDate`, `paymentDate`, `period`→`period_label`, `franking`; splits `date`→`effective_date`, `split`→`ratio`, and `new_units`, `old_units` are the two sides of the ratio's `/`.
- **`occurrence`** is the 0-based position of a record among the records of its file with the same date, ordered by `record_sha256`. It is `0` when the date is unique. In the coordinate it is an integer.
- An empty date or currency takes the sentinel key. `quote_currency_sk` is the listing's.
- Fact rows sort by `series_id`, then the coordinate date, then `occurrence` as a number, then the anchoring snapshot's `capture_order`.

**Vintages.** For each series, take the release's snapshots in capture order, skipping any that lack the series' file. For each record, compute its observation and value fingerprint. If the newest vintage of that observation has the same fingerprint, the record supports it: add a bridge row and no fact row. Otherwise it starts a new vintage, anchored at this snapshot, with this record as its origin. A record absent from a later snapshot changes nothing.

**Membership and corrections**

| Table | Columns | Notes | Sort |
|---|---|---|---|
| `fact_listing_presence` | `source_listing_sk,snapshot_id,instrument_sk,listing_sk,currency_sk` | one row for each release instrument found in a snapshot's exchange list; `currency_sk` is the vendor's stated currency | `snapshot_id,source_listing_sk` |
| `correction_rule` | `correction_id,observation_spec_sha256,source_symbol,action,ex_date,reason,evidence` | from the observation specs; `correction_id` is sha256 of the canonical JSON of `{"observation_spec_sha256", "action", "ex_date"}` | `source_symbol,ex_date` |
| `fact_correction_application` | `application_id,correction_id,snapshot_id,target_source_record_id,target_vintage_id,disposition` | for each snapshot holding the instrument's distributions: the records dated `ex_date` with a positive `unadjustedValue`. One gives an application with disposition `excluded`; none gives nothing; several refuse. `application_id` is sha256 of the canonical JSON of `{"correction_id", "snapshot_id", "target_source_record_id"}` | `correction_id,snapshot_id` |

**The corrected record stays in `fact_distribution_event`.** Only a selection leaves it out.

## 5. Selections

A selection names, for each member instrument, one snapshot. It lists every record of that instrument's `eod`, `div` and `splits` files in that snapshot.

- `selections/<selection_id>.json`: canonical JSON of `{"schema": "hio-selection/1", "name": n, "members": {source_symbol: snapshot_id}, "corrections": [sorted correction_id of the members' applications in their snapshots]}`. `selection_id` is the sha256 of those bytes.
- `selections/<selection_id>.csv`, columns `fact_table,series_id,observation_id,vintage_id,source_record_id,row_index,disposition,reason`. An `eod` record gives two rows, one for each of its fact tables. `disposition` is `selected`, or `excluded` with the `correction_id` as `reason`. Sorted by `fact_table`, `series_id`, then `row_index` as a number.
- **Refused:** a member instrument has a correction rule with no application in its selected snapshot.

## 6. Release

```text
<silver_root>/v2/<release_id>/
  manifest.json
  tables/<name>.csv
  selections/<selection_id>.json
  selections/<selection_id>.csv
```

`manifest.json` is `{"core": {...}, "release_id": "<sha256 of canonical_json(core)>"}`, written with indent 1, sorted keys and a trailing newline. The core:

```text
schema                 "hio.silver/2"
release_spec           {name, version, sha256}
register_sha256
observation_specs      [{source_symbol, sha256}] sorted by source_symbol
snapshots              [{name, manifest_sha256}] in capture order
code_commit
tables                 [{name, header_sha256, file_sha256, rows}] sorted by name
selections             [{selection_id, name, policy_sha256, file_sha256, rows}] sorted by selection_id
```

`header_sha256` is the sha256 of the header line without its line end; `rows` counts data rows. No build time, path or run id is in the core. The same inputs give the same `release_id` and the same bytes; an existing release with different bytes is refused.

**Refusals when building:** a pin that does not match its manifest; a file that does not match its manifest entry; snapshots out of capture order; an instrument with no mapping, no observation spec or no file in any snapshot; the vendor's listing currency differing from the listing's quote currency; `eod` dates not unique and ascending, or a close not positive; several records matching one correction; an output path inside the repository.

## 7. Reading, and the version 1 export

A reader opens a release by `release_id`, recomputes the id from the core, and verifies every table and selection file against the manifest before returning a row.

**Compatibility export.** For a selection and a member instrument it returns the bytes of the three version 1 files, rows in `row_index` order, excluded rows left out:

| File | Header | From |
|---|---|---|
| `closes.csv` | `date,close,adjusted_close` | the selected bar rows, each joined to its adjusted-close row by `source_record_id` |
| `distributions.csv` | `ex_date,amount,split_adjusted_amount,currency,payment_date,record_date,declaration_date,period` | the selected distribution rows |
| `splits.csv` | `date,ratio` | the selected split rows |

These bytes must equal the version 1 silver set's files for the same snapshot and corrections.

## 8. Module placement

| Module | Holds | May import |
|---|---|---|
| `hio.contracts.silver` | table names, headers and sort keys; the key functions; CSV reading and writing; the manifest core, `release_id` and release verification | nothing else in `hio` |
| `hio.reference.instruments` | loading and validating the register | `hio.contracts` |
| `hio.marketdata.silver_build` | bronze to a release | `hio.contracts`, `hio.reference` |
| `hio.marketdata.silver_reader` | the verified reader, selections, the compatibility export | `hio.contracts` |

Tools are thin commands over these.
