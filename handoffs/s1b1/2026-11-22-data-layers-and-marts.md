---
id: HANDOFF-2026-11-22-data-layers-and-marts
date: 2026-11-22
actor: claude/implementation-agent (Claude Fable 5.2, Claude Code; hiomux orchestrator)
work_status: "T-0024 proposed; a distribution screen, one correction, local data layers, a dimensional silver and four gold marts built under their own owner instructions: local, exploratory, unaccepted. Distil 3 accepted"
base_revision: 6e7a538e41af2f618ae94e4a7d07b5bb24751475
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-data-layers-and-marts.md
work_commits: [e52cd04, 405717a, 0f2a008, 03b72fe, 62e7f9d, 619d7c8, f315264, e22131d, ab550d8]   # merge commits of PRs #155 to #163
work_card: T-0024
stream: s1b1
---

# Handoff: data layers and marts

> A dated snapshot. **Not a decision.** It follows `2026-11-22-factor-programme-first-packages.md`. **It holds no value from a licensed series** (OD-0210): results are in local files, named below, and were reported to the owner in the session.

## How the session ran

The owner authorised one step at a time and set the direction: series for factor and portfolio construction, with small corrections, in immutable and reconstructable layers; silver as a dimensional model; gold marts read through a Python API. The solution architect was consulted four times (advice only; each summarised to the owner). Every build followed one pattern: the owner's instruction recorded as an OD with the test declared first, a literal contract, workers building in parallel by file, then Claude's run on real data with an equivalence or comparison test and a deliberate break.

## Done

| Step | OD | What exists | Record |
|---|---|---|---|
| Distribution screen | OD-0228 | rules D1, D2, D3 in `tools/factor_build.py`; run on fourteen fund files | `docs/evidence/factors/distribution-screen-1.md` |
| IGB duplicate | OD-0229, OD-0230 | one duplicate vendor distribution confirmed on public pages and excluded; IGB spec at 0.1.2 | `build-9.md` |
| Local data layers | OD-0231 | silver version 1 sets, a DuckDB catalogue, a backup tool; backups in `hio-backup` beside the repository | `data-layers-1.md`; `docs/decisions/local-data-layers-proposal.md` |
| Dimensional silver | OD-0232, OD-0233 | a proposed model and contract; an instrument register; a release of nine funds from four snapshots | `silver-dimensional-1.md`; `silver-dimensional-model-proposal.md`; `silver-v2-contract.md` |
| Gold-mart foundation | OD-0233 | a monthly panel, a portfolio path, a planner and `ResearchStore` | `gold-marts-1.md`; `gold-marts-contract.md` |
| Covariance and risk marts | OD-0234 | sample covariance by window and risk contributions | `gold-marts-2.md` |
| Distil 3 | OD-0234, OD-0235 | 97 Inbox lines given dispositions; 71 Settled lines accepted | `docs/decisions/distil-3-proposal.md` |

**Local state** (never copy into the repository), all under `~/.hio-research/`:

- `silver/<instrument>/<silver_id>/`: version 1 sets. `silver/v2/<release_id>/`: two dimensional releases of the same inputs at two commits; the later is `ac293ef4…`, selection `compat-v1`.
- `factor-store/`: 39 builds. Each of the nine fund series has three builds with identical bytes (from bronze, silver 1 and silver 2).
- `gold/<kind>/<build_id>/`: six bundles (two panels and two portfolio paths at two commits, one covariance, one risk contribution).
- `catalogue/lake.duckdb`: rebuilt from the above; disposable.
- Backups: `/Users/elusivenode/Developer/elusivenode/hio-backup/`, three, the last after the risk marts.

**Nothing is in flight.** Every hiomux run is closed and cleaned up, and the tmux session is down. PRs #155 to #163 are merged.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Repository and suite | `tools/check_repo.py`; the pre-push gate; CI on each PR | PASS on every PR |
| The screen on real data | an independent recomputation of every flagged day, and two deliberate breaks | agrees on all fourteen files |
| Silver version 1 | every fund series rebuilt from it | 9 of 9 byte-identical |
| Silver version 2 | each version 1 file exported from it; every fund series rebuilt through it; a rebuild from a restored backup | 27 of 27 and 9 of 9 byte-identical; the same release id and bytes |
| Panel and portfolio marts | against today's analytics output, and an independent recomputation in exact rationals | below 1e-15, and within 1e-48 |
| Covariance and risk marts | against today's `risk_model.py` output, bar 1e-9 declared first | 1,580 figures, worst 3.9e-11 |
| Worker changes | `hiomux check`, then cherry-pick of exactly the checked commit | 25 tasks; one blocked once and resolved |

## Known limitations and not verified

- **No independent review of anything built today.** Every check is the author's.
- **The instrument register is unverified:** names, issuers and markets are the vendor's; listing start dates are not established.
- **Silver covers the nine funds only.** The exchange-rate file, the RBA history, the par curve and CPI are not in it.
- **Knowability and quality facts are deferred** in the dimensional silver; the fund data carries capture time only.
- **The marts' factor series are pinned inputs.** A silver correction reaches a mart only when its lock is updated to the rebuilt series.
- **The covariance is a plain sample estimate.** Whether it is a good one is Milestone C.
- **The backup is on the same disk as the store.**
- The IGB correction rests on two public pages, one a syndicated copy; the issuer's page was not reached, and the evidence bytes are not retained.
- Three large-distribution flags on IGB, and those on IEF, VGB and IHVV, are unchecked against the issuer.
- A code commit is part of every release and mart identity, so several builds of identical content exist.

## Didn't work

- **A contract that ignored the import rules.** The gold contract let the planner import the calculations; `hio.jobs` may not import `hio.models` or `hio.portfolio`, and the hook refused the worker's commit. The planner is now handed them by the tool.
- **A record's file name that looked like a secret.** The scanner reads "sk-" followed by twenty characters as an API key; a name containing "risk-mart-and-…" matched. Renamed.
- **Passing a tool's arguments in one shell variable.** zsh does not split it; use a function.
- **Piping a gate into `tail` before a commit.** The hook stopped the commit, not the chain. Write the gate's output to a file and test it.
- **Assuming no earlier distil 3 existed.** An unaccepted one from 3 November was on `proposal/distil-3`.
- **An `rm` with a shell variable in its path** is refused by a safety check; it was not needed.

## For the index

- `[tools] Gold marts also cover covariance and risk contribution: declare them in specs/gold/covariances/ and specs/gold/risk/, and run tools/gold_build.py run on the risk spec to build the whole chain. Their identities include the NumPy and Python versions. Source: docs/evidence/factors/gold-marts-2.md, docs/decisions/gold-marts-contract.md §6a.`
- `[repo] The secret scan matches "sk-" followed by twenty letters, digits, hyphens or underscores, so a file or branch name containing "risk-…" can fail it; rename. Source: tools/check_repo.py (the API secret key pattern); reproducible 2026-11-22.`
- `[process] Before drafting a numbered proposal, check for an unaccepted earlier branch of the same name: proposal/distil-3 (OD-0141) existed when distil 3 was redrafted. Source: docs/decisions/distil-3-proposal.md, reviewer's notes.`
- `[process] A code commit in a build identity means a later commit rebuilds identical content under a new id; compare payload hashes, not ids, to see that nothing changed. Source: docs/evidence/factors/gold-marts-2.md, docs/evidence/factors/silver-dimensional-1.md.`

## Open findings (from `reviews/README.md`)

Unchanged by this session:

- F-REVIEW-2026-11-22-e0004-1-1 (high): open, narrowed; E-0004 parked (OD-0207).
- F-REVIEW-2026-11-22-e0004-1-2 (high): open after four verifications; work parked (OD-0215).
- F-VERIFY-2026-10-28-h6-1-6-1 (high): open; H6 parked (OD-0114).
- E-0002's F-1 (a vendor record against its issuer): open; content in the local results store.

## Assumptions made

- **"Can we overlay a web search such as yahoo finance to confirm?"** was read as the instruction to do it (OD-0229).
- **"Approved."** was recorded as authorising the build it answered, not as approving a design (OD-0233).
- **"I do"** answered two questions put together and was read as yes to both: accepting distil 3 at the named revision, and the README correction (OD-0235). The owner can correct this.
- **Minting nine instrument codes** in a proposed register is within the yes to build the dimensional silver (OD-0233).
- **A lint-only import reordering** after integrating two workers' commits was done by Claude, not a worker.

## Conflicts found between documents

- `infra/tofu/README.md` said a failure test proves the Azure alert fires; `docs/evidence/b3/soak-1.md` says the alert's firing was not shown. Corrected under OD-0235.
- `docs/decisions/local-data-layers-proposal.md` describes silver version 1 as silver; `silver-v2-contract.md` makes it a compatibility export. Both are proposed; neither is amended.
- The `sources.yaml` conflict noted in earlier handoffs is unchanged.

## NOT approved by this session

No series is accepted and no spec is adopted. T-0024 is `proposed`. Four design documents are `proposed` and were built to, not approved: the local data layers, the silver dimensional model, the silver version 2 contract and the gold marts contract. The instrument register, the observation specs, the release spec and the gold specs are `proposed`. Distil 3's acceptance makes its lines Settled navigation lines and approves nothing they describe. No hosted or cloud component is authorised; the owner's direction toward Prefect on an Azure VM is recorded in OD-0233 and nothing was built. No finding is waived. The architect's performance review is still due.

## Next authorised action

**First, an owner instruction for the next session** (given at the close of this one, verbatim): "the remote repo has 241 branches. make a note in the handover that next session I want to delete all branches that have been merged, both locally and remote. we need to keep on top of tidiness".

- **Do this first, and record it in an OD at the time.** Counted at the close with `git fetch --prune`: 240 remote branches, of which 196 are merged into `main`; 39 local branches.
- **"Merged" means the branch tip is an ancestor of `main`** (`git branch -r --merged origin/main`). Delete those, remote and local, and nothing else.
- **Do not delete the 44 unmerged remote branches without asking:** 38 `review/*`, 4 `proposal/*`, `phase-b/h6` and one other. `STATUS.md` lists the branches that hold work not on `main`, and reviewer branches are received by tag, not by merge (operating model §6.2). List them for the owner and ask.
- **Keep it tidy from then on:** merge with `--delete-branch` (as this session did), and delete a local branch once its pull request is merged.

**Beyond that, nothing is authorised.** The next step needs an owner yes. Candidates, in the order Claude would take them:

1. **Milestone C on the marts:** a shrinkage estimator beside the sample covariance, with fixed windows declared first.
2. **Silver for the other inputs:** the H.10 exchange rate and the RBA cash history, so the translated and cash series build from silver.
3. **A lock update path:** rebuild the derived factor series from the silver-built parents and repoint the marts' lock, so a correction flows end to end.
4. **B1:** a USD overnight cash leg.
5. **An independent Codex review** of one coherent slice (the silver contract module and builder would be the first).

Lower priority, only if the owner raises them: the architect review, accepting T-0023, the dead-man exercise, C5, disposing of the superseded `proposal/distil-3` branch.

## Completion block (operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/session-close-data-layers`; `git log -n1 --format=%H -- handoffs/s1b1/2026-11-22-data-layers-and-marts.md` |
| Pushed? PR link | pushed with this commit; PR opened and merged by Claude under OD-0184 |
| Received into `main`? | yes, once that PR merges |
| Next actor | Claude (the next orchestrator session), then the owner |
| Prompt for the next actor | Run the start-of-session sequence (PROTOCOL hash record OD-0199; hiomux OD-0111). Stop if `ab550d8` is not in `main`. Read this handoff, `docs/decisions/silver-v2-contract.md` and `docs/decisions/gold-marts-contract.md`. Then delete the merged branches, local and remote, as the owner instructed at the close (see "Next authorised action"), and ask the owner one yes/no for the first candidate there. Records never carry a value from a licensed series |
