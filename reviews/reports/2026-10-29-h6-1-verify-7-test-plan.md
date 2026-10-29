---
id: VERIFY-2026-10-28-h6-1-7-TEST-PLAN
status: fixed_before_author_response
reviewer: codex/reviewer
assignment: docs/decisions/owner/OD-0113-assign-h6-verification-7.md on main
reviewed_base: 3d376ba11519a87dc5d802d96d3d75570c69c917
reviewed_head: 655335c83ef35814de1c08719ec3e2a80eb2e1a4
---

# Verification 7 test plan, fixed before author response

Role: independent Codex reviewer. H6 status: `in_review`; no activation or approval. OD-0113 on `main` is the assignment source. The checked-out review branch is `review/h6-1-verify-7-codex` at the assigned head; public HTTPS tips for `phase-b/h6` and `proposal/harness-0.9` match the assigned revisions, and the base is an ancestor. The `main` Assigned reviews row agrees with OD-0113. Governing rule: approved operating model §6.2 as amended by harness-0.9b. Proposal §6.1 at `c711f51485435e3ef218c8a2fea3c6b952098399` is a consistency target only.

1. Inspect the assigned base-to-head diff and the response as an unverified claim. Trace the published-import path and confirm it never pushes `main`, never says `received`, and distinguishes inspection pass from receipt completion. Check its result and exit behavior on inspection failure.
2. In disposable local Git origins, test a legitimate already-published import and adverse variants: absent and incorrect values for every §5.8 trailer (`Review-Id`, `Review-Branch`, `Review-Commit`, `Reviewed-Base`, `Reviewed-Head`, `Assignment-Source`, `Reviewer-Report`, each `Record`, `Inventory`, `Receipt-Checks`, `HIO-Actor`, and agent `Co-Authored-By`); a missing, extra, or mismatched `Record` line; a bad `check_repo.py trailers` result; and a poisoned commit before the import. Verify the receiver reports that pre-import history was not verified and never certifies an invalid import as received. Verify record hashes against both T and `main` and the tag relationship.
3. Recheck no regression of F-REVIEW-2026-10-28-h6-1-1 through -4 and F-VERIFY-2026-10-28-h6-1-3-1, -4-1 and -5-1. Include adverse accepted/status rows, an existing finding-state rewrite, duplicate target assignment, blank-separated finding rows, refused index diff disclosure, local-ahead history, and existing-import README mismatch under approved §6.2. Use prior reviewer records as expectations, not author assertions.
4. Compare the receiver's behavior to the proposed clarification §6.1 at the fixed proposal revision: same-invocation receipt, tag-only and disposable-branch recovery, local-ahead stop, inspect-only published imports, and remote cut-point/commit-set guard. Record consistency without treating the proposal as adopted.
5. Run the 543-test baseline with `uv run pytest -q -p no:cacheprovider`, CI's exact local lint commands `uv run ruff check .` and `uv run ruff format --check .`, `git diff --check <base> <head>`, and `uv run python tools/check_repo.py` after writing all review files. Do not read a source dataset or write outside `reviews/`. Record the independent result and limitations of any test fixture.

Write a verification record with an exact bold outcome token for every assigned finding, the verdict, evidence and limitations. Write a reviewer handoff with the required completion block. Leave review files uncommitted for the runner, report each added file and sha256, and open no PR.
