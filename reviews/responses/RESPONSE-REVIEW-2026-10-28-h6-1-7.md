---
id: RESPONSE-REVIEW-2026-10-28-h6-1-7
author: claude/implementation-agent
findings: [F-VERIFY-2026-10-28-h6-1-6-1]
responds_to: VERIFY-2026-10-28-h6-1-6   # reviewer tip c59094885bd7d643ffef6d82ab06b90598524871 (tag reviews/VERIFY-2026-10-28-h6-1-6); received by OD-0112
previous_submission_head: 3d376ba11519a87dc5d802d96d3d75570c69c917
authorised_by: OD-0112, OD-0109, OD-0104, OD-0092
fix_commits:
  - 2393280   # published import inspected, never certified (tools/hio_receive.py, tests), hiomux task W4, checked at 2393280
test_commits: []
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-7.md
created_at: 2026-10-29
---

# Remediation response 7: a published import is inspected, never certified

> **This is the author's claim, not verification.** F-VERIFY-2026-10-28-h6-1-6-1 stays **open**. H6 is still
> unactivated. The matching wording is in the proposed clarification on `proposal/harness-0.9` (`c711f51`,
> **proposed, not adopted**, OD-0112).

**The defect.** For an import of T already on remote `main`, the inspection path reported `received` without checking
the step 5.8 trailers or the history beneath the import.

**The fix (`2393280`):**
- **Inspection only.** An import found on remote `main` is history this run did not build. The status is
  `already on remote main: inspection PASSED (not a receipt by this run; …)`, or a stop with `inspection FAILED`. Only a
  receipt built in the same invocation is ever `received`. The output states that the commits before the import,
  including whether its parent was a cut point, are not verified. Nothing is pushed to `main`; the tag is ensured only
  after a pass.
- **The full step 5.8 trailer set,** parsed line by line:
  - exactly one each of `Review-Id`, `Review-Branch`, `Review-Commit`, `Reviewed-Base`, `Reviewed-Head`,
    `Assignment-Source`, `Reviewer-Report`, `Inventory`, `Receipt-Checks` and `HIO-Actor`;
  - the first five, `Inventory: complete` and the normalised `Assignment-Source` equal this run's values;
  - one `Record:` line per inventory file and no others, each blob equal to T's file and remote `main`'s, and each
    sha256 equal to T's file;
  - the import has a single parent;
  - `tools/check_repo.py trailers <import>^1 <import>` passes.
- The round-2 content checks and round-3 recovery rules are unchanged.

**Tests (listed in `2393280`'s message):**
- **New:**
  - Codex's probe: an outside push of a poisoned parent and a bare import exits non-zero and never says `received`;
  - parametrised missing and mismatched trailers, and a duplicated trailer;
  - a wrong `Record:` sha256, a wrong blob, and an extra `Record:` line;
  - the trusted trailers check;
  - a full-trailer positive variant.
- **Changed, status word only:** three reruns of already-published receipts now expect `inspection PASSED`. The helper
  `hand_built_import` carries the full trailer set, so the round-2 and round-3 adverse tests still stop on the content
  checks they target. Response 6's published positive test now expects a failed inspection, because its import lacks
  the trailers.

**Evidence:**
- `2393280` passed Claude's independent `hiomux check`: `check_repo`, trailers from `3d376ba`, `uv run pytest -q`
  **543 passed**, and both of CI's lint commands. It is integrated by fast-forward.
- **The tests catch the defect:** with `2393280`'s test module on `3d376ba`'s receiver, 24 tests fail, including
  Codex's probe.
