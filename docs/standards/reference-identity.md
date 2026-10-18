---
id: HIO-STD-REF
title: Reference identity (instruments, listings, indices, futures, taxonomies)
status: approved
approved_by: OD-0008   # at a82aa0d, blob 7796e7b38331
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0003
---

# Reference identity (v0.1)

HIO's reference context is the master for multi-portfolio reference data. The SMSF's
held-vehicle dimension (HIO-001) is a separate, SMSF-owned identity. The two are joined by
external identifiers (HIO-ADR-0003).

**Reused from HIO-001.** These conventions from `macsmsf` ADR 0003 are adopted deliberately:
- stable natural slugs, assigned once and never changed;
- dated identifiers with validity windows;
- explicit ticker-change and ticker-reuse handling;
- normalised identifier forms;
- registry-only minting;
- dated, provenance-backed classifications with retraction.

## Entities

| Entity | Key | Notes |
|---|---|---|
| Issuer | `issuer_code` | manager or obligor |
| Instrument | `instrument_code` (slug) | one economic vehicle or security; a share class or hedged variant is separate |
| Listing | (`instrument_code`, MIC, ticker, `valid_from`) | ISO 10383 MIC; dated; multiple listings allowed |
| Identifier | (type, value, `valid_from`) | ISIN, FIGI and other types. Each type carries a **rights note**: some identifier systems are licensed [EXT] |
| Index | `index_code` | provider, family, **variant** (price / gross TR / net TR), currency, hedging; a methodology document reference and version |
| Futures root | `root_code` | exchange MIC, symbol, multiplier, tick, currency, settlement method, listing cycle |
| Futures contract | (`root_code`, delivery month) | first trade, last trade, first notice, expiry, delivery dates |
| Taxonomy | (`taxonomy_code`, version) | versioned tree; nodes never removed in place |
| Classification | (subject, taxonomy, `valid_from`) | dated, with `basis` (manual judgement / issuer document / unclassified) and provenance; retraction instead of deletion |

## Rules

- Never mint from an ambiguous label. Resolution failures raise.
- Index and futures definitions are reference data, so factor specs reference them by code.
- **Translation to consumers** (the SMSF):
  - by (MIC, ticker, date), or by ISIN;
  - never by slug or surrogate;
  - an unmatched or ambiguous translation fails loudly in the consumer contract test.
- Bitemporal knowledge (what reference data said at an earlier time) is **deferred**.
  Validity windows plus audit stamps are kept from the start, so it can be added.
