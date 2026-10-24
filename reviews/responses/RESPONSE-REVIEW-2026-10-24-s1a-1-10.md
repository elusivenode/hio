---
id: RESPONSE-REVIEW-2026-10-24-s1a-1-10
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-24-s1a-1-7]
responds_to: VERIFY-2026-10-24-s1a-1-9   # commit 63df7ff269da03fe0c4542141ad388ddd91bd357, record sha256 e3211b1815cee091c93a8e730eb95672b942011d88adabd1866f931f62c8b600 (checked; OD-0035)
contract: OBS-AMEND-Q002-R1 revision 1 (approved, OD-0035; blob cb7a937dc6e8cc20314e2ae33cd20ce1163fd584)
previous_submission_head: 0e900e88acc0113fc42c4215b1379af9b7ea2f0e
authorised_by: OD-0035
fix_commits: [3016796]
test_commits: [5d5d519]
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-24-s1a-1-10.md
created_at: 2026-10-25
---

# Remediation response 10: F7, the quality_digest pin (Q-002-R1)

> **Author's claim, not verification.** F7 stays **open** (and so does F4). The approved contract
> blobs are unchanged (Q-001 `419992f2`, Q-002 `d0a25b3b`, Q-002-R1 `cb7a937d`).

## The gap (VERIFY-2026-10-24-s1a-1-9)

- No result pin identified HIO quality decisions.
- Two valid stores, one with an owner `QUARANTINED` decision before the cutoff, gave different
  results under identical `evidence_digest`, `resolution_digest` and `algorithm_revision`.
- I reproduced this on `0e900e8`, under OD-0034.

## Implementation (`3016796`), to the approved amendment

**The pin.** `quality_digest` is the SHA-256 of the canonical JSON
`{"schema": "hio-quality-digest/1", "series_id", "events"}`.
- **Which events:** the series' quality events with `decided_at ≤ Q`.
- **Each event carries:**
  - the decided vintage, identified by its evidence (`series_id`, `valid_time`, `receipt_id`,
    `captured_at`);
  - `status`, `decided_at`, `actor` and `evidence`.
- **Excluded:** `vintage_seq`, `event_seq` and `recorded_at`.
- **Ordering:** the approved ordering.
- **Empty history:** the documented fixed value.
- **An event naming a vintage that isn't stored refuses.**

**The other pins.** `ALGORITHM_REVISION` moves to `hio-obs-select/3`. The meanings of
`evidence_digest`, `resolution_digest` and `algorithm_revision` are unchanged.

**Immutable references.** Every view carries:
- E(Q) as (`source_id`, `captured_at`, `receipt_id`, verified disposition). Its SHA-256 is
  `evidence_digest`.
- The quality and resolution events, each by storage key and SHA-256 of the stored bytes.

The references identify exact objects, so they take no part in result equality: a faithful copy
recorded at another time is the same result with the same four pins.

**Release provenance.** Each release's existing `inputs` record now carries `quality_digest` and
the three reference lists. The manifest core field set is unchanged.

**Refusal.**
- `VintageStore.verify_pins` refuses (`PinMismatch`) when any of the four pins differs from a
  reconstruction.
- `s1a.verify_release_inputs` reconstructs every input from the store and refuses on any difference
  in the input record: pins, references or the vintage cut.
- Missing or altered evidence refuses through the existing completeness and integrity checks.

**Unchanged:** the selection, quality, conflict, completeness and admissibility rules.

## Evidence

| Check | Result |
|---|---|
| The gap on `0e900e8` (scratch reproduction, OD-0034) | two stores: `{2026-01-12: 3.60}` versus `{}`, with three identical pins |
| `tests/test_q002_r1_quality_digest.py` (AT-Q2R1-1..7, 11 tests) against `0e900e8` | new: they don't import there (`PinMismatch` doesn't exist) |
| The same tests now | 11 passed |
| Whole suite | `pytest` 273 passed, exit 0. That includes F1–F6, the original F4/F7 cases and rounds 6–8. One existing assertion changed by design: AT-Q2-7's `algorithm_revision` is now `hio-obs-select/3` |
| `ruff check`, `ruff format --check`, `tools/check_repo.py` | 0, 0, 0 |
| Financial output versus `0e900e8`, the implementation Codex verified in round 9 (Codex's probe) | all four `data.csv` **byte-identical** (SHA-256 and length) |
| Release identity versus `0e900e8` | **every release id changes.** Explained entirely by `quality_digest`, the three reference lists, `algorithm_revision` (`/2` to `/3`), and the resulting FX upstream content hashes. Verified by stripping exactly those and comparing the manifests: identical |

## Also in this submission

The observations v0.3 **candidate** now incorporates Q-002-R1 (commit `dc0ac10`; blob
`61ddd58e`). It remains pending its own exact-revision approval.
