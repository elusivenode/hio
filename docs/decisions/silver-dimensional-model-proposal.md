---
id: HIO-PROPOSAL-SILVER-DIMENSIONAL-MODEL
title: "Silver as a dimensional model (proposed): facts, dimensions, keys, vintages, corrections and releases"
status: proposed            # drafted under OD-0232; approves nothing and authorises no build
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-22
base_revision: 03b72fe5122c847b1554936ee128104955afc7ff
instruction: OD-0232 (proposal only)
amends_if_adopted: "docs/decisions/local-data-layers-proposal.md: silver version 1 becomes a compatibility export of version 2"
sources: ["architect consultation 20261122T192012-ask-d8f1 (asked to act as a Kimball expert; advice only)", docs/standards/observations-and-point-in-time.md, docs/standards/reference-identity.md, docs/decisions/local-data-layers-proposal.md]
---

# Silver as a dimensional model

> **Proposed.** Two models were drafted independently, Claude's and the solution architect's, and are combined here. Where they differed, the last section says which was taken and why. The architect's full answer is in the run log, not in the repository.

## Shape

A set of star schemas, one fact table per business process, sharing conformed dimensions. **CSV tables and a manifest are the record; DuckDB is rebuilt from them.** A silver release is one frozen set of all tables. Gold pins a release and a selection inside it.

## Bus matrix

Every process also carries `dim_source` and `dim_audit`.

| Business process | Date | Period | Instrument | Listing | FX pair | Series | Currency | Tenor |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Listed-fund daily bars | ✓ | | ✓ | ✓ | | ✓ | ✓ | |
| Vendor adjusted closes | ✓ | | ✓ | ✓ | | ✓ | ✓ | |
| Fund distributions | roles | | ✓ | | | ✓ | ✓ | |
| Fund splits | ✓ | | ✓ | | | ✓ | | |
| Vendor FX daily bars | ✓ | | | | ✓ | ✓ | roles | |
| Official FX fixings | ✓ | | | | ✓ | ✓ | roles | |
| Official overnight cash rates | ✓ | | | | | ✓ | ✓ | |
| Treasury par-curve yields | ✓ | | | | | ✓ | ✓ | ✓ |
| CPI index levels | release | ✓ | | | | ✓ | | |
| Issuer NAVs | ✓ | | ✓ | | | ✓ | ✓ | |
| Exchange-list membership | snapshot | | optional | optional | | | ✓ | |

"Roles" means one dimension used through several keys: ex-date and payment date, or base and quote currency.

## Facts

Every measurement fact has the grain shown **times a vintage**: a distinct value for the same coordinate. An unchanged value seen again in a later snapshot is provenance, not a new row.

| Fact | Grain | Measures (exact decimal text) | Type |
|---|---|---|---|
| `fact_listing_bar_day` | listing, bar series, trading date | open, high, low, close, volume | periodic snapshot |
| `fact_vendor_adjusted_close_day` | listing, adjustment series, trading date | adjusted close | periodic snapshot |
| `fact_distribution_event` | one source-identified distribution event | unadjusted amount, split-adjusted amount; ex, declaration, record and payment dates | transaction |
| `fact_split_event` | one source-identified split event | new units, old units, the ratio as written | transaction |
| `fact_fx_bar_day` | FX pair, bar series, session date | open, high, low, close | periodic snapshot |
| `fact_fx_fixing_day` | FX pair, fixing series, fixing date | rate | periodic snapshot |
| `fact_cash_rate_day` | cash-rate series, date | rate | periodic snapshot |
| `fact_par_yield_day` | curve, date, tenor | yield | periodic snapshot |
| `fact_cpi_index_month` | CPI series, reference month | index level | periodic snapshot |
| `fact_fund_nav_day` | share class, NAV series, valuation date | NAV per unit | periodic snapshot |
| `fact_listing_presence` | source listing, exchange-list snapshot | none | factless |
| `fact_correction_application` | one correction rule applied to one source record | none | factless |

- **An ex-date does not identify a distribution.** Two real distributions can share one. The event key is a source-scoped event identity, and an issuer's record of the same event is a separate row linked to the vendor's.
- **Nothing is filled.** A daily grain does not create rows for missing days.
- **None of these measures adds up.** Prices, rates, yields, index levels and per-unit amounts are not summed across rows. The table contract says so.
- **The vendor's adjusted close has its own fact,** so a change in the vendor's adjustment never looks like a revision of the traded close. It is a diagnostic and never an input to a return.

## Dimensions

| Dimension | Natural key | Main attributes | History |
|---|---|---|---|
| `dim_date` | calendar date | year, month, day, weekday | fixed |
| `dim_period` | frequency, start, end | label | fixed |
| `dim_instrument` | HIO `instrument_code` | name, issuer, vehicle type, share class, domicile | new row on a meaningful change |
| `dim_listing` | instrument, market (MIC), ticker, valid-from | quote currency, market time zone | new row on change; a reused ticker is a new listing |
| `dim_source_listing` | source, vendor exchange code, vendor code | the vendor's name, country, currency, ISIN, type | new row when the vendor's attributes change |
| `dim_source` | `source_id` | publisher, dataset, time zone | versioned |
| `dim_series` | `series_id` and definition version | quantity, unit, currency, frequency, calendar, convention | a changed definition is a new version |
| `dim_currency` | ISO code | name | fixed |
| `dim_fx_pair` | base and quote, ordered | "quote units per one base unit" | fixed |
| `dim_tenor` | tenor code | length; overnight is distinct | fixed |
| `dim_audit` | fingerprint of the build context | code commit, schema version, observation-spec hash | fixed |

**Identity follows the reference-identity standard.** A vendor symbol, a ticker or an ISIN is never HIO's instrument identity: the instrument has an HIO code, and a mapping table ties each vendor symbol to it. HIO has no instrument register yet, so the first version needs one, `registers/instruments.yaml`, with a code, an issuer and a dated listing for each fund.

## Keys

Every surrogate key is the SHA-256 of the canonical form of the row's natural key (and, where a dimension keeps history, of the change that created the row). Sequence-assigned integers depend on load order and cannot be rebuilt identically, so they are not used. The natural key is kept beside the hash, and a collision or a conflicting definition refuses the build.

## Vintages and provenance

| Table | Holds |
|---|---|
| `source_record` | one row of one bronze file: its file, its position and its hash |
| `snapshot`, `snapshot_member` | each pinned snapshot and the files in it |
| `bridge_vintage_support` | which source records, in which snapshots, support each vintage |

- When snapshots overlap, an unchanged value keeps its one vintage and gains a support link. A changed value is a new vintage. A record missing from a later snapshot is not treated as deleted.
- Two snapshots that disagree are both kept. Neither file order nor snapshot order decides which is right.

**Deferred to the official sources:** separate facts for knowability claims and for quality decisions (the four clocks of the point-in-time standard: what a value refers to, when it was public, when HIO captured it, when HIO judged it). The vendor fund data has one knowledge mode, a reconstruction from one snapshot, so the first version records capture time only. The tables are added, as the architect specifies them, when cash rates and CPI enter silver.

## Corrections

| Table | Holds |
|---|---|
| `correction_rule` | from the observation spec: action, target, the target record's expected hash, reason, evidence |
| `fact_correction_application` | the rule, the source record it hit, and the disposition (`excluded`) |

The corrected record **stays in its fact table.** The selection leaves it out, and the application row says why. A future replacement value is a new, separately marked row linked to its original, never a silent overwrite.

## Releases and selections

```text
silver/v2/<release_id>/
  manifest.json
  tables/<table>.csv
  selections/<selection_id>.csv
```

- **`release_id`** is the SHA-256 of the manifest's core: schema version, input snapshot hashes, register and observation-spec hashes, code commit, and each table's name, schema hash, file hash and row count. No build time, path or run id is in it.
- **A selection** is the list of vintages a gold build may read under one named policy (which snapshots, which corrections). It lists excluded rows with their reason as well as selected ones.
- **Gold pins** `silver_release_id`, `selection_id`, the factor spec's hash and the code commit. Nothing resolves "latest".

## First version, and how it is proved

**Build first:** the fund path only. Five facts (`fact_listing_bar_day`, `fact_vendor_adjusted_close_day`, `fact_distribution_event`, `fact_split_event`, `fact_listing_presence`), their dimensions, the provenance and correction tables, the instrument register, and one selection that reproduces today's inputs.

**Proof, in order:**

1. A worked example on invented data: an unchanged row seen in two snapshots, a revised value, two distributions on one ex-date, and a declared exclusion.
2. Version 2 is built from the bronze snapshots, not from version 1 (version 1 dropped open, high, low and volume).
3. A compatibility export from version 2 reproduces each version 1 file (`closes.csv`, `distributions.csv`, `splits.csv`) byte for byte, for all nine funds.
4. Every fund series built through version 2 is byte-identical to its existing build.
5. From a restored backup, in an empty directory, the whole of it rebuilds to the same hashes.

**Left out of the first version:** the FX, cash-rate, par-curve, CPI and NAV facts (each is added when its source enters silver); a full history engine for reference data; classification hierarchies; aggregate tables; Parquet; anything hosted.

## Where the two drafts differed

| Point | Claude's draft | Architect's | Taken |
|---|---|---|---|
| Snapshot handling | each fact row carries its snapshot | vintage-grain rows, with snapshots as support links | architect's: overlapping snapshots would otherwise multiply every row |
| Instrument identity | one dimension keyed by symbol and exchange | instrument, listing and source listing, with HIO-minted codes | architect's: the reference-identity standard requires it |
| Adjusted close | a column to drop | its own fact | architect's |
| FX | one fact with a source key | bars and fixings as separate facts | architect's: different grains and measures |
| Rates | one fact with a tenor, overnight for cash | cash rates and par yields separate | architect's |
| Series | separate rate and economic series dimensions | one `dim_series` across all facts | architect's |
| Knowability and quality facts | not drafted | separate transaction facts from the start | **deferred**, Claude's judgement: heavy for vendor snapshot data with one knowledge mode; added with the official sources |
| Surrogate keys, immutable releases, visible corrections | hash keys; whole frozen releases; flagged rows | the same | agreed |

The architect also advised keeping the bytes of a correction's evidence locally, since a link or a quotation alone does not prove it. For IGB that means saving the announcement page beside the store.

## Decisions this proposal needs

Each is the owner's: adopting the model; authorising the first version's build; the instrument codes minted in the new register.
