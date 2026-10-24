---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-6
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]
responds_to: REVIEW-2026-10-24-s1a-1   # findings 4 and 7, received at e55cc89 (OD-0022)
contracts: [OBS-AMEND-Q001 revision 4 (OD-0029; blob 419992f2f0be008dd505a69ed58fb463197ff33c), OBS-AMEND-Q002 revision 5 (OD-0030; blob d0a25b3b981474bbe57304829aaf5379b04c9e91)]
previous_head: b4c398df4dcba983bce043b0f92a083082527efa
authorised_by: OD-0030
fix_commits: [e3efc9f, eb7e92c]
test_commits: [92cef1c]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-6.md
created_at: 2026-10-24
---

# Remediation response 6: findings 4 and 7 (F4/F7)

> **Author's claim, not verification.** Both findings stay **open** until a verification record
> closes them. Responses 1–5 are unchanged.
>
> - Implemented to the approved amendments.
> - The observations standard v0.3 consolidation is a separate **candidate**
>   (`docs/standards/drafts/observations-and-point-in-time-v0.3-candidate.md`), not approved.

## Codex's counterexamples (mandatory regressions)

| Finding | Counterexample (REVIEW-2026-10-24-s1a-1) | At `b4c398d` (old API) | Now |
|---|---|---|---|
| F4 | a jump captured 15 Jan, released by an event dated 16 Jan: the same 15 Jan `as_captured_by_hio` query changed | reproduced: excluded before the release, **included after** | AT-Q1-1: the 15 Jan view is byte-identical before and after release and re-quarantine |
| F7 | 3.60 and 3.61 with identical `publisher_timestamp`, ingested in opposite orders: 3.61 versus 3.60 | reproduced: **3.61 in one order, 3.60 in the other** | AT-Q2-1: identical results; the key is absent with a `suppresses_key` conflict until an owner resolution |

## What was implemented

**Two cutoffs (Q-001)**, in `src/hio/marketdata/queries.py`:
- Q = T is fixed for `as_captured_by_hio`, and explicit for the other modes.
- Quality is the decision in force at Q.
- The labels are `quality_after_cutoff`, `restated_quality` and `descriptive`.
- `predictive_pit_admissible` is computed, with no override, and enforced by
  `require_predictive_pit()`.
- Each selected key reports `eligibility_decided_at` and `validated_after_cutoff`.

**Decision clock (Q-001)**, in `src/hio/marketdata/vintages.py` (`set_quality`):
- no backdating, measured against an injected recording clock;
- decisions are strictly increasing, and never at or before the capture;
- a store holding legacy events without `decided_at` refuses to load.

**Derived conflicts (Q-002):**
- ranking is by (instant, strength) only;
- each conflict id is the SHA-256 of its canonical members' evidence (`receipt_id`, value);
- the conflict in force is derived from evidence held at Q, and every conflict is reported with
  one effect;
- `conflicts(series_id, Q)` gives the derived chain;
- no conflict record is persisted.

**Owner resolutions (Q-002):** `resolve_conflict` is owner-only. A resolution must name the
`conflict_id` in force at its `decided_at`, with completeness established. Events are
content-keyed, append-only and strictly later per conflict.

**Pins (Q-002):** every result records `evidence_digest`, `resolution_digest` and
`ALGORITHM_REVISION = "hio-obs-select/2"`.

**Completeness (Q-002):**
- Before every query and resolution, each receipt captured by Q is checked against the processed
  vintages, **by observation identity and content** (a vintage from that receipt with that value,
  or an append-on-change no-op), never by count. A failure raises `IncompleteProcessing`, with no
  partial output.
- A captured receipt that can't be verified keeps F3's `ReceiptIntegrityError`.

**Capture-order processing (`eb7e92c`).** Ingest refuses a receipt while an earlier-captured
receipt of its source is unprocessed. Without that, a later duplicate processed first could make
an earlier receipt "redundant" and leave a non-canonical vintage set, which the completeness
check would then refuse for ever. With the guard, only the capture-order set is reachable, so
OBS-INV-011 holds outright.

**Jump gate:** it uses quality as decided at the receipt's capture, so a replay decides
identically.

**Releases** (`src/hio/jobs/s1a.py`):
- Q is passed through build, rebuild and the CLI (`--quality-as-of`);
- each view's provenance is recorded in the manifest's existing `inputs` field: Q, admissibility,
  the pins and the conflicts. The approved releases standard fixes the core field set.

## Evidence

| Check | Result |
|---|---|
| Acceptance tests `tests/test_f4_f7_acceptance.py` (AT-Q1-1..6, AT-Q2-1..9, OBS-INV-019) | 20 passed. They don't import against `b4c398d` (new API). The two Codex counterexamples are reproduced there with the old API (see the table above) |
| Whole suite | `pytest` 242 passed, exit 0. That includes every F1, F2, F3, F5 and F6 regression (rounds 1–5) with **unchanged** test code |
| `ruff check`, `ruff format --check`, `tools/check_repo.py`, `git diff --check` | 0, 0, 0, 0 |
| Financial output, Codex's probe (fixed code reference), `b4c398d` versus this head | all four `data.csv` **byte-identical** (SHA-256 and length). Release ids **changed**: the manifests gain only the new `inputs` fields, plus, for the FX datasets, the resulting upstream content hashes (verified by stripping those fields and comparing) |
| S1a golden check (AT-Q1-6 / AT-Q2-9) | `data.csv` hashes equal the reviewed values; S1a views and diagnostics hold **no conflicts** |

## Existing tests whose expectations changed (each documented in the test)

1. `test_same_time_vintages_resolve_deterministically`, now
   `test_same_time_contradictions_are_conflicts_not_ingestion_order`.
   - It asserted that the later-recorded 3.61 won: the F7 behaviour itself.
   - It now asserts that the key is absent with a `suppresses_key` conflict, and 3.61 on the
     capture clock.
2. `test_latest_is_the_most_recently_recorded_valid_vintage`, now
   `…ranks_by_knowable_at_then_strength…`. `latest` no longer uses recording order.
3. `test_market_keys_are_a_subset_of_reconstructed_keys`. Reconstructed may now lose a key to a
   reported unresolved conflict that market doesn't see.
4. `test_quality_events_override_the_recorded_status`. Decisions now need a `decided_at` in force
   at Q.
5. **Q is now passed explicitly** for market, reconstructed and latest calls, in the observation
   and pipeline tests.
   - Where a test was about knowability placement (on-time scheduled capture, §4.1 Case B, the
     pipeline's in-arrears FX leg), I kept its values and passed Q after the captures. Those
     results are labelled and not admissible.
   - Added assertions cover Q = T and Q-before-capture.

## Interpretations to note (literal readings of the approved text)

- **Conflict members include every held observation in the slot,** whatever its quality. A slot
  whose members are all excluded by quality is reported `not_eligible_in_mode`, the closest of
  the four approved effects.
- **Ties between evidence-identical observations** (the same receipt and value) are broken by the
  earliest capture. The value is unaffected. A property test found this order dependence in the
  pure `select`.
- **A single archive receipt carrying a key's revision history** has several vintages at one
  `captured_at` with equal strength. That is a **capture-clock conflict** under the approved
  ranking, so `as_captured_by_hio` reports the key absent (`suppresses_key`). The old code
  returned the later revision.
  - This doesn't affect any S1a fixture or release.
  - It is raised for the owner as an open decision.

## Residual limits

- **Single writer and local filesystem** (unchanged).
- **Capture mode is not recorded,** so completeness treats a same-value row whose only effect would
  have been stronger evidence as a no-op.
- **After a crash between capture and ingest,** the next ingest for that source is refused until
  the earlier receipt is processed. This fails closed.
- **Completeness re-reads the source's receipts on each query.** That is fine at S1a scale.
