---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-1, F-REVIEW-2026-10-24-s1a-1-2, F-REVIEW-2026-10-24-s1a-1-3, F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-5, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]
reviewed_head: 98e6a8e08fca8b28241d9e4e7c04c181d75f1eef
receipt_commit: e55cc8922ca2f018956fe6c6f4ff97e43d5acc17
authorised_by: OD-0023
fix_commits: [1c117e6c2a6fa9512ace0c55481caca694be79c6, 3185443953c6ba78f921ba1d1e11762ff9c01fa9, 7076452fff582e259ebf42759bbd04fe49cd9c4f, 6bbf562ebba6e0dba331d6cf1d59a4599b0fefbb, 39d37dade6e90cfe7cdb99411ae244bb4d9400d7]
draft_commits: [d1edf1e8b78ad23c35810cf6cbdcb5bf00d03a65]   # Q-001 and Q-002 drafts only
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-1.md
created_at: 2026-10-24
---

# Remediation response: REVIEW-2026-10-24-s1a-1

> **Author's claims, not verification.** Every finding stays **open** until a verification
> record closes it. Codex verifies at the **submission head** (the commit that adds this file),
> under a separate owner assignment.
>
> **Five remediation claims (findings 1, 2, 3, 5, 6) and two unresolved policy questions
> (findings 4, 7).**

Branch `remediation/s1a-1`, cut from `main` at `6fe35cf`. Receipt commit `e55cc89` is an
ancestor (checked before starting).

**Method, per finding:** Codex's counterexample was written as a regression test and run
against the code **before** the fix (the "before" result below), then the fix was made and the
test rerun ("after"). All regression tests are in `tests/test_remediation_s1a_1.py`.

## Remediation claims (five)

| Finding | Fix commit | What changed (files) | Evidence: before → after | Residual risk or disagreement |
|---|---|---|---|---|
| **F-…-1-1** (high) consumer rights checked against an unrelated source | `39d37da` | `src/hio/contracts/layout.py` (new: shared key layout); `src/hio/publish/lineage.py` (new: transitive lineage from verified receipts, capture records and upstream releases; fail closed); `publish/release.py`, `publish/status.py` (no caller source ids; lineage authorised; dataset id must own the hash); `jobs/s1a.py`, `marketdata/vintages.py` (build and rebuild authorise the sources of the selected vintages) | `-k f1`: **2 failed** (Codex's counterexample for use and for approval: "DID NOT RAISE") → **6 passed** (also: transitive lineage, fail closed on a missing receipt, no `source_ids` parameter, dataset/hash mismatch) | **API change.** `source_ids` was removed from `write_release`, `append_status` and `resolve_for_use`. Existing call sites in `test_pipeline.py` and `test_rights.py` were updated. The store_derived refusal test now asserts per-release lineage: the USD cash leg depends only on `synthetic.nyfed`, so a refusal of `synthetic.rba` correctly does not block it. Lineage requires upstream releases to be stored first, as `publish_releases` already orders them. |
| **F-…-1-2** (high) approval for one class authorised another | `6bbf562` | `src/hio/contracts/status.py` (an optional class on `withdrawn`; `effective_status_for`); `src/hio/publish/status.py` (class-specific effective status at use) | `-k f2`: **2 failed** (hio_internal approval resolved for smsf_app; class-scoped withdrawal could not be expressed) → **3 passed** (independent approvals; class withdrawal; re-approval; a global withdrawal refuses every class and is terminal) | **Representation.** A class's effective status is the latest event that is class-agnostic or names that class. A later class-agnostic lifecycle event therefore supersedes a class approval until re-approved. Anything beyond this is owner question **Q-005b**. The overall effective status (highest seq, releases standard §5) is unchanged. |
| **F-…-1-3** (high) a missing receipt did not block a vintage or release | `3185443` | `src/hio/marketdata/vintages.py` (`view()` verifies each selected vintage's capture record and receipt bytes; `ReceiptIntegrityError`) | `-k f3`: **2 failed** (deleted and corrupted receipt: "DID NOT RAISE") → **3 passed** (query and build both refused; intact receipts still work) | Verification is at selection time, so a damaged receipt for an unselected vintage is not reported until it is selected. A whole-store audit is not part of this fix. |
| **F-…-1-5** (medium) rebuild check passed on corrupt stored bytes | `7076452` | `src/hio/jobs/s1a.py` (`rebuild_report`: reproduced only if `verify_release` passes and the manifest and files equal the rebuilt ones byte for byte; `rebuild_check` keeps its boolean API) | `-k f5`: **2 failed** (corrupt `data.csv`, corrupt `manifest.json`: True) → **3 passed** | None known. |
| **F-…-1-6** (medium) multi-object writes not atomic after commit began | `1c117e6` | `src/hio/storage/objectstore.py` (a group under a new directory is built in hidden staging and renamed atomically; otherwise an intent journal with rollback, and recovery on reopen); `marketdata/vintages.py` (one catalogue transaction per receipt); `marketdata/capture.py` (bytes and capture record committed together) | `-k f6`: **4 failed** (Codex's counterexample, induced failures on both paths, crash recovery), then the partial-ingest case **1 failed** → **6 passed** | **Single-writer assumption.** Journal recovery assumes one writer, as S1a does. The journal path is all-or-nothing on failure, but between its first and last object another reader could briefly see a partial set; the release path (directory rename) has no such window. Jump detection now also sees earlier rows of the same receipt (needed once ingest became one transaction; covered by the existing quarantine test). |

## Unresolved policy questions (two; no remediation claimed)

| Finding | State | Why no fix | Prepared for the decision |
|---|---|---|---|
| **F-…-1-4** (high) a later quarantine release changes an earlier point-in-time query | open; **blocked on Q-001** | changing it alters approved temporal semantics (observations standard §2/§4), which OD-0023 forbids before the decision | draft [OBS-AMEND-Q001](../../docs/standards/drafts/OBS-AMEND-Q001-quality-event-time.md) (`d1edf1e`): options A (recommended: event-time quality in the point-in-time modes, labelled restatement elsewhere), B, C; proposed OBS-INV-008 |
| **F-…-1-7** (medium) conflicting same-time values resolved by ingestion order | open; **blocked on Q-002** | §4 defines no tie-break for contradictory evidence; any rule changes approved semantics | draft [OBS-AMEND-Q002](../../docs/standards/drafts/OBS-AMEND-Q002-same-time-conflicts.md) (`d1edf1e`): options A (recommended: quarantine both, key absent, order-independent), B, C; proposed OBS-INV-009 |

The code paths for findings 4 and 7 are unchanged. `marketdata/queries.py` is identical to
`98e6a8e`, and the quality application in `vintages.py` is unchanged.

## Whole-change evidence (at the submission head)

- **Tests:** `pytest` **199 passed** (exit 0). That is 150 at the reviewed head, 28 from the
  harness-0.7 gate tests, and 21 regression tests here.
- **Checks:** `ruff check` 0; `ruff format --check` 0; `tools/check_repo.py` 0.
- **CI:** cited in the PR description.
- **Financial outputs unchanged.** An end-to-end synthetic build at the 2026-01-29 cutoff gives
  `data.csv` bytes identical to the reviewed head `98e6a8e` for all four datasets. Release ids
  differ only through `code_ref`.

## Not claimed

- No finding is closed or verified.
- S1a is not accepted.
- No standards change is approved.
- S1b is not authorised.
