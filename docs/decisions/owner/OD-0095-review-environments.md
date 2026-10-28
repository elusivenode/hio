---
id: OD-0095
title: "Owner instructs pre-built, per-review cloned uv environments for Codex reviewers in hiomux (after the H6 review finishes); reviewer authority, network default and repository write paths unchanged"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-review-env.md (owner's messages, verbatim, with Claude's question)
  sha256: 0adf6c678c038a8c4b76d890415da952c2fc4cb90a486c84616489db61a880f6
  date: 2026-10-28
  quote: "how can we assist by providing a good environment for its reviews, which it can extend."
applies_to:
  - path: ~/.hio-runs/bin/hiomux (outside the repository)
    revision: "new hash to be recorded in the corrections below; current 052a63f5… (OD-0088 correction 2)"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0072, OD-0077, OD-0094]}
---

# OD-0095: review environments for Codex

## What is authorised (after task CH6N finishes)

- **A base environment per locked dependency set.** hiomux builds it outside the sandbox from `uv.lock` at the
  assigned head, under `~/.hio-runs/envs/<hash>/`, and rebuilds it only when the lock changes.
- **A private copy per review.** Each Codex review gets a copy-on-write clone of that base as its own writable uv
  cache. It can extend it (install extra tools, network as now) without touching the base, other reviews or the
  Claude workers.
- **Afterwards:** a fresh `hiomux sa probe` and a reviewer boundary check; the new hiomux hash recorded here.

## Unchanged

- Reviewer authority.
- The network default (OD-0077).
- What a reviewer may write in the repository (`reviews/**`).
- Credentials boundaries.

## Corrections (append-only)

1. **2026-10-28, done (after CH6N finished).**
   - **hiomux changes** (backup `notes/hiomux.pre-review-env.bak`; one line replaced, the rest added):
     - `review_env` builds a base uv cache per `uv.lock` (keyed by its sha256) under `~/.hio-runs/envs/<hash>/`,
       outside any sandbox, with `uv sync --frozen --python 3.13`;
     - `prepare_review_cache` gives each Codex review a copy-on-write clone of it at
       `/private/tmp/hiomux-<run>-<task>-uv`, its `UV_CACHE_DIR`;
     - one reviewer-prompt line tells the reviewer the environment is there, that it may extend it, and to
       list what it adds.
   - **Unchanged:**
     - the sandbox profiles (`/private/tmp` was already writable in both);
     - the network default;
     - the reviewer's repository write paths and authority;
     - Claude workers (still the run's uv cache).
   - **Tests:**
     - base build 1.4 s; reuse 0.01 s; clone 0.12 s;
     - a fresh checkout synced **offline** from the clone and ran `tests/test_hio_assign.py` (27 passed) in 4 s
       in total;
     - `hiomux sa probe` ALL PASS after the change.
   - **New hashes:**

     | File | sha256 |
     |---|---|
     | `~/.hio-runs/bin/hiomux` | `25f7b2722daa70003b73e9f90513ba602f1129bb097129f2b8e8885c4230665f` (supersedes `052a63f5…`, OD-0088 correction 2) |
     | `~/.hio-runs/orch-prompt.md` | `d2ae1f8e130d4c8dba25414b40be000316868dbf1e614e9f83b74d23924d50c7` (now points to this correction) |
