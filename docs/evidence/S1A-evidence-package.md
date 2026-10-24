---
id: HIO-EVIDENCE-S1A
title: S1a evidence package (author's submission for independent review)
status: submitted_for_review
owner: implementation agent (author); owner (assigns the review, accepts or not)
version: 1
last_reviewed: 2026-10-24
authorised_by: [OD-0017, OD-0020]
base_revision: 9370256bac6ba2193b09c342170bd11ca57b70a3   # the revision OD-0020 reviewed
head_revision: self   # resolve: git log -n1 --format=%H -- docs/evidence/S1A-evidence-package.md
---

# S1a evidence package

> **Author's claims, not verification.** Nothing here accepts S1a. Codex reviews at a fixed head
> once the owner assigns the review. The owner decides acceptance. The §10 fresh-session test
> has **not** been run.

## How to reproduce (clean checkout of the head)

```sh
uv sync --locked                      # the only networked step: the package index
uv run python tools/check_repo.py     # harness checks: links, front matter, YAML, STATUS, public safety, imports, OBS-INV-005
uv run ruff check . && uv run ruff format --check .
uv run pytest                         # 150 tests; network blocked; Hypothesis derandomised
uv run python -m hio.jobs.s1a --world tests/fixtures/synthetic/s1a_world \
    --rights tests/fixtures/synthetic/rights.yaml --store "$(mktemp -d)" --cutoff 2026-01-29T00:00:00Z
```

Run the last command twice into two empty stores: the four release ids must be identical. They
depend on the head commit (`code_ref`), so they are not listed here; a file cannot contain its
own commit id. CI runs the same checks on every push (`.github/workflows/ci.yml`).

## Commits (`9370256..head`)

| Step (OD-0020 order) | Commit |
|---|---|
| Owner instruction recorded (OD-0020) | `f71852d` |
| 1. Harness CI and public-repository safeguards | `cfd60ad` |
| 2. Python 3.13 / uv skeleton | `583db8e` |
| 3. Contracts and local object store | `426f5b6` |
| 4. Observation, vintage and knowability model; query modes | `8e5fff0` |
| 5. Cash and FX constructions | `af5f1ee` |
| 6. Rights gate, releases, status, consumers, catalogue index, pipeline | `0f6247d` |
| Evidence package, handoff, status (this commit) | head |

## ADR-0010 rev 3 S1a acceptance list → evidence

| Requirement | Evidence (tests are in `tests/`) |
|---|---|
| OBS-INV-001 | `test_observations.py::test_obs_inv_001_*`, `::test_identical_consecutive_refetch_is_a_no_op` |
| OBS-INV-002, -003 | `test_query_properties.py::test_obs_inv_002_and_003` (Hypothesis, 300 cases) |
| OBS-INV-004 | `test_observations.py::test_obs_inv_004_*`; `test_objectstore.py::test_receipt_hash_verifies_on_write_and_read` |
| OBS-INV-005 | `tools/check_repo.py valid_time` (lint); `test_independence.py`; `test_contracts.py::test_obs_inv_005_*`; parser refuses instants as dates |
| OBS-INV-006 | `src/hio/marketdata/knowability.py`; `test_observations.py` late-capture, rule-inferred and backfill tests |
| OBS-INV-007 (mandatory regression) | `tests/fixtures/synthetic/obs_inv_007_*.csv`; `test_observations.py::test_obs_inv_007_case_a_*`, `::test_obs_inv_007_case_b_*` (both ingestion orders) |
| RA §3.2 fixtures, CASH-USD-INV-3 | `test_constructions.py::test_usd_fri_to_mon`, `::test_usd_fri_to_tue_with_monday_holiday`, `::test_usd_thu_to_mon`, `::test_usd_look_ahead_trap_*`, `::test_aud_fri_to_mon_*`, `::test_weekend_is_not_compounded_daily` |
| FXC-INV-1…4 | `test_constructions.py::test_fxc_inv_4_*` (with -1, -2); identities checked in every period in `src/hio/library/fx.py`; FXC-INV-3 by `::test_worked_example_14_5_*` |
| RA-INV-021 | `test_constructions.py::test_ra_inv_021_fixtures` (a) and (b) |
| Releases §6.1 | fixture 1 `test_pipeline.py::test_fixture_1_*`; 2 `::test_fixture_2_*`; 3 `::test_fixture_3_*`; 4 `test_contracts.py::test_manifest_core_refuses_self_reference` |
| Rights fail-closed fixtures: fetch, store raw, build, store derived, rebuild, publish | `test_rights.py`: the matrix (every operation × deny/unknown/unsatisfied conditional × each required permission; unverified and vendor_asserted), and atomicity through the real code paths (`::test_fetch_refusal_*`, `::test_build_refusal_*`, `::test_store_derived_refusal_*`, `::test_rebuild_refusal_*`, `::test_publish_refusal_*`) |
| Import and independence checks | `tools/check_repo.py imports`; `test_independence.py` (deliberate violations fail; no `macsmsf` in the lockfile) |
| Reproducible rebuild | `test_pipeline.py::test_fixture_1_*`, `::test_rebuild_from_stored_receipts_reproduces_every_release` |
| Harness CI checks | `tools/check_repo.py`; `.github/workflows/ci.yml` |
| Codex review at an assigned head | **pending**: not assigned |

## Implementation-plan stage mapping (S1a part)

| Test | State | Evidence or note |
|---|---|---|
| S1-A1 | met for S1a | import rule, lockfile check, socket block in tests. No CI egress firewall: see limitation 8 |
| S1-A2 | met | `test_independence.py::test_deliberate_violations_fail` |
| S1-A3 (local store) | met | `test_objectstore.py`. Bucket versioning is S1b |
| S1-A4 | met | as OBS-INV-001 |
| S1-A5 | met | as OBS-INV-002/003/007 |
| S1-A6 | met | as OBS-INV-005 |
| S1-A7 | met | RA §3.2 fixtures; CASH-USD-INV-4 `test_constructions.py::test_usd_period_is_knowable_*` |
| S1-A8 | met | FXC-INV-1/2/4; RA-INV-007 rising and falling `q`; RA-INV-016 |
| S1-A9 | met | `test_pipeline.py::test_four_releases_including_the_decomposition_companion` |
| S1-A11 | met | as reproducible rebuild |
| S1-A12 (fixtures) | met | as the rights fixtures. Real sources are S1b |
| S1-A14 | met | malformed receipts quarantined whole; staleness and completeness tests |
| S1-A15 | met | harness checks pass; handoff written |
| S1-A16 | **not run** | the §10 fresh-session test needs a session with no prior chat history (OD-0020) |

## OD-0020 considerations → evidence

1. **Deterministic query modes.** Order (instant, basis strength, vintage_seq); order-independence
   property; reload gives identical results. Tests: same-time vintages, revision sequence with a
   revert, quarantine and owner-only release, late capture, evidence insufficiency
   (rule_inferred, schedule_only), schedule-only backfills; OBS-INV-007.
2. **Every RA §3.2 and FX fixture**, numbers and availability: period `knowable_at` is the
   latest input; Fri→Mon USD knowable at Friday's SOFR publication; the FX excess waits for the
   in-arrears USD leg (`test_pipeline.py::test_fx_period_waits_for_the_in_arrears_usd_leg_*`);
   absent periods are recorded, never filled.
3. **Rights fixtures** cover all six operations, every permission state and both insufficient
   verification levels, with refusal atomicity. Synthetic `owner_verified` lives only in
   `tests/fixtures/synthetic/rights.yaml`. Loaders refuse mixing. The genuine register is
   byte-identical after the tests and still refuses every operation for the S1 sources.
4. **Public-repository safeguards:** `docs/engineering/repository-safeguards.md`,
   `.gitignore`, `tools/check_repo.py public`, pre-commit hook, SHA-pinned actions,
   `contents: read`, no secrets or schedules. Network: install allowed; tests and `src/` blocked.
5. **Provenance and approved documents intact.** No approved document changed in
   `9370256..head`. `tools/verify_migration.py` is excluded from formatting, and ruff is limited
   to Python so Markdown records are never reformatted (one accidental reformat of a historical
   handoff was caught and reverted before commit).

## Interpretations a reviewer should test (the standards are silent or open here)

1. **OBS-INV-007 Case B, `reconstructed(2021-01-01)`.** §4's definition gives **110**: the
   schedule-only vintage is placed at its scheduled release, one day after the archive's 100.
   The standard specifies only `as_known_by_market` for Case B. Should publisher evidence
   override a schedule-only placement? That is a standard question for the owner.
2. **A revision's `knowable_at`.** A scheduled capture that sees a changed value for a key
   already held is `captured_on_schedule` at the **capture instant**, not the original release.
3. **The capture grace window.** `captured_on_schedule` needs `release <= captured_at <= release
   + grace`. A later capture is `schedule_only`, because the value may already be a revision.
4. **Redundancy.** A new vintage is created when the value differs from the latest-recorded
   vintage (so reverts are kept), or when it adds stronger or earlier evidence for the same value.
5. **Duplicate receipts.** Only an identical *consecutive* re-fetch of a source is a no-op.
   Identical bytes after a different response are a new capture event.
6. **Same-time tie-break:** stronger basis, then later-recorded vintage.
7. **Publishing to `hio_internal`** is the owner's `approved_for_consumer(hio_internal)` status
   event, gated by `distribution.hio_internal`. The job itself only marks releases
   `exploratory`.
8. **No CI egress firewall.** Enforcement is the import rule plus the test socket block, not
   the runner's network.
9. **Status levels** for consumers: superseded and deprecated rank with exploratory.
10. **Stack addition:** `pyyaml` (YAML specs and registers); `hatchling` as the build backend.

## Known limitations

- Synthetic data only. The world's values are invented, and its release times model the specs'
  [EXT] claims, which T-0002 has not verified.
- No artefact envelope beyond releases (§4 envelopes are not needed until a consumer exists).
- The catalogue index is in-memory per use. A persisted index file is never committed.
- T-0002 and T-0003 made no progress in this session.

## NOT approved or done

- S1a is **not accepted**.
- The Codex review is **not assigned**.
- The §10 fresh-session test is **not run**.
- S1b is not authorised.
- No source permission is verified.
- No vendor contact. No `macsmsf` change. No T-0004 merge.
