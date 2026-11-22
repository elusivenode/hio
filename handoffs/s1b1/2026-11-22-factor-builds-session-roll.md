---
id: HANDOFF-2026-11-22-factor-builds-session-roll
date: 2026-11-22
actor: claude/implementation-agent (Claude Opus 5.5, then Claude Fable 5.2, Claude Code; hiomux orchestrator)
work_status: "first local factor builds (USD, excess, AUD unhedged and hedged), analytics, a risk model and a hedge-ratio sweep: exploratory, unaccepted; E-0004 parked with F-1 and F-2 open"
base_revision: cf146106b460619ee21f6e8f6eb467893ad6b3de
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-factor-builds-session-roll.md
work_card: none (owner instructions OD-0198 to OD-0217; no task card exists for the factor builds)
stream: s1b1
---

# Handoff: factor builds, and the session roll

> A dated snapshot. **Not a decision.** It follows `2026-11-22-e0004-eodhd-account-switch.md`. **It holds no value from a licensed series** (OD-0210): results are in local files, named below.

## The owner's direction (read this first)

Midway through, the owner said: *"We are spending a lot of cycles here on things that are not advancing the core goal ... to develop investment factors and portfolio construction and analytics capabilities."* The session had by then spent four Codex verification rounds, sentence-level redactions and a results-store tool on E-0004, a parked experiment. Everything after that was factor work. **For the next session:**

- **Lead with the next factor or analytics step.** Put assurance items last, with their cost.
- **A finding on parked or exploratory work gets one remediation and one verification.** After a NOT READY, stop and ask: leave open, or waive (OD-0213).
- **Workers first, maximum concurrency, never block** (OD-0199, now in `orch-prompt.md` and `PROTOCOL.md`).

## Done: factors and analytics (OD-0213, OD-0215, OD-0216)

Seven tools, each written by a hiomux worker on invented data, accepted by `hiomux check`, then run by Claude on the real local data and checked by an independent script that uses none of the library code.

| Tool | Does | Evidence |
|---|---|---|
| `tools/factor_build.py` | a fund's market total-return series from its spec and a snapshot pinned by hash; RA-INV-001, index chain, RA-INV-020 | `docs/evidence/factors/build-1.md` |
| `tools/portfolio_analytics.py` | return, volatility, drawdown, correlation and sleeve contribution for a fixed-weight, monthly-rebalanced portfolio | `build-1.md` |
| `tools/factor_excess.py` | arithmetic excess over a cash leg from two exactly-compounded legs; RA-INV-004, RA-INV-005 | `build-2.md` |
| `tools/risk_model.py` | covariance, volatility, Euler risk contributions, diversification ratio, rolling risk; funded and excess never mixed | `build-2.md` |
| `tools/factor_cash_aud.py` | AUD cash: RBA rate accrual joined to the RBA Total Return Index | `build-3.md` |
| `tools/factor_translate.py` | USD to AUD, unhedged (RA §4.1) or hedged at ratio one with a CIP-implied forward (RA §4.3) | `build-3.md` |
| `tools/hedge_sweep.py` | a USD asset's AUD return across hedge ratios, alone and in a portfolio; descriptive | `build-4.md` |

**Built locally,** all at spec version 0.1.0, proposed, in `~/.hio-research/factor-store/<factor_id>/0.1.0/<build_id>/`:

- USD: `equity.us.spy`, `rates.us.ief`, `cash.us.bil` (`.market_total_return`), from EODHD snapshot `s3`.
- USD excess over BIL: `equity.us.spy_vs_bil.excess`, `rates.us.ief_vs_bil.excess`.
- AUD: `cash.aud.overnight_reconstructed`; the three `.aud_unhedged.total_return`; `equity.us.spy` and `rates.us.ief` `.aud_hedged.total_return`; two `_aud_unhedged_vs_aud_cash.excess`.

**Outputs for the owner:** `~/.hio-research/analytics/` (with `owner-report.md`) and `~/.hio-research/risk/`. The findings were reported to the owner in the session and are not repeated here.

**Nothing is in flight.** hiomux run `20261122T030739Z-f0c1` is closed and cleaned up.

## Done: E-0004 and the review loop (OD-0198 to OD-0214)

- **CPI first-release question (F-1).** The release parser was fixed on real layouts; 257 archived BLS releases were retained; four first-published levels differ from the flat file (May to August 2016); the states recomputed from first-release levels are identical in all 233 periods (`docs/evidence/e0004/cpi-first-release-check-2.md`, `cpi-first-release-states-1.md`). Codex verified that independently and left **F-1 open (narrowed)**: the run's inputs still departed from the rule. The owner left it open with E-0004 parked (OD-0207).
- **Restricted derived values (F-2).** Four verifications, each NOT READY. After the third, on the architect's advice, the ten result-bearing evidence records became public stubs and their content moved to a local results store (`~/.hio-research/results-store`, `tools/results_store.py`, OD-0210). The fourth verification passed the stubs and failed the summaries. **The owner left F-2 open with the work parked** (OD-0215). `reviews/records/VERIFY-2026-11-22-e0004-1-4.md` holds the inventory to act on if the owner ever wants more cleaned.
- **F-VERIFY-2026-11-22-e0004-1-1** (the PDF dependency) is verified closed (OD-0207).

## Done: tooling and rules

- **Orchestrator rules** in `~/.hio-runs/orch-prompt.md` and `PROTOCOL.md`: workers first, maximise concurrency, never block. **The PROTOCOL hash record is now OD-0199**; hiomux's is still OD-0111.
- **CI runs once per change** (OD-0212, approved by the owner at `c2ca8fd`, OD-0215): `pull_request`, and `push` only for `main`, `review/**` and `reviews/**` tags; runs on `main` are never cancelled.
- **A local pre-push gate** in this clone (`.git/hooks/pre-push`): ruff, format, repository checks, trailers and the full suite when the checked-out commit is pushed. Skip once with `HIO_SKIP_PREPUSH=1`.
- **Merges:** `.claude/settings.local.json` now lets Claude run `gh pr merge` itself. Run it as a bare command, or in a chain that checks CI first.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Repository and suite | `tools/check_repo.py`; `uv run pytest -q` via the pre-push gate | PASS; see the PR for this head |
| Each factor tool on real data | an independent recomputation in exact arithmetic, per `build-1.md` to `build-3.md` | every period within 1e-12 |
| Results store | `uv run python tools/results_store.py verify --store ~/.hio-research/results-store` | passes; 47 entries |

## Known limitations and not verified

- **One vendor, unvalidated.** Every fund series rests on EODHD's closes and distributions. Nothing independent validates them beyond T-0023's partial corroboration.
- **The hedged AUD series are not tradable returns:** the forward is implied from AUD cash against BIL's return, with no market forward points or costs, reset every period.
- **BIL is a bill fund, not an overnight rate;** the USD excess series are proxies. `cash.usd.overnight` has no captured series.
- **H.10 is a noon New York fix; the funds close at 4 pm.** Daily AUD figures mix two instants.
- **No task card** covers the factor builds; they ran on owner instructions recorded as ODs. A card would help if this becomes a programme of work.
- **The results store and the factor store are on one Mac with no backup.** A private, deletable cloud copy is a separate design, not authorised (OD-0210).

## Didn't work

- **Sentence-by-sentence redaction of licensed-derived values.** Three rounds each missed something, twice in sentences written during the previous round. Relocating whole records was the right move; it should have been the first.
- **Claiming a remediation without re-reading the files.** Response 1 said OD-0190's correction 2 was redacted; it was not. Sweep the repository before claiming.
- **A pre-push hook that inherits git's environment.** A test that creates its own repository ran against this one and set `core.bare = true`. The hook now runs `unset $(git rev-parse --local-env-vars)` first. If git says "this operation must be run in a work tree", check `.git/config`.
- **`sa ask` with a stale local `main`:** the architect's clone is made from local branches and fails with "unable to read tree". Run `git fetch origin main:main` first.
- **Integrating before reading `hiomux check`'s result:** a chained command cherry-picked a rejected commit (a flaky test: a year string that a sha256 can contain by chance). Gate integration on `check.json`'s `ok`.
- **Pinning a merge to the wrong SHA** in a stacked PR: take the head from `gh pr view <n> --json headRefOid`, never from `git rev-parse HEAD`.
- **Pushing without the full suite:** a stub broke a test that reads SEC filing numbers from a record. The pre-push gate now prevents this.
- **zsh does not split an unquoted variable into arguments:** `git checkout T -- $FILES` passes one argument. Name each path.

## For the index

- `[process] The goal is factors and analytics. A finding on parked or exploratory work gets one remediation and one verification; after a NOT READY, ask the owner: leave open or waive. Source: OD-0213.`
- `[rights] Results that depend on licensed data live in the local results store; the public file is a stub (identifier, kind, standing, pointer). Do not redact sentence by sentence. Source: OD-0210, tools/results_store.py.`
- `[factors] A factor build is a spec plus inputs pinned by hash, giving series.csv and build.json under ~/.hio-research/factor-store; tools refuse an unpinned or tampered input, and rebuild byte-identically. Source: tools/factor_build.py, docs/evidence/factors/build-1.md.`
- `[factors] Excess return is arithmetic per period over a named cash leg, each leg compounded exactly between common dates; never chain the excess. Funded and excess series are never combined in one portfolio or risk run. Source: tools/factor_excess.py, tools/risk_model.py.`
- `[fx] H.10's Australian series is USD per AUD, so an Australian holder's spot return on USD is q_prev/q_now - 1; check the sign on a known episode. Source: tools/factor_translate.py, docs/evidence/factors/build-3.md.`
- `[workers] Seven of seven worker-written factor tools passed real data first time (one needed a retry for a flaky test, not the tool) when the brief fixed the file format, named the functions to reuse, and listed the refusals and hand-computed tests. Source: this handoff.`
- `[verification] Check a worker's tool on real data with a separate script that shares no code with it, in exact arithmetic; a disagreement is as likely to be the checker's convention (a partial final month) as the tool. Source: docs/evidence/factors/build-2.md.`
- `[git] A git hook exports GIT_DIR; tests that create repositories then act on the real one. Unset git's local environment in the hook. Source: this handoff.`
- `[hiomux] sa ask clones from local branches: run git fetch origin main:main first, or it fails with "unable to read tree". Source: this handoff.`
- `[ci] CI runs on pull_request, and on push only for main, review/** and reviews/** tags; a branch with no pull request gets no run, so the local pre-push gate is the first check. Source: OD-0212.`

## Open findings (from `reviews/README.md`)

- F-REVIEW-2026-11-22-e0004-1-1 (high): open, narrowed; E-0004 parked (OD-0207).
- F-REVIEW-2026-11-22-e0004-1-2 (high): open after four verifications; work parked (OD-0215).
- F-VERIFY-2026-10-28-h6-1-6-1 (high): open; H6 parked (OD-0114).
- E-0002's F-1 (a vendor record against its issuer): open; content in the local results store.

## Assumptions made

- "Act autonomously" (OD-0198) means carrying authorised work through without asking at each step. The owner later narrowed it: for factor work, not for extending assurance work.
- "Distill the session" (OD-0217) means this handoff and its Inbox lines, not distil 3.
- Reporting series results to the owner in the session is within the EODHD rights row (agents may review; the owner is the licensee). Nothing derived went into the repository.

## Conflicts found between documents

- `registers/sources.yaml`'s EODHD row says no derived value enters the repository, while owner decision records and `docs/history/` still hold some qualitative readings. Codex raised it as an observation; the owner left F-2 open (OD-0215). Not resolved.
- Older handoffs' "Next" lists name E-0004 steps as current. This handoff supersedes them.

## NOT approved by this session

No series is accepted and no spec is adopted: fourteen factor specs are `proposed`. T-0003 is undecided. E-0004 is unaccepted and parked. T-0023 is not accepted. No finding is waived. Nothing is published or approved for a consumer or the SMSF. The architect's performance review is still due.

## Next, in order (one question at a time to the owner)

1. **Nothing is owed from this session.** The hedge-ratio sweep ran (`docs/evidence/factors/build-4.md`).
2. **Ask the owner for the next factor step.** Candidates, each needing its own yes: Australian equities from the earlier snapshot's ASX funds (rights: the same EODHD row); a proper USD cash leg (`cash.usd.overnight` needs a source); an independent check of the fund prices (T-0003's open question); a risk model with shrinkage; a task card and a short roadmap for the factor programme.
3. **Lower priority, only if the owner raises them:** the architect performance review; distil 3; T-0023's acceptance; the dead-man exercise; C5.

## Completion block (operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `feat/hedge-sweep-and-handoff`; `git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-factor-builds-session-roll.md` |
| Pushed? PR | pushed with this commit; PR opened and merged by Claude under OD-0184 A1 |
| Received into `main`? | yes, once that PR merges |
| Next actor | Claude (the next orchestrator session), then the owner |
| Prompt for the next actor | Run the start-of-session sequence (PROTOCOL hash record OD-0199; hiomux OD-0111). Read this handoff. Then lead with the next factor step: ask the owner which candidate in "Next" to build. Records never carry a value from a licensed series |
