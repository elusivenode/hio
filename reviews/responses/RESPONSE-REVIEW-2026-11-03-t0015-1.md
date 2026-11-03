---
id: RESPONSE-REVIEW-2026-11-03-t0015-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-11-03-t0015-1-1]
reviewed_head: 3d259d34772f0876c8cb90c61bf73b1e80ece244
fix_commits: [cf50736]
submission_head: self            # resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-11-03-t0015-1.md
created_at: 2026-11-03
---

# Remediation response: REVIEW-2026-11-03-t0015-1

> Written by the author on `feat/t0015` under OD-0137, from the receipt merged as `7b362ee`. A claim, not a verification. The finding
> stays open until a verification record closes it.

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| F-1 (medium): an inconclusive properties result was treated as proof of existence | `cf50736` | `src/hio/storage/azure_blob.py` `_key_exists`: the result must pass `_info` (version id, UTC write time, size) and its `name` must equal the key; otherwise it is False and the original 403 is raised. `tests/test_t0015_backend.py`: a seven-case regression test | The seven new cases fail on the pre-fix code (7 failed, 23 passed) and pass after it. Focused backend tests: 90 passed. Full suite: 1007 passed. `ruff check`, `ruff format --check` pass | Offline fakes only. That a real current-version read carries `name` and `version_id` on Azure is unproved here: the SDK source sets `name` (`azure/storage/blob/_blob_client.py`). If Azure omitted a field, the result is the original 403, which fails closed |

**Not addressed, and outside this finding:** `BlobStagedWrites.commit` has no rollback, and a storage exception escapes `run_capture`
without a failed run record. Mapping the 403 does not change that. It is put to the owner in the proposed
`docs/evidence/S1B1-authorisation-B-revision-1.md` (PR #60).
