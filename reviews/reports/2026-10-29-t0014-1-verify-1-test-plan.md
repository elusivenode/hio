---
id: VERIFY-2026-10-29-t0014-1-1-TEST-PLAN
title: T-0014 remediation verification test plan
status: in_review
created_at: 2026-10-29
---

# Fixed plan before reading the author response

Assignment: `docs/decisions/owner/OD-0134-accept-t0013-verify-t0014-build-t0015-distil.md`, item 4, corroborated by its Assigned reviews row. Base `13d2ea5efeeacc22289a0e41ecbf6c114a4a2d8a`; head `e0aaa4d9648b153dd37afd1e27c810439324063c`; branch `review/t0014-1-verify-1-codex`. Original review: `REVIEW-2026-10-29-t0014-1` at reviewer branch `c4ecac2c6ed6fad54171672788cee86452f17618f`.

1. Check F-1 directly: a rebuild must compare to the release selected by the cutoff pin, including when two valid releases for one dataset coexist. Confirm the pinned hash and stored bytes govern the result; a different rebuilt release must fail.
2. Check F-2 directly: successful rebuild must require a present running code reference that equals the code/lockfile pin. Missing and mismatched references must fail, including the CLI default path.
3. Inspect the base-to-head diff and relevant P-3 path for adjacent regressions. Recheck P-1 to P-4 against the task card and original review, including the external finality limitation under HIO-ADR-0012 §4.3.3–4.3.4, inactive consumer template, and no changed return math, ADR, approved standard, manifest, or `s1b1.py`.
4. Run focused T-0014 tests, the full pytest suite in the clean checkout, Ruff where changed, and `tools/check_repo.py`. Investigate a failure only as needed to distinguish a regression from the known ignored `.terraform/` issue.
5. Record exact commands, evidence, verdict per finding, limitations, and any new findings. Write navigation rows and reviewer handoff; do not alter finding states in the index, since §6.2 step 5.12 is a later owner-authorised reconciliation.

No live data source, Azure operation, workflow activation, real release, PR, commit, or push is in scope.
