---
id: OD-0085
title: "Owner instructs the orchestrator out of tmux and a two-pane read-only view (architect | workers and Codex) in a separate Warp window; hiomux and PROTOCOL hashes recorded; nothing in the repository's harness changed"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-hiomux-layout.md (typed by the owner, verbatim)
  sha256: 9590fd327c1bc180c9108ae165a73178fcc89f3882d96107fd57c94afbc8e14b
  date: 2026-10-28
  quote: "let's keep this session out of our tmux set up.  it just orcestrates hiomux"
applies_to:
  - path: ~/.hio-runs/bin/hiomux (outside the repository)
    revision: "sha256 fbc6085061310f3c2fc9f24bc16a3e545f50707fadbe58e60137e2cec1f9a552"
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 b4e81ff4832565c2d8df9071903eb82f1b4cabaf982fb50c26066deabbdc98bb"
  - path: ~/.warp/launch_configurations/hio-workers.yaml (outside the repository)
    revision: "sha256 f3de17e94ea9349e0777a1e0f836977839c5c862a59f909b6dcccec68b2b58d5"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0072, OD-0073, OD-0077, OD-0082, OD-0083, OD-0084]}
---

# OD-0085: hiomux layout, and the tool hashes

## Owner instructions (verbatim in the source file)

The owner could not switch tmux windows from Warp, because Warp intercepts tmux's keys. The owner then instructed:
1. a separate Warp window showing the workers;
2. "this session is the only one I will issue command to";
3. "keep this session out of our tmux set up. it just orcestrates hiomux";
4. in that window, "the architect in one pane and sonnet workers and codex review in a 2nd";
5. record the hashes and write the session handoff.

## What changed (outside the repository; tested by Claude)

- **The orchestrator runs outside tmux.** `hiomux up --no-orch` starts a detached tmux session `hio` with no `orch`
  window. `spawn` and `sa pane` start it if it is missing.
- **Window `view`, read-only, two panes:**
  - **left:** the architect feed, `<run>/view/architect.log`, holding every `sa` call with its question and
    answer;
  - **right:** the workers-and-Codex feed, `<run>/view/workers.log`. Every worker pane's output is copied there
    through `pipe-pane`, tagged by task id, with terminal escapes stripped.

  The processes stay in the hidden window `workers`.
- **How the owner opens it:** `hiomux view` attaches to `view`. The Warp launch configuration `hio-workers` runs
  it, in a new Warp window: `open "warp://launch/hio-workers"`.
- **The interactive architect pane is retired.** Consultations go through `hiomux sa ask` from the orchestrator,
  are logged, appear in the feed, and are summarised to the owner (OD-0081).
- **Tests:**
  - a dummy worker's lines reached the right-hand feed tagged `[T0]`, with colour codes removed;
  - one consultation reached the left-hand feed: "state your role and limits", 21 s, `gpt-6.1-sol`/`high`, no
    auto-loaded `AGENTS.md`; the answer matched identity v0.2.

## Hashes (the record G3 called for; the latest values)

| File | sha256 | Earlier records |
|---|---|---|
| `~/.hio-runs/bin/hiomux` | `fbc6085061310f3c2fc9f24bc16a3e545f50707fadbe58e60137e2cec1f9a552` | `752d2cec…` OD-0073; `436833b7…` OD-0077; `b5e341bb…` OD-0082; `8ca77587…` OD-0083 |
| `~/.hio-runs/PROTOCOL.md` | `b4e81ff4832565c2d8df9071903eb82f1b4cabaf982fb50c26066deabbdc98bb` | `52fa861a…` OD-0073; `2f947c59…` and `c8bac354…` OD-0077; `13e60010…` OD-0082 |
| `~/.warp/launch_configurations/hio-workers.yaml` | `f3de17e94ea9349e0777a1e0f836977839c5c862a59f909b6dcccec68b2b58d5` | new |

Backups of the versions replaced this session are in `~/.hio-runs/notes/`: `hiomux.pre-network.bak`,
`hiomux.pre-no-orch.bak`, `hiomux.pre-view.bak` and `PROTOCOL.pre-network.bak`.

**Still open:** the change to hiomux before OD-0077 (`752d2cec…` to `63c997b3…`) remains unexplained
(OD-0077, finding 1).

## Not changed

No repository harness, tool, CI or authority. hiomux remains outside the repository (harness-0.9 Phase B).

## Corrections (append-only)

1. **2026-10-28, run close.** The owner instructed "yes, close the run and clean up".
   - **Result:** run `20261028T043057Z-e4d8` closed (`summary.md`), the tmux session stopped, and the task clones
     removed.
   - **A gap in slice 1:** `cleanup` did not remove the architect's per-session checkouts and packages (81 MB).
     It now removes each session's `repo/`, `package/` and `tmp/`, and keeps the consultation records. The run is
     now 4.8 MB.
   - **New hiomux hash:** `e659b0bcca7960bba88e3ca89621af47df45850e8d427f87e6ca0dd280f2a1cd` **supersedes**
     `fbc60850…` above (backup of the prior version: none; the change is the eight-line block in `cleanup`).
   - **Unchanged:** `PROTOCOL.md` (`b4e81ff4…`) and the launch configuration.
