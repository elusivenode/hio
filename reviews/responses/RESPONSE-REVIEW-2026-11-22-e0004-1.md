---
id: RESPONSE-REVIEW-2026-11-22-e0004-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2]
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
