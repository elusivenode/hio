---
id: HIO-STD-OBS-V0.3-CANDIDATE
title: Observations, point-in-time knowledge and vintages (v0.3 candidate)
status: proposed   # consolidation for separate exact-revision approval (OD-0030); NOT approved
owner: HIO architecture lead (owner); market-data maintainer
version: 0.3-candidate
last_reviewed: 2026-10-24
decision: HIO-ADR-0004
supersedes_on_approval: docs/standards/observations-and-point-in-time.md v0.2 (OD-0008; blob 341cd608604d)
incorporates: [OBS-AMEND-Q001 revision 4 (OD-0029; blob 419992f2f0be008dd505a69ed58fb463197ff33c), OBS-AMEND-Q002 revision 5 (OD-0030; blob d0a25b3b981474bbe57304829aaf5379b04c9e91), OBS-AMEND-Q002-R1 revision 1 (OD-0035; blob cb7a937dc6e8cc20314e2ae33cd20ce1163fd584)]
---

# Observations, point-in-time knowledge and vintages (v0.3 candidate)

> **Candidate, not approved.** Until the owner approves this exact revision, observations v0.2
> (OD-0008) and the two approved amendments, OBS-AMEND-Q001 revision 4 (OD-0029) and
> OBS-AMEND-Q002 revision 5 (OD-0030) with its
> amendment OBS-AMEND-Q002-R1 revision 1 (OD-0035), govern. This document consolidates them **without changing
> their substance**. The editorial changes are listed in the changelog.

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
| `quality_status` | enum | `pending`, `valid`, `quarantined`, `superseded` | Quality is a history, not a field. The ingest gate's verdict is the vintage's first quality
decision, with `decided_at = captured_at`. Every later change is an append-only *quality event*
(`status`, `actor`, `evidence`, `decided_at`), and `decided_at` must satisfy the rule in the
clocks table. The vintage's status at Q is its latest decision with `decided_at ≤ Q`. Only
`valid` at Q is eligible at Q. |

### 2.1 Two questions, two clocks

A point-in-time result answers two separate questions:

| Question | Who knows | Clock |
|---|---|---|
| Was this value **publicly knowable** by T? | the market | `knowable_at` (§2, §3), compared with the **information cutoff T** |
| Did **HIO hold** this value, and judge it **eligible**, by Q? | HIO | `captured_at`, and the time of each HIO decision, compared with the **HIO decision cutoff Q** |

Rule: market knowability never implies HIO eligibility, and HIO eligibility never backdates
market knowability.

**The clocks:**

| Clock | On | Meaning | Rule |
|---|---|---|---|
| `valid_time` | vintage | what the value refers to (market-local) | unchanged (OBS-INV-005) |
| `knowable_at` | vintage | earliest public knowability (market claim, with its basis) | unchanged (§3) |
| `captured_at` | vintage | when HIO acquired the receipt; the start of HIO holding the vintage | unchanged |
| `decided_at` | quality event; conflict resolution (§6.1) | when HIO **made** the decision. This is HIO's own clock, not the market's | never earlier than the vintage's `captured_at`. Strictly increasing per vintage. **No backdating**: never earlier than the moment the event is recorded |
| `detected_at` | derived conflict (§4.3) | when HIO first held both conflicting vintages, i.e. the later `captured_at` | derived; never chosen |
| `event_seq` | any event | storage order only | **never** decides a result |
| **T** | query | information cutoff: `captured_at` for `as_captured_by_hio`; `knowable_at` otherwise | as in §4 |
| **Q** | query | HIO decision cutoff: which vintages HIO held, and which quality and conflict decisions it had made | new; recorded on every result |

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

Predictive work labelled point-in-time requires a result with `predictive_pit_admissible = true` (§4.2).

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
| `as_known_by_market(2021-01-01, Q = after the archive was ingested)` | **100**, labelled `quality_after_cutoff`; `predictive_pit_admissible = false` |
| `as_known_by_market(2025-07-01, Q = after the archive was ingested)` | **110**, labelled `quality_after_cutoff`; `predictive_pit_admissible = false` |
| `as_known_by_market(2021-01-01, Q = 2021-01-01)` | **absent**: HIO did not hold the archive at Q |

Case A is unchanged. `reconstructed` takes Q after the backfill and is never admissible.

**Consequence.** Archive-backed market evidence (Case B) remains available, labelled, for
descriptive work and diagnostics. It may support predictive point-in-time research only under a
future evidence-based admissibility rule (§4.2).



### 4.2 The HIO decision cutoff and admissibility

**HIO decision cutoff Q.** Every mode evaluates eligibility at Q. A vintage is eligible at Q
only if all of these hold:
- `captured_at ≤ Q` (HIO held it);
- its status at Q is `valid` (§2);
- it is not suppressed by an unresolved conflict at Q (§4.3).

A result is a function of (mode, T, Q) and of events dated `≤ Q` only. A decision made after
Q never changes it. Q is set per mode:

| Mode | T (information) | Q (HIO decisions) | Label recorded with every result |
|---|---|---|---|
| `as_captured_by_hio(T)` | `captured_at ≤ T` | **Q = T, fixed** (it cannot be overridden): "what HIO held and judged eligible at T" | `point_in_time`; `quality_as_of = T` |
| `as_known_by_market(T, Q)` | `knowable_at ≤ T` and a "yes" basis (§3) | **explicit and required**. Q may be later than T, because vintage evidence such as an archive is often acquired after T | `point_in_time` (market claim); `quality_as_of = Q`; and **`quality_after_cutoff`** whenever Q > T |
| `reconstructed(T, Q)` | `knowable_at ≤ T`, any basis | explicit and required | `reconstructed`; `quality_as_of = Q`; **`restated_quality`** whenever Q > T |
| `latest(Q)` | none | explicit and required | `descriptive`; `quality_as_of = Q`; **`restated_quality`** always |

**Admissibility.** Every result also records `predictive_pit_admissible`:

| Mode | `predictive_pit_admissible` |
|---|---|
| `as_captured_by_hio(T)` | **true** (Q = T) |
| `as_known_by_market(T, Q)` | **true only if Q ≤ T**; **false** whenever Q > T |
| `reconstructed(T, Q)` | false, always |
| `latest(Q)` | false, always |

**Q > T is never admissible by default.** A result with Q > T applies HIO decisions, or HIO's
possession of evidence, dated after its information cutoff. Such a result:
- is labelled (`quality_after_cutoff` or `restated_quality`), never silently;
- has `predictive_pit_admissible = false`;
- **must not** feed predictive work, TAA evaluation or any release labelled point-in-time. It
  remains usable for descriptive work and for diagnostics.

Any future exception, for example archive-backed market evidence, needs its own
**evidence-based admissibility rule**. That rule is a separate owner-approved amendment, stating
the evidence required and its invariants. It is not a parameter, and no consumer or agent can
grant it.

**Market knowability and later HIO validation stay distinguishable.** Every selected vintage in
a result reports:
- `knowable_at` and `knowable_basis` (the market claim);
- `captured_at` (when HIO acquired it);
- `eligibility_decided_at`: the `decided_at` of the quality decision in force at Q;
- `validated_after_cutoff`: whether `eligibility_decided_at` is later than T.

A reader can therefore see, per value, whether it was knowable by T and whether HIO had judged
it eligible by T.

### 4.3 Conflicts

**Ranking.** Each mode ranks a key's vintages by an instant, then by the §3 basis strength:
- the instant is `captured_at` for `as_captured_by_hio` (the *capture clock*);
- it is `knowable_at` for the other three modes (the *knowability clock*).

**Observation evidence identity.** An observation's identity is `(receipt_id, value)`:
- `receipt_id` is the SHA-256 of the receipt bytes (§1);
- `value` is the canonical decimal string, normalised so that `3.6` and `3.60` are the same
  value.

`vintage_seq` is never part of a conflict's identity.

**Slot.** A slot is one (`series_id`, `key`, rank clock, instant, basis strength). Its *members*
are the observations in that slot.

**Fixed capture-time evidence.** A receipt's `captured_at` is fixed when it is captured. The
capture record is written in the capture transaction, and capture times are strictly increasing
per source.
- The **evidence at Q**, E(Q), is the set of receipts whose capture records have
  `captured_at ≤ Q`, with their bytes verified (OBS-INV-004).
- *Processing* (deriving vintages from receipts) may run in a different order, for example in a
  rebuild, a replay, or after a crash between capture and ingest.
- HIO's knowledge at Q is defined by E(Q) processed in capture order. It never depends on the
  actual processing order.

**Conflict, and the canonical conflict chain.**
- The **conflict in force at Q** for a slot is the set of its members drawn from E(Q), provided
  that set holds at least two different values. Equal values alone are not a conflict
  (OBS-INV-001).
- The member set grows only when a member's `captured_at` is reached, and members with the same
  `captured_at` join together.
- The sequence of member sets is the slot's **canonical conflict chain**: a pure function of the
  evidence.

**Conflict identity** (deterministic, from the evidence):

```
conflict_id = SHA-256( canonical_json({
    "series_id":  …,
    "key":        …,                      # valid_time, ISO form
    "rank_clock": "knowable_at" | "captured_at",
    "instant":    …,                      # UTC, ISO form
    "strength":   …,                      # §3 basis order
    "members":    sorted([{"receipt_id": …, "value": …}, …])
}) )
```

A conflict's `detected_at` is the latest `captured_at` among its members. It is derived, never
stored.

**Three distinctions** (A, B and C contradict each other in one slot):

| Case | Example | What is guaranteed |
|---|---|---|
| 1. The same fixed evidence, processed in different orders | captures A at t1, B at t2, C at t3 with t1 < t2 < t3, processed A→B→C or A→C→B | **Identical** results at every (mode, T, Q), and an **identical** derived chain: {A,B} from t2, then {A,B,C} from t3. Processing writes no conflict state, so the persisted conflict state (resolution events only) cannot differ |
| 2. Genuinely different acquisition histories | store X captures B at t2 and C at t3; store Y captures C at t2 and B at t3 | different evidence, so a **different** chain: X has {A,B} then {A,B,C}; Y has {A,C} then {A,B,C}. Results at Q in [t2, t3) may legitimately differ. Each store's results are stable. Once both hold A, B and C with no differing resolutions, the final conflict and the results are identical |
| 3. Final state versus history | — | the final state at Q (the conflict in force, its id, the resolution in force, the result) is a function of E(Q) and the resolution events dated ≤ Q. The history of member sets is the derived chain. Owner resolutions are the only persisted conflict history |

**No ingestion-order tie-break.** Among a key's eligible vintages, the mode's instant decides,
then the stronger basis (§3). `vintage_seq`, `event_seq`, processing order and storage order
never decide a result.

**Conflicts are derived, not stored.** The conflict in force at Q for each slot is derived from
E(Q) (§4.3) when a result is computed. No conflict-detection record is persisted.

**An unresolved conflict suppresses the key.** The key is **absent** from a mode's result if
both hold:
- the mode's top-ranked eligible slot for the key has a conflict in force at Q;
- no resolution of that exact `conflict_id` is in force at Q.

A result at Q < `detected_at` is unchanged: HIO did not yet hold the contradiction.

**Diagnostics never hide a contradiction.** Every result lists **every** conflict in force at Q
that involves the result's series and keys. Each listed conflict is marked with one of these
effects:
- `suppresses_key`: an unresolved conflict at the selected rank, so the key is absent;
- `resolved`: a resolution in force at Q decided the key;
- `outranked`: a higher-ranked vintage decided the key. The conflict is real, but it is not at
  the selected rank;
- `not_eligible_in_mode`: its members are excluded by the mode, or it lies on the other rank
  clock.

The diagnostics query `conflicts(series_id, Q)` lists, per slot, the derived chain up to Q, the
conflict in force, and its resolution state.

**Reproducibility.** Every result records three pins:
- `evidence_digest`: SHA-256 over the sorted (`source_id`, `captured_at`, `receipt_id`) of E(Q)
  for the series' sources;
- `resolution_digest`: SHA-256 over the sorted resolution events in force at Q for the series;
- `algorithm_revision`: a declared identifier of the derivation and selection rules, changed
  whenever their semantics change. It is recorded with the code reference in releases.

Recomputing from the pinned receipts and resolution events under the pinned algorithm revision
must reproduce the result byte for byte. A result whose pins cannot be verified is refused.

#### Quality decisions pin (OBS-AMEND-Q002-R1)

Every result records a fourth pin, **`quality_digest`**, alongside `evidence_digest`,
`resolution_digest` and `algorithm_revision`. Their meanings are unchanged.

**Events included.** Every append-only quality decision event (§2) for a vintage of the
result's series with `decided_at ≤ Q`. Nothing else is included:
- the ingest gate's first verdict at `captured_at` is **not** an event: it is re-derived from the
  verified receipt by the completeness check (OBS-INV-019);
- resolution events are pinned by `resolution_digest`.

**Fields per event, and only these:**
- the decided vintage, identified by its evidence: `series_id`, `valid_time`, `receipt_id`,
  `captured_at`;
- the decision: `status`, `decided_at`, `actor`, `evidence`.

**Excluded:**
- `vintage_seq`, because the vintage is identified by evidence, never by arrival order;
- `event_seq` and the storage key, which are storage order only;
- `recorded_at`. It serves the no-backdating check (OBS-INV-012) and does not affect the
  result, so a faithful copy of the history gives the same pin.

**Ordering and encoding.**
- Events are sorted by (`series_id`, `valid_time`, `receipt_id`, `captured_at`, `decided_at`).
  That order is total, because `decided_at` is strictly increasing per vintage (§2.1).
- The pin is the SHA-256 of the repository's canonical JSON encoding of:

  ```
  {"schema": "hio-quality-digest/1", "series_id": <series_id>, "events": [<event>, ...]}
  ```

  In that encoding, keys are sorted, instants are UTC with a `Z` suffix and microseconds, and
  strings are UTF-8 without insignificant whitespace.
- The schema tag versions the encoding. A change to the event fields or ordering needs a new tag
  and a new `algorithm_revision`.

**Empty history.** No event with `decided_at ≤ Q` gives `"events": []`, and the pin is the
SHA-256 of that encoding: a fixed, non-empty value per series. The pin is never absent or the
empty string.

**Exclusion after Q.** An event with `decided_at > Q` is not included, so a later decision never
changes the pin, or the result, at Q (OBS-INV-008). No-backdating (OBS-INV-012) makes this
stable over time: no event can be recorded later with `decided_at ≤` an earlier recording time.

**Provenance.**
- Every `View` records `quality_digest`.
- Every release's input record for a view (in the manifest's existing `inputs` field) records it
  beside the other pins. The manifest core field set is unchanged (releases standard §2).
- Recomputing from the pinned receipts, resolution events and quality events, under the pinned
  `algorithm_revision`, must reproduce the result byte for byte.
- A recomputation, rebuild or reuse whose four pins do not all equal the recorded pins is
  **refused** (a pin mismatch). It never silently replaces the recorded result.

**Algorithm revision.** Adding this pin changes the content of every result, so implementing it
moves `algorithm_revision` from `hio-obs-select/2` to `hio-obs-select/3`. The meaning of
`algorithm_revision` is unchanged: it still identifies the derivation and selection rules,
including what a result records.

**Migration.** Release identities change, because each input record gains `quality_digest`.
`data.csv` bytes do not change (no rule changes). A release built before the pin existed is not
reinterpreted. Its rebuild under `hio-obs-select/3` is a new release, and the old one keeps its
own recorded pins.

**Completeness.** A result or resolution at Q is computed only when processing is complete at
Q. That means the stored vintages with `captured_at ≤ Q` for the series equal the vintages
derived from E(Q) processed in capture order (receipts quarantined at ingest are accounted for
by their quarantine record).
- If that cannot be established, the query or resolution is **refused**: it raises, and no
  partial result is returned.
- The S1a pipeline ingests each receipt immediately after capturing it, in capture order.
- Evidence first recorded later than its `captured_at`, a *late capture*, is outside this
  amendment (open decision Q-004).

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

### 6.1 Conflict adjudication

**Adjudication (S1a: the owner only).** The only persisted conflict state is the append-only
*resolution event*: `conflict_id`, `outcome`, `actor`, `evidence`, `decided_at`.
- Its storage key is derived from its content
  (`catalogue/resolutions/<series_id>/<conflict_id>/<decided_at>-<sha256 of the event>.json`).
- Processing never writes one.

The outcome is one of:
- `select({"receipt_id": …, "value": …})`: names a member by its evidence identity;
- `reject_all`: the key stays unavailable at that rank, with a reason.

Rules for resolution events:
- only the owner may append one in S1a; an agent may propose one;
- it must name **the exact `conflict_id` in force at its `decided_at`**, derived from
  E(`decided_at`) with completeness established;
- `decided_at ≥ detected_at`, and no backdating (§2.1, §4.2);
- a later resolution of the same `conflict_id` supersedes the earlier one from its own
  `decided_at`. Nothing is edited or deleted;
- a resolution applies only to its own `conflict_id`, and only for Q ≥ `decided_at`. When the
  chain grows, the earlier resolution stays in the history but does not decide the new conflict.

**Point-in-time stability.** A result at (mode, T, Q) depends only on E(Q), the chain derived
from it, and resolutions with `decided_at ≤ Q`. Processing order and later evidence or events
never change it.

## 7. Invariants (tested from S1)

| ID | Invariant |
|---|---|
| OBS-INV-001 | an identical re-fetch creates no new vintage; a changed value creates `vintage_seq + 1`, and earlier vintages remain retrievable |
| OBS-INV-002 | `as_captured_by_hio(T)` never returns `captured_at > T` |
| OBS-INV-003 | `as_known_by_market(T)` never returns `knowable_at > T`, and never returns a vintage whose basis is `schedule_only` or `rule_inferred` |
| OBS-INV-004 | every observation references an existing receipt whose hash verifies |
| OBS-INV-005 | `valid_time` is never derived by converting a UTC instant to a date |
| OBS-INV-006 | a backfilled observation's `knowable_basis` is `publisher_timestamp`, `publisher_vintage` or `archived_receipt` only with that vintage-specific evidence; otherwise it is `schedule_only` or `rule_inferred` |
| OBS-INV-007 | §4.1 Case A as before. Case B at Q after the archive ingestion gives 100 and 110, labelled and not admissible; at Q = 2021-01-01, absent |
| OBS-INV-008 | a result at (mode, T, Q) depends only on vintages with `captured_at ≤ Q` and on decisions with `decided_at ≤ Q` |
| OBS-INV-009 | `as_captured_by_hio(T)` uses Q = T; a quality event with `decided_at > T` never changes it |
| OBS-INV-010 | every result records `knowledge_mode`, T, Q (`quality_as_of`), `weakest_knowable_basis`, `predictive_pit_admissible`, and the labels `quality_after_cutoff` and `restated_quality` exactly when §4 requires them. Every selected vintage reports `knowable_at`, `knowable_basis`, `captured_at`, `eligibility_decided_at` and `validated_after_cutoff` |
| OBS-INV-011 | **Processing-order independence (case 1).** For the same fixed evidence and the same resolution events, every result at every (mode, T, Q) is identical whatever the processing order. That covers values, the conflict list with ids and effects, labels and pins. Processing writes no conflict state |
| OBS-INV-012 | a quality event is refused if `decided_at` is earlier than the vintage's `captured_at`, not later than the vintage's previous decision, or earlier than its recording time |
| OBS-INV-013 | **Point-in-time stability.** Results at Q < `detected_at` are unchanged when a contradicting observation is captured. Results at Q < `decided_at` are unchanged when a resolution is appended. Results at Q ≥ `decided_at` apply it, to its own `conflict_id` only. A chain extension ends a resolution's effect only from the new member's `captured_at` |
| OBS-INV-014 | `predictive_pit_admissible` is true only for `as_captured_by_hio`, and for `as_known_by_market` with Q ≤ T. No API parameter, label or caller can set it otherwise. A consumer or release path that requires point-in-time input refuses any result where it is false |
| OBS-INV-015 | **Deterministic derived identity.** The chain is a function of the evidence only. A member set always has the same `conflict_id`; `vintage_seq` never enters it |
| OBS-INV-016 | **No silent concealment.** Every conflict in force at Q on the result's series and keys appears in the result with exactly one effect. The result's list equals `conflicts(series_id, Q)` restricted to its keys |
| OBS-INV-017 | **Acquisition-history semantics (case 2).** Stores with different capture histories may differ at intermediate Q. Each is stable over time. With the same evidence and no differing resolutions, their final conflict and their results are identical |
| OBS-INV-018 | the reproducibility pins are `evidence_digest`, `resolution_digest`, `quality_digest` and `algorithm_revision`. Recomputing from them is byte-identical, and a mismatch on any pin refuses |
| OBS-INV-019 | **Completeness.** A query or resolution at Q is refused, with no partial output, unless the stored vintages with `captured_at ≤ Q` equal the capture-order derivation of E(Q) |
| OBS-INV-020 | `quality_digest` is a function only of the quality events of the series with `decided_at ≤ Q`, through the fields and ordering above |
| (append-only resolutions) | resolution events are only appended; none is edited or deleted; their storage key is a function of their content |
| (refusals) | a resolution is refused if it names anything but the `conflict_id` in force at its `decided_at`, if it names a member outside that conflict, if `decided_at < detected_at`, if it is backdated, if completeness at `decided_at` cannot be established, or if the actor is not the owner. The store is unchanged after a refusal |

### 7.1 Executable forms (from the approved amendments)

| ID | Executable form |
|---|---|
| OBS-INV-007 | the existing fixture, with Q explicit |
| OBS-INV-008 | Hypothesis: build a store from random receipts and quality events, and compute every mode at a random (T, Q). Then append random later receipts and events (all dated `> Q`) and recompute. The results must be byte-identical (canonical JSON of the `View`, labels included) |
| OBS-INV-009 | the §4 table as a fixture test, in both directions, plus a Hypothesis property over event dates |
| OBS-INV-010 | a parametrised test over the four modes and over Q <, = and > T |
| OBS-INV-011 | Hypothesis over permutations of the processing order of a fixed receipt set (captures fixed); compare canonical JSON of every `View` at sampled (T, Q). Assert that processing writes nothing under `catalogue/resolutions/` or any conflict prefix |
| OBS-INV-012 | negative tests; the store is unchanged after a refusal (snapshot equality, as for the rights gate) |
| OBS-INV-013 | the §4(a) table as a fixture; a property that adding evidence or resolutions dated after Q leaves every result at Q byte-identical |
| OBS-INV-014 | a property over all modes and over (T, Q); a negative test that a release or model input requiring point-in-time refuses Q > T results |
| OBS-INV-015 | permutation property over derived chains and ids; the §4(b) fixture |
| OBS-INV-016 | computed both ways and compared (raise on disagreement); a fixture for each effect |
| OBS-INV-017 | the stores X and Y fixture from §2 |
| OBS-INV-018 | a round-trip test (compute, recompute from the pins, compare bytes); negative tests for each broken pin; amended: the round-trip test, extended to quality events |
| OBS-INV-019 | a fixture that captures a receipt but leaves it unprocessed (the §4(b) midway state): refused. After processing: served |
| OBS-INV-020 | the property and fixture tests of OBS-AMEND-Q002-R1 §4 (AT-Q2R1-1..7) |
| (append-only resolutions) | store-level test: append, reopen, and compare the bytes of every existing event |
| (refusals) | negative tests with snapshot equality |

## Changelog

- 0.1 (2026-10-18): initial.
- 0.2 (2026-10-18): knowability is vintage-specific; `schedule_only` cannot support `as_known_by_market`; new `reconstructed(T)` mode; §4.1 fixture; OBS-INV-003/006/007 (F-REVIEW-2026-10-18-a01-1).
- 0.3 (candidate, 2026-10-24; not approved): incorporates OBS-AMEND-Q001 revision 4 (OD-0029) and OBS-AMEND-Q002 revision 5 (OD-0030) without changing their substance. Editorial changes only: (1) the amendments' instructions became text in place (§2 `quality_status` rule, §2.1, §4.1 Case B, §4 predictive-work sentence, §4.2, §4.3, §6.1, §7, §7.1); (2) blockquote markers removed, and cross-references to the amendments replaced by section numbers; (3) in the clocks table, the `detected_at` row reads "derived conflict" instead of "conflict event (Q-002)", because Q-002 revision 5 (Option A′) derives conflicts and stores no conflict events; (4) the invariants' executable forms are listed in §7.1; (5) v0.2's duplicated "## 5. Capture clock" heading is removed. The worked examples, options, acceptance tests and implementation outlines remain in the amendments.
- 0.3 (candidate, updated 2026-10-25; not approved): also incorporates OBS-AMEND-Q002-R1 revision 1 (OD-0035; the `quality_digest` pin) without changing its substance: its proposed text is in §4.3 ("Quality decisions pin"), OBS-INV-018 is amended and OBS-INV-020 added in §7 and §7.1. Editorial changes only: blockquote markers removed; cross-references to Q-001 sections replaced by this document's section numbers.
