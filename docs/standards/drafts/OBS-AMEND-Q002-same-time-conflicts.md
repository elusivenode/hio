---
id: OBS-AMEND-Q002
title: "Draft amendment to the observations standard: equally evidenced contradictions are recorded as conflicts, never resolved by ingestion order (Q-002)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
revision: 2        # revision 1 at d1edf1e (OD-0023); revision 2 under OD-0026 (Option A, refined)
owner: owner + solution architect (decide); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d in this repository, bd9eff0893ea in macsmsf history)
source: F-REVIEW-2026-10-24-s1a-1-7; open-decisions Q-002; solution-architecture advice recorded by OD-0026
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

Each mode ranks a key's eligible vintages (eligible at Q, per OBS-AMEND-Q001) by:
- its **instant**: `captured_at` for `as_captured_by_hio`; `knowable_at` for the other three;
- then the §3 **basis strength**.

A **conflict** for a mode is two or more eligible vintages of one key that:
- share the mode's highest (instant, strength) rank;
- and have **different values**.

Equal values are not a conflict (OBS-INV-001). The same pair of vintages can conflict in one mode
and not another. For example, they may share a `knowable_at` but have different `captured_at`.

## 3. Proposed text

**§4: add after the table.**

> **No ingestion-order tie-break.** Among a key's eligible vintages, the mode's instant decides,
> then the stronger basis (§3). `vintage_seq`, `event_seq` and storage order never decide a
> result.
>
> If the top rank is shared by vintages with different values, the key is in **conflict**:
> - an **unresolved** conflict at Q makes the key **absent** from that mode's result;
> - the result lists the conflict (key, vintages, `detected_at`).
>
> A conflict is in force from its `detected_at` (the later `captured_at` of its vintages; see
> OBS-AMEND-Q001). So a result at Q < `detected_at` is unchanged: HIO did not yet hold both
> values. A later vintage of higher rank, by a later instant or a stronger basis, supersedes the
> conflict for that mode. The conflict record stays.

**§6: add a gate and an adjudication rule.**

> **Evidence conflict (recorded, not resolved).** When a vintage is recorded, the ingest
> transaction appends a *conflict event* for every mode in which it creates a conflict, in the
> same atomic catalogue transaction (F-REVIEW-2026-10-24-s1a-1-6). A conflict event holds
> `conflict_id`, `series_id`, `key`, `mode`, `instant`, `strength`, the vintages and
> `detected_at`.
> - The vintages are **not** modified, deleted or quarantined: the original observations are
>   preserved.
>
> **Adjudication.** A conflict is resolved by an append-only *resolution event*
> (`conflict_id`, `outcome`, `actor`, `evidence`, `decided_at`). The outcome is one of:
> - `select(vintage_seq)`, with evidence of why that value is right;
> - `reject_all`: the key stays unavailable for that rank, with a reason.
>
> Rules for resolution events:
> - only the owner may append one in S1a; an agent may propose one;
> - `decided_at ≥ detected_at`, and no backdating (OBS-AMEND-Q001);
> - a later resolution event for the same conflict supersedes the earlier one from its own
>   `decided_at`. Nothing is edited.
>
> A resolution applies to results with Q ≥ `decided_at` only.

**§7: add invariants** OBS-INV-011 and -013 (§5 below).

## 4. Mode behaviour, worked example (Codex's counterexample)

The setup:
- v1 = 3.60 and v2 = 3.61 for key K, both `publisher_timestamp` at `knowable_at` 2026-01-12T00:00Z;
- v1 captured 2026-01-12T01:00Z, v2 captured 2026-01-13T01:00Z, so `detected_at` =
  2026-01-13T01:00Z;
- a resolution R, `select(v1)`, `decided_at` 2026-01-14T09:00Z.

| Query | Result | Why |
|---|---|---|
| `as_known_by_market(T = 2026-01-12T12:00Z, Q = 2026-01-12T12:00Z)` | **3.60** | only v1 held at Q; unchanged by anything later |
| `as_known_by_market(T = 2026-01-12T12:00Z, Q = 2026-01-13T12:00Z)` | **absent**, conflict listed | both held, unresolved at Q |
| `as_known_by_market(T = 2026-01-12T12:00Z, Q = 2026-01-15T00:00Z)` | **3.60**, conflict listed as resolved by R | R in force at Q |
| `as_captured_by_hio(2026-01-13T12:00Z)` | **3.61** | different `captured_at`, so no conflict in this mode; the later capture wins |
| either ingestion order, any Q | identical rows | OBS-INV-011 |

## 5. Executable regression invariants

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-011 | for every mode and every (T, Q), the result, including its conflict list, is independent of ingestion order | Hypothesis over **permutations of receipts and their capture records**, not over pre-numbered vintages (the gap Codex noted). Build one store per permutation; canonical JSON of every `View` must be identical. Codex's counterexample is the explicit two-order case |
| OBS-INV-013 | an unresolved conflict at Q makes the key absent and listed. Results at Q < `detected_at` are unchanged when the second vintage arrives. Results at `detected_at ≤ Q < decided_at` are unchanged when a resolution is appended. Results at Q ≥ `decided_at` apply it | a fixture test over the §4 table; a property that appending a resolution changes only results with Q ≥ its `decided_at` |
| (cross-check) | every conflict found by `select()` at Q has a recorded conflict event with the same key, mode, vintages and `detected_at ≤ Q`, and vice versa | computed both ways, from the vintages and from the event log; raise on disagreement (the repository's "two figures that must agree" method) |
| (refusals) | a resolution with `decided_at < detected_at`, by a non-owner actor, or naming a vintage outside the conflict, is refused, and the store is unchanged | negative tests with snapshot equality |

## 6. Options (Option A is the advised choice)

| Option | Effect | Assessment |
|---|---|---|
| **A, refined (advised)** | conflict and resolution events; the key is absent while unresolved, from `detected_at` on the decision clock; the observations are preserved | deterministic; order-independent; no retroactive change; needs the owner's adjudication path |
| A, revision 1 | quarantine both vintages at ingest | superseded: it mutates vintage quality, and it conflated conflict with data quality |
| B | a deterministic content rule (lower value, smaller receipt hash) | order-independent, but meaningless economically, and it hides the problem |
| C | keep the last-ingested value | not recommended: results depend on operational order |

## 7. Implementation outline if adopted (not done; needs an owner authorisation)

- Ingest:
  - detect conflicts per mode against the vintages already held;
  - append conflict events in the same journalled catalogue transaction (`StagedWrites`).
- Owner resolution API, with the validation above.
- `select()`:
  - rank by (instant, strength) only;
  - compute conflicts at Q, apply the resolutions in force at Q, and report both on the `View`.
- **The S1a synthetic fixtures** are expected to hold no equal-instant contradictions; the
  implementation must confirm this. Financial outputs should then be byte-identical, and any
  difference is reported, not absorbed.

## 8. What this draft does not change

- the §3 basis order;
- the use of the stronger basis at equal instants;
- the revision and revert rules;
- the quarantine gate;
- the rule that only the owner or the gate may release from quarantine.
