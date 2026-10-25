---
id: HIO-OPEN-DECISIONS
title: Open decisions queue (navigation only; grants no authority)
status: current   # harness-0.7 §6.3 (OD-0021)
owner: owner (decides); any agent may add an entry
last_reviewed: 2026-10-25
---

# Open decisions

> **Navigation only.** An entry is a pointer to a question, not a decision and not advice.
> Options and recommendations live in the linked source (a review record, an evidence package,
> a remediation response or a decision package). Decisions are made by the owner (with the
> solution architect where named) and recorded in an OD, whose id is then added here. Resolved
> G1 decisions stay in [`pending-owner-decisions.md`](pending-owner-decisions.md) as history.

**2026-10-25:** S1a is accepted (OD-0042). Every question that blocked S1a acceptance (Q-001,
Q-002, Q-007, Q-008) is decided. Still open: Q-003, Q-004, Q-005b, Q-006 and Q-010, none of which
OD-0042 resolves.

| ID | Question | Source (holds the options) | Who decides | Blocks | Decided by |
|---|---|---|---|---|---|
| Q-001 | Does a later quality adjudication change an earlier point-in-time view? | F-REVIEW-2026-10-24-s1a-1-4; draft [OBS-AMEND-Q001](../standards/drafts/OBS-AMEND-Q001-quality-event-time.md) | owner + solution architect | S1a acceptance | [OD-0029](owner/OD-0029-approve-q001-select-q002-a-prime.md) (revision 4, blob `419992f2`) |
| Q-002 | How are contradictory same-time, same-strength values resolved? | F-REVIEW-2026-10-24-s1a-1-7; draft [OBS-AMEND-Q002](../standards/drafts/OBS-AMEND-Q002-same-time-conflicts.md) | owner + solution architect | S1a acceptance | [OD-0030](owner/OD-0030-approve-q002-authorise-f4-f7.md) (revision 5, Option A′, blob `d0a25b3b`); amended by [OD-0035](owner/OD-0035-approve-q002-r1-verify-9-exception.md) (Q-002-R1, `quality_digest`, blob `cb7a937d`) |
| Q-003 | Should `reconstructed(T)` prefer vintage evidence over a schedule-only placement? | S1a evidence package, interpretation 1; review item 1 | owner | research use of `reconstructed` | — |
| Q-004 | Should a late first capture remain market evidence (e.g. a `captured_late` basis)? | interpretation 3; review item 3 | owner | S1b design | — |
| Q-005a | Is **exploratory internal use** within HIO a consumer use that needs any owner event? | interpretation 7; review item 7 | owner | S1a consumer API semantics | [OD-0038](owner/OD-0038-s1a-remaining-decisions.md) (confirmed: no individual owner event for exploratory internal research; `hio_internal` publication still needs `approved_for_consumer` and the rights checks) |
| Q-005b | How is **distribution-class approval** represented (one `approved_for_consumer(C)` per class; how several classes and per-class withdrawal coexist)? | F-REVIEW-2026-10-24-s1a-1-2; review item 7 | owner | consumer integration | — |
| Q-006 | Do `superseded` and `deprecated` releases fail closed for consumers? | review item 9 | owner | consumer integration | — |
| Q-007 | Ratify `pyyaml` (runtime) and `hatchling` (build backend)? | review item 10 | owner | S1a acceptance | [OD-0038](owner/OD-0038-s1a-remaining-decisions.md) (ratified as used at `084154c`: `pyyaml` 6.0.3 locked; `hatchling>=1.25`) |
| Q-008 | Accept the S1a network control level (no CI egress firewall)? | review item 8 | owner | S1a acceptance | [OD-0038](owner/OD-0038-s1a-remaining-decisions.md) (accepted for **S1a only**, as a known limitation; a separate network and credential-control decision is required before S1b is authorised) |
| Q-009 | Adopt harness-0.7 at an exact revision? | [`harness-0.7-proposal.md`](harness-0.7-proposal.md) | owner | the next review round's mechanics | [OD-0021](owner/OD-0021-approve-harness-0.7.md) (rev 3 at `9b58811`) |
| Q-010 | How is an archive receipt that carries a key's revision history placed on the capture clock? (Today its same-instant, equal-strength vintages are a capture-clock conflict, so `as_captured_by_hio` suppresses the key: fail closed) | [response 6](../../reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-6.md); [S1a readiness](../evidence/S1A-acceptance-readiness.md) §5 | owner | S1b design | deferred to S1b design by [OD-0038](owner/OD-0038-s1a-remaining-decisions.md); current behaviour unchanged |
| Q-011 | How is the cross-lineage T-0004 review (`macsmsf` `review/t0004-codex` @ `db305a3`, READY) received into `elusivenode/hio`, given that a `--no-ff` merge would import private `macsmsf` history? | [OD-0039](owner/OD-0039-s1a16-run1-assessment.md); [HARNESS-2026-10-25-s1a16-1](../../reviews/records/HARNESS-2026-10-25-s1a16-1.md); OD-0018 | owner | the S1-A16 Codex retest baseline | [OD-0040](owner/OD-0040-t0004-cross-lineage-receipt.md) (byte-identical cross-lineage copy; received from `macsmsf@db305a3`) |
| Q-013 | For an HIO-captured vintage whose publication instant is not evidenced, may `captured_on_schedule` carry `knowable_at` = the capture instant, as accepted S1a code already does for a revised value (`knowability.py:51-52`), as an **opt-in S1b behaviour** that leaves every S1a release unchanged? Or is `schedule_only` (no `as_known_by_market` claim) the rule? The approved observations standard §3 defines `captured_on_schedule` by the documented release time and does not state the capture-instant reading | [HIO-ADR-0012](HIO-ADR-0012-staged-s1b.md) §4.3.1; [REVIEW-2026-10-25-adr0012](../../reviews/records/REVIEW-2026-10-25-adr0012.md) F1; [response 1](../../reviews/responses/RESPONSE-REVIEW-2026-10-25-adr0012-1.md) | owner + solution architect | the S1b-1 gate (ADR-0012 §4.2 (d3)); the ADR stands without it, falling back to `schedule_only` | — |
