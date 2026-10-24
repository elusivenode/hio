---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-9
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-7]
responds_to: VERIFY-2026-10-24-s1a-1-8   # commit db1722c35fe2136461b6b936a8d6d9d0044e656b, record sha256 6776d92b47225f5e408824a084ec1162a752bd64c1829e76fe4ee1532ae673d4 (checked; OD-0033)
previous_submission_head: 6720a6cbeac5aa45e51fa8bcd2433f8b9bbe2968
authorised_by: OD-0033   # within OD-0030/OD-0031/OD-0032
fix_commits: [7b267f5]
test_commits: [b6f98d1]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-9.md
created_at: 2026-10-24
---

# Remediation response 9: F7 round 4 (the completeness trust boundary)

> **Author's claim, not verification.** F7 stays **open** (and so does F4). The approved contract
> blobs are unchanged (Q-001 `419992f2`, Q-002 `d0a25b3b`). No structural change and no owner
> design decision was needed.

## The trust boundary, assessed as a whole

Completeness trusts what the store says about each receipt. Before this round:

| Stored artefact | Before | Now |
|---|---|---|
| Raw receipt bytes | verified, **except for quarantined receipts** | verified **first**, for every receipt (`ReceiptIntegrityError` otherwise) |
| Quarantine record | **trusted on sight** | re-derived with ingest's own validation (now one `_validate`). A receipt the rules quarantine needs exactly the derived record, and no outcome or vintage. A valid receipt must have **no** record |
| Processing outcome | re-derived (round 3) | the same, and refused beside a quarantine record |
| Vintages | must equal the derivation (round 3) | the same, plus **no held vintage without a verified capture event** in E(Q) (found in this assessment: a removed capture record left its vintage able to create or outrank conflicts) |
| Capture records | define E(Q) | still the boundary: removing one changes E(Q), and so the evidence pin, and orphaned vintages refuse. Under the single-writer contract nothing else indexes captures |
| Evidence pin | computed from markers and outcomes as found | computed only from **verified** dispositions, so it refuses exactly when a query would |

The principle now holds throughout: **every disposition is re-derived from verified bytes with the
rules that created it**. Markers, outcomes and vintages are claims to check, never proof.

## Evidence

| Check | Result |
|---|---|
| `tests/test_f7_round4.py`, run against `6720a6c` | 8 failed, 1 passed (exit 1): both Codex counterexamples and six related bypasses. The genuine-quarantine baseline passed |
| The same tests now | 9 passed. Every path refuses (query, captured view, `conflicts`, `evidence_digest`, `resolve_conflict`), on the store and after reopening, with the store unchanged. A genuine quarantine is still served, with stable pins across reopen and replay. The malformed-receipt tests are unchanged and pass |
| Whole suite | `pytest` 260 passed, exit 0. That includes F1–F6, the original F4/F7 cases and rounds 6–7, with unchanged test code |
| `ruff check`, `ruff format --check`, `tools/check_repo.py` | 0, 0, 0 |
| Financial output versus `6720a6c` (Codex's probe) | **fully identical** (`cmp` exit 0): `data.csv` and the release ids alike |
