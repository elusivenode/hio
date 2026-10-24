---
id: OBS-AMEND-Q001
title: "Draft amendment to the observations standard: quality eligibility is evaluated on HIO's decision clock, never retroactively (Q-001)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
revision: 3        # revision 1 at d1edf1e (OD-0023); revision 2 at baa8e4e (OD-0026); revision 3 under OD-0027 (admissibility and distinguishability)
owner: owner + solution architect (decide); drafted by claude/implementation-agent
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d in this repository, bd9eff0893ea in macsmsf history)
source: F-REVIEW-2026-10-24-s1a-1-4; open-decisions Q-001; solution-architecture advice recorded by OD-0026
companion: OBS-AMEND-Q002 (conflicts use the same decision clock)
---

# Draft: quality eligibility on HIO's decision clock (Q-001)

> **Draft only.** Nothing here is approved or implemented. The S1a code keeps its current
> behaviour (current quality in every mode) until the owner adopts an exact revision.

## 1. The problem (F-REVIEW-2026-10-24-s1a-1-4)

§2 gives every vintage a `quality_status`, and §4 says each mode uses "the latest `valid`
vintage", without saying *as of when* the vintage is valid.

Codex's counterexample:
1. a jump value captured on 15 January is quarantined, so it is absent from
   `as_captured_by_hio(15 Jan 12:00)`;
2. the owner releases it with an event dated 16 January;
3. the same 15 January query now includes it.

So a point-in-time result changes after the fact, and research gains hindsight that HIO did not
have.

## 2. Two questions, two clocks

A point-in-time result answers two separate questions:

| Question | Who knows | Clock |
|---|---|---|
| Was this value **publicly knowable** by T? | the market | `knowable_at` (§2, §3), compared with the **information cutoff T** |
| Did **HIO hold** this value, and judge it **eligible**, by Q? | HIO | `captured_at`, and the time of each HIO decision, compared with the **HIO decision cutoff Q** |

Rule: market knowability never implies HIO eligibility, and HIO eligibility never backdates
market knowability.

**The clocks used by this draft and OBS-AMEND-Q002:**

| Clock | On | Meaning | Rule |
|---|---|---|---|
| `valid_time` | vintage | what the value refers to (market-local) | unchanged (OBS-INV-005) |
| `knowable_at` | vintage | earliest public knowability (market claim, with its basis) | unchanged (§3) |
| `captured_at` | vintage | when HIO acquired the receipt; the start of HIO holding the vintage | unchanged |
| `decided_at` | quality event; conflict resolution (Q-002) | when HIO **made** the decision. This is HIO's own clock, not the market's | never earlier than the vintage's `captured_at`. Strictly increasing per vintage. **No backdating**: never earlier than the moment the event is recorded |
| `detected_at` | conflict event (Q-002) | when HIO first held both conflicting vintages, i.e. the later `captured_at` | derived; never chosen |
| `event_seq` | any event | storage order only | **never** decides a result |
| **T** | query | information cutoff: `captured_at` for `as_captured_by_hio`; `knowable_at` otherwise | as in §4 |
| **Q** | query | HIO decision cutoff: which vintages HIO held, and which quality and conflict decisions it had made | new; recorded on every result |

## 3. Proposed text

**§2, `quality_status` row: replace the rules cell with:**

> "Quality is a history, not a field. The ingest gate's verdict is the vintage's first quality
> decision, with `decided_at = captured_at`. Every later change is an append-only *quality event*
> (`status`, `actor`, `evidence`, `decided_at`), and `decided_at` must satisfy the rule in the
> clocks table. The vintage's status at Q is its latest decision with `decided_at ≤ Q`. Only
> `valid` at Q is eligible at Q."

**§4: add after the table.**

> **HIO decision cutoff Q.** Every mode evaluates eligibility at Q. A vintage is eligible at Q
> only if all of these hold:
> - `captured_at ≤ Q` (HIO held it);
> - its status at Q is `valid` (§2);
> - it is not suppressed by an unresolved conflict at Q (OBS-AMEND-Q002).
>
> A result is a function of (mode, T, Q) and of events dated `≤ Q` only. A decision made after
> Q never changes it. Q is set per mode:

| Mode | T (information) | Q (HIO decisions) | Label recorded with every result |
|---|---|---|---|
| Mode | T (information) | Q (HIO decisions) | Label recorded with every result |
|---|---|---|---|
| `as_captured_by_hio(T)` | `captured_at ≤ T` | **Q = T, fixed** (it cannot be overridden): "what HIO held and judged eligible at T" | `point_in_time`; `quality_as_of = T` |
| `as_known_by_market(T, Q)` | `knowable_at ≤ T` and a "yes" basis (§3) | **explicit and required**. Q may be later than T, because vintage evidence such as an archive is often acquired after T | `point_in_time` (market claim); `quality_as_of = Q`; and **`quality_after_cutoff`** whenever Q > T |
| `reconstructed(T, Q)` | `knowable_at ≤ T`, any basis | explicit and required | `reconstructed`; `quality_as_of = Q`; **`restated_quality`** whenever Q > T |
| `latest(Q)` | none | explicit and required | `descriptive`; `quality_as_of = Q`; **`restated_quality`** always |

> **Admissibility.** Every result also records `predictive_pit_admissible`:

| Mode | `predictive_pit_admissible` |
|---|---|
| `as_captured_by_hio(T)` | **true** (Q = T) |
| `as_known_by_market(T, Q)` | **true only if Q ≤ T**; **false** whenever Q > T |
| `reconstructed(T, Q)` | false, always |
| `latest(Q)` | false, always |

> **Q > T is never admissible by default.** A result with Q > T applies HIO decisions, or HIO's
> possession of evidence, dated after its information cutoff. Such a result:
> - is labelled (`quality_after_cutoff` or `restated_quality`), never silently;
> - has `predictive_pit_admissible = false`;
> - **must not** feed predictive work, TAA evaluation or any release labelled point-in-time. It
>   remains usable for descriptive work and for diagnostics.
>
> Any future exception, for example archive-backed market evidence, needs its own
> **evidence-based admissibility rule**. That rule is a separate owner-approved amendment, stating
> the evidence required and its invariants. It is not a parameter, and no consumer or agent can
> grant it.
>
> **Market knowability and later HIO validation stay distinguishable.** Every selected vintage in
> a result reports:
> - `knowable_at` and `knowable_basis` (the market claim);
> - `captured_at` (when HIO acquired it);
> - `eligibility_decided_at`: the `decided_at` of the quality decision in force at Q;
> - `validated_after_cutoff`: whether `eligibility_decided_at` is later than T.
>
> A reader can therefore see, per value, whether it was knowable by T and whether HIO had judged
> it eligible by T.

**§4: amend the sentence "Predictive work labelled point-in-time requires `as_captured_by_hio` or
`as_known_by_market`" to:** "Predictive work labelled point-in-time requires a result with
`predictive_pit_admissible = true` (above)."

**§4.1: replace the Case B table with:**

| Query | Result |
|---|---|
| `as_known_by_market(2021-01-01, Q = after the archive was ingested)` | **100**, labelled `quality_after_cutoff`; `predictive_pit_admissible = false` |
| `as_known_by_market(2025-07-01, Q = after the archive was ingested)` | **110**, labelled `quality_after_cutoff`; `predictive_pit_admissible = false` |
| `as_known_by_market(2021-01-01, Q = 2021-01-01)` | **absent**: HIO did not hold the archive at Q |

Case A is unchanged. `reconstructed` takes Q after the backfill and is never admissible.

**Consequence.** Archive-backed market evidence (Case B) remains available, labelled, for
descriptive work and diagnostics. It may support predictive point-in-time research only under a
future evidence-based admissibility rule (§4).

**§7: add invariants** OBS-INV-008, -009, -010, -012 and -014 (§5), and amend OBS-INV-007 to name
Q and admissibility.

## 4. Mode behaviour, worked example (Codex's counterexample, both directions)

Vintage v: captured 2026-01-15T09:00Z and quarantined by the gate. Event E1: released to
`valid`, `decided_at` 2026-01-16T10:00Z. Event E2: re-quarantined, `decided_at`
2026-01-20T10:00Z.

| Query | Result after E1 and E2 are recorded | Why |
|---|---|---|
| `as_captured_by_hio(2026-01-15T12:00Z)` | **absent**, the same as before E1 existed | E1 is dated after T = Q |
| `as_captured_by_hio(2026-01-17T00:00Z)` | **v** | E1 is in force at Q = T |
| `as_captured_by_hio(2026-01-21T00:00Z)` | **absent** | E2 is in force |
| `as_known_by_market(T = 2026-01-15T12:00Z, Q = 2026-01-15T12:00Z)` | absent | unchanged by E1 |
| `as_known_by_market(T = 2026-01-15T12:00Z, Q = 2026-01-17T00:00Z)` | **v**, labelled `quality_after_cutoff`; not admissible; v reports `eligibility_decided_at` 2026-01-16T10:00Z and `validated_after_cutoff = true` | later HIO judgement: labelled and distinguishable |
| `latest(Q = 2026-01-21T00:00Z)` | absent, labelled `restated_quality`; not admissible | E2 is in force |

**Why no-backdating is needed.** It is what makes "unchanged" hold for queries that were *run*
before an event existed. A decision recorded on 16 January cannot claim `decided_at` 15 January,
so a query at Q = 15 January gives the same answer whenever it is run.

## 5. Executable regression invariants

| ID | Invariant | Executable form |
|---|---|---|
| OBS-INV-008 | a result at (mode, T, Q) depends only on vintages with `captured_at ≤ Q` and on decisions with `decided_at ≤ Q` | Hypothesis: build a store from random receipts and quality events, and compute every mode at a random (T, Q). Then append random later receipts and events (all dated `> Q`) and recompute. The results must be byte-identical (canonical JSON of the `View`, labels included) |
| OBS-INV-009 | `as_captured_by_hio(T)` uses Q = T; a quality event with `decided_at > T` never changes it | the §4 table as a fixture test, in both directions, plus a Hypothesis property over event dates |
| OBS-INV-010 | every result records `knowledge_mode`, T, Q (`quality_as_of`), `weakest_knowable_basis`, `predictive_pit_admissible`, and the labels `quality_after_cutoff` and `restated_quality` exactly when §4 requires them. Every selected vintage reports `knowable_at`, `knowable_basis`, `captured_at`, `eligibility_decided_at` and `validated_after_cutoff` | a parametrised test over the four modes and over Q <, = and > T |
| OBS-INV-012 | a quality event is refused if `decided_at` is earlier than the vintage's `captured_at`, not later than the vintage's previous decision, or earlier than its recording time | negative tests; the store is unchanged after a refusal (snapshot equality, as for the rights gate) |
| OBS-INV-014 | `predictive_pit_admissible` is true only for `as_captured_by_hio`, and for `as_known_by_market` with Q ≤ T. No API parameter, label or caller can set it otherwise. A consumer or release path that requires point-in-time input refuses any result where it is false | a property over all modes and over (T, Q); a negative test that a release or model input requiring point-in-time refuses Q > T results |
| OBS-INV-007 (amended) | §4.1 Case A as before. Case B at Q after the archive ingestion gives 100 and 110, labelled and not admissible; at Q = 2021-01-01, absent | the existing fixture, with Q explicit |

**Acceptance tests for adoption (each must fail on the current code, or be new, and pass after):**

| Test | Covers |
|---|---|
| AT-Q1-1: Codex's counterexample in both directions (release, then re-quarantine); the §4 table row by row | F-REVIEW-2026-10-24-s1a-1-4, OBS-INV-009 |
| AT-Q1-2: append-later-events property over random stores | OBS-INV-008 |
| AT-Q1-3: labels, admissibility and per-vintage eligibility fields for every mode and for Q <, = and > T | OBS-INV-010, OBS-INV-014 |
| AT-Q1-4: backdated or out-of-order quality events refused, store unchanged | OBS-INV-012 |
| AT-Q1-5: amended §4.1 fixture | OBS-INV-007 |
| AT-Q1-6: S1a releases byte-identical to the verified head, or every difference reported | releases standard; no silent change |

## 6. Options (Option A is the advised choice)

| Option | Effect | Assessment |
|---|---|---|
| **A, refined (advised; revision 3)** | the decision clock Q on every mode; Q = T for `as_captured_by_hio`; explicit, labelled Q elsewhere; Q > T never admissible to predictive point-in-time work by default | no retroactive change to any (mode, T, Q) result; market knowability and HIO validation are kept apart and visible per value; keeps §4.1 Case B (with Q stated), for descriptive use |
| A, revision 1 | event-time quality for the two point-in-time modes, with no separate Q | superseded: it left open which HIO decisions `as_known_by_market` uses for evidence acquired after T |
| B | current quality everywhere, documented as restatement | point-in-time results change after adjudication |
| C | event-time quality with Q = T in every mode | breaks §4.1 Case B: an archive acquired after T could never support `as_known_by_market(T)` |

## 7. Implementation outline if adopted (not done; needs an owner authorisation)

- `VintageStore` keeps the full quality history per vintage. The current code keeps only the
  latest status in memory.
- `set_quality` validates `decided_at` (OBS-INV-012) against an injected recording clock.
- `select()` takes Q:
  - it filters vintages by `captured_at ≤ Q`;
  - it evaluates status at Q;
  - `vintage_seq` is removed from the rank (OBS-AMEND-Q002).
- `View` records Q, the labels, `predictive_pit_admissible` and the per-vintage eligibility
  fields. Releases record `quality_as_of` and admissibility in the manifest. Point-in-time
  consumers and release paths refuse inadmissible results (OBS-INV-014).
- **The S1a pipeline uses `as_captured_by_hio`,** so its releases take Q = cutoff automatically.
  Financial outputs should be byte-identical unless a fixture holds a quality event dated after
  the cutoff. The implementation must report any difference rather than absorb it.

## 8. What this draft does not change

- the vintage record and the §3 basis order;
- the quarantine gate's rules;
- the rule that only the owner or the gate may release from quarantine;
- OBS-INV-001…006.
