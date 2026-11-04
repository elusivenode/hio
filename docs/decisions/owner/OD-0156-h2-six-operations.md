---
id: OD-0156
title: "Owner allows the six remaining H2 operations for the Treasury par yield curve; the curve gets its own owner_verified record, with retrieval still held for the experiment's yes"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-h2-six-operations.md (owner's message, verbatim)
  sha256: cd2cc01738a78fb06618667afb2bf6caeb51135033ca13baec605a0ec98269c5
  date: 2026-11-04
  quote: "yes to the six remaining H2 operations"
base_revision: 2e1ded8b9aba28fbb4b4e431e1034785ed5a4a2a
related: {adrs: [], tasks: [T-0002], findings: [], ods: [OD-0065, OD-0116, OD-0150, OD-0155]}
---

# OD-0156: the six remaining H2 operations

Claude's question: do you allow calculate, store derived, rebuild and reconstruct, external processing, `hio_internal` and agent context for the par yield curve, on the same conditions? Claude said a yes lets it mark the par curve `owner_verified`, and authorises no download and no duration experiment.

## What was done

**A new record, `us_treasury.par_yield_curve`,** with parent `us_treasury_rates` and `owner_verified` by this OD, following the dataset records of OD-0065. The parent row also covers bills, which aren't decided, so it stays `unverified` and still refuses everything.

| Pack operation | Register permissions | Value |
|---|---|---|
| Retain raw (OD-0155) | `raw_retention` | conditional: cite Treasury, no implied endorsement; `raw_retention_duration: indefinite` |
| Calculate | `internal_compute`, `derivation` | same condition |
| Store derived | `derived_storage` | same condition |
| Rebuild and reconstruct | no permission of its own; the gate requires the ones above | same condition |
| External processing | `external_processing` | same condition |
| `hio_internal` | `distribution.hio_internal` | same condition |
| Agent context | `agent_context` | same condition |
| Retrieve, one-off (OD-0155 V2) | `automated_retrieval` | conditional, **not satisfied**: one modest one-off download, declared User-Agent, after the experiment's own yes |

**Fail closed:** the record lists no satisfied conditions, so the gate still refuses every operation until a later OD records them with evidence.

## How Claude read it

- **The owner's own reading isn't stated.** The pack rests this decision on the owner reading the live pages. Claude asked directly, and this message answered only the operations. `owner_verified` here records the owner's decision, and the row says the reading is unconfirmed. If the owner says otherwise, this OD gets a correction.
- **Mapping is Claude's.** The pack's operation names are mapped to the register's permissions as tabled. "Calculate" is taken to include `derivation`, since a factor is a derivation.

## Not authorised

- Any download; the duration experiment; any real yield.
- Permissions left `unknown`: post-termination, audit retention, quotation in documents, and every distribution class except `hio_internal`.
- Bills, H.15, scheduled capture of the curve, any release to a consumer, the comparison reference.
- Changing the spec: `rates.us.cmt_10y.total_return` stays proposed and still names the parent row. The experiment's card should repoint it.

## Corrections (append-only)

1. **2026-11-04:** the owner confirmed reading the three live pages (OD-0161).
