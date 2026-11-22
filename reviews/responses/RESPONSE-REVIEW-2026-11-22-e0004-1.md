---
id: RESPONSE-REVIEW-2026-11-22-e0004-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2, F-VERIFY-2026-11-22-e0004-1-1]
reviewed_head: 6720c5c34a130db8ae0a6196fa530e10f3888e91
fix_commits: [ce57c6d989eeb35df099b63847f4650bdb848a59, e8d43a07ed3dabfc0f0ccfc76c011522d388d664, f9b03822354f36e60fa3ce305050d7009ee7965c, 2d7b6f288abe21307a09301f3b9d5333baf7417a]
submission_head: self   # the commit adding this file; resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-11-22-e0004-1.md
created_at: 2026-11-22
---

# Remediation response: REVIEW-2026-11-22-e0004-1

> Written by the author under OD-0196 (F-2) and OD-0201 (F-1). A claim, not a verification. Each finding stays open until a verification record closes it.

| Finding | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|
| F-1 (high): first-release CPI state was not established | **No rerun and no design change** (OD-0201). The claim is a recorded deviation plus a complete check of its effect. `tools/bls_cpi_releases.py` fetches and reads Table 1 of every archived release; `tools/e0004_first_release_states.py` builds the first-release series (each month from its own release) and recomputes the states with `tools/e0004_state.py`, unchanged. Records: `docs/evidence/e0004/cpi-first-release-check-2.md`, `cpi-first-release-states-1.md`; Addendum 1 appended to `preregistration-1.md` and `result-1.md`, the adopted text untouched | 257 releases retained locally under two manifests (hashes in `cpi-first-release-states-1.md`), covering every level the state reads, April 2005 to September 2026. Four first-published levels differ from the flat file (May to August 2016). The flat-file states reproduce the run's `states.csv`; 0 of 233 periods differ under the primary rule and the equality sensitivity; no month the rule reads is missing. The tool was broken on purpose four ways and caught each. Tests: `tests/test_bls_cpi_releases.py` (real BLS snippets), `tests/test_e0004_first_release_states.py` (invented data) | **The run's inputs were not first-release values for four months, and still are not:** the finding's fact stands and is now recorded, with its effect shown to be nil for this run. `tools/e0004_state.py` still reads the flat file; a future run would need the first-release series wired in, which no one has authorised. The check sees a correction only through a month's own release and, from 2013, a later year-ago column. The retained bytes are local, not in the repository: a verifier needs read access to `~/.hio-research/E-0004/{raw,releases,releases-2005,first-release-states}` and the run's `states.csv`, all BLS-derived |
| F-2 (high): public evidence contains restricted derived measurements | `docs/evidence/e0004/step1-1.md`, `step1b-1.md`, `result-1.md` and OD-0190's correction 2: measurements derived from EODHD returns removed; readings and yes/no only (`ce57c6d`, PR #122) | A reader can check the current files hold no count, width or interval computed from EODHD returns. `docs/evidence/e0002/stability-1.md` sets the pattern for later records | **Git history still holds the earlier revisions.** The owner keeps the history as it stands on the owner's reading of EODHD's terms (OD-0196); that is the owner's acceptance of the history, not a waiver. The tools still compute these values locally, by design |

Suite at the submission head: see the PR's CI; `check_repo.py` PASS.

## Response 2 (2026-11-22, after VERIFY-2026-11-22-e0004-1-1, NOT READY; under OD-0203, OD-0184 A8)

> A claim, not a verification. The verification's points are accepted as stated.

| Finding | What changed (files) | Evidence | Residual |
|---|---|---|---|
| F-REVIEW-2026-11-22-e0004-1-1 (narrowed, open) | The coverage overstatement is corrected: the states read **256** months (April 2005 to August 2026), not 257. `docs/evidence/e0004/preregistration-1.md` Addendum 1 and `cpi-first-release-states-1.md` now say so; Claude re-counted the months the rule reads with a recording table and got 256 under both rules | the two files; the reviewer's own enumeration | **Nothing here removes the reviewer's reason for leaving the finding open:** the run's executed inputs departed from the adopted rule for four months, and `tools/e0004_state.py` still reads the flat file. That needs an owner action (a waiver, or a run on first-release inputs) or stays open with the line parked. No claim of closure is made |
| F-REVIEW-2026-11-22-e0004-1-2 (open) | `docs/decisions/owner/OD-0190-adopt-e0004-preregistration.md`, Correction 2: the step 1b half-width is removed and replaced by the reading. **Response 1 said this correction was already redacted. It was not; that claim was wrong** | `grep` of the current E-0004 records and OD-0188 to OD-0203 for a count, width or interval computed from EODHD returns | git history kept (OD-0196) |
| F-VERIFY-2026-11-22-e0004-1-1 (medium, open) | `pyproject.toml` and `uv.lock`: `pypdf` added to the `dev` group. `tests/test_bls_cpi_releases.py`: the two PDF tests no longer skip when `pypdf` is missing | a frozen environment runs the PDF tests; the real check runs with `uv run`, no `--with` | the PDF text layout is tested on generated PDFs in the real shape, not on a committed real PDF |

## Response 3 (2026-11-22, after VERIFY-2026-11-22-e0004-1-2, NOT READY; under OD-0206)

> A claim, not a verification.

| Finding | What changed (files) | Evidence | Residual |
|---|---|---|---|
| F-REVIEW-2026-11-22-e0004-1-2 (open) | The verification's instance (`docs/evidence/e0002/assessment-1.md`) and every other number a repository-wide sweep found that is taken or computed from EODHD data: also in `docs/evidence/t0023/corroboration-1.md`, `docs/evidence/t0023/recommendation-1.md`, `registers/experiments.yaml`, two 2026-11-04 handoffs and `knowledge/findings.md`. Each is replaced by a reading. The owner set the line in OD-0206: numbers go; qualitative readings (signs, size words, the dates where EODHD disagrees with a reference, the sample length) stay | The sweep read every current tracked file; code, tests, specs and reviewer records held none. After the edits, a search of those records for "N of M" and counted periods finds only RBA-derived figures | **The line between a derived measurement and a reading is the owner's (OD-0206).** A verifier who reads EODHD's terms more strictly could still object to the qualitative wording; that would be a question for the owner, not a missed instance. One AUD/USD rate in `docs/research/T-0003-vendor-assessment-2026-11-04.md` stays, as probably public. Git history kept (OD-0196) |

## Response 4 (2026-11-22, after VERIFY-2026-11-22-e0004-1-3, NOT READY; under OD-0210)

> A claim, not a verification. Responses 1 and 3 each claimed more than was true; the verifications were right each time.

| Finding | What changed (files) | Evidence | Residual |
|---|---|---|---|
| F-REVIEW-2026-11-22-e0004-1-2 (open) | **Sentence-level redaction is abandoned** (OD-0210, on the architect's advice). The ten result-bearing evidence records are now public stubs that state what each record is, its standing and where its content is: `docs/evidence/e0002/assessment-1.md`, `e0002/stability-1.md`, `e0003/result-1.md`, `t0023/corroboration-1.md`, `t0023/episodes-1.md`, `t0023/recommendation-1.md`, `t0023/panel-1.md`, `e0004/step1-1.md`, `e0004/step1b-1.md`, `e0004/result-1.md`. Their content, at every revision in their history, is copied byte-for-byte into a local results store (`tools/results_store.py`, worker W1). Result statements in `registers/experiments.yaml`, `knowledge/findings.md`, three handoffs, `STATUS.md` and one rate in the T-0003 vendor assessment are replaced by pointers | `tools/results_store.py verify` passes on the store: 47 entries, each file's sha256 and size equal to its manifest entry, no unlisted file, catalogue equal to the manifest. Claude altered a stored file and planted an extra one; both were reported. A stored file was compared with `git show` at its revision: identical. `tests/test_results_store.py` (invented data) | **Not touched, by the owner's decision (OD-0210): owner decision records, `docs/history/` and review records,** which may still hold readings; any residual there is for a scoped owner decision after verification. **Still public by decision:** preregistrations, which name thresholds and some facts learned from earlier work (for example a disputed month-end close that a sensitivity excludes). The store is on one machine with no backup; a private backup is a separate, unauthorised design. Git history kept (OD-0196) |

