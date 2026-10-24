---
id: OBS-AMEND-Q002
title: "Draft amendment to the observations standard: equally evidenced contradictions are recorded as conflicts, never resolved by ingestion order (Q-002)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
revision: 3        # revision 1 at d1edf1e (OD-0023); revision 2 at baa8e4e (OD-0026); revision 3 under OD-0027 (identity, stability, diagnostics)
owner: owner + solution architect (decide); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d in this repository, bd9eff0893ea in macsmsf history)
source: F-REVIEW-2026-10-24-s1a-1-7; open-decisions Q-002; solution-architecture advice recorded by OD-0026; OD-0027
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

Neither element depends on ingestion order. `vintage_seq` is **never** part of a conflict's
identity, because it records arrival order.

**Conflict.** On one rank clock, a conflict is the set of **all** vintages of one
(`series_id`, `key`) that:
- share the same instant and the same basis strength;
- and between them hold **at least two different values**.

Equal values alone are not a conflict (OBS-INV-001).

**Conflict identity.** The conflict's id is computed from its contents:

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

- The same evidence gives the same `conflict_id` in any store and under any ingestion order.
- If a further contradicting observation joins the same slot (same clock, instant and
  strength), the member set changes, and so does the id. That is a new conflict.
- The earlier conflict stays recorded. Its resolution, if any, does not carry over to the new
  member set.

**A conflict is a fact about evidence, not about a query.** Whether it affects a query result
depends on the mode, T and Q (§3).

## 3. Proposed text

**§4: add after the table.**

> **No ingestion-order tie-break.** Among a key's eligible vintages, the mode's instant decides,
> then the stronger basis (§3). `vintage_seq`, `event_seq` and storage order never decide a
> result.
>
> **An unresolved conflict suppresses the key.** The key is **absent** from a mode's result if
> both hold:
> - the mode's top-ranked eligible vintages for the key form a conflict whose members HIO held
>   at Q (Q-001: `captured_at ≤ Q`);
> - no resolution of that exact `conflict_id` is in force at Q.
>
> A conflict is in force from its `detected_at`, the latest `captured_at` among its members.
> So a result at Q < `detected_at` is unchanged: HIO did not yet hold the contradiction.
>
> **Diagnostics never hide a contradiction.** Every result lists **every** conflict, resolved or
> unresolved at Q, that involves the result's series and keys and whose members HIO held at Q.
> Each listed conflict is marked with one of these effects:
> - `suppresses_key`: an unresolved conflict at the selected rank, so the key is absent;
> - `resolved`: a resolution in force at Q decided the key;
> - `outranked`: a higher-ranked vintage, at a later instant or with a stronger basis, decided
>   the key. The conflict is real, but it is not at the selected rank;
> - `not_eligible_in_mode`: its members are excluded by the mode, for example a `schedule_only`
>   conflict in `as_known_by_market`, or it lies on the other rank clock.
>
> The selected value therefore never stands alone while a contradiction about the same key
> exists. A diagnostics query, `conflicts(series_id, Q)`, lists all conflicts and their
> resolution state at Q, independent of any mode.

**§6: add a gate and an adjudication rule.**

> **Evidence conflict (recorded, not resolved).** When a vintage is recorded, the ingest
> transaction derives the conflicts it creates on each rank clock. It appends one *conflict event*
> per new `conflict_id`, in the same atomic catalogue transaction (F-REVIEW-2026-10-24-s1a-1-6).
> - The event holds the identity fields above, plus `detected_at`.
> - Its storage key is derived from the identity
>   (`catalogue/conflicts/<series_id>/<conflict_id>.json`), not from a sequence number. So the same
>   evidence produces the same event bytes in any ingestion order.
> - The vintages are **not** modified, deleted or quarantined: the original observations are
>   preserved.
>
> **Adjudication (S1a: the owner only).** A resolution is an append-only *resolution event*
> (`conflict_id`, `outcome`, `actor`, `evidence`, `decided_at`). Its outcome is one of:
> - `select({"receipt_id": …, "value": …})`: names a member by its evidence identity, never by
>   `vintage_seq`;
> - `reject_all`: the key stays unavailable at that rank, with a reason.
>
> Rules for resolution events:
> - only the owner may append one in S1a; an agent may propose one;
> - `decided_at ≥ detected_at`, and no backdating (OBS-AMEND-Q001);
> - a later resolution of the same `conflict_id` supersedes the earlier one from its own
>   `decided_at`. Nothing is edited or deleted;
> - a resolution applies only to its own `conflict_id`, and only for Q ≥ `decided_at`.
>
> **Historical stability.** Conflict and resolution events are immutable and keyed by content.
> A result at (mode, T, Q) depends only on vintages with `captured_at ≤ Q`, conflicts with
> `detected_at ≤ Q` and resolutions with `decided_at ≤ Q`. A later arrival or decision never
> changes it (OBS-INV-008, OBS-INV-013).

**§7: add invariants** OBS-INV-011, -013, -015 and -016 (§5).

## 4. Worked example (Codex's counterexample, extended)

The setup:
- v1 = 3.60 (receipt r1) and v2 = 3.61 (receipt r2), key K, both `publisher_timestamp` at
  `knowable_at` 2026-01-12T00:00Z;
- v1 captured 2026-01-12T01:00Z, v2 captured 2026-01-13T01:00Z;
- conflict C = id over {(r1, 3.60), (r2, 3.61)} on the knowability clock, `detected_at`
  2026-01-13T01:00Z;
- a resolution R of C, `select(r1, 3.60)`, `decided_at` 2026-01-14T09:00Z;
- later, v3 = 3.62 (receipt r3), the same `knowable_at` and basis, captured 2026-01-16T01:00Z.
  This creates conflict C′ = id over {r1, r2, r3}, `detected_at` 2026-01-16T01:00Z.

| Query (T = 2026-01-12T12:00Z unless shown) | Result | Conflicts listed |
|---|---|---|
| `as_known_by_market`, Q = 2026-01-12T12:00Z | **3.60** | none (v2 not yet held) |
| `as_known_by_market`, Q = 2026-01-13T12:00Z | **absent** | C: `suppresses_key` |
| `as_known_by_market`, Q = 2026-01-15T00:00Z | **3.60** | C: `resolved` (R) |
| `as_known_by_market`, Q = 2026-01-17T00:00Z | **absent** | C′: `suppresses_key`; C: `resolved`, historical |
| `as_captured_by_hio(2026-01-13T12:00Z)` | **3.61** | C: `not_eligible_in_mode` (the capture clock has no tie; the later capture wins) |
| any of the above, in either ingestion order | identical, including the conflict ids and event bytes | |

All the `as_known_by_market` rows with Q > T also carry `quality_after_cutoff` and
`predictive_pit_admissible = false` (OBS-AMEND-Q001).

## 5. Executable regression invariants

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-011 | for every mode and (T, Q), the result is independent of ingestion order. That covers the selected values, the conflict list with ids and effects, and the labels | Hypothesis over **permutations of receipts and their capture records**, not over pre-numbered vintages. One store per permutation; canonical JSON of every `View` identical. Codex's counterexample is the explicit two-order case |
| OBS-INV-013 | knowledge-state stability. Results at Q < `detected_at` are unchanged when a contradicting vintage arrives. Results at Q < `decided_at` are unchanged when a resolution is appended. Results at Q ≥ `decided_at` apply it, to its own `conflict_id` only | the §4 table as a fixture; a property that appending any event dated after Q leaves every result at Q byte-identical |
| OBS-INV-015 | conflict identity is deterministic and order-free. The same evidence gives the same `conflict_id` and the same conflict-event bytes and storage keys in any ingestion order. A change of member set gives a new id. `vintage_seq` never enters the identity | permutation property over the conflict event log (the set of keys and bytes); a fixture showing that C and C′ differ and that R does not apply to C′ |
| OBS-INV-016 | no silent concealment: every conflict with members held at Q, on the result's series and keys, appears in the result with exactly one effect. The result's conflict list equals `conflicts(series_id, Q)` restricted to its keys | computed both ways and compared (raise on disagreement); fixtures for each effect, including `outranked` and `not_eligible_in_mode` |
| (cross-check) | every conflict derived from the vintages at Q has a recorded conflict event with the same `conflict_id` and `detected_at ≤ Q`, and vice versa | computed both ways, from the vintages and from the event log; raise on disagreement |
| (refusals) | a resolution is refused if `decided_at < detected_at`, if it is backdated, if the actor is not the owner, if it has an unknown `conflict_id`, or if it names a member outside the conflict. The store is unchanged after a refusal | negative tests with snapshot equality |

**Acceptance tests for adoption (each must fail on the current code, or be new, and pass after):**

| Test | Covers |
|---|---|
| AT-Q2-1: Codex's counterexample in both orders: identical results and the key absent while unresolved | F-REVIEW-2026-10-24-s1a-1-7, OBS-INV-011 |
| AT-Q2-2: the §4 table row by row, including C′ superseding C's resolution | OBS-INV-013, OBS-INV-015 |
| AT-Q2-3: permutation property over results and the conflict event log | OBS-INV-011, OBS-INV-015 |
| AT-Q2-4: diagnostics fixtures, one per effect, and the two-way comparison | OBS-INV-016 |
| AT-Q2-5: refusals, store unchanged | (refusals) |
| AT-Q2-6: S1a releases byte-identical to the verified head, or every difference reported, with a check that the S1a fixtures contain no conflicts | releases standard; no silent change |

## 6. Options (Option A is the advised choice)

| Option | Effect | Assessment |
|---|---|---|
| **A, refined (advised; revision 3)** | content-addressed conflict and resolution events; the key is absent while unresolved, from `detected_at` on the decision clock; every contradiction listed with its effect; observations preserved | deterministic; order-independent; historically stable; nothing hidden; needs the owner's adjudication path |
| A, revision 1 | quarantine both vintages at ingest | superseded: it mutates vintage quality, and it conflated conflict with data quality |
| B | a deterministic content rule (lower value, smaller receipt hash) | order-independent, but meaningless economically, and it hides the problem |
| C | keep the last-ingested value | not recommended: results depend on operational order |

## 7. Implementation outline if adopted (not done; needs an owner authorisation)

- Ingest:
  - derive conflicts per rank clock against the vintages already held;
  - append content-keyed conflict events in the same journalled catalogue transaction
    (`StagedWrites`).
- An owner resolution API, with the validation above. It names members by evidence identity.
- `select()`:
  - rank by (instant, strength) only;
  - compute conflicts at Q, apply the resolutions in force at Q, and attach every relevant
    conflict and its effect to the `View`.
- A `conflicts(series_id, Q)` diagnostics query.
- **The S1a synthetic fixtures** are expected to contain no conflicts; AT-Q2-6 confirms this.
  Financial outputs should then be byte-identical, and any difference is reported, not absorbed.

## 8. What this draft does not change

- the §3 basis order;
- the use of the stronger basis at equal instants;
- the revision and revert rules;
- the quarantine gate;
- the rule that only the owner or the gate may release from quarantine.
