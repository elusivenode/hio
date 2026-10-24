---
id: OBS-AMEND-Q002
title: "Draft amendment to the observations standard: contradictory same-time evidence is quarantined, not resolved by ingestion order (Q-002)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
owner: owner + solution architect (decide); drafted by claude/implementation-agent under OD-0023
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d)
source: F-REVIEW-2026-10-24-s1a-1-7; open-decisions Q-002
---

# Draft: contradictory same-time evidence (Q-002)

> **Draft only.** Nothing here is approved or implemented. The S1a code keeps its current
> tie-break (stronger basis, then later-recorded vintage) until the owner decides.

## The problem (F-REVIEW-2026-10-24-s1a-1-7)

§4 picks "the latest" qualifying vintage per key, but defines no tie-break when two vintages
have the same instant. Codex's counterexample:
- values 3.60 and 3.61 for one key, both with the same `publisher_timestamp`;
- ingested in opposite orders into two stores;
- `as_known_by_market` returned 3.61 in one store and 3.60 in the other.

Breaking the tie by the later-recorded vintage makes a point-in-time result depend on
operational order, not on evidence.

## Proposed text

**§4: add after the table.**

> **Ties.** Among a key's qualifying vintages, the mode's instant decides
> (`captured_at` for `as_captured_by_hio`, `knowable_at` otherwise). At equal instants the
> stronger `knowable_basis` (§3 order) decides. Two qualifying vintages with the same instant and
> the same basis strength but **different values** are an *evidence conflict*: the key is
> **absent** from that mode's result, and the conflict is reported with the result. Equal values
> are not a conflict (OBS-INV-001).

**§6: add a gate.** "**Evidence conflict:** when a new vintage would conflict with an existing
valid vintage of the same key, at the same `knowable_at` and the same basis strength, both are
quarantined, pending adjudication by the owner or the gate's rules (§6). The outcome is
independent of which vintage arrived first."

**§7: add an invariant.**

| ID | Invariant |
|---|---|
| OBS-INV-009 | every mode's result is independent of ingestion order; contradictory vintages with equal instant and basis strength never produce a value for the key until adjudicated |

## Options

| Option | Effect | Assessment |
|---|---|---|
| **A (recommended; Codex's recommendation)** | quarantine both at ingest, and report the key as absent with a conflict at query time | deterministic; nothing is invented; needs an owner adjudication path (with Q-001, adjudication takes effect at its own time) |
| B | a deterministic content rule (for example the lower value, or the smaller receipt hash) | order-independent, but the choice has no economic meaning and silently hides a data problem |
| C | keep the last-ingested value, documented | not recommended: point-in-time results depend on operational order |

## Implementation and tests if approved (not done)

**Implementation:**
- the ingest transaction checks each new vintage against existing vintages of the key at the
  same `knowable_at` and basis strength;
- on a conflict, both are quarantined in the same catalogue transaction (finding 6's atomic
  commit);
- `select()` reports conflicts.

**Tests:**
- Codex's counterexample with both receipt orders;
- an OBS-INV-009 Hypothesis property over receipt permutations (not over vintages already
  numbered, which was the gap Codex noted);
- equal values remain redundant.

## What this draft does not change

- the §3 basis order;
- the use of the stronger basis at equal instants;
- the revision and revert rules;
- the rule that only the owner or the gate may release from quarantine.
