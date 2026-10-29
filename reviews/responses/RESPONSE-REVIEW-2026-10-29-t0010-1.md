---
id: RESPONSE-REVIEW-2026-10-29-t0010-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-29-t0010-1-1, F-REVIEW-2026-10-29-t0010-1-2]
reviewed_head: f345d1ea1498c451fe91f09bbddf327f0fd54ea8
fix_commits: [08be64a, 42ed126]
submission_head: self            # resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-29-t0010-1.md
created_at: 2026-10-29
---

# Remediation response: REVIEW-2026-10-29-t0010-1, F-1 and F-2

> Written by the author on `feat/t0010` under OD-0121. This is a claim, not a verification. Each finding stays open
> until a verification record closes it. The review record itself is not yet received (receipt stopped at §6.2 step
> 5.3 on the record's `assignment` text; reported to the owner).

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| F-1 (high): cross-origin redirects bypass the approved request identity | `08be64a` (hiomux R1, checked `bb2a66a`) | `src/hio/sources/http_transport.py`: a redirect is followed only to the exact origin (scheme, lowercase host, effective port) of the original URL; any other raises `TransportError` naming both origins, before any request to the other origin | `tests/test_t0010_transport.py`: two loopback origins; the second server receives no request; same-origin redirect followed; leave-and-return refused at the first hop. On `f345d1e` the updated module has **6 failures** | a same-origin redirect to a different path is still followed (within `max_redirects`); the final URL is recorded in the attempt record |
| F-2 (high): a run from another GitHub workflow can become finality evidence | `42ed126` (hiomux R2b, checked `03292a5`; R2 superseded for a contract gap) | `src/hio/marketdata/runrecord.py`: `Execution` records `workflow_ref`, `ref`, `event` unaltered; the CI platform is recorded only for `<repo>/.github/workflows/s1b1-capture.yml@refs/heads/main`, `refs/heads/main`, and `schedule` or `workflow_dispatch`, else `other`. `src/hio/marketdata/finality.py` C6 requires the same, failing closed on any missing field; older records load but never pass C6 | `tests/test_t0010_execution.py`, `tests/test_t0010_finality.py` (different workflow, non-main ref, `pull_request`/`push`, missing fields, the reviewer's `unrelated_ci_job` case; positive `schedule` and `workflow_dispatch`); `tests/test_t0010_capture_cli.py` ENV updated. On `f345d1e` the new modules **fail to import** (2 collection errors, since the new fields do not exist there): evidence that the behaviour is new, weaker than per-test failures | C6 remains a recorded-assertion check; the CI-history audit (ADR-0012 §4.3.3) is still required for the soak sample |

Full suite 790 passed; `ruff`, `ruff format`, `check_repo` and trailers pass.
