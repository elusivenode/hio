---
id: HANDOFF-2026-11-22-e0004-eodhd-account-switch
date: 2026-11-22
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator)
work_status: "E-0004 ran (not distinguished), reviewed NOT READY (two high findings, one remediated in files); EODHD s3 taken (revisions not explained); CPI first-release check tooling built, failing on real layouts"
base_revision: c6886d9e50d034f3a21cb57fa5d736e2a078592c
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-e0004-eodhd-account-switch.md
work_card: T-0023
stream: s1b1
---

# Handoff: E-0004, EODHD stability, account switch

> A dated snapshot. **Not a decision.** Written at 91% of the 5-hour usage limit, before the owner changes Claude account. It follows `2026-11-22-restart-delegation-t0023-review.md` and holds no licensed-derived value.

## Done (OD-0188 to OD-0197)
- **BLS CPI:** `bls_cpi` owner-verified (OD-0188). One download under OD-0189 and its correction 1: the API returned 503 twice, so the flat file was used instead (16 requests in all). It gave 293 release dates, 2002 to 2026, with the October 2025 gap. A 10-release sample check found 20 of 20 levels equal.
- **E-0004 (inflation acceleration and duration's downside benefit):** preregistration adopted at `067bd7b` (OD-0190). Step 1 and step 1b passed their bars. Step 2 ran once (OD-0191): **not distinguished** in every block length and sensitivity. Readings only are in `docs/evidence/e0004/result-1.md`; the numbers are local.
- **IEF NAV:** the owner's browser download, read by a new iShares reader. C1 and C2 pass for IEF; C5's audited-NAV row fails (`docs/evidence/t0023/corroboration-2.md`).
- **Architect (3 more consultations):** E-0004's draft (adopted with its tightening), what follows E-0004 ("park the line; return to factors"), and the EODHD plan (start with SPY only; no style factors; the risk is circular validation). **Two consultations have passed the review threshold:** `performance-review-1.md` is due.
- **Codex review of E-0004 (OD-0192, OD-0195):** **NOT READY.**
  - **F-1, high:** the first-release CPI rule isn't established.
  - **F-2, high:** EODHD-derived measurements were published in public evidence.
  - **F-2 fixed in the current files** (PR #122). **The owner keeps the git history** (OD-0196).
  - Receipt went through two tips; the received tip is tagged `-r2`.
- **T-0023's two findings are reconciled to verified_closed** (OD-0193). T-0023 is not accepted.
- **EODHD (owner subscribed: EOD Historical Data, the same plan):** `s3` taken for SPY, IEF and BIL (OD-0194). Stability against `s2` reads **revisions not explained**: a SPY ex-date moved, IEF closes re-rounded or revised, BIL payment dates filled in. Every series must pin its snapshot.
- **hiomux:** run `20261103T065037Z-3d12` closed and cleaned (2.5 GB freed). Run `20261121T232821Z-7052` is open, with W1, W2 and C2 to C3 done. Usage is visible through `~/.hio-runs/bin/statusline.sh` (writes `~/.hio-runs/statusline.json`), set in the project's local settings.

## In flight at the switch
| Item | State | Next |
|---|---|---|
| PR #122 (F-2 fix, OD-0196) | conflict resolved, CI re-running | merge when green |
| PR #123 (EODHD s3, stability 1, OD-0194) | conflict resolved, CI re-running | merge when green |
| `feat/cpi-first-release` (OD-0197, W2's `tools/bls_cpi_releases.py`, BLS snippets) | pushed, **no PR yet** | **don't run the download yet.** On the 10 retained real releases the parser read 4 and refused 6: the 2009 and 2011 `<PRE>` layouts ("reference-month label not found") and 2022, 2024 and 2026 ("first unadjusted-index column is not the reference month"; newer tables list the year-ago month first). Fix with a worker against those real files (the snippets alone weren't enough), then run the 245-page download once (cap 250) |
| F-1 coverage gap | known | the base levels for April 2005 to March 2006 were first published in releases before May 2006, which OD-0197 doesn't cover. Report it; asking for 12 more pages is the owner's call |

## Didn't work
- **Publishing "counts" from EODHD-derived returns** (stress months, half-widths): they are derived values (F-2). Records now give readings and yes/no only.
- **Closing a run's last pane closes tmux window `workers`,** and hiomux then can't spawn. Recreate it with `tmux new-window -d -t hio -n workers`.
- **The Codex CLI can't resume a session** (`thread/resume … not supported`): `hiomux answer` on a blocked Codex task fails; add a fresh task instead.
- **An assignment merged after its head makes Codex block:** put its location on public `main` in the goal.
- **`cmd || exit 1` chains whose first step was `ruff ... >/dev/null &&`** let a commit through (#117). Gate each check on its own.
- **Workers' invented-data tests passed while real files failed, three times** (W13's ampersands, W2's layouts, W10's year-earlier rule from my brief). Always run on real inputs before trusting a check.

## For the index
- `[data] EODHD revises its own history between pulls without notice (ex-dates, re-rounded closes, filled payment dates); every series built from it must pin the snapshot hash. Source: docs/evidence/e0002/stability-1.md.`
- `[rights] Aggregate statistics computed from licensed returns (counts, interval widths) are derived values: keep them out of the public repository; record readings only. Source: reviews/records/REVIEW-2026-11-22-e0004-1.md.`
- `[sources] BLS API v1 refused this client with 503 twice; the flat file download.bls.gov/pub/time.series/cu/cu.data.1.AllItems served at once. Source: OD-0189 correction 1.`
- `[hiomux] Codex tasks can't be resumed; a blocked Codex task needs a fresh task. Closing the last workers pane removes the workers window. Source: this handoff.`
- `[research] E-0004: the duration-benefit difference across CPI-acceleration states was not distinguished; the line is parked (architect, OD-0191). Source: docs/evidence/e0004/result-1.md.`

## NOT approved by this session
No experiment, result, data series or factor is accepted. E-0004 is unaccepted and its two findings are open. T-0003 is undecided. No factor spec is adopted. No SMSF use.

## Next, in order (one question at a time to the owner)
1. **Claude:** merge #122 and #123 once green; open a PR for `feat/cpi-first-release` and merge it, since the tool is unused.
2. **Claude:** fix W2's parser on the six real layouts (worker), then run OD-0197's download and comparison once. Report all equal, differences, or the 2005–06 gap.
3. **Owner:** F-1's outcome, then a Codex verification of F-1 and F-2 (Claude can assign under A2).
4. **EODHD line (architect's sequence):** a Codex reproduction of SPY's distribution check from retained bytes (OD-0176 lets Codex read EODHD data locally); the narrow T-0003 decision; build SPY's total-return series from `s3`, pinned; then one regional proxy at a time.
5. **Owner, lower priority:** accept T-0023, the dead-man exercise, C5, distil 3, the architect review.

## Completion block (operating model §6.2 step 9)
| Field | Value |
|---|---|
| Branch and full SHA | `feat/cpi-first-release`; `git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-e0004-eodhd-account-switch.md` |
| Pushed? PR | pushed with this commit; PR opened and merged by Claude under OD-0184 A1 |
| Received into `main`? | yes, once that PR merges |
| Next actor | Claude (the next session), then the owner |
| Prompt for the next actor | Run the start-of-session sequence (orch-prompt; PROTOCOL hash record is OD-0184; hiomux OD-0111). Read this handoff and `2026-11-22-restart-delegation-t0023-review.md`. Run waits in background subagents or background Bash. Kill dead panes; close a run after its batch. Records never carry EODHD-derived numbers |
