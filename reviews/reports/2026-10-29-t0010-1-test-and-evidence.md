---
id: REPORT-2026-10-29-t0010-1
title: T-0010 independent review test and evidence report
status: complete
review: REVIEW-2026-10-29-t0010-1
reviewed_head: f345d1ea1498c451fe91f09bbddf327f0fd54ea8
---

# Test plan fixed before author handoff

Assignment: OD-0120 Assignment 1 on `main`; base `150f8136bf0cd803746f997e37e3365e2638f8b7`, head `f345d1ea1498c451fe91f09bbddf327f0fd54ea8`, branch `review/t0010-1-codex`. Scope is exactly its Assignment 1. The base is an ancestor of the head, and public `ls-remote` confirms the fixed head.

1. Read the changed implementation against T-0010 W-1 to W-4, OD-0115/0117/0118, HIO-ADR-0012 §4.3.3–4.3.4 and the release standard; derive counterexamples for network boundary, write-once storage, capture refusal, C1–C7 and finality.
2. Check the five dataset rights records against OD-0116 correction 1, OD-0118 and the T-0002 matrix. Confirm conditions and release notices, and that blocked third-party data remain denied.
3. Check that no path can perform live capture without an explicit `LIVE_AUTHORISATION`, and that `.github/workflows/` has no enabled schedule. Check the proposed workflow's permissions and wiring without running it.
4. Run `tools/check_repo.py`, deliberate network and Azure-import boundary probes without editing the work under review, CI's exact lint commands and `uv run pytest`. Compare the test count with the assigned 747 baseline.
5. Re-run or inspect T-0009 A-1 to A-11 and verify the four S1a `data.csv` SHA-256 values against their pinned test evidence; look for any regression caused by this diff.
6. Record independent observations, untested limits, findings and readiness at the fixed head. Do not treat author completion claims as evidence.

## Results

| Check | Independent result |
|---|---|
| Assignment integrity | OD-0120 Assignment 1 agrees with the owner's verbatim `docs/history/2026-10-29-owner-assign-t0010-t0011-reviews.md` and the Assigned reviews row on `main`; no conflicting owner-authored assignment found there. Checkout head and public `ls-remote` both equal the assigned head; base is an ancestor. |
| Full suite | `uv run pytest -q`: **747 passed in 61.80s**, matching the assigned baseline. No test contacted a data source. |
| Focused regression and guards | `uv run pytest -q` on the S1a four-hash fixture, T-0009 capture/releases/schedule, T-0010 notices, and network/Azure import guards: **185 passed in 4.90s**. The S1a test asserts all four pinned `data.csv` SHA-256 values in `tests/test_f4_f7_acceptance.py`. The T-0009 A-1 to A-11 paths remain covered by the full suite and the focused checks; this review did not independently re-create every historical fixture. |
| CI commands | `uv run ruff check .`: pass; `uv run ruff format --check .`: 100 files formatted; `uv run --no-project --python 3.13 --with pyyaml==6.0.2 python tools/check_repo.py`: `PASS: 0 problem(s)`; `git diff --check` on the assigned range: pass. No package was added beyond the project's locked environment and CI's declared PyYAML tool dependency from the provided cache. |
| Rights records | Loaded genuine register: D1/D2/D3/D8/D9 are `owner_verified` by OD-0116 correction 1 and the gate permits the five intended capture, build, derived-store and `hio_internal` operations; the RBA and NY Fed parent records remain unverified and refuse. D5/D6 stay unknown in the matrix and are not given dataset rights records. The four S1b-1 release kinds have deterministic RBA and NY Fed notices in `quality_summary`, covered by `tests/test_t0010_notices.py`. |
| Live boundary | `LIVE_AUTHORISATION` is `None` at the assigned head, no production URL is configured, and `infra/workflows/s1b1-capture.yml` is outside `.github/workflows/`; no workflow there has a schedule. The fake-only CLI tests reproduce refusal before constructing transport, credential or store. |
| W-2 storage | The adapter requests a single conditional upload, verifies provider version metadata, exposes no overwrite or delete, and its fake tests cover conflict, versions and pagination. Azure WORM enforcement and whole-second `Last-Modified` suitability for C5 remain unverified pending the H4 S-6 provider probe; the author and OD-0119 both identify this gate. |
| W-4 finality | C1–C7 have synthetic positive and negative cases in the full suite. The finality implementation is currently an unwired computed verdict, and no release is labelled final. A separate execution-binding probe below found a false positive. |

### Counterexample 1: redirect leaves the approved origin

Two local loopback HTTP servers were started in one process. The first returned a 302 `Location` pointing to the second port. `HttpTransport(allow_loopback_http=True).get()` made a request to the second server and returned its `synthetic` body, with `final_url` at that server. In production the same `urljoin` step accepts any HTTPS origin. `run_capture` authorises the original publication's dataset ids before the request; it does not re-authorise the redirect target. No source data was read in this probe.

### Counterexample 2: unrelated GitHub job qualifies as finality evidence

On an in-memory synthetic store, a valid attempt with `Execution("github_actions", "1001", "1", "unrelated_ci_job", pinned_sha)` passed all C1–C7 checks and `vintage_finality(...).final` returned `True`. Separately, `Execution.from_environ` returned `platform: github_actions` for both a `ci` push on `main` and a `workflow_dispatch` on a feature branch; it checks only `GITHUB_ACTIONS`. The synthetic record had correct response bytes, dates and store time, so the difference was the untrusted run context. The current code never checks workflow, ref or event and only checks that `job` is nonempty.

## Limits

No Azure account, credential, provider probe, source website, real capture or CI run was used. The 2027 calendar remains a recorded W-5 gap and is outside OD-0120 Assignment 1. The review is at the fixed submitted head; later changes require a separately assigned verification.
