---
id: REPORT-2026-10-29-t0010-1-1
title: T-0010 remediation verification test and evidence
status: complete
review: VERIFY-2026-10-29-t0010-1-1
reviewed_head: 62adccd3cc1febff28b491f5564c9cae2f047202
---

# Test plan fixed before the author response or handoff

I am Codex, the independent reviewer. T-0010 remains `in_review`; this verification grants no acceptance or live authority. OD-0122 Assignment 1 on `main` fixes base `f345d1ea1498c451fe91f09bbddf327f0fd54ea8`, head `62adccd3cc1febff28b491f5564c9cae2f047202`, branch `review/t0010-1-verify-1-codex`, findings F-REVIEW-2026-10-29-t0010-1-1 and -2, and the no-regression, 790-test, and exact CI lint checks. The owner's verbatim message AV and the Assigned reviews row agree. The base is an ancestor, and public `ls-remote` and the checkout both identify the assigned head.

1. Compare the F-1 transport change with the original finding, T-0010 W-1 and fail-closed rights rules. Test same-origin redirects, cross-origin redirects and URL edge cases using local servers only; check that every fetched response retains an authorised request identity.
2. Compare the F-2 execution and C6 changes with HIO-ADR-0012 §4.3.3–4.3.4. Probe workflow, ref, event, job and missing or malformed environment values, including an unrelated workflow at the pinned SHA. Confirm false context cannot become finality evidence.
3. Inspect the whole base-to-head diff and check no regression against OD-0120 Assignment 1: W-1 to W-4, release notices, dataset rights, live refusal, workflow schedules, `check_repo` import allowances, T-0009 A-1 to A-11, and the four S1a `data.csv` hashes.
4. Run focused synthetic tests, the full `uv run pytest` suite against the assigned 790-test baseline, CI's exact `uv run ruff check .` and `uv run ruff format --check .`, `tools/check_repo.py`, and a diff whitespace check. Report actual counts and any limits.
5. Read the author's response only after this plan; verify each claim independently and record the outcome for each finding at the pinned head.

## Evidence and results

| Check | Independent result |
|---|---|
| F-1 redirect boundary | `HttpTransport.get` computes the original origin after a validated first fetch and computes each redirect target's origin before fetching it. Scheme, lowercase host and effective port must match. The two-server local tests show that a cross-port redirect and a leave-and-return chain raise `TransportError` while the second server sees no request; a same-origin redirect succeeds. URL policy also rejects credentials, a non-HTTPS target and file URLs before a second request. `final_url` remains the fetched URL. |
| F-2 execution boundary | `Execution.from_environ` records `github_actions` only when `GITHUB_WORKFLOW_REF` names the capture workflow in `GITHUB_REPOSITORY` on `refs/heads/main`, `GITHUB_REF` is main, and the event is `schedule` or `workflow_dispatch`; other runs become `other`. C6 independently requires the capture workflow suffix, main ref, allowed event, pinned SHA, numeric run identifiers and a job. The synthetic finality cases reject an unrelated workflow and push event, a non-main ref, missing fields and a legacy record; a valid scheduled or dispatched capture passes. The unrelated-job counterexample is rejected by its unrelated workflow and event. |
| Focused synthetic regression | `uv run pytest -q tests/test_t0010_transport.py tests/test_t0010_execution.py tests/test_t0010_finality.py tests/test_t0010_capture_cli.py tests/test_s1b1_capture.py tests/test_f4_f7_acceptance.py`: **197 passed in 5.53s**. All traffic in the transport tests is loopback; the other tests use synthetic fixtures. The S1a acceptance test compares all four generated `data.csv` SHA-256 values with its pinned hashes. |
| Full baseline | `uv run pytest -q`: **790 passed in 62.69s**, matching OD-0122's baseline. The test suite blocks non-loopback sockets. |
| Exact CI lint and repository check | `uv run ruff check .`: pass. `uv run ruff format --check .`: **101 files already formatted**. `uv run --no-project --python 3.13 --with pyyaml==6.0.2 python tools/check_repo.py`: **PASS: 0 problem(s)**. `git diff --check f345d1ea1498c451fe91f09bbddf327f0fd54ea8 62adccd3cc1febff28b491f5564c9cae2f047202`: pass. These are local executions of CI's commands, not a CI-run conclusion. |
| No regression in OD-0120 Assignment 1 | The base-to-head diff contains the transport, execution and C6 fixes, tests, and the response only. There is no change to Azure storage or authentication, capture orchestration, release notices, dataset rights, workflow files, `check_repo.py`, or S1a fixtures. `LIVE_AUTHORISATION` remains `None`; `.github/workflows/ci.yml` has push and pull-request triggers only, and the capture schedule remains in `infra/workflows/`. The full and focused suites pass T-0009 and S1a assertions. This is a non-live regression check, not an Azure provider or live-source validation. |

The supplied uv cache installed the project's 27 locked packages into this worktree's `.venv`; the exact CI-style `check_repo.py` command installed its declared PyYAML 6.0.2 dependency in a temporary uv environment. I added no package or tool to the cache. Public HTTPS `git ls-remote` was the only external read. No data source, Azure account, credential or production workflow was accessed.

The changed code resolves both assigned counterexamples at the pinned head. C6 remains a recorded assertion under the approved ADR; a sample CI-history audit and an H4 S-6 Azure provider probe are later gates. This verification does not claim those gates have run, and it does not authorise live capture or accept T-0010.
