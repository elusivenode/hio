---
id: HIO-ADR-0003
title: Instrument identity boundary and HIO-001
status: proposed
owner: owner (decides for both SMSF and HIO)
date: 2026-10-18
gates: [HIO-001 activation in macsmsf, HIO reference context design]
review_record: null
related: ["macsmsf docs/adr/0003-instrument-identity-and-economic-classification.md", "macsmsf docs/hio-001-review-record.md"]
---

# HIO-ADR-0003: instrument identity boundary and HIO-001

> **This ADR changes nothing in `macsmsf`.** It assesses ownership and impact, and proposes a
> next approval step. HIO-001 code, migrations, ADR 0003 and the review record are untouched.

## Context: what HIO-001 is, observed on 2026-10-18

All of the following is [OBS]:
- **Status:**
  - merged to `macsmsf` `main` (`fea8203`); code-complete;
  - **not applied** to the authoritative database (`to_regclass('silver.dim_instrument')` is
    null);
  - not promoted; not deployed.
- **Activation prerequisites:**
  - A17 (a verified promotion procedure);
  - owner confirmation of five classification calls (GLIN, GOLD, AAA, MXT, GROW) and of the
    vehicle types.
- **Objects:**
  - `sql/048` creates `silver.dim_instrument`, `silver.instrument_identifier` and
    `silver.instrument_asset_map`;
  - `sql/049` creates `silver.classification_taxonomy`, `silver.classification_node` and
    `silver.instrument_classification`;
  - two guard trigger functions;
  - rollback in `docs/adr/0003-rollback.sql`.
- **Registry:** `silver/instrument_registry.py` defines **exactly the 11 held instruments**.
- **Loader coupling:** `silver/instrument_master.py`:
  - applies **both** SQL files (`SQL_FILES = ("048…", "049…")`);
  - imports `macsmsf` alias dicts (`CMC_TICKER_ALIASES`, `SECURITY_LABEL_TO_TICKER`,
    `yfinance_symbol`);
  - corroborates SF360 security codes and ids against SF360 Bronze `/fund/chartAccounts`;
  - **raises if any active instrument lacks a live classification** in a required taxonomy.
- **API:** read-only `/api/instruments` and `/api/classification-taxonomies`. These return 503
  when the tables are absent.

**Inference** [INF]: HIO-001 is, in substance, an SMSF **held-vehicle identity** reconciled to
accounting sources, plus an **economic classification** layer. The first half is inseparable from
SF360 and broker reconciliation. The second half overlaps with what HIO reference data must own
for a multi-portfolio research system.

## Ownership and impact assessment

| HIO-001 component | What the SMSF needs it for | What HIO needs | Proposed owner | Impact if activated as-is |
|---|---|---|---|---|
| `dim_instrument` (vehicle identity, `instrument_code` slug) | stable identity of held vehicles across SF360 renames and rekeys | its own instrument identity covering un-held vehicles, indices and futures | **SMSF**, as the *held-vehicle dimension* | none harmful; it remains SMSF-local |
| `instrument_identifier` (SF360 code and id, CMC code, yfinance symbol, exchange ticker + MIC, ISIN) | corroboration against SF360 Bronze and broker aliases | exchange ticker + MIC and ISIN, as **translation keys** | **SMSF** for the SF360, CMC and yfinance types; **shared vocabulary** for MIC + ticker and ISIN | none harmful; the MIC + ticker and ISIN rows become the translation keys |
| `instrument_asset_map` (`dim_asset` → instrument) | maps accounting assets to vehicles | nothing directly | **SMSF** | none |
| `classification_taxonomy` / `node` (`HIO_ECONOMIC` v1) | none today: the trustee strategy classification stays in `reporting/asset_classes.py` | a versioned economic taxonomy as **HIO reference data** | **HIO** (proposed) | **dual ownership risk.** The name says "HIO" but it lives in the SMSF database, and is populated from an SMSF code registry |
| `instrument_classification` (five pending judgement calls) | none today | dated classification of instruments, held or not | **HIO** (proposed) | the same risk. The judgement calls would be confirmed into an SMSF table rather than HIO reference data |
| Loader, registry, API endpoints | operating the above | nothing | SMSF | — |

## Options

| Option | Description | `macsmsf` code change? | Assessment |
|---|---|---|---|
| A. Activate HIO-001 unchanged; HIO reads it | HIO depends on SMSF schema and runtime | no | **reject**: runtime coupling; HIO's master would live in the SMSF |
| B. Move all of HIO-001 to HIO | SMSF consumes identity from HIO | yes, large | **reject**: puts an external dependency into the accounting identity path; breaks preservation |
| **C1. Split; activate unchanged, but re-scope `HIO_ECONOMIC` by amendment as an *SMSF-local, consumed* classification** | SMSF activates 048 + 049 as built. ADR 0003 is amended to state that the taxonomy and classification are SMSF-local, become a consumer of a future HIO taxonomy projection, and are not HIO's master | **no** (documentation only) | **recommended near-term.** It preserves the reviewed code and its evidence. The cost is a misleading name (`HIO_ECONOMIC`), mitigated by documentation, with a rename deferred |
| C2. Split; activate identity only (048) and defer classification (049) | Requires changing the loader, which applies both files and enforces coverage | **yes** (the loader and its tests), with a full HIO-001 evidence re-run | viable later. Not worth reopening a five-round reviewed slice now |
| C3. Split; rename the taxonomy (`SMSF_ECONOMIC`) before activation | a cosmetic but schema-visible change | yes (registry, tests, migration seed) | defer; bundle with the first real HIO taxonomy projection, if ever needed |

## Decision (proposed): C1, with translation by external identifiers

1. **SMSF owns** the held-vehicle dimension:
   - `dim_instrument`, `instrument_identifier` and `instrument_asset_map`;
   - their SF360 and broker corroboration.
2. **HIO owns** reference data:
   - instruments (held or not), listings (MIC + ticker, dated), identifiers;
   - indices, futures roots and contracts;
   - **economic taxonomies and classifications**.

   See the [reference identity standard](../standards/reference-identity.md).
3. **Translation contract:**
   - SMSF ↔ HIO instruments join on `(MIC, exchange ticker, valid date)`, and ISIN where
     present;
   - never on surrogate keys or slugs;
   - a non-resolving or ambiguous join **fails loudly on the consumer side**.
4. **`HIO_ECONOMIC` in `macsmsf`** is declared SMSF-local:
   - it may later be populated from a HIO taxonomy projection, or retired;
   - the five pending judgement calls are re-homed as HIO reference-data decisions when HIO's
     taxonomy exists;
   - until then, SMSF can confirm them as SMSF-local values.

## Proposed amendment text for `macsmsf` ADR 0003

This is staged here and **not applied**. It would be added under the ADR's "Not decided here"
section:

> **Boundary with HIO (amendment, YYYY-MM-DD, owner-approved).** The instrument master in this
> ADR is the SMSF's **held-vehicle dimension**. HIO, a separate system, owns multi-portfolio
> reference data and economic taxonomies (`hio` HIO-ADR-0003). The `HIO_ECONOMIC` taxonomy and
> `instrument_classification` rows created here are **SMSF-local**. They are not HIO's master,
> and they may later be populated from a HIO taxonomy projection or retired. Joins to HIO use
> `(MIC, exchange ticker, date)` and ISIN, never `instrument_code` or surrogate keys. No code or
> schema change follows from this amendment.

## Next approval step (specific)

1. The owner approves or rejects C1 (task T-0004).
2. If approved: a **documentation-only** `macsmsf` commit adds the amendment above to ADR 0003,
   and a pointer line to the HIO-001 review record. There is no code, migration or activation
   change. HIO-001's activation prerequisites (A17, the judgement calls, vehicle types) are
   unchanged.
3. HIO's reference context is designed in a later slice. It does not depend on HIO-001's
   activation.

## Consequences

- No reviewed SMSF code is reopened.
- HIO is free to model futures, indices and un-held vehicles without touching the SMSF.
- One naming wart (`HIO_ECONOMIC` inside the SMSF) remains, documented.

## Rollback or exit

- Revert the documentation commit.
- If HIO later needs SMSF classifications populated from HIO, a C3-style slice is proposed
  under SMSF preservation rules.

## Approval

_Unapproved._
