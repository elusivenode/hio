---
id: T-0018
title: "A repeatable local cash rebuild from retained receipts, for a stated history window"
status: accepted   # OD-0148 correction 1 at acf1487, merged into main as a881882; no Codex review
accepted_by: OD-0148
owner: owner
assignee_role: "implementation engineer (Claude orchestrator); independent reviewer: Codex, if the owner assigns one"
created_at: 2026-11-04
updated_at: 2026-11-04
authorised_by: OD-0148
base_revision: ac36cbf2520cb38880c80baa093b512a513eb981
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0014 (accepted), T-0017 (accepted)]
  blocks: ["base-camp criterion 3 (proposed): a repeatable rebuild"]
---

# T-0018: repeatable cash rebuild

> **Authorised by OD-0148.** The first rebuild (`docs/evidence/b3/cash-rebuild-1.md`, on PR #80) showed the build can't read the real F1 receipt: it runs back to 2011, past the cited calendars, and needed a window applied in a throwaway driver.

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| R-1 | `vintage_store(earliest=...)`: rows labelled before the window aren't read; the receipt keeps them; dates inside the window still refuse if a calendar doesn't cover them | old rows refuse without a window; the rows built with a window are byte-identical to a build whose file never held them |
| R-2 | `build_releases(history_from=...)` states the window in each manifest; with none, a manifest is unchanged | the same test; the existing release tests and pinned hashes pass |
| R-3 | `tools/cash_rebuild.py`: read-only copy from the evidence store, build under the genuine gate, report, summary. Refuses an output inside the repository or not empty, and a dirty tree. Provider errors are named by type | `tests/test_t0018_cash_rebuild.py` |

## Exclusions

Any change to return mathematics, a cash spec, the classifier or the capture path; historical calendars; running the tool, which OD-0147 covers for a 2026 window; any new dependency.

## Submission (filled by the implementer)

Branch `feat/t0018`, built by the orchestrator. Submitting approves nothing.
