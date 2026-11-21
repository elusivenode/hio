---
id: HANDOFF-2026-11-22-restart-delegation-t0023-review
date: 2026-11-22
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code; hiomux orchestrator)
work_status: "standing delegation in force (OD-0184); T-0023 reviewed, remediated and verified, unaccepted; E-0004 preregistration proposed; CPI rights decision pending"
base_revision: 4b6472e54aa7a1d989ee78ee49f83d6967a27536
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-restart-delegation-t0023-review.md
work_card: T-0023
stream: s1b1
---

# Handoff: restart, standing delegation, T-0023 review cycle, E-0004 draft

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the review index. It holds no licensed-derived value. Written because the owner is changing the Claude account login; the next session starts cold.

## Done (OD-0181 to OD-0187)
- **Five yeses (OD-0181):** #104 merged by the owner; recommendation 1 adopted; the CPI source drafted (`docs/research/cpi-source-1.md`); **the soak's bar met: 0 misses of 80** (`docs/evidence/b3/soak-1.md`).
- **Standing delegation (OD-0183, OD-0184; harness-0.10):** approved at `5ddbb7a`. Claude merges its own PRs within authorised scope, assigns and receives Codex reviews of its own work, delegates to workers, runs read-only checks and refreshes the reference calendars; **excluded merges and every acceptance, approval, waiver, finding closure and rights verification stay the owner's.** `~/.hio-runs/PROTOCOL.md` is now `25dfb779…9045` and `orch-prompt.md` `9fbfce08…b7`, both recorded in OD-0184 correction 1. Uses are logged in OD-0185 and OD-0186.
- **2027 RITS and NSW calendars (OD-0185, #108):** from one manual read each of the RBA pages; tests cover the year boundary.
- **T-0023 review cycle (OD-0182, OD-0186):** `REVIEW-2026-11-22-t0023-1` gave **NOT READY**, with two medium findings (C5 completeness; panel identity not recomputed). Both were fixed in `0288120` (#110). `VERIFY-2026-11-22-t0023-1-1` gave **READY**, with both technically verified_closed. All three records are received (#109, #112). Real-input reruns after the fix reproduce every reported status. Codex traced the six audited fund-years to SEC filings, and they equal the local transcription (24 of 24).
- **E-0004 preregistration (OD-0187):** `docs/evidence/e0004/preregistration-1.md`, `proposed`, revised after the architect (`20261122T083318-ask-b4ca`). PR #113.
- **CPI rights reading pack:** `docs/research/T-0002-cpi-reading-pack.md`. The owner's decision is pending.
- **Restart report** for ChatGPT: `~/Downloads/hio-restart-reconciliation-2026-11-22.md` (outside the repository).

## Architect (4 consultations this session)
Restart priorities; the delegation design (it found the operating-model amendment necessary and named self-merge the riskiest power); the E-0004 draft (it found the core design sound, and its tightening is adopted). All were summarised to the owner. **The performance review is due** (`docs/agents/solution-architect/performance-review-1.md`, proposed).

## Tests and evidence
| Claim | Method | Result |
|---|---|---|
| Suite at the remediation head | `uv run pytest -q` | 1,693 passed |
| CI on every merged PR | GitHub | green before each merge; one lint failure on #108, fixed before merging |
| Soak | `tools/soak_report.py`, read-only, the owner's `az` login | 80/80, 0 missing, failed, late or manual |

## Didn't work
- **Pushing without running `ruff` locally** let a lint failure reach CI (#108). Run `ruff check .` and `ruff format --check .` before every push.
- **`git checkout <file>` to undo one experiment** also reverted my new tests in that file. Use a scratch copy instead.
- **zsh treats `"$T:r…"` as a history modifier** (`:r`), which breaks `git show "$T:reviews/…"`. Write `${T}:path`.
- **hiomux checks the local `main`**, so a stale local `main` makes `task add` refuse an assignment OD that is on origin. Run `git fetch origin main:main` first.
- **A branch cut before a merge lands** misses that merge's rows. Fetch and merge `origin/main` before editing the index.
- **Foreground waits (CI, `hiomux wait`, `sa ask`) locked the orchestrator.** The owner asked for background subagents; merges stay with the orchestrator.

## For the index
- `[harness] Since OD-0184 (harness-0.10) Claude merges its own PRs within authorised scope and assigns reviews of its own work; workflows, infra, the live capture path, credentials and governance files still need the owner's exact-head approval. Source: docs/decisions/owner/OD-0184-standing-delegation.md.`
- `[hiomux] hiomux task add validates --assignment against the LOCAL main; run git fetch origin main:main first. Source: this handoff.`
- `[shell] zsh expands "$VAR:r" as a modifier; write ${VAR}:path in git show arguments. Source: this handoff.`
- `[build] Run ruff check and ruff format --check before pushing; CI's lint step fails a PR the tests pass. Source: PR #108.`
- `[research] E-0004's state uses unrounded CPI-U ratios from first-release index levels, carried forward, so October 2025's missing release needs no special case. Source: docs/evidence/e0004/preregistration-1.md.`

## Open findings
F-REVIEW-2026-11-22-t0023-1-1 and -2: `remediation_claimed`, technically verified_closed at `602be49`; **the owner's reconciliation is pending.** F-1 (BGBL) stays open.

## NOT approved by this session
T-0023 isn't accepted. No finding is closed. No data series, source or factor is accepted. E-0004's preregistration is proposed, not adopted. `bls_cpi` is unverified. No download or experiment is authorised. S1b-1 isn't complete.

## Next authorised action
**Claude:** merge #113 once green, and the PR holding this handoff. Nothing else is in progress.
**Owner, one at a time:**
1. The `bls_cpi` rights decision (the reading pack).
2. Then a yes for one bounded CPI download.
3. Adopting E-0004's preregistration at an exact revision, confirming the 0.20-point threshold.
4. Reconciling the two T-0023 findings.
5. IEF's NAV file.
6. Accepting T-0023.
7. The dead-man exercise and the other soak follow-ons.
8. Lower priority: C5, distil 3 (#72), the architect review and held-out cases.

## Completion block (harness-0.7, operating model §6.2 step 9)
| Field | Value |
|---|---|
| Branch and full SHA | `rights/bls-cpi`; `git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-restart-delegation-t0023-review.md` |
| Pushed? PR | pushed with this commit; PR opened and merged by Claude under OD-0184 A1 |
| Received into `main`? | yes, once that PR merges |
| Next actor | owner (the `bls_cpi` decision) |
| Prompt for the next actor | Run the start-of-session sequence (orch-prompt). The PROTOCOL hash record is now **OD-0184** (`25dfb779…9045`); hiomux is unchanged (OD-0111). Read this handoff, then ask the owner the `bls_cpi` question from `docs/research/T-0002-cpi-reading-pack.md`. Run waits in background subagents. The hiomux run `20261103T065037Z-3d12` stays open, with a T-0023 brief that needs rewriting before new worker tasks (E-0004 tooling is the next worker candidate, after adoption) |
