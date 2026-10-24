---
id: REPORT-2026-10-24-s1a-1-build-addendum
title: Independent S1a build-check addendum
status: reviewer_opinion
reviewer: codex/reviewer
reviewed_head: 98e6a8e08fca8b28241d9e4e7c04c181d75f1eef
created_at: 2026-10-24
---

# Build-check addendum to REVIEW-2026-10-24-s1a-1

The immutable [review record](../records/REVIEW-2026-10-24-s1a-1.md) reports that a fresh
`uv sync --locked` could not be run before the record was committed because the sandbox denied
access to the default uv cache. During the reviewer-only commit, the local pre-commit hook
created `.venv` in this isolated worktree, built `hio` and installed 11 packages. I then ran
`uv sync --locked --offline` with permitted cache access: **12 packages resolved, 11 checked**.

Using that worktree-specific Python 3.13.3 environment, I reran `pytest -q` (**150 passed**),
`ruff check .` (**pass**), `ruff format --check .` (**47 files formatted**) and
`python tools/check_repo.py` (**0 problems**). No lockfile or tracked file changed. This
strengthens the local build evidence; it does not change the seven findings or the
**REQUEST CHANGES** verdict. Remote GitHub CI was not independently checked.
