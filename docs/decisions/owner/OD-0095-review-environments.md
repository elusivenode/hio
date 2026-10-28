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
