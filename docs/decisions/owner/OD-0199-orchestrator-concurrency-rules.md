---
id: OD-0199
title: "Owner adds three orchestrator rules to the hiomux start-up prompt and protocol: workers first, maximise concurrency, never block; new PROTOCOL hash"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-concurrency-rules.md (owner's messages, verbatim, with Claude's question)
  sha256: f05c67268dd055b8ee5b5c8591cce1dd31dccb9b48b9b38e84974eb7a81a92c7
  date: 2026-11-22
  quote: "Yes"
base_revision: e8d43a07ed3dabfc0f0ccfc76c011522d388d664
approved_revisions:
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 e4325793a1d00dbdc7e2aacfd9f58c36f0bc8a057184e181a4fde242447b8f90"
  - path: ~/.hio-runs/orch-prompt.md (outside the repository)
    revision: "sha256 28293b6ddd1b5c970b3bb14bca5166226bb48a1c0a79db70f76a8f0cfd12f954"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0072, OD-0086, OD-0111, OD-0184, OD-0198]}
---

# OD-0199: workers first, maximise concurrency, never block

Until now these lived only in Claude's auto-memory, which is not a record. `PROTOCOL.md` said "Five is a ceiling, not a target". The owner's instruction puts three rules into both files:

| Rule | Text |
|---|---|
| Workers first | Bounded implementation and test work goes to hiomux Sonnet workers. The orchestrator keeps the diagnosis on real data, runs on licensed workspaces, records, merges and owner reports |
| Maximise concurrency | Split each batch by file ownership into as many parallel tasks as have disjoint files, up to five at once. Only tasks that share files run in sequence |
| Never block | `hiomux wait`, CI watches, `sa ask` and long runs go to background subagents or background Bash |

## Hashes (the start-up check compares against these)

| File | sha256 |
|---|---|
| `~/.hio-runs/PROTOCOL.md` | `e4325793a1d00dbdc7e2aacfd9f58c36f0bc8a057184e181a4fde242447b8f90` (supersedes `25dfb779…`, OD-0184) |
| `~/.hio-runs/orch-prompt.md` | `28293b6ddd1b5c970b3bb14bca5166226bb48a1c0a79db70f76a8f0cfd12f954` (now names this OD as the PROTOCOL hash record) |
| `~/.hio-runs/bin/hiomux` | unchanged: `54fe4e863a1e48b101d3241e6506b4d873d21177a379996409f124151454ceac` (OD-0111) |

## Not authorised

Any change to the `hiomux` tool, the worker limit of five, worker isolation, or any authority rule. The rules change how authorised work is carried out, not what is authorised.

## Corrections (append-only)
