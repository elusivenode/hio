---
id: RESPONSE-REVIEW-2026-10-29-t0014-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-29-t0014-1-1, F-REVIEW-2026-10-29-t0014-1-2]
reviewed_head: 13d2ea5efeeacc22289a0e41ecbf6c114a4a2d8a
fix_commits: [ede5763]
submission_head: self            # resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-29-t0014-1.md
created_at: 2026-10-29
---

# Remediation response: REVIEW-2026-10-29-t0014-1

> Written by the author on `feat/t0014` under OD-0132. A claim, not a verification. Both findings stay open until a
> verification record closes them. REVIEW-2026-10-29-t0014-1 (NOT READY) is not yet received.

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| F-1 (high): a rebuild could pass against a release other than the cutoff pin | `ede5763` | `tools/restore_exercise.py` `compare_rebuild`: a rebuilt release whose `content_sha256` differs from `pins["releases"][ds]` is `identical: false`, with the note "rebuilt hash differs from the cutoff pin", before any bytes are read; only the pinned path is then compared | `tests/test_t0014_recovery.py::test_a_rebuild_that_is_not_the_cutoff_pin_is_never_identical`: pins pointing at a different release give no identity. On `13d2ea5` it fails (the old code reported identical) | the regression case points the pin elsewhere instead of building a second real release for the dataset; the property tested is the same (comparison against the pin only) |
| F-2 (medium): success did not require the running code and lockfile pin | `ede5763` | `rebuild_and_compare`: `ok` requires `running_code_matches_pin is True`, so an absent or different reference is never `ok`. The CLI always checks the running code; `--check-running-code` is removed | `test_an_absent_running_code_reference_is_never_ok`; the CLI test now expects exit 1 when the pin (`test`) is not the running commit. Both fail on `13d2ea5` | `current_code_ref()` defines "the running code"; its lockfile coverage is as implemented in P-3 and unchanged here |

Full suite at the fix: **968 passed**, plus 1 local failure, T-0013's A-4 defect. An ignored `.terraform/` directory is
present on this machine; the fix is on `feat/t0013`, not on this branch; CI does not see it.
