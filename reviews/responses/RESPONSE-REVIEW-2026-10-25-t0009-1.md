---
id: RESPONSE-REVIEW-2026-10-25-t0009-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-25-t0009-1, F-REVIEW-2026-10-25-t0009-2, F-REVIEW-2026-10-25-t0009-3, F-REVIEW-2026-10-25-t0009-4, F-REVIEW-2026-10-25-t0009-5, F-REVIEW-2026-10-25-t0009-6, F-REVIEW-2026-10-25-t0009-7]
responds_to: REVIEW-2026-10-25-t0009-1   # reviewer tip 71f5b3737290164eab89dd7f2c6176dbe6bf2b6e (tag reviews/REVIEW-2026-10-25-t0009-1); record blob 69ccb9362644f65240eb403454d424eab4fe5ece, sha256 3a822a5b57c7df1f462ccfb1b970858d80700d5b96b2aa0d9469da3dab4ccf22; received by OD-0067 (merge 9efabbe), read from main at 950cce7
previous_submission_head: ce0c3b534ac98eb89663cf15c439f5ccad93b969
authorised_by: OD-0067
fix_commits:
  - c5d4421265532d5a5d87cbcd3884dc1982e0b313   # F-1, F-2
  - d85b1c37cdf033ffd1cf3d86c15607cf29a18467   # F-6
  - 42ad1b868b935253a128112c1b9e24303a4ccd96   # F-3, F-4
  - fe7e2447f78335864f7657d09a6c28e3ba88a019   # F-5
  - 30c7b6818838b5980e3c7b849d74a0b542a786a3   # F-7
test_commits: []   # each fix commit carries its own regression tests
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-t0009-1.md
created_at: 2026-10-28
---

# Remediation response 1: T-0009 S1b-1.0

> **Author's claim, not verification.** All seven findings stay **open** (`remediation_claimed`
> at most). Only Codex may verify closure, at a fixed head the owner assigns. **F-5 is remediated
> in part only:** the dated, cited calendar mechanism exists, but no real RITS or NSW reference
> data has been retained (see F-5 below).

Branch `impl/t0009-remediation-1`, cut from the reviewed head `ce0c3b5` (kept in its ancestry, never
rebased). `main` was **not** merged into the branch, so no harness-0.9 record is on it. Nothing was
fetched, provisioned or enabled.

## Closure map

| Finding | Root cause | Fix | The review's own scenario, re-run |
|---|---|---|---|
| **F-1** (high) | `rights_sources` treated a receipt with no link as single-dataset, so a lost F1 link made `rba.f1` the rights subject | `src/hio/contracts/publications.py`: a fixed, immutable publication → dataset → series mapping in code. `lineage.rights_sources` decides "shared" from the receipt's **publication id**, not from whether a link exists; for `rba.f1` it requires every capture's expected link, byte for byte | Store copied with every F1 link removed, gate allowing only `rba.f1`: **refused** (`LineageError`) before the gate, nothing written. At `ce0c3b5` the same probe wrote the release |
| **F-2** (high) | the link's dataset was trusted if it contained the series | attribution comes from the fixed mapping (`owning_dataset`); the stored link must equal the canonical link the mapping implies (publication, receipt, capture instant, datasets). Missing, extra, duplicate, substituted, swapped or re-dated links refuse; a link on a single-dataset receipt refuses. The vintage view checks the same mapping and refuses a `SeriesDef` whose `dataset_id` disagrees (either way). The adapters' `Publication` refuses at import if it drifts from the mapping | Links rewritten to give AONIA to `wrong.dataset`, gate allowing only `wrong.dataset`: **refused**. At `ce0c3b5` it wrote |
| **F-3** (medium) | levels anchored only at period ends; `continue` dropped periods; precision inferred from data; first-order bound | `ours = 1 + r_t` exactly (no anchor). **Every** eligible cash period is a row, including each absent cash period; an uncomparable one is `not_compared` with its cause (`reference_missing_at_start/end/start_and_end`, `cash_period_absent`), counted in `not_compared_by_cause`. Precision is **declared** in the cited spec (`reference_decimals`, `rate_decimals`); an observed value finer than declared is `precision_exceeds_declared`, never "rounding". The bound is exact interval arithmetic over both rounding sources | AUD: 9 periods, 9 rows, 9 compared (was 8). USD: every period a row; the two around the derived US holiday (12 Oct) are `not_compared` with cause (was silently dropped). Validated by an independent 400-draw simulation per model: no draw exceeds the bound and the bound is attained within 3x |
| **F-4** (medium) | S1b releases cited the S1a spec versions | `cash.aud.overnight` and `cash.usd.overnight` **0.3.0** describe the S1b inputs (`rba.cash_rate.aonia` from dataset `rba.cash_rate`; `nyfed.sofr`), RITS selection and period ends, NSW period ends, the derived NY calendar, the in-arrears regime, P3 placement and the comparison model. 0.2.0 is kept byte-identical in `specs/factors/archive/`. S1a pins 0.2.0 (`S1A_SPECS`); S1b cites 0.3.0 (`S1B_SPECS`); `spec_ref` refuses a version that exists nowhere. `check_repo` accepts `archive/<factor_id>@<version>.yaml` | All four S1b releases cite `@0.3.0`. The four S1a releases cite `@0.2.0` with **content hashes identical** to `ce0c3b5` (code_ref fixed), not just `data.csv` |
| **F-5** (medium) | calendars were ad hoc objects in tests | `load_reference_calendar`: a dated, cited document (id, kind, `as_of`, citation, coverage, weekend, each closure with a reason); a date outside the coverage raises `CalendarCoverageError`, never assumed open. `kind: reference` needs a URL and a rights-register id; `kind: synthetic` loads only in tests. `Calendars` refuses an uncited RITS or NSW calendar. Each cash release names the calendar files it used (`id@as_of#sha256`) | Synthetic dated fixtures with a RITS-only and an NSW-only closure: RITS closure carries the prior RITS rate for 2 days and ends no AUD period; the same date ends an NSW period; an NSW closure ends no USD period |
| **F-6** (high) | the record had no `keys_checked` | every verified record (changed **and** unchanged) carries `keys_checked`: sorted `(series_id, valid_time, sha256 of the canonical value text)`, flags as `rba.expert_judgement.fallback_type`. A failed record claims none. New error class `key_missing`: a served series with no key, or a held key inside the new response's span that is absent. A key rolled off the start of a window is not missing | Changed and unchanged runs replay to the same digests from the stored bytes (C3's arithmetic, independently); a response dropping a held key writes only a `failed`/`key_missing` record; a tampered `keys_checked` fails the record hash. **No C1–C7 check or finality is implemented** (OD-0063) |
| **F-7** (medium) | no gate, no definition, no production caller | `src/hio/sources/schedule.py`: first and final checks per HIO-ADR-0012 §4.3 (09:45 and 16:30 Sydney on RITS days; 08:30 and 15:00 New York on weekdays), 12 UTC cron slots covering both DST regimes plus a same-day retry, a 3-hour due window. `src/hio/jobs/s1b1_capture.py`: `run_due` is the production caller; the slot and due instant come from the gate, a verified slot is not re-run, a failed one is retried. `run_capture` and `RunRecord` refuse a slot without a due instant, an unknown slot, or a start before the due instant, **before any request**. The definition is `infra/workflows/s1b1-capture.yml`, kept **outside** `.github/workflows/`, `--dry-run` only | Every slot on every weekday of 2026–2027 has a firing and a retry inside its window, and the gate agrees at each; deleting one cron slot fails the test. No `.github/workflows` file has a schedule. The entry point refuses anything but a dry run |

## Evidence

| Check | Result |
|---|---|
| Full suite at the fix head `30c7b68` | `uv run --no-sync pytest -q`: **408 passed** (348 baseline + 60 new) |
| Repository checks | `uv run --no-sync python tools/check_repo.py`: PASS, 0 problems; `ruff check` and `ruff format --check`: clean; `check_repo.py trailers ce0c3b5 HEAD`: PASS |
| The four S1a `data.csv` sha256 | unchanged (`tests/test_f4_f7_acceptance.py` `S1A_DATA_SHA256`, passing) |
| S1a release identities | content hashes equal at `ce0c3b5` and at the head (`tests/test_s1b1_remediation_specs.py`, values computed by running the base code from a worktree) |
| Review probes F-1, F-2 | at `ce0c3b5`: `WROTE` both; at the head: `REFUSED LineageError` both (scratch probe using only APIs present at both revisions) |
| New regression tests at `ce0c3b5` | all six files fail there (the symbols they exercise do not exist) |
| Governance paths | `git diff --stat ce0c3b5 HEAD -- registers docs/standards docs/decisions AGENTS.md docs/harness .github templates .claude` is empty |

**Existing tests changed (three assertions, each encoding the defect):**
- `test_a_shared_receipt_without_its_link_fails_closed`: expected the incidental `rba.f1: no rights
  record` refusal; now expects `LineageError` (F-1's point).
- `test_a_link_naming_the_wrong_dataset_fails_closed`: the error message changed.
- `test_index_comparisons_are_recorded_and_agree_within_publisher_rounding`: asserted every row
  "within" only because omitted periods had been dropped; now asserts it over compared rows.
- The test world's RITS and NSW calendars now load the dated synthetic fixtures (same closures as
  before, plus a RITS-only closure outside the world's dates).

## Decisions taken within scope (for the reviewer to test)

1. **Precision declarations are assumptions.** AONIA 2 dp, TRI 4 dp, SOFR 2 dp and the SOFR Index
   8 dp are marked `[EXT, unverified]` in the specs. A wrong declaration surfaces as
   `precision_exceeds_declared` or `outside_expected_bound`, never as false agreement.
2. **"Disabled" means outside `.github/workflows/`.** A `schedule:` trigger there on `main` would
   be an enabled schedule even with a guarded job, which the owner forbade.
3. **One OBS-INV-005 lint exemption.** `schedule.py` takes the local wall-clock date of a check
   with `.date()`. That date is never a `valid_time`. The exemption is a counted allowlist entry
   in `tools/check_repo.py` (`VALID_TIME_EXEMPT`): a second call in the file still fails.
4. **The card's §4 line** "`keys_checked` digests (from the stored bytes)" was "reconstructable
   later". OD-0067 instructs recording them now, so they are recorded.
5. **The review index cell** for each finding is not edited on this branch: it is cut from
   `ce0c3b5`, which predates the rows. The claim is this response. The index row update
   (`remediation_claimed`, submission head) goes on `main` with the verification assignment.

## F-5: what remains open

The format, loader, refusal rules and selection behaviour are in place and tested. **No real RITS
or NSW calendar is retained.** Retaining one is an operation on readiness-package dataset D7 (RBA
RITS and bank-holiday pages). D7's rights are not `owner_verified` (T-0002), and committing data
to this public repository needs them. Reading the pages is also a fetch from a real source, which
STATUS forbids. The owner must decide D7 before F-5 can close. Until then the release builder
accepts only cited calendars, and only tests can construct one, from synthetic data.

## Not done, not claimed

- No C1–C7 checks, finality or final label (OD-0063 staging, unchanged).
- No provisioning, credentials, real fetch, `tofu init/validate/plan/apply`, or enabled schedule.
- No source right marked verified; no acceptance of T-0009 or S1b.
