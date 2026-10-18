---
id: HIO-STD-OBS
title: Observations, point-in-time knowledge and vintages
status: approved
approved_by: OD-0008   # at a82aa0d, blob bd9eff0893ea
owner: HIO architecture lead (owner); market-data maintainer
version: 0.2
last_reviewed: 2026-10-18
decision: HIO-ADR-0004
---

# Observations, point-in-time knowledge and vintages (v0.2)

## 1. Entities

| Entity | Definition | Key |
|---|---|---|
| **Source** | a publisher or vendor endpoint, with a rights record | `source_id` |
| **Receipt** | the immutable bytes of one response, plus the request and capture metadata | `receipt_id` = SHA-256 of the bytes |
| **Series** | a named quantity with unit, currency, calendar, `series_class` and source | `series_id` |
| **Observation** | one value of a series for one key, from one receipt | (`series_id`, `key`, `vintage_seq`) |
| **Vintage** | a distinct value for the same (`series_id`, `key`); a new vintage is created only when the value or a material attribute changes (append-on-change) | `vintage_seq` (1, 2, …) |

A `key` is the observation's coordinate: a date; a (date, tenor); a (contract, trade date); or a
(period, release) for macro data.

## 2. Temporal attributes

| Attribute | Type | Meaning | Rules |
|---|---|---|---|
| `valid_time` | date or period, in the **market-local calendar** | what the value refers to | never converted through UTC. A trade date is the exchange's trade date, including for sessions that start the previous evening |
| `knowable_at` | UTC instant | earliest time the value was publicly knowable | a claim, always paired with `knowable_basis` |
| `knowable_basis` | enum | how `knowable_at` is known | see §3 |
| `captured_at` | UTC instant | when HIO fetched the receipt | a fact, from the receipt |
| `source_timezone` | IANA tz | the publisher's local zone | recorded for audit |
| `quality_status` | enum | `pending`, `valid`, `quarantined`, `superseded` | only `valid` is used by releases |

## 3. `knowable_basis`: evidence for **this value's vintage**, strongest first

Knowability is a property of a **specific vintage** (a specific value for a key). It is not a
property of the series or its release schedule. Every basis below must be evidence that *this
value* was public at `knowable_at`.

| Value | Meaning | May support `as_known_by_market`? |
|---|---|---|
| `publisher_timestamp` | the payload or headers carry this vintage's own publication timestamp | yes |
| `publisher_vintage` | the publisher's real-time vintage archive dates this value (e.g. ALFRED real-time periods [EXT]) | yes |
| `archived_receipt` | an independently dated archive of the earlier publication (an archived file or page) contains this value | yes, once the archive's date and integrity are recorded |
| `captured_on_schedule` | HIO captured this value itself, and `knowable_at` is the documented release time preceding that capture | yes, for HIO-captured vintages only |
| `schedule_only` | only the series' release schedule is known; nothing shows that this value (rather than a later revision) was what was published | **no** |
| `rule_inferred` | an assumed lag declared in the series spec | **no** |

**A schedule is not vintage evidence.** For a backfill, HIO usually receives only the *current*
value of each key. That value may be a revision. It gets `schedule_only` or `rule_inferred`
unless the source supplies vintage evidence. A backfill never has a basis stronger than its
evidence, and is never treated as captured history.

## 4. Query modes

| Mode | Returns | Claim it supports |
|---|---|---|
| `as_captured_by_hio(T)` | per key, the latest `valid` vintage with `captured_at ≤ T` | "HIO actually held this at T" (provable) |
| `as_known_by_market(T)` | per key, the latest `valid` vintage with `knowable_at ≤ T` **and** a basis from the "yes" rows of §3. If no vintage of the key qualifies, the key is **absent** (unknown), not filled | "this value was publicly knowable at T", with vintage evidence |
| `reconstructed(T)` | per key, the latest `valid` vintage with `knowable_at ≤ T` under any basis, including `schedule_only` and `rule_inferred` | **reconstructed availability only.** Results carry the label, and may not be described as point-in-time evidence |
| `latest()` | the latest `valid` vintage | descriptive work only; MUST NOT feed predictive or TAA evaluation |

Every release and model result records:
- its `knowledge_mode`;
- its `knowledge_cutoff` T;
- `weakest_knowable_basis`.

Predictive work labelled point-in-time requires `as_captured_by_hio` or `as_known_by_market`.

### 4.1 Fixture: original, revision, current-only backfill (F-REVIEW-2026-10-18-a01-1)

Series X, key 2020-02, synthetic:

| Event | Value | Instant | Evidence |
|---|---|---|---|
| original release | 100 | 2020-03-15T00:30Z | (not held by HIO) |
| revision | 110 | 2025-06-01T00:30Z | (not held by HIO) |
| HIO backfill | 110 | captured 2026-01-10 | the current file only; the schedule says release ≈ mid-March |

Case A: the backfill alone. The vintage stored is 110, with `knowable_basis: schedule_only`.

| Query | Result |
|---|---|
| `as_known_by_market(2021-01-01)` | **absent** (no qualifying vintage) |
| `reconstructed(2021-01-01)` | 110, labelled reconstructed |
| `as_captured_by_hio(2021-01-01)` | absent |
| `as_captured_by_hio(2026-02-01)` | 110 |

Case B: the publisher's vintage archive is also ingested. That gives vintages 100
(`publisher_vintage`, 2020-03-15) and 110 (`publisher_vintage`, 2025-06-01).

| Query | Result |
|---|---|
| `as_known_by_market(2021-01-01)` | **100** |
| `as_known_by_market(2025-07-01)` | **110** |

## 5. Capture clock
## 5. Capture clock

- Each source records `capture_started_at`, the first scheduled capture.
- Gaps in scheduled capture are recorded as **capture gaps** with their cause. A gap is never
  filled by a later fetch presented as captured.
- Revisions observed by scheduled capture are first-class research data, for example the
  revision behaviour of a macro release.

## 6. Quality gates (minimum, from S1)

- schema and type validation of each receipt;
- calendar completeness against the declared calendar (holidays known);
- staleness (the expected next valid date has not arrived after the documented schedule plus
  grace);
- jump detection with a series-specific threshold, which quarantines pending review;
- revision detection (a new vintage), which is logged and does not quarantine by itself;
- duplicate receipt (identical hash), which is a no-op.

Quarantine is decided deterministically. An agent may *propose* a release from quarantine; only
the gate's rules or the owner can release it.

## 7. Invariants (tested from S1)

| ID | Invariant |
|---|---|
| OBS-INV-001 | an identical re-fetch creates no new vintage; a changed value creates `vintage_seq + 1`, and earlier vintages remain retrievable |
| OBS-INV-002 | `as_captured_by_hio(T)` never returns `captured_at > T` |
| OBS-INV-003 | `as_known_by_market(T)` never returns `knowable_at > T`, and never returns a vintage whose basis is `schedule_only` or `rule_inferred` |
| OBS-INV-004 | every observation references an existing receipt whose hash verifies |
| OBS-INV-005 | `valid_time` is never derived by converting a UTC instant to a date |
| OBS-INV-006 | a backfilled observation's `knowable_basis` is `publisher_timestamp`, `publisher_vintage` or `archived_receipt` only with that vintage-specific evidence; otherwise it is `schedule_only` or `rule_inferred` |
| OBS-INV-007 | the §4.1 fixture: Case A gives `as_known_by_market(2021-01-01)` absent and `reconstructed` 110; Case B gives 100 at 2021-01-01 and 110 at 2025-07-01 |

## Changelog

- 0.1 (2026-10-18): initial.
- 0.2 (2026-10-18): knowability is vintage-specific; `schedule_only` cannot support `as_known_by_market`; new `reconstructed(T)` mode; §4.1 fixture; OBS-INV-003/006/007 (F-REVIEW-2026-10-18-a01-1).
