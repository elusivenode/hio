---
id: HIO-EVIDENCE-FACTORS-SILVER-DIMENSIONAL-1
title: "Dimensional silver, first version: a release built from the real snapshots and proved equivalent to version 1 (OD-0233)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0233
---

# Dimensional silver 1

> **Exploratory and unaccepted.** The contract is `docs/decisions/silver-v2-contract.md` (proposed); the tests were declared in OD-0233 before the build. **No value from a series is recorded here** (OD-0210). Run once, by the author; not reviewed.

## What was built

Seven worker tasks in three phases, each integrated at its checked commit:

| Code | Does | Checked commit |
|---|---|---|
| `src/hio/contracts/silver.py` | table formats, hash keys, release writing and verification | `eaf0584`, `69d5270` |
| `src/hio/reference/instruments.py` | loads and validates the instrument register | `d7a27d7` |
| `src/hio/marketdata/silver_build.py`, `tools/silver_release.py` | bronze snapshots to a release: dimensions, vintage-grain facts, provenance, corrections, selections | `4fd5502` |
| `src/hio/marketdata/silver_reader.py`, `tools/silver_compat_export.py` | the verified reader and the version 1 export | `8f833ea` |
| `tools/lake_catalogue.py` | indexes version 2 releases, with query views | `82d1c82` |
| `tools/factor_build.py` (silver 2 mode) | builds a fund series from a release and a selection | `586b072` |

Proposed records: `registers/instruments.yaml` (nine HIO instrument codes) and `specs/silver/funds.yaml` (four snapshots, nine instruments, one selection, `compat-v1`, that names the snapshot each existing build used).

## The release

`~/.hio-research/silver/v2/ac293ef4bbb4cfb226538a02c20f0c2e29f99353d27c0d44555111227858e4db/`, selection `9dc35eaa8ccaa3b026e399e05ffd2f74388cb8cf7d9ac27c2a9f2a25b6fed067`. An earlier release of the same inputs at an earlier commit (`ad32fa0d…`) is kept beside it.

| Table | Rows |
|---|---|
| `fact_listing_bar_day` | 45,995 |
| `fact_vendor_adjusted_close_day` | 42,268 |
| `fact_distribution_event` | 920 |
| `fact_split_event` | 3 |
| `fact_listing_presence` | 24 |
| `fact_correction_application` | 1 |
| `dim_instrument`, `dim_listing`, `dim_source_listing` | 9 each |
| `dim_series` | 36 |
| `dim_date` | 8,640 |
| `source_record` | 62,069 |
| `bridge_vintage_support` | 122,666 |

## The declared tests

| Test | Result |
|---|---|
| Each version 1 silver file reproduced byte for byte from version 2 | **27 of 27 identical** (three files for each of nine funds) |
| Every fund series built through version 2 is byte-identical to its existing build | **9 of 9 identical** |
| A rebuild from a restored backup gives the same hashes | the release rebuilt from the restored snapshots has the same `release_id` and identical bytes in every file; IGB and VAS rebuilt from it have the same `build_id` and series hash |

**Broken on purpose:** one digit changed in a copy of the release's distribution table; the factor build refuses, naming the table.

**The catalogue** rebuilt with 0 problems: 2 releases, 39 gold builds, 147 lineage rows.

## What the vintage model shows

Three funds are in two snapshots taken seventeen days apart. Where the vendor changed a value, both versions are held as vintages of one observation:

- one fund's bars changed on about four trading days in five, mostly volume, highs and lows; its close changed on 80 days, all by small amounts;
- another fund's adjusted close changed on several hundred days, and its volume on a few;
- a few distribution records changed their declaration, record or payment dates.

That the vendor revises history was known (`docs/evidence/e0002/stability-1.md`). The differences are now rows that can be queried. The sizes are in the owner's session report.

## Limits

- **Fund path only.** Exchange rates, cash rates, the par curve, CPI and issuer NAVs are not in silver.
- **Knowability and quality facts are deferred** (the proposal says why). The fund data carries capture time only, and no point-in-time claim.
- **The register is unverified.** Names, issuers and markets come from the vendor's listing; listing start dates are not established.
- Two releases of the same inputs exist because the code commit is part of a release's identity.
- Worker notes, all low: an interrupted release build leaves a scratch directory that the catalogue reports as a problem; a vendor exchange list with two entries for one code would be refused (none of the four has one); the distribution view reaches a listing through the vendor mapping.
- Checked by the author on real data and by the workers' tests on invented data; no independent review.

## Not established

That any series is right. Nothing is accepted, no spec or model is adopted, and both proposals stay proposed.
