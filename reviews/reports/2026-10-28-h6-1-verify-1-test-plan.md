---
id: REPORT-2026-10-28-h6-1-verify-1-test-plan
title: Independent test plan for VERIFY-2026-10-28-h6-1-1
status: current
owner: codex/reviewer
created_at: 2026-10-28
---

# VERIFY-2026-10-28-h6-1-1: test plan

Fixed before reading the author's response or handoff. Source: OD-0097 on `main`, the matching assigned-review row, the received REVIEW-2026-10-28-h6-1 record (OD-0096), approved operating model §6.2 on `main`, and harness-0.9 proposal §6.1 at `2df83b4` as the H6 design. The verification covers `9e07b8b1493a4b4dca2a7d1eb3cf6e7de3f8f33c..ab0288fe57fb2ae9100c989142102445e5046bc5`. The latter is the current checkout and the public `phase-b/h6` tip; the base is an ancestor. OD-0097 and the index agree; no conflicting owner assignment was found in those sources or the owner message.

1. Read the fixed response and compare each claim to its original finding, the implementation diff, and independent reproductions. For F-1, an unsupported `accepted` row with negated prose and unrelated scope must be refused through the receipt path. For F-2, a negated or quoted `verified_closed` must not support Class S; an affirmative outcome at the reviewed head must. For F-3, an active same-target, same-scope assignment must be refused by the CLI. For F-4, a valid later-finding Class S transition must work against the real index shape while malformed transitions still fail. State one of `verified_closed`, `remediation_rejected`, or `open` for each.
2. Inspect both changed tools and tests against §6.2 steps 1, 3, 4, 4a, 5.0–5.11 and H6 §6.1. Independently exercise the nine H6 failure categories with disposable local Git fixtures or direct pure-function probes as appropriate: moved tip, wrong assignment head, extra and missing files, disallowed path, hash mismatch, duplicate/conflicting receipt, incorrect index transition, stale target, and interrupted receipt. Check nonzero outcomes and reconcilable state. Verify the final recheck and recovery behavior.
3. Run a valid dry run against a disposable bare origin and compare remote refs before and after. Inspect all push paths to verify `main` cannot be pushed without `--publish`. Verify that scope, assignment and repository checks execute from `main` and have not been weakened.
4. Run the full pinned test suite and confirm the assigned 490-test baseline. Review the changed tests for meaningful assertions. Record exact commands, outcomes, limitations, and any regressions in an immutable verification record. Write only Markdown under `reviews/`; add the reviewer handoff and index rows as appropriate. Leave the files uncommitted and unpushed per the runner's instruction; report their sha256 values.
