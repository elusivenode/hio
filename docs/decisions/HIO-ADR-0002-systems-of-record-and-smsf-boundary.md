---
id: HIO-ADR-0002
title: Systems of record and the SMSF boundary
status: approved
approved_by: OD-0008   # at a82aa0d, blob d27994cd3663
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [any SMSF integration, consumer contract v1]
review_record: null
---

# HIO-ADR-0002: systems of record and the SMSF boundary

## Context

- HIO must be able to analyse portfolios that the SMSF does not hold and may never hold.
- The SMSF is the authoritative source of its own holdings, cash flows, tax and realised returns
  ([OBS] `macsmsf` `CLAUDE.md`, "Source authority").
- The owner requires that HIO never mutate accounting truth.

## Decision (proposed)

### Ownership

| Domain | System of record |
|---|---|
| SMSF receipts, transactions, holdings, cash, tax, member equity, realised returns, unit prices | `macsmsf` |
| SMSF trustee strategy, asset-class ranges, minutes, decisions with legal effect | `macsmsf` (trustee governance) |
| SMSF held-vehicle identity and the accounting map | `macsmsf` (HIO-001, scope per HIO-ADR-0003) |
| Market observations, vintages, availability, rights records | HIO market data |
| Reference data: instruments held or not, listings, indices, futures, economic taxonomies | HIO reference |
| Factor specifications and runs; models; research memory | HIO |
| Mandate parameters for HIO analysis | **supplied by the consumer's governance** (HIO stores a copy, with provenance) |
| Allocation proposals | HIO (proposals only); adoption belongs to consumer governance |

### Interfaces

1. **SMSF → HIO: `smsf_fund_projection` (contract v1, to be specified in S-later).**
   - Fund-level only: date; vehicle external identifiers (MIC + ticker, ISIN when present);
     units; AUD market value; staleness and provisional flags; fund-level external flows; fund
     TWR index; the producing `macsmsf` revision.
   - **No member data, TFNs, names or balances.**
   - Produced by an additive, read-only `macsmsf` exporter, run outside `local_refresh`.
   - Delivered as an artefact file. HIO never connects to SMSF databases.
2. **HIO → consumer: pinned artefacts.** A consumer references `artefact_id` + `content_sha256`
   and never "latest". The SMSF stores the pin with any pack that uses it, so a pack regenerated
   later reproduces the same numbers.
3. **No shared** database, credentials, storage bucket, code library or runtime.

## Consequences

- An SMSF pack never depends on a HIO job's timing. It renders only previously pinned
  artefacts.
- Implementing either side of the interface is a separate, approved slice. The `macsmsf` side
  carries full preservation evidence (fingerprints, API and pack equivalence; the HIO-001
  method).

## Rollback or exit

- Remove the pins or the exporter. Neither system's core is affected.

## Evidence required before approval

- The owner confirms that the fund-level projection fields are acceptable to leave the SMSF
  environment.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `d27994cd3663`). Edits after that commit record status only.
