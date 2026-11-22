---
id: HIO-DISTIL-3
title: "Findings distil 3, a draft: a disposition for each of the 97 Inbox lines"
status: accepted   # OD-0235 at 9bca57e (drafted under OD-0234)
owner: owner (accepts); drafted by claude/worker, reviewed by claude/implementation-agent
last_reviewed: 2026-11-22
---

# Findings distil 3 (draft)

The third distil under harness-0.9a (operating model §4.1). It is a **draft** authorised by the owner's instruction
OD-0234 ("Look for an opportunity to distill the session"; the brief for task D1 quotes it; no OD-0234 record is on `main` at
the base, see open point 1). **Accepting it is the owner's later, separate action.** Nothing in it is approved, and no Settled
line in `knowledge/findings.md` is accepted by this document being written.

**Base revision:** `f3152641a3a2398b60ee7343c95831b99d154a5b` (`main`). **Inbox count: 97 lines** (the lines under `## Inbox`
in `knowledge/findings.md` at the base, numbered 01 to 97 in file order; the Inbox was last emptied by distil 2, OD-0135).
The operating model's housekeeping signal is 25 lines. **Every line leaves the Inbox.**

## Outcome

| Outcome | Inbox lines | Count |
|---|---|---|
| Settled as written, or lightly shortened (one new Settled line each) | 05, 09, 10, 11, 12, 13, 14, 16, 18, 20, 23, 24, 25, 26, 27, 30, 31, 32, 33, 35, 36, 40, 42, 44, 47, 48, 49, 54, 62, 63, 65, 68, 69, 70, 71, 72, 74, 76, 77, 78, 84, 87, 88, 89, 92, 94, 95, 96, 97 | 49 |
| Settled with a substantive update (one new Settled line each) | 21, 22, 28, 29, 45, 59, 82, 83, 85 | 9 |
| Merged into one new Settled line (13 groups) | 01+07, 03+04, 06+08, 19+39, 37+55, 38+52, 41+46+73, 43+50+51, 60+67, 61+66, 75+79, 80+81, 86+91+93 | 29 lines, 13 new lines |
| Folded into an existing Settled line, which is marked | 02 (the `flagged:` line, resolved), 90 | 2 |
| Superseded, kept in Settled marked `superseded by …` | none of the Inbox lines; one existing Settled line is marked (see below) | 0 |
| Dropped from the index | 15, 17, 34, 53, 56, 57, 58, 64 | 8 |
| **Total** | | **97** (49 + 9 + 29 + 2 + 0 + 8) |

The proposed additions are **71 new Settled lines** (49 + 9 + 13), under the existing six `###` sections and four new ones:

| Section | New lines |
|---|---|
| Repository and CI | 6 |
| Releases, specs and rights | 5 |
| Review practice | 4 |
| Harness and process | 5 |
| hiomux and the owner's tools | 4 |
| Infrastructure and providers (Azure, GitHub) | 6 |
| **Capture and sources** (new) | 12 |
| **Factor builds and vendor data** (new) | 18 |
| **Data layers and marts** (new) | 6 |
| **Orchestration with workers** (new) | 5 |
| **Total** | **71** |

Each added line ends with `(distil 3, proposed)`, and each section carries a note directly above the lines distil 3
adds: `_Distil 3, PROPOSED under OD-0234 (2026-11-22), not yet accepted. Dispositions: docs/decisions/distil-3-proposal.md._`
The four new sections consist only of proposed lines and say so in their note. The Inbox is left as its heading and one note.

## How the lines were checked

All checks were made in the repository at the base. There was no network, and nothing outside the repository was read.

- **Re-read.** Each line's cited source was opened (the OD, evidence file, tool, test, review record, spec or handoff) and compared
  with the line. Where a cited line number had drifted the new Settled line cites the function or section instead
  (`missed_slots` for the completeness check, `BlobStagedWrites.commit`, `resolve_for_use`, `ALLOWED_IMPORTS`, the CI `on:` block).
- **Sources that could not be re-read: 13 lines,** because the cited source is not in the repository or no longer holds the claim:
  - **GitHub runs and pull requests (3):** 16, 28, 37 (Actions runs `098bb96`, `52abaff`, `58fe532`, `41734200727`, `41741724257`;
    PRs #74 to #88). A repository record corroborates each in part: OD-0146 correction 1 for the cancelled run, `soak-1.md` for
    start lateness, the 2026-11-04 handoff for the classifier refusal. The runs and PRs were not re-read.
  - **An architect consultation as the only source (1):** 82 (`20261122T185346-ask-1f88`, in `~/.hio-runs`). Lines 10 and 27 also cite one,
    but their repository sources (`resolve_for_use`; `monitoring.tf` and `soak-1.md`) were read.
  - **Session observations stated as "reproducible" (3):** 15, 57, 90. Not re-run here. Two are duplicates of Settled lines anyway.
  - **Local results store stubs (5):** 43, 47, 50, 51, 60. OD-0210 moved the results behind them out of the repository
    (`docs/evidence/t0023/corroboration-1.md`, `docs/evidence/e0002/stability-1.md` are stubs); the lines keep their wording and say so.
  - **An external page (1):** 32 (the Federal Reserve Board page, read 2026-11-04). The repository's reading pack
    `docs/research/T-0002-h3-reading-pack.md` states the same two facts and is cited instead.
- **Source read, but it does not state the whole line.** The settled wording keeps only what the source supports, or says what is the
  line's own advice:
  - 01: OD-0155 correction 2 says `tofu apply` failed because Azure refuses to delete a container or account with version-level
    immutability that holds blobs. It does not say "409" or "even expired" (the retention had expired, and the deletes were not refused).
    The 409 `BlobImmutableDueToPolicy` is in `rerun-1.md` for the 7b delete, which is a different step. The new line says what the OD says.
  - 22: OD-0143 does not state the 22:45 to 23:00 UTC overlap. `first-run.md` (slot table, run 41733292506) and the 2026-11-04 handoff do.
  - 29: OD-0146 correction 1 supports "a full plan shows differences, so use a targeted plan". "Inputs can be read from state without printing
    them" is not in the cited text and is left out.
  - 36: OD-0151 shows the index-row conflict. `git merge-tree` is the line's advice, not in the record.
  - 38: the aside "Distil 3 doesn't shrink it" is not in OD-0142 and is left out (open point 2).
  - 44: the tool's docstring (`tools/e0002_aud.py`) gives "monthly only, because noon New York is not a market close (RA 4.4)"; OD-0167 was
    not found to say it and stays cited as the line cited it.
  - 48: `tools/t0023_episodes.py` does not state the identity. It is algebra (the same positive FX path scales both wealth paths) and the new
    line says so.
  - 49: OD-0179 records the declared contact for the one SEC read; the refusal of `www.sec.gov` is a session observation not stated in it.
  - 52: `docs/history/2026-11-04-architect-t0023-step7.md` supports the `answer.md` path and the repointed links. "`--rev` reads a pushed
    branch, so push first" is a session observation.
  - 09: `BlobStagedWrites.commit` was read (l.145, no rollback). The escape from `run_capture` and `run_due` is from OD-0140 and not re-derived.
- **Where the source had moved on (substantive updates, each cites the newer source):**
  - 21: capture went live (OD-0143) and the reviewer rule was removed (OD-0146 correction 1); the line now carries an "Applies to".
  - 28: `soak-1.md` shows start lateness over the soak (median about 7 minutes, latest about 20), more than the first-day "one to five".
  - 45: `tools/e0003_aud_cash.py` now has `interval_classes` and `verdict_words`; T-0023 step 1 fixed it (OD-0177). "The code is unfixed" was stale.
  - 59: OD-0201 records that the run used a later vintage that differs from the first-published level in four months, with identical states under both rules.
  - 82, 83, 85: the layers, the catalogue, the backup and the first dimensional silver were built (OD-0231, OD-0233; `data-layers-1.md`,
    `silver-dimensional-1.md`); see the next item.
- **Several lines were the same thing changing during 2026-11-22; the latest state is settled once** and the earlier lines are merged or
  superseded, so no two Settled lines contradict:
  - *Where a data correction lives:* 81 (factor spec `construction.source_corrections`) and 80 (a confirmed stub duplicate) are one line. The current
    state is the observation spec (`specs/observations/IGB.AU.yaml`); the factor spec IGB 0.1.2 declares none; `factor_build.py` refuses a spec
    declaring corrections in both silver modes and still honours it in bronze mode (archived IGB 0.1.1 declared it). 83 already says corrections
    go in the observation spec. "Likely duplicate" does not occur in the Inbox; 80 says "confirmed", and the evidence (`distribution-screen-1.md`,
    OD-0229) confirms it.
  - *Backup:* 82 (advice for a tested backup, cloud backup unauthorised) is settled as the state: a backup exists, in a folder beside the
    repository on the same disk, which guards against a deleted or damaged store and not against loss of the disk (`data-layers-1.md`,
    OD-0231 correction 1); cloud backup stays unauthorised (OD-0210).
  - *Silver version 1 and version 2:* 83 (silver sets), 85 (dimensional silver, proposed), 86 and 91 (build commands) are settled so that version 2
    is the dimensional release and version 1 is reproduced from it as a compatibility export (27 of 27 files identical at the first build);
    both remain `proposed`.
  - *Merging PRs:* 37 (the classifier refused `gh pr merge`) and 55 (OD-0184 lets Claude merge within scope) are one line, with the earlier state
    marked as earlier.
  - *Codex's record:* 19 and 39 are one line (T-0013, T-0014, T-0015 and T-0019 each NOT READY; T-0016 and T-0017 READY first time).
  - *The `set -e` flag:* 02, resolved below.
- **Resolution of the one `flagged:` line (02).** It said the Settled receipt-chain advice "under `set -e`" (OD-0098) conflicts with the Settled
  lines that found `set -e` does not stop a chain in Claude Code's Bash tool. The records settle it: OD-0098 prescribed `set -e`; the later
  Settled lines (OD-0101 correction 1, OD-0113 correction 1) and the 2026-11-04 consolidation handoff (Inbox 53's source) show it failed in this
  harness and prescribe `|| exit 1`. The flag is resolved by marking the old Settled line `superseded in part by` those lines (below), so 02 is
  folded into that mark. Line 53 repeats the same finding and is dropped as a duplicate.

## Dispositions

**S** settled as written or lightly shortened; **S\*** settled with a substantive update; **M** merged (with the lines named);
**F** folded into an existing Settled line; **D** dropped from the index. "Went to" names the section and the new line's first words.

| # | Line begins | Disp. | Went to, or why dropped |
|---|---|---|---|
| 01 | [infra] An Azure account or container with version-level immutability | M with 07 | Infrastructure: "An Azure storage account or container with version-level immutability can't be deleted…" (409 claim removed: not in the source) |
| 02 | [process] flagged: the Settled line advising receipt chains "under `set -e`" | F | Flag resolved from OD-0101 c1, OD-0113 c1 and the 2026-11-04 handoff; existing Settled `[repo]` zsh line marked `superseded in part` |
| 03 | [infra] Azure's x-ms-version-id carries sub-second time | M with 04 | Infrastructure: "With `completed_at` taken before the write, C5's existing rule failed 45 of 50…" |
| 04 | [infra] With completed_at taken before the write | M into 03 | as 03 |
| 05 | [infra] Azure's response Date header ran up to about a second behind | S | Infrastructure: "Azure's response `Date` header…" (still unexplained) |
| 06 | [infra] Storage Blob Data Contributor has no blobs/deleteBlobVersion/action | M with 08 | Infrastructure: "Under version-level immutability, deleting a retained version gives 409…" |
| 07 | [infra] az storage blob delete has no --version-id | M into 01 | as 01 |
| 08 | [infra] Under version-level immutability, deleting a retained version | M into 06 | as 06 |
| 09 | [storage] BlobStagedWrites.commit creates keys one at a time | S | Infrastructure: "`BlobStagedWrites.commit` checks existing keys first…" (cites the function, not l.145) |
| 10 | [publish] resolve_for_use resolves stored releases only | S | Releases, specs and rights: "`resolve_for_use` resolves stored releases only…" |
| 11 | [process] A refusal test counts only if the refusal's reason is read | S | Review practice: first new line |
| 12 | [process] Match a precondition to the risk of its step | S | Harness and process: first new line |
| 13 | [process] A pipe to head kills the check with SIGPIPE | S | Repository and CI: first new line (retagged `[repo]`) |
| 14 | [process] The auto-mode classifier refuses Azure role grants | S | Harness and process: second new line |
| 15 | [repo] In zsh, $T:path applies a history modifier | D | Duplicate of the Settled `$REF:r` line (brace and quote) and the Settled `=` line; session observation, not re-run |
| 16 | [ci] A newer merge to main cancels the running main CI | S | Repository and CI: "A newer merge to `main` cancels…" (runs not re-read) |
| 17 | [review] A reviewer's README diff failed to apply in all three receipts | D | Duplicate of the Settled "reviewer's README diff often fails to apply… receive without the index" lines; the advance go-ahead is recorded in OD-0137 item 1 |
| 18 | [hiomux] A Codex reviewer's clone has no origin remote | S | hiomux: first new line |
| 19 | [review] In three tasks running (T-0013, T-0014, T-0015) | M with 39 | Review practice: "Codex found a real defect or spec overclaim… in T-0013, T-0014, T-0015 and T-0019…" (updated, extends the Settled line naming T-0013 and T-0014) |
| 20 | [capture] The completeness check has no start date | S | Capture and sources: first line (cites `missed_slots`; 27 h = 3 h + 24 h, checked) |
| 21 | [capture] Moving the workflow with LIVE_AUTHORISATION set arms cron | S\* | Capture and sources: adds "Applies to": capture went live and the reviewer rule was removed |
| 22 | [capture] Under AEDT and EST, 22:45 to 23:00 UTC | S\* | Capture and sources: source changed from OD-0143 (silent) to `first-run.md` and the handoff; "Applies to" added |
| 23 | [sources] The RBA expert-judgement CSV opens with prose | S | Capture and sources |
| 24 | [sources] Publication URLs: F1 serves two datasets | S | Capture and sources |
| 25 | [sources] The live FIRMMCTRI has up to 6 decimals | S | Capture and sources |
| 26 | [build] The F1 file runs back to 2011 | S | Capture and sources |
| 27 | [alert] A failed capture still writes an attempt record | S | Capture and sources (`monitoring.tf` read; `infra/tofu/README.md` l.86 still says the opposite, open point 3) |
| 28 | [ci] GitHub's scheduled firings ran about a minute to five minutes late | S\* | Capture and sources: adds the soak's start lateness from `soak-1.md` |
| 29 | [infra] tofu inputs can be read from state without printing them | S\* | Infrastructure: unsupported half removed; cites OD-0146 c1 and `plan-differences.md` |
| 30 | [factors] In CMT, the decomposition residual tests the Taylor terms only | S | Factor builds and vendor data: first line |
| 31 | [factors] A maturity-anchored schedule breaks on a leap-day strike | S | Factor builds and vendor data |
| 32 | [rights] The Federal Reserve Board's change removes Build Your Package | S | Releases, specs and rights (re-sourced to the repository's reading pack) |
| 33 | [rights] No Treasury page read grants or restricts reuse | S | Releases, specs and rights (adds that H2 is decided for the par curve only) |
| 34 | [process] A worker-free receipt from a scratch clone | D | Duplicate of the Settled "In a fresh scratch clone, `check_review_assignment.py` fails… `git branch review/<id>-codex <T>` first" line; "must run in a worktree at T" not found in OD-0144 |
| 35 | [process] A verification record linking to the response file | S | Review practice |
| 36 | [process] A records PR that adds an OD index row conflicts | S | Review practice (`git merge-tree` marked as the line's own advice) |
| 37 | [process] The classifier refuses gh pr merge from Claude | M with 55 | Harness and process: "Since OD-0184 (harness-0.10) Claude merges its own PRs…" with the earlier state stated as earlier |
| 38 | [hiomux] sa ask refuses at main when the bundle exceeds 90,000 bytes | M with 52 | hiomux: "`sa ask` refuses at `main` when its context bundle exceeds the manifest budget…" (aside about distil 3 left out) |
| 39 | [review] Codex has now found a real defect or spec overclaim | M into 19 | as 19 |
| 40 | [research] E-0003's report text is adapted by string replacement | S | Factor builds and vendor data (five `.replace(` calls and nine tests exist; one-test-per-replacement not checked) |
| 41 | [hiomux] sa ask defaults to local main | M with 46, 73 | hiomux: "`sa ask` clones from local branches and defaults to local `main`…" |
| 42 | [rights] All HIO agents may review EODHD data | S | Releases, specs and rights (adds the OD-0176 "Unchanged" limits) |
| 43 | [data] The issuer checks on the three sleeves have an unexplained pattern | M with 50, 51 | Factor builds and vendor data: "Three checks of EODHD-derived sleeve data… have their outcomes in the local results store" |
| 44 | [method] H.10 is usable for AUD translation only monthly | S | Factor builds and vendor data |
| 45 | [research] E-0003's intervals_span_zero treats any block length excluding zero | S\* | Factor builds and vendor data: it was fixed in T-0023 step 1 (OD-0177); `interval_classes`, `verdict_words`; T-0023 not accepted |
| 46 | [hiomux] The architect's clone holds local branches | M into 41 | as 41 |
| 47 | [research] Workers' invented-data tests missed three real-data shapes | S | Orchestration with workers (source is now a stub; shapes not re-readable) |
| 48 | [research] Two translated USD portfolios' compounded difference | S | Factor builds and vendor data (identity stated as algebra; cited tool does not state it) |
| 49 | [sources] SEC www.sec.gov refuses a client with no declared contact | S | Capture and sources (refusal is a session observation; the contact itself is not named) |
| 50 | [data] The sleeves' distributions were checked against audited fund reports | M into 43 | as 43 |
| 51 | [data] A payment-date reinvestment basis was tested | M into 43 | as 43 |
| 52 | [hiomux] sa ask --rev <sha> reads a pushed branch | M into 38 | as 38 |
| 53 | [shell] In this harness set -e didn't stop a failed step | D | Duplicate of the Settled lines on gating each step with an exit-code guard and on pipes hiding exit status; its source is the evidence used to resolve 02 |
| 54 | [build] Reloading a tool module under its own name in a test | S | Repository and CI (cites `tests/test_t0022_eodhd_eval.py` l.18) |
| 55 | [harness] Since OD-0184 (harness-0.10) Claude merges its own PRs | M into 37 | as 37 |
| 56 | [hiomux] hiomux task add validates --assignment against the LOCAL main | D | Duplicate of the Settled "hiomux checks an assignment OD against the LOCAL main; pull main before `task add --kind codex`" line |
| 57 | [shell] zsh expands "$VAR:r" as a modifier | D | Duplicate of the Settled `$REF:r` line (and of 15) |
| 58 | [build] Run ruff check and ruff format --check before pushing | D | Duplicate of the Settled "CI's Lint and format step runs `ruff check .` and `ruff format --check .`" line |
| 59 | [research] E-0004's state uses unrounded CPI-U ratios | S\* | Factor builds and vendor data: adds the vintage deviation of OD-0201 |
| 60 | [data] Every series built from EODHD data must pin the snapshot hash | M with 67 | Factor builds and vendor data: "A factor build is a spec plus inputs pinned by hash…" |
| 61 | [rights] Aggregate statistics computed from licensed returns | M with 66 | Releases, specs and rights: "Results that depend on licensed data live in a local results store…" |
| 62 | [sources] BLS API v1 refused this client with 503 twice | S | Capture and sources |
| 63 | [hiomux] Codex tasks can't be resumed | S | hiomux (near the Settled OD-0111 resume line, not the same fact) |
| 64 | [research] E-0004 ran once and is parked and unaccepted | D | A status note: STATUS, OD-0207, OD-0213 and the experiments register hold it; the result is in the local results store (OD-0210) |
| 65 | [process] The goal is factors and analytics | S | Harness and process |
| 66 | [rights] Results that depend on licensed data live in the local results store | M into 61 | as 61 |
| 67 | [factors] A factor build is a spec plus inputs pinned by hash | M with 60 | as 60 (adds that inputs are now a bronze snapshot, a silver set or a silver release) |
| 68 | [factors] Excess return is arithmetic per period over a named cash leg | S | Factor builds and vendor data |
| 69 | [fx] H.10's Australian series is USD per AUD | S | Factor builds and vendor data |
| 70 | [workers] Seven of seven worker-written factor tools passed real data | S | Orchestration with workers |
| 71 | [verification] Check a worker's tool on real data with a separate script | S | Orchestration with workers |
| 72 | [git] A git hook exports GIT_DIR | S | Repository and CI (retagged `[repo]`) |
| 73 | [hiomux] sa ask clones from local branches | M into 41 | as 41 |
| 74 | [ci] CI runs on pull_request, and on push only for main | S | Repository and CI (cites the `on:` block of `ci.yml`) |
| 75 | [data] A fund build's structural checks and its agreement with the vendor's adjusted close | M with 79 | Factor builds and vendor data: "A fund build's structural checks… do not catch a wrong distribution record…" |
| 76 | [data] The vendor may hold an estimated distribution | S | Factor builds and vendor data |
| 77 | [data] A vendor split date can sit one day from the price split | S | Factor builds and vendor data |
| 78 | [factors] The CIP-implied hedged series tracks a traded hedged fund | S | Factor builds and vendor data |
| 79 | [data] factor_build.py now screens distributions | M into 75 | as 75 |
| 80 | [data] The vendor can hold a stub duplicate of a distribution | M with 81 | Factor builds and vendor data: "The vendor can hold a stub duplicate of a distribution…": the correction now lives in the observation spec |
| 81 | [tools] A data correction is declared in the factor spec | M into 80 | as 80: the factor-spec location is the older state (IGB 0.1.1 archived; 0.1.2 declares none) |
| 82 | [architecture] On persistence the architect advised a local inventory | S\* | Data layers and marts: the advice was followed (catalogue, backup); backup beside the repository on the same disk; cloud backup still unauthorised |
| 83 | [architecture] Local data is three layers of immutable directories | S\* | Data layers and marts: adds the two silver forms, version 1 now a compatibility export of version 2 |
| 84 | [verification] The test of a new data layer is byte equivalence | S | Data layers and marts (adds 27 of 27 for silver version 2) |
| 85 | [architecture] A dimensional silver for HIO needs hash-derived surrogate keys | S\* | Data layers and marts: first version built and proved equivalent (OD-0233); still `proposed` |
| 86 | [tools] Dimensional silver: build a release with tools/silver_release.py | M with 91, 93 | Data layers and marts: "Build a fund series with `factor_build.py` in one of three input modes…" |
| 87 | [process] Parallel workers that cannot see each other's code | S | Orchestration with workers |
| 88 | [tools] Gold marts: declare a panel or portfolio in specs/gold/ | S | Data layers and marts (adds `plan` and `verify`, and what `ResearchStore` opens) |
| 89 | [repo] hio.jobs may not import hio.models or hio.portfolio | S | Orchestration with workers (kept `[repo]`; verified `ALLOWED_IMPORTS` and contract §8) |
| 90 | [repo] [rediscovery] zsh does not word-split an unquoted variable | F | Folded into the existing Settled word-splitting line as its recurrence on 2026-11-22 |
| 91 | [tools] Build fund series with factor_build.py --silver-root … | M into 86 | as 86 |
| 92 | [process] Declare the bars and readings in the OD before reading | S | Harness and process |
| 93 | [tools] factor_build.py takes --root as the snapshot workspace | M into 86 | as 86 |
| 94 | [tools] eodhd_eval.py fetches only symbols in ETFS or EXTRA_FUNDS | S | Factor builds and vendor data |
| 95 | [tools] portfolio_analytics.py takes no zero weight | S | Factor builds and vendor data |
| 96 | [process] Never push with HIO_SKIP_PREPUSH=1 | S | Repository and CI (retagged `[repo]`) |
| 97 | [web] A PDF fetched through the web-fetch agent comes back as bytes | S | Capture and sources |

Count check: 97 rows. S 49, S\* 9, M 29 (in 13 groups), F 2, D 8.

## Existing Settled lines changed

Only one existing Settled line is changed, and only by a marker added to its end; no wording of it is edited or removed:

1. `[repo] zsh does not word-split an unquoted variable: …` (distil 2; Source OD-0098). Marked `(distil 3, proposed: …)`:
   (a) its `set -e` advice is **superseded in part** by the Settled "Harness and process" lines that gate each step with `|| exit 1`
   (resolves Inbox 02); (b) the word-splitting point stands and **recurred 2026-11-22** (folds in Inbox 90).

No other existing Settled line is edited, shortened or deleted. The front matter of `knowledge/findings.md` is unchanged.

## Open points for the reviewer (found, not settled)

1. **OD-0234 is not on `main` at the base.** The brief quotes it, and `AGENTS.md` rule 2 asks that an instruction be transcribed into an OD record
   promptly; the highest record at the base is OD-0233. Not mine to write (outside my contract). The note text "PROPOSED under OD-0234" follows the brief.
2. **Inbox 38's aside "Distil 3 doesn't shrink it".** `sa ask` refused at `main` in OD-0142 because the bundle was 92,936 bytes against a 90,000 budget.
   The aside is unsupported (not in OD-0142), and a distil that moves lines into Settled need not shrink a bundle. Whether the architect still
   refuses at `main` at the base was not checked (no hiomux run). The line is settled without the aside.
3. **`infra/tofu/README.md` l.86 still says the scheduled-run failure test "proves the Azure alert fires".** `monitoring.tf` alerts only on the absence of a
   write to `catalogue/attempts/`, a failed run still writes one (Inbox 27), and `soak-1.md` says the alert's firing was not shown. The README is
   outside my contract; the new line records the contradiction.
4. **`docs/evidence/factors/issuer-check-1.md` l.36** states a result for the SPY sleeve against audited reports and a post hoc diagnostic about it, while
   OD-0210 moved EODHD-derived results to the local store and Inbox 43, 50 and 51 say those outcomes are held there. It also bears on whether the
   "unexplained pattern" of 43 is still unexplained. I did not edit it or settle a view; the new merged line (43+50+51) keeps only the pointer.
5. **An older Settled `[process]` line** (OD-0131: the classifier blocks merging PRs and the owner grants `Bash(gh pr merge *)` through `/permissions`)
   now sits beside the new merged line on OD-0184. Whether the classifier still refuses Claude's merge under the delegation is not recorded in
   OD-0184 or OD-0185, so I did not mark it superseded. The reviewer may prefer to.
6. **Inbox 82 advised "before any … silver layer", and a silver layer was then built** under OD-0231. I settled the state (advice followed in part
   and extended) rather than the advice; the architect's text was not re-read (outside the repository).
7. **Inbox 63 and the Settled OD-0111 line** are near each other (a Codex task resuming on its own branch needs the runner fix; Codex tasks cannot be
   resumed). I treated them as different facts. The reviewer should confirm they do not conflict.
8. **Inbox 25:** `cash.aud.overnight` is still at 0.3.0 with 4 decimals in the spec file, so the finding still holds at the base. Whether a later spec
   version should declare 6 decimals is the owner's (the cash-rebuild record assigns it to the approval package).
9. **Inbox 89 is kept as `[repo]` but placed in "Orchestration with workers"**, because its point is that a worker contract must be checked against the
   import rules. The reviewer may prefer it under "Repository and CI".
10. **Inbox 45 and T-0023.** The fix is on `main`, but T-0023 is not accepted (STATUS lists it as owed). The new line says so, and "Applies to: `main`".
11. **Several new lines cite sources only the owner's machine holds** (consultations, runs, the local results store). They keep their original
    wording, as the brief requires; the Settled section is navigation only and the cited source wins (operating model §4.1).

## Reviewer's notes (claude/implementation-agent, 2026-11-22)

The draft above is the worker's (task D1 of hiomux run `20261122T103322Z-dc8b`, checked commit `0346e10`). I read the outcome, the checking notes, the eight dropped lines, the one changed Settled line, the open points and the two new sections that cover 2026-11-22. I did not re-read every cited source a second time.

- **An earlier distil 3 exists and was never accepted.** Branch `proposal/distil-3` (`4c36bae`, drafted under OD-0141 on 2026-11-03) proposed 17 Inbox lines into Settled and two `MAP.md` rows. This draft is on `proposal/distil-3-r2`, covers those 17 lines among its 97, and changes no `MAP.md` row. If the owner accepts this one, the earlier branch is superseded; disposing of it is the owner's action. The worker did not know of it, and Inbox line 38's aside ("Distil 3 doesn't shrink it") referred to it.
- **One line reworded by me.** The proposed line on persistence and backup restated OD-0210 as needing the owner's reading of the vendor's terms. The owner's later direction is recorded in OD-0231, so the line now says only that no cloud copy is authorised and points to both records.
- **Open point 1 is resolved by sequence:** OD-0234 is in the pull request for the covariance and risk marts (#162) and reaches `main` when that merges.
- **Open point 3 is real and outside a distil:** `infra/tofu/README.md` overstates what the failure test proves. It needs its own small correction, on an owner instruction.
- **Open points 4 and 5 I leave as the worker left them.** The issuer-check note states results in words and holds no value from a series. The older line on the merge classifier is not marked superseded: this session merged its pull requests without a refusal, which is an observation and not a record.
- **The eight dropped lines are duplicates or a status note.** I agree with each.
- **Not covered:** the covariance and risk marts (OD-0234) added no Inbox line; their candidate lines go to the Inbox with the session handoff, after this distil.

## What acceptance means

**The owner accepts the Settled section of `knowledge/findings.md` at an exact revision** (or asks for changes). That is a separate explicit
action, recorded in an OD. Until then the 71 added lines are proposals marked `(distil 3, proposed)`, and the Inbox is empty only
in the sense that every line has a disposition. Accepted lines would take precedence rank 5: navigational, and the cited source wins.
Acceptance would not approve anything the lines describe; the proposed designs they mention (the data layers, the dimensional silver, the gold marts)
stay `proposed`.
