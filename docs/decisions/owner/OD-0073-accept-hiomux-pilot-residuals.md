---
id: OD-0073
title: "The owner accepts the hiomux pilot's stated residual risks (Fable condition C4) and waives Fable's re-verification of the fixes for C1–C3 and C5; the Codex CLI test instruction recorded; nothing in the harness changes"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-hiomux-signoff-and-acceptance.md
  sha256: 56e1958f67194f55e3ef0ddfc28b421fd0b6ad083044b47b40f423632bcbfed4
  date: 2026-10-28
  quote: "I accept at this juncture.  no need for fable."
applies_to:
  - path: ~/.hio-runs/bin/hiomux (outside the repository)
    revision: "sha256 752d2ceca2460a73e59749530e75ae9cecbec71be654a3ef15d973fd04e107ab"
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 52fa861a80103355dfa9975d21c18faa4cbdb4b82df4f27f08235b2ac884bded"
  - path: ~/.hio-runs/notes/codex-cli-assessment-2026-10-28.md (outside the repository)
    revision: "sha256 104685b9f92a6b917ef051fb711bb26f82ef163ac113af66276d82106dbc2119"
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], open_decisions: [Q-014], ods: [OD-0072]}
---

# OD-0073: hiomux pilot residuals accepted

## Owner actions (verbatim in the source file)

1. **"I would like to get this tmux work done first."** This message asked for:
   - Fable's sign-off on the initial architecture and design;
   - a test of the Codex binary across models and reasoning strengths, assessed against the Codex
     documentation.
2. **"I accept at this juncture. no need for fable."** This answered Claude's question about Fable
   condition C4: the owner accepts the stated residuals in writing, and declines Fable's
   re-verification of the C1–C3 and C5 fixes.

## What preceded the acceptance

**Fable's review (same-vendor, advice; operating model §10).**
- First pass: FIT WITH CHANGES (3 high, 9 medium, 10 low).
- Second pass: **SIGNED OFF WITH CONDITIONS** for the architecture and design as a pilot, with
  conditions C1–C5 before real HIO work.

**The conditions, and what Claude did:**

| Condition | What Claude did (claimed; tested by Claude, not re-verified by Fable) |
|---|---|
| C1 (N1: unsandboxed git in a worker repository can run a worker-planted command; N2: workers could write `~/.claude` settings, hooks and skills, and the shared uv cache) | **Git:** no git runs inside a worker's clone once a worker has used it; commits are read through git alternates in the main repository. **Writes:** narrowed to Claude's runtime directories and a per-run uv cache. **Detection:** an attempt fails if the MCP, hook or permission keys of `~/.claude.json` change. **Environment:** workers get an allowlisted environment. **Probes:** Fable's fsmonitor attack, replayed, created no marker; writes to settings, hooks, skills, `CLAUDE.md` and the shared caches were all denied |
| C2 (N3: the shared `.git/objects` was deletable) | **Clones:** a `git clone --shared` per worker; the main `.git` is not writable. **Probe:** writes to objects and refs were denied |
| C3 (N5: orphaned model processes; N6: the reviewer commit path) | **Process groups:** recorded and killed on stop, reap and reset; `spawn` refuses while one is alive; tested. **Reviewer commit:** built in the main repository from reported bytes (only reported files, each in the contract, each hash-matched; no deletions, no hooks); refusals tested on synthetic data |
| C4 (the owner's written acceptance of the residuals) | **Accepted by this record** |
| C5 (completion-report data for Codex reviews) | `result.json` records the review branch tip and each file's sha256 |

**Accepted residuals:**
- HTTPS stays open, because the model APIs need it.
- `uv run pytest` runs code the worker wrote, inside the sandbox.
- A worker can tamper with the run ledgers and its own clone. Ledgers are operational evidence,
  never authority.
- Transcripts under `~/.hio-runs` hold what workers read. Keep licensed data out of briefs and
  contracts.
- Commits are imported through git alternates.

**Codex CLI assessment** (codex-cli 0.164.0; the assessment note, by hash above):
- **Models and effort:** 11 model and effort pairs were run; the applied settings were verified from
  Codex's own session records.
- **Effort:** the CLI accepts a level a model does not list, so hiomux validates levels.
- **`resume`** inherits nothing, so every flag is re-passed.
- **`workspace-write`** has no network, and `.git` stays read-only, so the runner commits for the
  reviewer.
- **User MCP servers** block headless runs, so Codex runs with `--ignore-user-config`.
- **Overhead:** about 14–15k input tokens a call.
- **Independence holds:** a real Codex reviewer refused a smoke task, because OD-0072 assigns no
  review.

## Scope

hiomux may be used for HIO work under its protocol, with these residuals accepted. Each use stays
inside existing authority: a task card and OD for the work itself, and for any Codex review an
owner-authored assignment. The tool remains outside the repository.

## Not authorised or changed

- **Harness:** no change to `AGENTS.md`, the operating model, templates, skills, hooks, CI or
  `tools/`. Bringing hiomux into the repository is harness-0.9 Phase B work (Q-014) and needs its
  own authorisation.
- **Fixes not independently verified:** the C1–C3 and C5 fixes have not been independently
  verified. The owner chose not to have Fable re-verify them. That is an owner choice, not a
  verification.
- **No review assigned:** no Codex review is assigned. An end-to-end Codex review smoke test needs
  an owner assignment.
- **T-0009 unchanged:** its findings are still open, and its pending owner decisions are untouched
  (push and PR, verification assignment, D7).

## Corrections (append-only)

None.
