---
id: OBS-AMEND-Q002
title: "Draft amendment to the observations standard: equally evidenced contradictions are recorded as conflicts, never resolved by ingestion order (Q-002)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
revision: 4        # revision 1 at d1edf1e (OD-0023); revision 2 at baa8e4e (OD-0026); revision 3 at 6f013a7 (OD-0027); revision 4 under OD-0028 (processing order vs acquisition history)
owner: owner + solution architect (decide); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d in this repository, bd9eff0893ea in macsmsf history)
source: F-REVIEW-2026-10-24-s1a-1-7; open-decisions Q-002; solution-architecture advice recorded by OD-0026; OD-0027; OD-0028
companion: OBS-AMEND-Q001 (defines the clocks, including the HIO decision cutoff Q)
---

# Draft: equally evidenced contradictions (Q-002)

> **Draft only.** Nothing here is approved or implemented. The S1a code keeps its current
> tie-break (stronger basis, then the later-recorded vintage) until the owner adopts an exact
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

**Observation evidence identity.** An observation's identity for conflicts is
`(receipt_id, value)`:
- `receipt_id` is the SHA-256 of the receipt bytes (§1);
- `value` is the canonical decimal string, normalised so that `3.6` and `3.60` are the same
  value.

`vintage_seq` is **never** part of a conflict's identity, because it records arrival order.

**Slot.** A slot is one (`series_id`, `key`, rank clock, instant, basis strength). Its *members*
are all vintages in that slot.

**Fixed capture-time evidence.** A receipt's `captured_at` is fixed when it is captured. The
capture record is written in the capture transaction, and capture times are strictly increasing
per source.

*Processing* means deriving vintages and conflicts from receipts, and it may run in a different
order from capture. It happens that way in a rebuild or replay, or when a crash falls between a
capture and its ingest. **HIO's knowledge at Q is defined by the evidence with
`captured_at ≤ Q`, never by the order in which that evidence was processed.**

**Conflict, and the canonical conflict chain.**
- The **conflict in force at Q** for a slot is the set of its members with `captured_at ≤ Q`,
  provided that set holds at least two different values. Equal values alone are not a conflict
  (OBS-INV-001).
- As Q advances, the set grows only when a member's `captured_at` is reached. Members with the
  same `captured_at` join together.
- The sequence of distinct member sets is the slot's **canonical conflict chain**. It is a pure
  function of the fixed evidence: the same in every processing order.

**Conflict identity.** A member set's id is computed from its contents:

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

- The same member set always has the same `conflict_id`, in any store and processing order.
- A conflict's `detected_at` is the latest `captured_at` among its members, so it is also derived
  from the evidence.

**Three distinctions** (A, B and C contradict each other in one slot):

| Case | Example | What is guaranteed |
|---|---|---|
| 1. The same fixed evidence, processed in different orders | captures A at t1, B at t2, C at t3 with t1 < t2 < t3, processed A→B→C or A→C→B | **Identical** results at every (mode, T, Q). **Identical** canonical chain: {A,B} from t2, then {A,B,C} from t3. **Identical** set of canonical conflict records. The processing log may differ (see "artefact" below), and that is **not** asserted equal |
| 2. Genuinely different acquisition histories | store X captures B at t2 and C at t3; store Y captures C at t2 and B at t3 | different evidence, so a **different** chain: X has {A,B} then {A,B,C}; Y has {A,C} then {A,B,C}. Results at Q in [t2, t3) may legitimately differ. Each store's results are stable over time. Once both hold A, B and C, the **final** conflict (`conflict_id` over {A,B,C}) and the results at Q ≥ t3 are identical, unless a resolution decided earlier differs (an owner action, case 3) |
| 3. The final conflict state versus the historical event history | — | the **final** state at Q (the conflict in force, its id, the resolution in force, the result) is a function of the evidence and of resolutions dated ≤ Q. The **history** (which member sets existed when, and which resolutions were made) is a function of the acquisition history. Byte equality of the *processing* log is not a meaningful guarantee, and is not required |

## 3. Proposed text

**§4: add after the table.**

> **No ingestion-order tie-break.** Among a key's eligible vintages, the mode's instant decides,
> then the stronger basis (§3). `vintage_seq`, `event_seq`, processing order and storage order
> never decide a result.
>
> **An unresolved conflict suppresses the key.** The key is **absent** from a mode's result if
> both hold:
> - the mode's top-ranked eligible slot for the key has a conflict in force at Q (§2: members
>   with `captured_at ≤ Q`);
> - no resolution of that exact `conflict_id` is in force at Q.
>
> A result at Q < `detected_at` is unchanged: HIO did not yet hold the contradiction.
>
> **Diagnostics never hide a contradiction.** Every result lists **every** conflict in force at Q
> that involves the result's series and keys. Each listed conflict is marked with one of these
> effects:
> - `suppresses_key`: an unresolved conflict at the selected rank, so the key is absent;
> - `resolved`: a resolution in force at Q decided the key;
> - `outranked`: a higher-ranked vintage, at a later instant or with a stronger basis, decided
>   the key. The conflict is real, but it is not at the selected rank;
> - `not_eligible_in_mode`: its members are excluded by the mode (for example a `schedule_only`
>   conflict in `as_known_by_market`), or it lies on the other rank clock.
>
> The diagnostics query `conflicts(series_id, Q)` lists, per slot:
> - the canonical chain up to Q;
> - the conflict in force and its resolution state;
> - any processing artefacts (§6).

**§6: add a gate and an adjudication rule.**

> **Conflict records (append-only provenance).** Each processing step derives the canonical chain
> of every slot it touches, from all the evidence held so far. It appends a *conflict record* for
> each chain element that has no record yet, in the same atomic catalogue transaction
> (F-REVIEW-2026-10-24-s1a-1-6).
> - A record holds the identity fields and `detected_at`. Its storage key is
>   `catalogue/conflicts/<series_id>/<conflict_id>.json`.
> - Equal member sets give equal bytes, in any processing order.
> - The vintages are **not** modified, deleted or quarantined.
>
> **Processing artefacts.** When processing runs out of capture order, a step may record a member
> set that the full evidence shows never existed at any Q. Example: C (t3) is processed before
> B (t2), so a record for {A,C} is written. Such a record:
> - stays: the log is append-only;
> - is classified on read as a **processing artefact**, because its member set is not an element
>   of the slot's canonical chain under the evidence now held;
> - is listed in diagnostics;
> - is **never** used by a result or a resolution.
>
> In capture-order processing (the S1a pipeline ingests each receipt immediately after capturing
> it), no artefacts arise.
>
> **Adjudication (S1a: the owner only).** A resolution is an append-only *resolution event*
> (`conflict_id`, `outcome`, `actor`, `evidence`, `decided_at`). Its outcome is one of:
> - `select({"receipt_id": …, "value": …})`: names a member by its evidence identity, never by
>   `vintage_seq`;
> - `reject_all`: the key stays unavailable at that rank, with a reason.
>
> Rules for resolution events:
> - only the owner may append one in S1a; an agent may propose one;
> - it must target **the conflict in force at its `decided_at`**, so a processing artefact or any
>   other chain element is refused;
> - `decided_at ≥ detected_at`, and no backdating (OBS-AMEND-Q001);
> - a later resolution of the same `conflict_id` supersedes the earlier one from its own
>   `decided_at`;
> - a resolution applies only to its own `conflict_id`, and only for Q ≥ `decided_at`. When the
>   chain grows (a new member arrives), the earlier resolution stays in the history but does not
>   decide the new conflict.
>
> **Processing completeness.** Results and resolutions at Q are valid only once all evidence with
> `captured_at ≤ Q` has been processed. The S1a pipeline ingests each receipt in capture order,
> immediately after capture. A rebuild finishes processing before it serves queries or accepts
> resolutions.
>
> Evidence first recorded later than its `captured_at`, a *late capture*, is outside this
> amendment (open decision Q-004).
>
> **Point-in-time stability.** A result at (mode, T, Q) depends only on:
> - vintages with `captured_at ≤ Q`;
> - the canonical chain derived from them;
> - resolutions with `decided_at ≤ Q`.
>
> Processing order and later records never change it (OBS-INV-008, OBS-INV-013).

**§7: add invariants** OBS-INV-011, -013, -015, -016 and -017 (§5).

## 4. Worked examples

**(a) Codex's counterexample, extended.** The setup:
- v1 = 3.60 (receipt r1) and v2 = 3.61 (receipt r2), key K, both `publisher_timestamp` at
  `knowable_at` 2026-01-12T00:00Z;
- v1 captured 2026-01-12T01:00Z and v2 captured 2026-01-13T01:00Z, so the chain element
  C = {r1, r2} has `detected_at` 2026-01-13T01:00Z;
- resolution R of C, `select(r1, 3.60)`, `decided_at` 2026-01-14T09:00Z;
- v3 = 3.62 (receipt r3), the same slot, captured 2026-01-16T01:00Z, so the next chain element is
  C′ = {r1, r2, r3}.

| Query (T = 2026-01-12T12:00Z) | Result | Conflicts listed |
|---|---|---|
| `as_known_by_market`, Q = 2026-01-12T12:00Z | **3.60** | none |
| `as_known_by_market`, Q = 2026-01-13T12:00Z | **absent** | C: `suppresses_key` |
| `as_known_by_market`, Q = 2026-01-15T00:00Z | **3.60** | C: `resolved` (R) |
| `as_known_by_market`, Q = 2026-01-17T00:00Z | **absent** | C′: `suppresses_key` (C and R remain in the chain history) |
| `as_captured_by_hio(2026-01-13T12:00Z)` | **3.61** | C: `not_eligible_in_mode` (the capture clock has no tie) |

The `as_known_by_market` rows with Q > T also carry `quality_after_cutoff` and
`predictive_pit_admissible = false` (OBS-AMEND-Q001).

**(b) The owner's A, B, C case.** A, B and C share a slot, captured at t1 < t2 < t3.

| | Processed A→B→C | Processed A→C→B (a replay out of capture order) |
|---|---|---|
| Records written | {A,B}, then {A,B,C} | {A,C} (when C is processed), then {A,B} and {A,B,C} (when B is processed) |
| Canonical chain (derived) | {A,B} from t2; {A,B,C} from t3 | **the same** |
| Artefacts | none | {A,C}: listed in diagnostics, never used |
| Results at any (mode, T, Q) | — | **identical** |
| A resolution at `decided_at` in [t2, t3) | must target {A,B} | **the same**; targeting {A,C} is refused |

## 5. Executable regression invariants

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-011 | **Processing-order independence (case 1).** For the same fixed evidence (receipts with fixed `captured_at`) and the same resolutions, every result at every (mode, T, Q) is identical whatever the processing order. That covers selected values, the conflict list with ids and effects, and labels. So is the canonical chain, and so is the set of canonical conflict records (keys and bytes). The full processing log, including artefacts, is **not** required to be identical | Hypothesis over **permutations of the processing order of a fixed set of receipts** (captures fixed). Compare canonical JSON of every `View` at sampled (T, Q), the derived chains, and the set of canonical records |
| OBS-INV-013 | **Point-in-time stability.** Results at Q < `detected_at` are unchanged when a contradicting vintage is captured. Results at Q < `decided_at` are unchanged when a resolution is appended. Results at Q ≥ `decided_at` apply it, to its own `conflict_id` only. A chain extension (a new member) supersedes the resolution only for Q at or after the new member's `captured_at` | the §4(a) table as a fixture; a property that adding any evidence or event dated after Q leaves every result at Q byte-identical |
| OBS-INV-015 | **Deterministic identity and canonical classification.** A member set always has the same `conflict_id`, and `vintage_seq` never enters it. The canonical chain is a function of the evidence only. Every chain element has a record once processing is complete. Every record that is not a chain element is classified as an artefact, and no result or resolution uses one | permutation property over chains and records; the §4(b) fixture asserting the {A,C} artefact, its classification and its exclusion |
| OBS-INV-016 | **No silent concealment.** Every conflict in force at Q on the result's series and keys appears in the result with exactly one effect. The result's conflict list equals `conflicts(series_id, Q)` restricted to its keys and to the in-force element | computed both ways and compared (raise on disagreement); a fixture for each effect |
| OBS-INV-017 | **Acquisition-history semantics (case 2).** Two stores with genuinely different capture histories may differ at intermediate Q. Each store's results are stable over time (OBS-INV-013). Once both hold the same evidence with no differing resolutions, their final conflict (`conflict_id`, members, `detected_at`) and their results at that Q are identical | a fixture with stores X and Y from §2 (B and C captured in opposite orders): they differ at Q in [t2, t3) and are equal at Q ≥ t3 |
| (cross-check) | every chain element at Q has a record with the same `conflict_id` and `detected_at`, once processing is complete. Records that are not chain elements are exactly the artefacts | computed both ways, from the evidence and from the records; raise on disagreement |
| (refusals) | a resolution is refused if it targets anything but the conflict in force at its `decided_at` (an artefact, an earlier or later chain element, or an unknown id), if it names a member outside that conflict, if `decided_at < detected_at`, if it is backdated, or if the actor is not the owner. The store is unchanged after a refusal | negative tests with snapshot equality |

**Acceptance tests for adoption (each must fail on the current code, or be new, and pass after):**

| Test | Covers |
|---|---|
| AT-Q2-1: Codex's counterexample in both processing orders: identical results, and the key absent while unresolved | F-REVIEW-2026-10-24-s1a-1-7, OBS-INV-011 |
| AT-Q2-2: the §4(a) table row by row, including C′ ending R's effect from v3's capture | OBS-INV-013, OBS-INV-015 |
| AT-Q2-3: permutation property over processing order: results, chains and canonical records equal; artefacts allowed and classified | OBS-INV-011, OBS-INV-015 |
| AT-Q2-4: the §4(b) A, B, C fixture in both processing orders | OBS-INV-011, OBS-INV-015 |
| AT-Q2-5: the case-2 fixture (stores X and Y) | OBS-INV-017 |
| AT-Q2-6: diagnostics fixtures, one per effect, plus artefact listing and the two-way comparison | OBS-INV-016 |
| AT-Q2-7: refusals, store unchanged | (refusals) |
| AT-Q2-8: S1a releases byte-identical to the verified head, or every difference reported, with a check that the S1a fixtures contain no conflicts | releases standard; no silent change |

## 6. Options

| Option | Effect | Assessment |
|---|---|---|
| **A, refined (advised; revision 4)** | conflicts derived from fixed evidence (the canonical chain); append-only conflict records kept as provenance, with artefacts classified; resolutions bound to the conflict in force at `decided_at` | meets every stated guarantee without asserting an equal processing log; no change to the event types of revision 3 |
| A′, narrowest alternative (no conflict records) | conflicts are derived on read; only resolution events are stored. Detection times are derivable from `captured_at` | the stored log becomes identical across processing orders, and nothing economic is lost. But it drops the conflict records OD-0027 asked to preserve, so it changes the event representation |
| A, revision 1 | quarantine both vintages at ingest | superseded: it mutates vintage quality |
| B | a deterministic content rule (lower value, smaller receipt hash) | meaningless economically; hides the problem |
| C | keep the last-ingested value | results depend on operational order |

## 7. Implementation outline if adopted (not done; needs an owner authorisation)

- Ingest:
  - derive the canonical chain of each touched slot from all held evidence;
  - append missing chain records in the same journalled catalogue transaction.
- An owner resolution API that validates the target against the chain at `decided_at`.
- `select()`:
  - rank by (instant, strength) only;
  - take the conflict in force at Q from the chain, apply the resolution in force at Q, and
    attach every in-force conflict and its effect to the `View`.
- A `conflicts(series_id, Q)` diagnostics query, including artefact classification.
- **The S1a synthetic fixtures** are expected to contain no conflicts; AT-Q2-8 confirms this.
  Financial outputs should then be byte-identical, and any difference is reported, not absorbed.

## 8. What this draft does not change

- the §3 basis order;
- the use of the stronger basis at equal instants;
- the revision and revert rules;
- the quarantine gate;
- the rule that only the owner or the gate may release from quarantine;
- late capture (Q-004), which stays a separate open decision.
