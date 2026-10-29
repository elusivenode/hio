---
id: RESPONSE-REVIEW-2026-10-29-t0013-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-29-t0013-1-1]
reviewed_head: caf44dab923d32faaf462b15a79ca8dc7b677431
fix_commits: [b7517ee]
submission_head: self            # resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-29-t0013-1.md
created_at: 2026-10-29
---

# Remediation response: F-REVIEW-2026-10-29-t0013-1-1

> Written by the author on `feat/t0013` under OD-0132. A claim, not a verification. The finding stays open until a
> verification record closes it. REVIEW-2026-10-29-t0013-1 (NOT READY) is not yet received.

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| F-1 (medium): the probe scan still read ignored regular files | `b7517ee` | `tests/test_t0012_infra.py`: a `_tracked_probe_files()` helper (`git ls-files -z -- infra/tofu/probe`). The secrets scan reads only tracked files. **The same coupling in a second test is also fixed:** `test_there_is_no_backend_block…` globbed the working tree for `*.tfstate*`/`*.tfvars*` and now checks tracked names. A new `test_the_probe_scan_reads_only_tracked_files` asserts that no tracked probe file is a tfvars, state or `.terraform/` path | with an ignored `infra/tofu/probe/zz-review-check.tfvars` containing an email address **and** a `.terraform/` directory present, `tests/test_t0012_infra.py` gives 15 passed (on `caf44da`: 1 failure, the backend test); full suite **952 passed**; ruff and check_repo pass | the tests now need `git` and a checkout (true in CI and in hiomux checks); a file that is tracked by mistake is still scanned, as intended |
