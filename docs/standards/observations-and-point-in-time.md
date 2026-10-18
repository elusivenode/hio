---
id: HIO-STD-OBS
title: Observations, point-in-time knowledge and vintages
status: proposed
owner: HIO architecture lead (owner); market-data maintainer
version: 0.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0004
---

# Observations, point-in-time knowledge and vintages (v0.1)

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

## 3. `knowable_basis`: an evidence grade, strongest first

| Value | Meaning | Example |
|---|---|---|
| `publisher_timestamp` | the publisher's own release timestamp, carried in the payload or headers | an API field giving publication time |
| `publisher_vintage` | the publisher maintains real-time vintages | ALFRED real-time periods [EXT] |
| `documented_schedule` | the publisher's documented release calendar or time of day, applied to the valid date | "published daily at about 4pm Sydney" [EXT, per source] |
| `rule_inferred` | an assumed lag, declared in the series spec | "settlement + 1 business day, 07:00 exchange time" |

**For a backfill:** `captured_at` is the backfill time. `knowable_at` comes from the strongest
basis available, and is usually `documented_schedule` or `rule_inferred`. **A backfill never
has `knowable_basis` stronger than its evidence, and it is never treated as captured history.**

## 4. Query modes

| Mode | Returns | Claim it supports |
|---|---|---|
| `as_captured_by_hio(T)` | per key, the latest `valid` vintage with `captured_at ≤ T` | "HIO actually held this at T" (provable) |
| `as_known_by_market(T)` | per key, the latest `valid` vintage with `knowable_at ≤ T` | "the market could have known this at T", only as strong as the weakest `knowable_basis` used |
| `latest()` | the latest `valid` vintage | descriptive work only; MUST NOT feed predictive or TAA evaluation |

Every release and model result records:
- its `knowledge_mode`;
- its `knowledge_cutoff` T;
- `weakest_knowable_basis`.

Predictive work labelled point-in-time requires `as_captured_by_hio`, or `as_known_by_market`
with a basis no weaker than `documented_schedule`. Results built on `rule_inferred` availability
are labelled **"reconstructed availability"**.

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
| OBS-INV-003 | `as_known_by_market(T)` never returns `knowable_at > T` |
| OBS-INV-004 | every observation references an existing receipt whose hash verifies |
| OBS-INV-005 | `valid_time` is never derived by converting a UTC instant to a date |
| OBS-INV-006 | a backfilled observation's `knowable_basis` is not `publisher_timestamp` unless the backfilled payload carries the timestamp |
