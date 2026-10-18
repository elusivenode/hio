---
id: HIO-HARNESS-EXAMPLE
title: Harness worked example (end to end)
status: proposed
owner: HIO architecture lead (owner)
version: harness-0.2
last_reviewed: 2026-10-18
---

# Worked example: one factor, from task card to an approved release

**Illustrative only.** The ids, hashes and dates below are examples (`EXAMPLE-…`), not real
artefacts. The flow uses the real S1 factor spec `fx.usd_cash_vs_aud.excess`.

## 1. The owner authorises a task card

The owner commits `docs/decisions/owner/OD-EXAMPLE-12-authorise-s1.md`
(`kind: authorise_work`, `status: approved`, `applies_to: T-0005 @ <sha>`, `HIO-Actor: owner`).
T-0005 moves `proposed → authorised`, with `authorised_by: OD-EXAMPLE-12` and
`base_revision: <sha>`. A ChatGPT or Claude recommendation to start S1 would not have done
this. Only the OD record does.

The card links:
- HIO-ADR-0004, 0005, 0006, 0007, 0009 and 0010;
- the spec `fx.usd_cash_vs_aud.excess@0.1.0`;
- RA-INV-004…007 and RA-INV-016.

## 2. The implementation engineer bootstraps (fresh session)

Reads, in order (about 20k tokens):
1. `AGENTS.md`;
2. `STATUS.md`;
3. T-0005;
4. HIO-ADR-0010;
5. return standard §1, §4, §10 and §13;
6. the three cash and FX specs;
7. the latest handoff.

Records `start_revision`. Invokes skill `hio-return-accounting`.

## 3. The engineer works within scope

- Implements the RBA and NY Fed adapters, receipts, vintages, the cash-leg constructions and
  the FX excess construction.
- Writes tests FXC-INV-1/2/3 and OBS-INV-001…006.
- Runs capture on dev storage.
- Produces release `EXAMPLE-rel-9f3c…` with status `exploratory`. Its manifest shows
  `knowledge_mode: as_known_by_market` and `weakest_knowable_basis: documented_schedule`.
- Notices a conflict: the spec says "RBA fixing about 4pm Sydney", but the source page states
  a different time. Following AGENTS.md precedence, it does **not** edit the spec, which is the
  higher-precedence document. It records the conflict and opens a draft spec patch for owner
  review.

## 4. The engineer writes a handoff

`handoffs/2026-11-09-s1-fx-factor.md` (from the template) contains:
- revisions `a1b2…` → `c3d4…`;
- release `EXAMPLE-rel-9f3c…`;
- verified: all FXC/OBS invariants (`pytest -k "FXC or OBS"`, 42 passed); rebuild hash equal in
  CI run `EXAMPLE-run-77`;
- not verified: the H.10 triangulation (FRED terms pending, T-0002);
- the conflict above;
- next step: an independent review of T-0005 part 1.

## 5. The independent reviewer (Codex) reviews

Codex first fixes the target revision `c3d4…` and its test plan from T-0005 and the approved
specs. Only then does it read the handoff, treating it as claims.

- Gets a bundle: T-0005, the diff `a1b2..c3d4`, the specs, the manifest, CI logs.
- Reruns the tests and the rebuild.
- Writes `REVIEW-T-0005-1`, with verdict APPROVE WITH CONDITIONS. Finding F-1: "the quote
  inversion test covers only increasing q; add a decreasing case."

## 6. The engineer claims the fix; the reviewer verifies

- The engineer commits the F-1 fix (`HIO-Actor: claude/implementation`).
- It sets F-1's *Remediation claim* cell in `reviews/README.md` to the commit and test path.
  **F-1 is still open** (`remediation_claimed`).
- Codex reruns the new test on the fix commit. It appends to the review's verification log and
  sets F-1 to `verified_closed` (`HIO-Actor: codex/reviewer`).
- Had the test still failed, Codex would have returned F-1 to `open`.
- Had the owner chosen to accept the gap, it would be `waived` by an OD record. That is not a
  closure.

## 7. The owner accepts

- Through OD records:
  - accepts T-0005 (`submitted_for_review → accepted`);
  - sets the spec `status: validated` (from the review);
  - sets the release status `validated → approved_for_consumer(hio_internal)`.
- Possible only because T-0002 recorded `owner_verified` rights for RBA and NY Fed.
- `STATUS.md` is updated: "fx.usd_cash_vs_aud.excess v0.1.0 validated; release
  EXAMPLE-rel-9f3c…".

## 8. A later session needs this factor

It reads STATUS and finds the release id and spec version. It needs **no chat history**.
