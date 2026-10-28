---
id: OD-0083
title: "Owner accepts the solution-architect slice-1 pilot as built (main at 8e867da) and instructs a draft of identity v0.2 weighting independent authentication of external data; v0.2 drafted and regression-tested; v0.2 not approved"
decision: accept_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-accept-sa-pilot.md (typed by the owner, verbatim)
  sha256: 895d5755b7aed4abcbbf6ab430e48ad1480755a4f7b7232ce61872221d7f2dc5
  date: 2026-10-28
  quote: "yes accept pilot, and draft identity v0.2"
applies_to:
  - path: docs/agents/solution-architect/ and the hiomux sa mode
    revision: 8e867da93cc5   # main at acceptance (identity v0.1, blob 1aa06a60964f); hiomux sha256 b5e341bb…
  - path: docs/agents/solution-architect/identity.md (v0.2 draft, branch proposal/sa-identity-v0.2)
    revision: 72c0eaf
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0081, OD-0082]}
---

# OD-0083: solution-architect pilot accepted; identity v0.2 drafted

## Owner actions (verbatim in the source file)

1. **The pilot is accepted** as built (OD-0082; `main` at `8e867da`; identity v0.1; hiomux sha256
   `b5e341bb…`).
   - The owner and Claude may use the architect for real questions, under OD-0081's rules: logged and summarised
     consultations, advice only, no influence on Codex, no MACSMSF.
   - Accepting the pilot approves no harness change and makes the architect no authority.
2. **Draft identity v0.2,** weighting independent authentication of external data more heavily. The prompt was
   the case-2 divergence (OD-0082).

## v0.2 (drafted, not approved)

A new section, "Independence of evidence", added on branch `proposal/sa-identity-v0.2` at `72c0eaf`:
- a check is only as independent as its inputs;
- a hash authenticates content only when the content is present;
- assignment scope is not a reason to close an unauthenticated material fact;
- recommend the smallest step that makes the evidence independent, and make closing the gap versus accepting
  the limit an owner decision;
- apply it proportionately.

`main` stays on v0.1 until the owner approves v0.2.

## Regression results for v0.2

Six runs, two per case, against v0.2 (identity blob `5592dbf2`), with packages, model and settings identical to
OD-0082.
- **Applied settings:** every run showed `gpt-6.1-sol`/`high`/`danger-full-access`, with no auto-loaded
  `AGENTS.md`.
- **Citations:** all exist in their packages; no OD after the cutoff is cited; nothing directs Codex.

| Case | v0.1 (OD-0082) | v0.2 |
|---|---|---|
| 1. harness-0.9 trade-off | adopt with changes (both runs) | the same disposition and item calls (both runs): **no regression**. 236 to 320 s |
| 2. offline F-5 verification | receive and close F-5, limit recorded (both runs) | **receive as evidence, but defer closing F-5 until the calendar facts have independent support** (both runs). Accepting the limit is offered as an owner alternative, not recommended. This is the owner's actual choice (OD-0077) |
| 3. citation mismatch | stop; the owner decides (both runs) | the same, adding an independent check that the cited revision holds OD-0077 as assigned. Proportionate, not overcautious |

**Caveats:**
- **Case 2 can no longer test this.** v0.2 was written because of case 2, so its improvement there shows the
  principle took effect; it does not show that the principle generalises. Evidence that it generalises needs a
  new held-out case about external data that the identity was not tuned on.
- **The race that was found.** Two parallel runs crashed when concurrent sessions wiped the shared memories
  database. hiomux now wipes only when no architect process is running, and tolerates missing files
  (sha256 below). The crashed runs were rerun; none is counted.

hiomux after the fix: sha256 `8ca77587a61ab4e8faf4f7a58e03350cba77d65607098a830ef9a065b0498436`.

## Corrections (append-only)

None.
