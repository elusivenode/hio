---
id: OD-0072
title: "Pilot hiomux, a tmux orchestration stack (an Opus orchestrator, up to five Sonnet workers, Codex panes, file-based logs), kept outside the repository, with a same-vendor review by Fable; nothing in the harness changes"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-hiomux-pilot.md
  sha256: 25aa80b35a32b7608c13fbbddd6cd4a8bfdb1ae128b89c0060384f6f033ef9b7
  date: 2026-10-28
  quote: "i am happy with this.  have fable peform and independent review."
applies_to:
  - path: (none in this repository; the pilot lives in ~/.hio-runs)
    revision: 950cce7cbe3c20b4ca4183ee619afbff646c4d70   # main when recorded
related: {adrs: [HIO-ADR-0008], tasks: [T-0009], findings: [], open_decisions: [Q-014]}
---

# OD-0072: hiomux orchestration pilot

## Owner action

Three messages, verbatim in the source file. The owner:
- asked for a tmux workflow for HIO: an Opus 5.5 orchestrator (model overridable) in a full-window
  pane in the first tab; up to five Sonnet workers, and any Codex sessions, as panes in a second
  tab; Codex fired only by the orchestrator;
- stated that the owner types only into the orchestrator pane, that the other sessions communicate
  with the orchestrator, and that files and data structures must log sessions, findings, failures
  and results;
- answered Claude's proposal with "i am happy with this", asked for an independent review by Fable,
  and asked for one command, `hiomux`, that starts a new orchestrator session under the repository's
  harness and hooks, with the second tab starting as one empty worker pane.

The proposal the owner accepted (summarised; Claude's messages in the same session):
- **Files, not keystrokes:** workers run headless and report through files.
- **Isolation:** each worker gets its own git worktree; parallel work needs disjoint file sets.
- **Context:** one brief, written by the orchestrator only.
- **Logs:** append-only JSONL ledgers for events, issues, failures and decisions. Worker-raised
  problems are "issues", never "findings".
- **Codex:** a Codex verification or review is launched only after the owner assigns it in an
  owner-authored source.
- **Pilot:** kept outside the repository. Any move into the repository goes through harness-0.9
  (Q-014) Phase B with its own OD.

## Scope authorised

Bounded and reversible:
- build and test the tool under `~/.hio-runs` (the script, `PROTOCOL.md`, run directories);
- add a symlink at `~/.local/bin/hiomux`;
- run a same-vendor review by a Fable sub-agent.

Smoke tests may create throwaway local worktrees and branches, which are removed afterwards.

## Not authorised or changed

- **Repository and harness:** no change to `AGENTS.md`, the operating model, templates, skills,
  hooks, CI or `tools/`.
- **Status of the tool:** hiomux is not part of the harness and holds no authority. Its logs are
  operational evidence, never records.
- **Review independence:** the Fable review is a same-vendor dry run (operating model §10). It is
  advice, not an independent review.
- **Codex:** no Codex review is assigned, and the orchestrator may not assign one.
- **T-0009:** nothing changes. Its open findings and its pending owner decisions (push, verification
  assignment, D7) are untouched.

## Corrections (append-only)

None.
