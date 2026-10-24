---
id: HIO-OPEN-DECISIONS
title: Open decisions queue (navigation only; grants no authority)
status: current   # harness-0.7 §6.3 (OD-0021)
owner: owner (decides); any agent may add an entry
last_reviewed: 2026-10-24
---

# Open decisions

> **Navigation only.** An entry is a pointer to a question, not a decision and not advice.
> Options and recommendations live in the linked source (a review record, an evidence package,
> a remediation response or a decision package). Decisions are made by the owner (with the
> solution architect where named) and recorded in an OD, whose id is then added here. Resolved
> G1 decisions stay in [`pending-owner-decisions.md`](pending-owner-decisions.md) as history.

| ID | Question | Source (holds the options) | Who decides | Blocks | Decided by |
|---|---|---|---|---|---|
| Q-001 | Does a later quality adjudication change an earlier point-in-time view? | F-REVIEW-2026-10-24-s1a-1-4 | owner + solution architect | S1a acceptance | — |
| Q-002 | How are contradictory same-time, same-strength values resolved? | F-REVIEW-2026-10-24-s1a-1-7 | owner + solution architect | S1a acceptance | — |
| Q-003 | Should `reconstructed(T)` prefer vintage evidence over a schedule-only placement? | S1a evidence package, interpretation 1; review item 1 | owner | research use of `reconstructed` | — |
| Q-004 | Should a late first capture remain market evidence (e.g. a `captured_late` basis)? | interpretation 3; review item 3 | owner | S1b design | — |
| Q-005a | Is **exploratory internal use** within HIO a consumer use that needs any owner event? | interpretation 7; review item 7 | owner | S1a consumer API semantics | — |
| Q-005b | How is **distribution-class approval** represented (one `approved_for_consumer(C)` per class; how several classes and per-class withdrawal coexist)? | F-REVIEW-2026-10-24-s1a-1-2; review item 7 | owner | consumer integration | — |
| Q-006 | Do `superseded` and `deprecated` releases fail closed for consumers? | review item 9 | owner | consumer integration | — |
| Q-007 | Ratify `pyyaml` (runtime) and `hatchling` (build backend)? | review item 10 | owner | S1a acceptance | — |
| Q-008 | Accept the S1a network control level (no CI egress firewall)? | review item 8 | owner | S1a acceptance | — |
| Q-009 | Adopt harness-0.7 at an exact revision? | [`harness-0.7-proposal.md`](harness-0.7-proposal.md) | owner | the next review round's mechanics | [OD-0021](owner/OD-0021-approve-harness-0.7.md) (rev 3 at `9b58811`) |
