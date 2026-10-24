---
id: HIO-OPEN-DECISIONS
title: Open decisions queue (navigation only; grants no authority)
status: proposed   # part of harness-0.7 (proposed); becomes current only if the owner approves it
owner: owner (decides); any agent may add an entry
last_reviewed: 2026-10-24
---

# Open decisions

> **Navigation only.** An entry here is a question, not a decision. Decisions are made by the
> owner (with the solution architect where named) and recorded in an OD record, whose id is
> then added to the entry. Resolved G1 decisions stay in
> [`pending-owner-decisions.md`](pending-owner-decisions.md) as history.

| ID | Question | Source | Options (recommended first) | Who decides | Blocks | Decided by |
|---|---|---|---|---|---|---|
| Q-001 | Does a later quality adjudication (e.g. release from quarantine) change an earlier point-in-time view? | F-REVIEW-2026-10-24-s1a-1-4 | (a) **event-time quality for `as_captured_by_hio` and `as_known_by_market`: a quality event applies only to cutoffs at or after its `at`; a separately labelled restated view uses current quality** (Codex's recommendation; mine too); (b) current quality everywhere, documented as restatement; (c) event-time everywhere, with no restated view | owner + solution architect (observations standard §4, approved) | S1a acceptance | — |
| Q-002 | How are contradictory values with identical evidence time and strength resolved? | F-REVIEW-2026-10-24-s1a-1-7 | (a) **quarantine both until resolved; the key is absent meanwhile** (Codex's recommendation; mine too); (b) a deterministic content rule (e.g. order by value), which is stable but has no economic meaning; (c) keep last-ingested, documented (not recommended: results depend on operational order) | owner + solution architect | S1a acceptance | — |
| Q-003 | When a schedule-only vintage and a vintage-evidenced vintage of the same key conflict, does `reconstructed(T)` prefer the evidence? | S1a evidence package interpretation 1; review item 1 | (a) **prefer vintage-specific evidence wherever it covers the key; otherwise report a conflict** (standard revision); (b) keep §4 literal, labelled reconstruction | owner (observations standard §4) | not S1a acceptance; before any research use of `reconstructed` | — |
| Q-004 | Should a late first capture keep HIO's own observation as market evidence? | interpretation 3; review item 3 | (a) **a new basis `captured_late`, knowable no earlier than the capture** (standard revision); (b) keep `schedule_only` (current, conservative) | owner (observations standard §3) | S1b design | — |
| Q-005 | Is exploratory internal analysis a consumer use, and how are classes represented? | interpretation 7; review item 7; F-…-1-2 | (a) **exploratory use within HIO needs no approval event; every consumer class needs its own `approved_for_consumer(C)`** (the implementation fix for finding 2 assumes this; the owner may revise); (b) require approval even for `hio_internal` | owner (releases standard §5, §7) | consumer integration | — |
| Q-006 | Do `superseded` and `deprecated` releases fail closed for consumers? | interpretation 9; review item 9 | (a) **fail closed unless the owner names an exception and successor**; (b) rank with exploratory (current) | owner | consumer integration | — |
| Q-007 | Ratify the stack additions `pyyaml` (runtime) and `hatchling` (build backend)? | interpretation 10; review item 10 | (a) **ratify at S1a acceptance**; (b) replace | owner | S1a acceptance | — |
| Q-008 | Accept the S1a network control level (import rule + pytest socket block, no CI egress firewall)? | interpretation 8; review item 8 | (a) **accept for S1a; design egress control as part of S1b**; (b) require a CI egress control now | owner | S1a acceptance | — |
| Q-009 | Adopt harness-0.7? | [`harness-0.7-proposal.md`](harness-0.7-proposal.md) | approve, revise or reject the exact blob named there | owner | the next review round's mechanics | — |
