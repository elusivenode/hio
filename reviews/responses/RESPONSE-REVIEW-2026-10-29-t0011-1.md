---
id: RESPONSE-REVIEW-2026-10-29-t0011-1
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-29-t0011-1-1, F-REVIEW-2026-10-29-t0011-1-2, F-REVIEW-2026-10-29-t0011-1-3]
reviewed_head: 2cc7362b962a76b76a3100fbc241a7b204957619
fix_commits: [4f90f56ff7ab813ba9953fd597ecfcd643cb253b]
submission_head: self            # resolve with: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-29-t0011-1.md
created_at: 2026-10-29
---

# Remediation response: REVIEW-2026-10-29-t0011-1, F-1 to F-3

> Written by the author on `infra/t0011` under OD-0121. This is a claim, not a verification. Each finding stays open
> until a verification record closes it. The review record itself is not yet received (receipt stopped at §6.2 step
> 5.3 on the record's `assignment` text; reported to the owner).

| Finding | Fix commit(s) | What changed (files) | Evidence (tests, checks) | Residual risk or disagreement |
|---|---|---|---|---|
| F-1 (high): alert queries a table not written | `4f90f56ff7ab813ba9953fd597ecfcd643cb253b` (hiomux R3, checked `3b5b5b2`) | `infra/tofu/monitoring.tf`: `log_analytics_destination_type = "Dedicated"`; the alert query reads `StorageBlobLogs` directly (no `isfuzzy` union, no empty `datatable`), counting `PutBlob` under `catalogue/attempts/` | `tests/test_s1b1_infra.py`; the new tests fail on `2cc7362` (4 failed in the two infra test modules) and pass at the fix; `tofu validate` passes | the query's real behaviour is unverified until the workspace exists (B-1) and the deliberate-failure test runs (S1-A13) |
| F-2 (medium): no GitHub failure notification | same | `infra/tofu/README.md`: the GitHub notification setting for failed scheduled workflows, who must hold it (the owner) and its verification (the S1-A13 deliberate-failure test before the soak counts). I-5 is not narrowed | text-level README test | depends on an owner-side GitHub setting; verified only in the soak |
| F-3 (medium): `tofu output` ignores the external state | same | `infra/tofu/bootstrap/README.md`: the same `-state=<STATE_DIR>/bootstrap.tfstate` on plan, apply and output | `tests/test_t0011_bootstrap.py` checks every runbook command carries the same `-state` | none known |

Full suite 442 passed; `ruff`, `ruff format`, `check_repo` and trailers pass; `tofu validate` passes for both modules.
