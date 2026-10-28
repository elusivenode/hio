---
id: OD-0088
title: "Owner instructs a readable architect view for every interaction (after the OD-0087 runs finish), and the stress-test results as a private claude.ai page"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-architect-reading.md (typed by the owner, verbatim)
  sha256: db0274fb29359724486faa9fb0ae6e25b116d363d643d95524118491fe8d6900
  date: 2026-10-28
  quote: "yes to both, after the runs finish / this is for every interaction.  I need a better way to read the architect responses, even you I will interact with you. / the split view is very crowded and difficult to read."
base_revision: 1b52bc0
applies_to:
  - path: ~/.hio-runs/bin/hiomux (view and feed only), ~/.warp/launch_configurations/hio-workers.yaml (outside the repository)
    revision: "new hashes to be recorded in the corrections below; current hiomux e659b0bc…, launch config f3de17e9…"
related: {adrs: [], tasks: [], findings: [], ods: [OD-0081, OD-0085, OD-0087]}
---

# OD-0088: reading the architect

## What the owner authorised

Two yeses, both to take effect after the OD-0087 runs finish:
1. a change to hiomux's view so that architect responses are readable, for every interaction;
2. the OD-0087 answers and mechanical evidence delivered as a private claude.ai page. No grading.

## The design (Claude's, within that instruction)

- **No split.** The `hio-workers` launch configuration opens two full-width Warp tabs: `architect` and
  `workers & codex`.
- **A formatted terminal feed:**
  - wraps at word boundaries to the pane width;
  - a bold, coloured header per entry;
  - the question dimmed;
  - spacing between the question, the recommendation and the next step.
- **A local reading page.** `<run>/view/architect.html` is rewritten after every `sa` call. Newest first:
  - the full answer, rendered from markdown;
  - the question, folded;
  - the metadata.

  The page refreshes itself and has no network dependency.
- **Scope:** only the view and feed code. No change to the architect's boundary, prompts, identity, context or
  schema. Afterwards: `hiomux sa probe`, and the new hashes recorded here.

## Not authorised

- any change to the architect's behaviour or boundary, or to Codex's review path;
- grading;
- anything in the repository's harness.

## Corrections (append-only)
