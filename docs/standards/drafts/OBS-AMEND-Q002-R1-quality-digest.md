---
id: OBS-AMEND-Q002-R1
title: "Draft amendment to OBS-AMEND-Q002 revision 5: a quality_digest reproducibility pin for HIO quality decisions"
status: proposed   # draft for the owner; NOT approved; NOT implemented
revision: 1
owner: owner + solution architect (decide); drafted by claude/implementation-agent under OD-0034
last_reviewed: 2026-10-24
amends: docs/standards/drafts/OBS-AMEND-Q002-same-time-conflicts.md revision 5 (approved, OD-0030; blob d0a25b3b981474bbe57304829aaf5379b04c9e91), §3 "Reproducibility" and §5 OBS-INV-018
related: OBS-AMEND-Q001 revision 4 (approved, OD-0029; blob 419992f2f0be008dd505a69ed58fb463197ff33c), §2 and §3 (the quality decision history)
source: VERIFY-2026-10-24-s1a-1-9 (commit 63df7ff, record sha256 e3211b18...b600); OD-0034
---

# Draft: the `quality_digest` pin (Q-002 revision 5, amendment 1)

> **Draft only.** Nothing here is approved or implemented. It adds one pin. It changes **no**
> selection, quality, conflict or financial rule, and it does **not** change the meaning of
> `evidence_digest`, `resolution_digest` or `algorithm_revision`.

## 1. The gap (VERIFY-2026-10-24-s1a-1-9, reproduced independently under OD-0034)

Under Q-001 §3, a result depends on the HIO quality decisions in force at Q. The approved Q-002
pins cover:
- the captured receipts (`evidence_digest`);
- the conflict resolutions (`resolution_digest`);
- the rules (`algorithm_revision`).

None of them covers quality decisions. **The counterexample:** two valid stores hold one identical
receipt (`synthetic.rate`, 2026-01-12, 3.60). In store B the owner records `QUARANTINED` for that
vintage, `decided_at` 2026-01-14. Then `as_captured_by_hio(T = 2026-01-15)`:
- returns 3.60 in A and nothing in B;
- reports identical values for all three pins.

So OBS-INV-018's byte-identical reproduction from pins is not achievable: the pins do not identify
an input that the result depends on.

## 2. Proposed text (adds to Q-002 revision 5 §3, "Reproducibility")

> Every result records a fourth pin, **`quality_digest`**, alongside `evidence_digest`,
> `resolution_digest` and `algorithm_revision`. Their meanings are unchanged.
>
> **Events included.** Every append-only quality decision event (Q-001 §3) for a vintage of the
> result's series with `decided_at ≤ Q`. Nothing else is included:
> - the ingest gate's first verdict at `captured_at` is **not** an event: it is re-derived from the
>   verified receipt by the completeness check (OBS-INV-019);
> - resolution events are pinned by `resolution_digest`.
>
> **Fields per event, and only these:**
> - the decided vintage, identified by its evidence: `series_id`, `valid_time`, `receipt_id`,
>   `captured_at`;
> - the decision: `status`, `decided_at`, `actor`, `evidence`.
>
> **Excluded:**
> - `vintage_seq`, because the vintage is identified by evidence, never by arrival order;
> - `event_seq` and the storage key, which are storage order only;
> - `recorded_at`. It serves the no-backdating check (Q-001 OBS-INV-012) and does not affect the
>   result, so a faithful copy of the history gives the same pin.
>
> **Ordering and encoding.**
> - Events are sorted by (`series_id`, `valid_time`, `receipt_id`, `captured_at`, `decided_at`).
>   That order is total, because `decided_at` is strictly increasing per vintage (Q-001 §2).
> - The pin is the SHA-256 of the repository's canonical JSON encoding of:
>
>   ```
>   {"schema": "hio-quality-digest/1", "series_id": <series_id>, "events": [<event>, ...]}
>   ```
>
>   In that encoding, keys are sorted, instants are UTC with a `Z` suffix and microseconds, and
>   strings are UTF-8 without insignificant whitespace.
> - The schema tag versions the encoding. A change to the event fields or ordering needs a new tag
>   and a new `algorithm_revision`.
>
> **Empty history.** No event with `decided_at ≤ Q` gives `"events": []`, and the pin is the
> SHA-256 of that encoding: a fixed, non-empty value per series. The pin is never absent or the
> empty string.
>
> **Exclusion after Q.** An event with `decided_at > Q` is not included, so a later decision never
> changes the pin, or the result, at Q (OBS-INV-008). No-backdating (Q-001 OBS-INV-012) makes this
> stable over time: no event can be recorded later with `decided_at ≤` an earlier recording time.
>
> **Provenance.**
> - Every `View` records `quality_digest`.
> - Every release's input record for a view (in the manifest's existing `inputs` field) records it
>   beside the other pins. The manifest core field set is unchanged (releases standard §2).
> - Recomputing from the pinned receipts, resolution events and quality events, under the pinned
>   `algorithm_revision`, must reproduce the result byte for byte.
> - A recomputation, rebuild or reuse whose four pins do not all equal the recorded pins is
>   **refused** (a pin mismatch). It never silently replaces the recorded result.
>
> **Algorithm revision.** Adding this pin changes the content of every result, so implementing it
> moves `algorithm_revision` from `hio-obs-select/2` to `hio-obs-select/3`. The meaning of
> `algorithm_revision` is unchanged: it still identifies the derivation and selection rules,
> including what a result records.
>
> **Migration.** Release identities change, because each input record gains `quality_digest`.
> `data.csv` bytes do not change (no rule changes). A release built before the pin existed is not
> reinterpreted. Its rebuild under `hio-obs-select/3` is a new release, and the old one keeps its
> own recorded pins.

## 3. Invariants (adds to Q-002 revision 5 §5)

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-018 (amended) | the reproducibility pins are `evidence_digest`, `resolution_digest`, `quality_digest` and `algorithm_revision`. Recomputing from them is byte-identical, and a mismatch on any pin refuses | the round-trip test, extended to quality events |
| OBS-INV-020 | `quality_digest` is a function only of the quality events of the series with `decided_at ≤ Q`, through the fields and ordering above | the property and fixture tests below |

## 4. Acceptance tests (each must fail on the current code, or be new, and pass after)

| Test | Covers |
|---|---|
| AT-Q2R1-1: Codex's two valid stores (§1). The results differ, the `quality_digest`s differ, and the other three pins are equal | the gap; OBS-INV-018 |
| AT-Q2R1-2, fixed-cutoff stability: appending quality events with `decided_at > Q` (a release, a re-quarantine) leaves the result and all four pins at Q byte-identical, also after reopening | OBS-INV-020, OBS-INV-008 |
| AT-Q2R1-3, sensitivity: adding, removing or altering any field of an included event (`status`, `decided_at`, `actor`, `evidence`, or the vintage identity) changes `quality_digest`. Changing an excluded field (`recorded_at`, `event_seq`) does not | OBS-INV-020 |
| AT-Q2R1-4, independent reconstruction: a fresh store built from the same receipts plus a faithful copy of the quality events, recorded at different times, reproduces the result and all four pins byte for byte | OBS-INV-018 |
| AT-Q2R1-5, empty history: with no decisions, the pin equals the documented empty-history value for the series | the empty representation |
| AT-Q2R1-6, refusal on mismatch: the rebuild check reports a stored release whose quality history was later altered (`decided_at ≤ Q`) as differing, not reproduced. A reproduction asked to match recorded pins that differ is refused | OBS-INV-018 refusal |
| AT-Q2R1-7, release provenance: every S1a release input record carries `quality_digest`; `data.csv` is byte-identical to the current head; the release ids change only through the new field and `algorithm_revision` (verified by stripping those two and comparing) | migration; no silent change |

## 5. Options considered

| Option | Assessment |
|---|---|
| **A: separate `quality_digest` (selected by the owner, OD-0034)** | keeps owner decisions distinct from receipts and resolutions; one new field |
| B: fold quality events into `evidence_digest` | rejected by OD-0034: it would change the approved receipt-only meaning of `evidence_digest` |

## 6. What this draft does not change

- the selection, quality, conflict, admissibility and completeness rules;
- `evidence_digest`, `resolution_digest` and the meaning of `algorithm_revision`;
- the financial calculations;
- the approved Q-001 and Q-002 texts, which this draft amends by addition only.
