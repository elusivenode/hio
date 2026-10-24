---
id: OBS-AMEND-Q002
title: "Draft amendment to the observations standard: equally evidenced contradictions are derived conflicts, never resolved by ingestion order (Q-002)"
status: proposed   # draft for the owner; NOT approved; NOT implemented
revision: 5        # revision 1 at d1edf1e (OD-0023); 2 at baa8e4e (OD-0026); 3 at 6f013a7 (OD-0027); 4 at 4e57fa1 (OD-0028); 5 under OD-0029 (Option A′: derived conflicts, resolution events only)
owner: owner + solution architect (decide); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d in this repository, bd9eff0893ea in macsmsf history)
source: F-REVIEW-2026-10-24-s1a-1-7; open-decisions Q-002; OD-0026; OD-0027; OD-0028; OD-0029 (Option A′ selected)
companion: "OBS-AMEND-Q001 revision 4 (approved, OD-0029; blob 419992f2) defines the clocks and the HIO decision cutoff Q"
---

# Draft: equally evidenced contradictions (Q-002), Option A′

> **Draft only.** Nothing here is approved or implemented. The S1a code keeps its current
> tie-break (stronger basis, then the later-recorded vintage) until the owner approves an exact
> revision.

## 1. The problem (F-REVIEW-2026-10-24-s1a-1-7)

§4 picks "the latest" qualifying vintage per key, with no rule for equal instants. The code
breaks a remaining tie by `vintage_seq`, which is the ingestion order.

Codex's counterexample:
- values 3.60 and 3.61 for one key, with the same `publisher_timestamp`;
- ingested in opposite orders into two stores;
- `as_known_by_market` returned 3.61 in one store and 3.60 in the other.

## 2. Definitions

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

## 3. Proposed text

**§4: add after the table.**

> **No ingestion-order tie-break.** Among a key's eligible vintages, the mode's instant decides,
> then the stronger basis (§3). `vintage_seq`, `event_seq`, processing order and storage order
> never decide a result.
>
> **Conflicts are derived, not stored.** The conflict in force at Q for each slot is derived from
> E(Q) (§2) when a result is computed. No conflict-detection record is persisted.
>
> **An unresolved conflict suppresses the key.** The key is **absent** from a mode's result if
> both hold:
> - the mode's top-ranked eligible slot for the key has a conflict in force at Q;
> - no resolution of that exact `conflict_id` is in force at Q.
>
> A result at Q < `detected_at` is unchanged: HIO did not yet hold the contradiction.
>
> **Diagnostics never hide a contradiction.** Every result lists **every** conflict in force at Q
> that involves the result's series and keys. Each listed conflict is marked with one of these
> effects:
> - `suppresses_key`: an unresolved conflict at the selected rank, so the key is absent;
> - `resolved`: a resolution in force at Q decided the key;
> - `outranked`: a higher-ranked vintage decided the key. The conflict is real, but it is not at
>   the selected rank;
> - `not_eligible_in_mode`: its members are excluded by the mode, or it lies on the other rank
>   clock.
>
> The diagnostics query `conflicts(series_id, Q)` lists, per slot, the derived chain up to Q, the
> conflict in force, and its resolution state.
>
> **Reproducibility.** Every result records three pins:
> - `evidence_digest`: SHA-256 over the sorted (`source_id`, `captured_at`, `receipt_id`) of E(Q)
>   for the series' sources;
> - `resolution_digest`: SHA-256 over the sorted resolution events in force at Q for the series;
> - `algorithm_revision`: a declared identifier of the derivation and selection rules, changed
>   whenever their semantics change. It is recorded with the code reference in releases.
>
> Recomputing from the pinned receipts and resolution events under the pinned algorithm revision
> must reproduce the result byte for byte. A result whose pins cannot be verified is refused.
>
> **Completeness.** A result or resolution at Q is computed only when processing is complete at
> Q. That means the stored vintages with `captured_at ≤ Q` for the series equal the vintages
> derived from E(Q) processed in capture order (receipts quarantined at ingest are accounted for
> by their quarantine record).
> - If that cannot be established, the query or resolution is **refused**: it raises, and no
>   partial result is returned.
> - The S1a pipeline ingests each receipt immediately after capturing it, in capture order.
> - Evidence first recorded later than its `captured_at`, a *late capture*, is outside this
>   amendment (open decision Q-004).

**§6: add an adjudication rule.**

> **Adjudication (S1a: the owner only).** The only persisted conflict state is the append-only
> *resolution event*: `conflict_id`, `outcome`, `actor`, `evidence`, `decided_at`.
> - Its storage key is derived from its content
>   (`catalogue/resolutions/<series_id>/<conflict_id>/<decided_at>-<sha256 of the event>.json`).
> - Processing never writes one.
>
> The outcome is one of:
> - `select({"receipt_id": …, "value": …})`: names a member by its evidence identity;
> - `reject_all`: the key stays unavailable at that rank, with a reason.
>
> Rules for resolution events:
> - only the owner may append one in S1a; an agent may propose one;
> - it must name **the exact `conflict_id` in force at its `decided_at`**, derived from
>   E(`decided_at`) with completeness established;
> - `decided_at ≥ detected_at`, and no backdating (OBS-AMEND-Q001);
> - a later resolution of the same `conflict_id` supersedes the earlier one from its own
>   `decided_at`. Nothing is edited or deleted;
> - a resolution applies only to its own `conflict_id`, and only for Q ≥ `decided_at`. When the
>   chain grows, the earlier resolution stays in the history but does not decide the new conflict.
>
> **Point-in-time stability.** A result at (mode, T, Q) depends only on E(Q), the chain derived
> from it, and resolutions with `decided_at ≤ Q`. Processing order and later evidence or events
> never change it.

**§7: add invariants** OBS-INV-011, -013, -015, -016, -017, -018 and -019 (§5).

## 4. Worked examples

**(a) Codex's counterexample, extended.** The setup:
- v1 = 3.60 (receipt r1) and v2 = 3.61 (receipt r2), key K, both `publisher_timestamp` at
  `knowable_at` 2026-01-12T00:00Z;
- captured 2026-01-12T01:00Z and 2026-01-13T01:00Z, so C = {r1, r2} has `detected_at`
  2026-01-13T01:00Z;
- resolution R of C, `select(r1, 3.60)`, `decided_at` 2026-01-14T09:00Z;
- v3 = 3.62 (r3), the same slot, captured 2026-01-16T01:00Z, so the next chain element is
  C′ = {r1, r2, r3}.

| Query (T = 2026-01-12T12:00Z) | Result | Conflicts listed |
|---|---|---|
| `as_known_by_market`, Q = 2026-01-12T12:00Z | **3.60** | none |
| `as_known_by_market`, Q = 2026-01-13T12:00Z | **absent** | C: `suppresses_key` |
| `as_known_by_market`, Q = 2026-01-15T00:00Z | **3.60** | C: `resolved` (R) |
| `as_known_by_market`, Q = 2026-01-17T00:00Z | **absent** | C′: `suppresses_key` (C and R remain in history) |
| `as_captured_by_hio(2026-01-13T12:00Z)` | **3.61** | C: `not_eligible_in_mode` |

The `as_known_by_market` rows with Q > T also carry `quality_after_cutoff` and
`predictive_pit_admissible = false` (OBS-AMEND-Q001).

**(b) The owner's A, B, C case.** A, B and C share a slot, captured at t1 < t2 < t3.

| | Processed A→B→C | Processed A→C→B |
|---|---|---|
| Derived chain | {A,B} from t2; {A,B,C} from t3 | **the same** |
| Persisted conflict state | none (resolution events only) | **the same** |
| Results at any (mode, T, Q) | — | **identical** |
| A query at Q ≥ t3 while B is still unprocessed (A→C→B, midway) | — | **refused**: processing is incomplete at Q |
| A resolution at `decided_at` in [t2, t3) | must name `conflict_id`({A,B}) | **the same**; any other id is refused |

## 5. Executable regression invariants

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-011 | **Processing-order independence (case 1).** For the same fixed evidence and the same resolution events, every result at every (mode, T, Q) is identical whatever the processing order. That covers values, the conflict list with ids and effects, labels and pins. Processing writes no conflict state | Hypothesis over permutations of the processing order of a fixed receipt set (captures fixed); compare canonical JSON of every `View` at sampled (T, Q). Assert that processing writes nothing under `catalogue/resolutions/` or any conflict prefix |
| OBS-INV-013 | **Point-in-time stability.** Results at Q < `detected_at` are unchanged when a contradicting observation is captured. Results at Q < `decided_at` are unchanged when a resolution is appended. Results at Q ≥ `decided_at` apply it, to its own `conflict_id` only. A chain extension ends a resolution's effect only from the new member's `captured_at` | the §4(a) table as a fixture; a property that adding evidence or resolutions dated after Q leaves every result at Q byte-identical |
| OBS-INV-015 | **Deterministic derived identity.** The chain is a function of the evidence only. A member set always has the same `conflict_id`; `vintage_seq` never enters it | permutation property over derived chains and ids; the §4(b) fixture |
| OBS-INV-016 | **No silent concealment.** Every conflict in force at Q on the result's series and keys appears in the result with exactly one effect. The result's list equals `conflicts(series_id, Q)` restricted to its keys | computed both ways and compared (raise on disagreement); a fixture for each effect |
| OBS-INV-017 | **Acquisition-history semantics (case 2).** Stores with different capture histories may differ at intermediate Q. Each is stable over time. With the same evidence and no differing resolutions, their final conflict and their results are identical | the stores X and Y fixture from §2 |
| OBS-INV-018 | **Reproducibility.** Every result records `evidence_digest`, `resolution_digest` and `algorithm_revision`. Recomputing from the pinned receipts and events under that revision gives byte-identical output. A pin that does not verify (a missing or altered receipt or event, or an unknown revision) causes refusal | a round-trip test (compute, recompute from the pins, compare bytes); negative tests for each broken pin |
| OBS-INV-019 | **Completeness.** A query or resolution at Q is refused, with no partial output, unless the stored vintages with `captured_at ≤ Q` equal the capture-order derivation of E(Q) | a fixture that captures a receipt but leaves it unprocessed (the §4(b) midway state): refused. After processing: served |
| (append-only resolutions) | resolution events are only appended; none is edited or deleted; their storage key is a function of their content | store-level test: append, reopen, and compare the bytes of every existing event |
| (refusals) | a resolution is refused if it names anything but the `conflict_id` in force at its `decided_at`, if it names a member outside that conflict, if `decided_at < detected_at`, if it is backdated, if completeness at `decided_at` cannot be established, or if the actor is not the owner. The store is unchanged after a refusal | negative tests with snapshot equality |

**Acceptance tests for adoption (each must fail on the current code, or be new, and pass after):**

| Test | Covers |
|---|---|
| AT-Q2-1: Codex's counterexample in both processing orders: identical results, and the key absent while unresolved | F-REVIEW-2026-10-24-s1a-1-7, OBS-INV-011 |
| AT-Q2-2: the §4(a) table row by row, including C′ ending R's effect from v3's capture | OBS-INV-013, OBS-INV-015 |
| AT-Q2-3: permutation property over processing order: results and derived chains equal; no conflict state written | OBS-INV-011, OBS-INV-015 |
| AT-Q2-4: the §4(b) A, B, C fixture, including the refused midway query | OBS-INV-015, OBS-INV-019 |
| AT-Q2-5: the case-2 fixture (stores X and Y) | OBS-INV-017 |
| AT-Q2-6: diagnostics fixtures, one per effect, and the two-way comparison | OBS-INV-016 |
| AT-Q2-7: reproducibility round trip and broken-pin refusals | OBS-INV-018 |
| AT-Q2-8: resolution append-only behaviour and refusals, store unchanged | (append-only resolutions), (refusals) |
| AT-Q2-9: S1a releases byte-identical to the verified head, or every difference reported, with a check that the S1a fixtures contain no conflicts | releases standard; no silent change |

## 6. Options

| Option | Effect | Status |
|---|---|---|
| **A′ (selected by the owner, OD-0029)** | conflicts derived from fixed evidence at Q; only owner resolution events persisted; pinned, reproducible results; refusal when completeness cannot be established | this revision |
| A (revision 4) | the same, plus append-only conflict records and classified processing artefacts | not selected |
| A, revision 1 | quarantine both vintages at ingest | superseded |
| B | a deterministic content rule | meaningless economically; hides the problem |
| C | keep the last-ingested value | results depend on operational order |

## 7. Implementation outline if approved (not done; needs a separate owner authorisation)

- `select()`:
  - rank by (instant, strength) only;
  - derive slots and the conflict in force at Q from E(Q);
  - apply the resolution in force at Q;
  - attach every in-force conflict, its effect and the three pins to the `View`.
- A completeness check before every query and resolution, comparing the stored vintages with the
  capture-order derivation of E(Q). It may be cached by `evidence_digest`.
- An owner resolution API that validates the target against the chain at `decided_at`, writing
  content-keyed, append-only events in a journalled transaction.
- A `conflicts(series_id, Q)` diagnostics query.
- **The S1a synthetic fixtures** are expected to contain no conflicts; AT-Q2-9 confirms this.
  Financial outputs should then be byte-identical, and any difference is reported, not absorbed.

## 8. What this draft does not change

- the §3 basis order;
- the use of the stronger basis at equal instants;
- the revision and revert rules;
- the quarantine gate;
- the rule that only the owner or the gate may release from quarantine;
- late capture (Q-004).
