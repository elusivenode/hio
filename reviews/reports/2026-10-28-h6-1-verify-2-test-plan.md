---
id: REPORT-2026-10-28-h6-1-verify-2-test-plan
title: Independent test plan for VERIFY-2026-10-28-h6-1-2
status: current
owner: codex/reviewer
created_at: 2026-10-28
---

# VERIFY-2026-10-28-h6-1-2: test plan

Fixed before reading the author response or handoff. The owner message preserved at `docs/history/2026-10-28-owner-assign-h6-verify-2.md` on `main`, OD-0099 and the assigned-review row agree: review `ab0288fe57fb2ae9100c989142102445e5046bc5..5b9e49cae02da18fd019cbf4486760306bab098e` on `review/h6-1-verify-2-codex`. The checkout and public `phase-b/h6` tip equal the assigned head, and the base is an ancestor. The received original review and first verification records define the findings. Approved operating model §6.2 governs; harness-0.9 proposal §6.1 at `2df83b4` defines the unactivated H6 design. No conflicting owner assignment was found in the owner message, OD-0099 or `main`'s Assigned reviews table.

1. Compare each response claim to the diff and independently probe F-2's negated and quoted outcome cases, alongside a true affirmative outcome tied to the finding and reviewed head. Probe F-3's active same-target assignment with status `assigned; not received`, as well as inactive and identical-scope variants. Probe F-4's original six-cell ADR-0012 finding row and a later seven-cell finding row against the real index. Probe the F-1 fix regression: an otherwise valid Assigned reviews row whose scope merely mentions `accepted` must be allowed while a false accepted state remains refused. Record a separate exact bold outcome token for each of F-2, F-3 and F-4, and an explicit regression result.
2. Review both changed tools and tests for new regressions against the original REVIEW-2026-10-28-h6-1 assignment: §6.2 steps 1, 3, 4, 4a and 5.0–5.11; the nine H6 failure categories; no remote write during dry run; no `main` push without `--publish`; unchanged use of `main`'s check tools. Independently exercise representative success and failure cases with disposable local Git fixtures, including final recheck and interrupted receipt recovery.
3. Run the full frozen suite, check the assigned 501-test baseline, and run CI's exact `uv run ruff check .` and `uv run ruff format --check .` commands. Record exact results and limits. Write only Markdown under `reviews/`: immutable verification record, this plan and reviewer handoff; leave all files uncommitted and unpushed under the runner instruction, and report every added file's sha256.
