---
id: OBS-AMEND-Q001
title: "Draft amendment to the observations standard: quality adjudication is applied at its own time in point-in-time modes (Q-001)"
status: proposed   # draft for the owner and solution architect; NOT approved; NOT implemented
owner: owner + solution architect (decide); drafted by claude/implementation-agent under OD-0023
last_reviewed: 2026-10-24
amends: docs/standards/observations-and-point-in-time.md v0.2 (approved, OD-0008; blob 341cd608604d)
source: F-REVIEW-2026-10-24-s1a-1-4; open-decisions Q-001
---

# Draft: quality events take effect at their own time (Q-001)

> **Draft only.** Nothing here is approved or implemented. The S1a code keeps the current
> behaviour until the owner decides.

## The problem (F-REVIEW-2026-10-24-s1a-1-4)

§2 gives every vintage a `quality_status`, and §4 says each mode uses "the latest `valid`
vintage". It does not say *as of when* a vintage is valid. Codex's counterexample:
- a jump value captured on 15 January is quarantined, so it is absent from
  `as_captured_by_hio(15 Jan 12:00)`;
- the owner releases it with an event dated 16 January;
- the same 15 January query now includes it.

A point-in-time view therefore changes after the fact. Research that uses it gains hindsight
that HIO did not have on 15 January.

## Proposed text

**§2, `quality_status` row: add.** "A quality change is an append-only *quality event*
(`status`, `actor`, `evidence`, `at`). A vintage's status at instant T is its recorded status,
overridden by the latest quality event with `at ≤ T`."

**§4: add one paragraph after the table.**

> **Quality is evaluated at the cutoff.** `as_captured_by_hio(T)` and `as_known_by_market(T)`
> consider a vintage `valid` only if its status at T (§2) is `valid`. A quality event dated after
> T never changes their result. `reconstructed(T)` and `latest()` use the vintage's *current*
> status. That is a restatement: their results carry the label `restated_quality`, and may not be
> described as point-in-time evidence.

**§7: add an invariant.**

| ID | Invariant |
|---|---|
| OBS-INV-008 | for the point-in-time modes, the result at T is unchanged by any quality event with `at > T`; a release from quarantine dated D affects those modes only for cutoffs `T ≥ D` |

## Options

| Option | Effect | Assessment |
|---|---|---|
| **A (recommended; Codex's recommendation)** | event-time quality for the two point-in-time modes; current quality, labelled, for `reconstructed` and `latest` | no hindsight in point-in-time research; a corrected value remains available for descriptive work |
| B | current quality everywhere, documented as restatement | simplest, but point-in-time results change after adjudication, which defeats §4's claim |
| C | event-time quality in every mode | no restated view: an owner correction never reaches descriptive work at past cutoffs |

## Implementation and tests if approved (not done)

**Implementation:**
- `VintageStore` keeps every quality event, not only the latest;
- `select()` evaluates status at the cutoff for the two point-in-time modes;
- `View.label` reports `restated_quality` for the other two.

**Tests:**
- Codex's counterexample, in both directions (a release and a re-quarantine);
- OBS-INV-008 as a Hypothesis property over random quality events;
- OBS-INV-007 unchanged.

## What this draft does not change

- the vintage record;
- the knowable basis;
- the selection order;
- the quarantine gate;
- the rule that only the owner or the gate may release from quarantine.
