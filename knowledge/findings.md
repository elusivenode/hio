---
id: HIO-FINDINGS-INDEX
title: Findings index (findings, dead ends and settled assessments, one line each)
status: proposed   # seed for harness-0.9 H2 (OD-0068, OD-0070, OD-0080), revision 4 (Appendix A2); no authority. Every line cites its source; the source wins
owner: owner (approves Settled lines at distil); any agent appends to the Inbox
last_reviewed: 2026-10-28
---

# Findings index

> **Navigation only.** Before deriving something non-trivial, `grep` this file and say what you
> found. **Settled** lines (rank 5) were accepted by the owner at a distil. **Inbox** lines
> (rank 6) are claims, not facts. Each line cites repository evidence or a reproducible fact;
> "(branch …)" marks evidence not yet on `main`. Experiment results belong in
> `registers/experiments.yaml`, not here (point to them; never restate them). Tag a line
> `[rediscovery]` when re-deriving it cost real time. A line contradicted by newer evidence is
> marked `superseded by …` or `flagged: …`, never deleted; lines describe and never govern a later
> implementation revision (operating model §4.1, proposed).
>
> Format: `- [area] the finding. Source: <path:line, commit, test, record or "reproducible">. Applies to: <revision or component, where material>.`

## Settled

_(None yet. Every line below is an Inbox candidate for the first distil.)_

## Inbox

### Repository and CI mechanics
- [repo] A factor spec file must be named `<factor_id>.yaml`: the YAML check compares the file stem with `identity.factor_id`. New S1b specs need distinct factor ids. Source: `tools/check_repo.py:163`.
- [repo] Data files (`.csv .json .jsonl .xml .txt .tsv`) must live under `tests/fixtures/synthetic/` with `SYNTHETIC` on line 1; the repository is public. Source: `tools/check_repo.py` `check_public` (l.243–260); OD-0019.
- [repo] `check_repo.py | tail` returns `tail`'s exit status, so a chained `&& git commit` runs even when the check fails. Test the exit code of `check_repo.py` itself (or use `set -o pipefail`). Source: reproducible (shell pipeline semantics).
- [repo] YAML front-matter values containing `: ` must be quoted, or the front matter does not parse as a mapping and the front-matter check fails. Source: reproducible; `tools/check_repo.py` `check_frontmatter`.
- [repo] CI pins every GitHub Action by commit SHA; copy the pins from the existing workflow for any new one. Source: `.github/workflows/ci.yml`.
- [repo] CI requires an `HIO-Actor:` trailer on every non-merge commit, and the local hook does not check it. Run `uv run python tools/check_repo.py trailers origin/main HEAD` before pushing. Source: OD-0058 (the CI failure); OD-0059; operating model §6.2 step 5.7.
- [repo] [rediscovery] In zsh, `git show $REF:path` breaks when `path` starts with `r`, because `$REF:r` is a history modifier. Quote the argument: `git show "$REF:path"`. Source: reproducible.

### Releases and specs
- [releases] `spec_ref` is `factor_id@identity.version`. Editing an S1a spec either bumps its version (changing S1a release ids, whose outputs OD-0067 requires preserved) or silently changes a spec at an unchanged version. S1b releases need their own accurately versioned specs. Source: `src/hio/jobs/s1a.py:192-194`; `F-REVIEW-2026-10-25-t0009-4`; OD-0067.
- [releases] Count decimal places from the canonical string, not from a parsed `Decimal`: a parsed-then-reloaded value can lose trailing zeros. Source: `src/hio/jobs/s1b1.py` `_places` (on `main` since `7eba3f9`, OD-0079).
- [releases] One shared RBA F1 receipt serves `rba.cash_rate` and `rba.cash_rate_tri`. The receipt belongs to publication `rba.f1`, and each series carries its own `dataset_id`. A shared receipt with no link must not fall back to its publication id as the rights subject. Source: OD-0065; `F-REVIEW-2026-10-25-t0009-1`. Applies to: T-0009 at `ce0c3b5`. superseded by: the fixed publication mapping in `hio.contracts.publications` (F-1 `verified_closed` at `76539b5`, OD-0075).

### Rights and sources
- [rights] Every source permission is `unverified`; the genuine rights register refuses every operation. A design direction such as OD-0064 (F1 file retention) is not a rights verification. Source: `registers/sources.yaml`; OD-0013; OD-0064. Applies to: all sources as of `16ea0c6`. superseded by: OD-0076 (D7 `rba_calendar_pages` is `owner_verified` for retain-and-cite only; every other source is still `unverified`).
- [rights] A caller-supplied link record is not trustworthy evidence of which dataset a series belongs to: a substituted link authorised an unrelated dataset. Pin the series-to-dataset mapping in code. Source: `F-REVIEW-2026-10-25-t0009-2`.
- [sources] The US observation calendar can be derived from verified NY Fed publication dates, which avoids a SIFMA dependency. Source: `registers/tasks/T-0009-s1b1-cash-capture-and-research.md` §2 item 7; implemented as `calendar_from_observations` in `src/hio/reference/calendar.py` (accepted with T-0009, OD-0079; on synthetic data only).

### Review practice (useful to Codex and Claude)
- [review] Two probes found the T-0009 high findings: allow the publication id but deny the true dataset; substitute a single-owner link with the true dataset denied. Reuse both as standing adversarial tests for any change to the rights subject. Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` F-1, F-2.
- [review] A silent `continue` on a missing input in a comparison loop dropped periods without trace (AUD: 9 periods, 8 rows; USD: 13 periods, 10 rows). Count every omission and give its reason. Source: `F-REVIEW-2026-10-25-t0009-3`.
- [review] In REVIEW-2026-10-25-t0009-1, passing synthetic tests covered the happy paths; all three high findings were untested negative cases (missing link, substituted link, missing key). Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` verdict.

### Harness
- [harness] Assigning and receiving one review (`REVIEW-2026-10-25-t0009-1`) took two ODs, two transcripts, a tag, a receipt branch, index rows and five commits and merges, every step mechanical. Source: OD-0066; OD-0067; commits `c0588d9`..`eb19ef7`.
- [harness] Authority records left on an unmerged implementation branch make `main` contradict itself: at `eb19ef7`, `STATUS.md` did not mention T-0009 while OD-0067 authorised its remediation. Resolved for T-0009 by OD-0069 (merge `16ea0c6`); the failure mode remains possible (harness-0.9 H7). Source: `STATUS.md` and OD-0067 at `eb19ef7`; OD-0069.
- [harness] The HIO-ADR-0012 findings read three ways on `main` at `eb19ef7`: "3 findings open" (`STATUS.md` l.39), "technically verified closed" (`STATUS.md` l.47; OD-0054), and `remediation_claimed` for -1 and -3 (`reviews/README.md`), because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived. Read OD-0054 before relying on any of them. Source: OD-0053; OD-0054; OD-0057. Applies to: `main` at `16ea0c6` (`STATUS.md` now states the discrepancy).
- [harness] A same-vendor sub-agent standing in for Codex is an unverified dry run, and never satisfies an independent-review gate. Sub-agents return text and cannot write report files; the receiver transcribes. Source: operating model §10; `reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md`.

### From the 2026-10-28 T-0009 remediation, verification and acceptance session (handoff `handoffs/2026-10-28-t0009-acceptance-and-knowledge.md`)

#### Shell and git mechanics
- [repo] [rediscovery] The zsh `:r` trap (above) recurred three more times in one session, including `${T}:reviews/...` written as `$T:reviews/...`. Always brace and quote: `git show "${T}:${path}"`. Source: reproducible; session 2026-10-28.
- [repo] [rediscovery] The `| tail` exit-status trap (above) recurred: `check_review_assignment.py … | tail` reported exit 0 on a FAIL. Never pipe a gate. Source: reproducible; session 2026-10-28 (OD-0075 notes the rerun).
- [repo] `git merge -F -` does not read a message from stdin (`git commit -F -` does). Write the message to a file. Source: reproducible (git 2.x, 2026-10-28).
- [repo] In a fresh scratch clone, `tools/check_review_assignment.py` fails "review branch … does not resolve to a commit" until a local branch exists: `git branch review/<id>-codex <T>` first. Source: OD-0075 table, 5.3.
- [repo] A YAML flow mapping cannot hold a double-quoted value containing double quotes: write `conditional(attribution 'Source: …')` with single quotes inside. Source: reproducible; `registers/sources.yaml` entry `rba_calendar_pages`.
- [repo] When an author branch carries authority records that were imported to `main` byte-identically, the PR's merge conflicts in the OD index (`main`'s rows are a superset). Integrate by merging the exact head into `main`, keeping `main`'s index; GitHub marks the PR merged once its head is reachable. Never merge `main` into a verified head. Source: OD-0079 (merge `7eba3f9`).
- [repo] The owner's global git config rewrites `https://github.com/` to SSH (`url.git@github.com:.insteadOf`). A sandboxed process with SSH blocked needs `GIT_CONFIG_GLOBAL=/dev/null` to read public refs over HTTPS. Source: OD-0077 tests.

#### External data and rights
- [rights] D7 (RBA RITS and holiday pages) is the first `owner_verified` source: manual retrieval only, retain and cite on conditions. The pattern for a "facts, no judgement" source: one manual read, commit a dated, attributed extract with the page sha256, never the page. Source: OD-0076; `registers/sources.yaml` `rba_calendar_pages`; `src/hio/reference/calendars/`.
- [data] The RBA "Public & Bank Holidays" page lists one year only (2026 on 2026-10-28). RITS closes on named holidays "where they are observed in NSW and Victoria", so in 2026 RITS is open on three NSW-only weekdays (27 April, 3 August, 5 October). A 2027 calendar needs a new manual read (register `review_due: 2027-01-31`). Source: `src/hio/reference/calendars/*-2026.yaml`; VERIFY-2026-10-28-t0009-1-3.
- [data] RITS Advice 02/2026 (about the 27 April 2026 NSW Additional Day) has never been read; the calendar's RITS-open reading rests on the two pages only, and Codex confirmed it from them. Source: `RESPONSE-REVIEW-2026-10-25-t0009-1-2.md`; VERIFY-2026-10-28-t0009-1-3.
- [tools] WebFetch returns a small model's summary, not the page: unusable for exact facts (dates, quotations, hashes). For a source fact, fetch the bytes (`curl`), hash them, and parse locally. Source: session 2026-10-28 (OD-0076 read).

#### Review and receipt practice
- [review] An offline reviewer cannot verify external facts: a recorded page hash authenticates nothing without the bytes. Either retain the bytes in the repository or give the reviewer network; HIO chose network (OD-0077). With network, the reviewer's own fetch matched the author's recorded hashes, which made the data check independent. Source: VERIFY-2026-10-28-t0009-1-2 (limit) and -3; OD-0077.
- [review] Codex may write its record's `assignment` as `<path> on main at <sha>`; the checker compares the exact string and fails. Either state the exact expected string in the assignment, or treat a revision-pinned citation as an owner decision (OD-0078). Source: OD-0078.
- [review] Under OD-0061, every receipt in this session needed an owner go-ahead, for two reasons: each had a Class S row, and each report came through hiomux's run files, which OD-0061 does not list. Source: OD-0075, OD-0078. A candidate standing decision for the owner.
- [review] Cycle cost, measured: one Codex verification at `gpt-6-sol`/`high` took about 5 to 6 minutes; push, verify, remediate, re-verify and accept T-0009 took one session. The records dominate the effort: each receipt costs a tag, an import, a merge, an OD, a transcript, index rows and STATUS. Source: OD-0074 to OD-0079; hiomux run `20261028T043057Z-e4d8`.

#### hiomux (outside the repository; `~/.hio-runs`)
- [hiomux] macOS refuses a sandbox inside a non-trivial sandbox (`sandbox_apply: Operation not permitted`): a networked Codex reviewer runs under hiomux's profile with Codex's own sandbox off (`danger-full-access`). Source: OD-0077 tests.
- [hiomux] Denying the macOS security mach services breaks Codex's own TLS ("workspace routing discovery failed"). Denying file reads of `~/Library/Keychains` blocks keychain lookups just as well. Source: OD-0077 tests.
- [hiomux] Claude workers can look up the `gh` token in the login keychain (their profile does not block it, because Claude's own login lives there). Accepted residual. Source: OD-0077 correction 1.
- [hiomux] hiomux changed between OD-0073 (sha256 `752d2cec…`) and this session (`63c997b3…`, modified 14:40 local) with no record. Nothing checks an out-of-repository tool against its recorded hash at session start. Source: OD-0077 finding 1 (open).
- [hiomux] Codex task results carry token usage but `cost_usd: null`, so the run budget does not count Codex. Source: `~/.hio-runs/20261028T043057Z-e4d8/tasks/C1..C3/attempt-1/result.json`.

#### Owner interaction
- [process] The owner's answers in a question dialog are recorded verbatim in `docs/history/` together with the question text, because the selection alone ("Yes, push and receive (Recommended)") is meaningless without it. Source: the history files behind OD-0074 to OD-0079.
- [process] The owner wants a pending decision stated as one precise yes/no question naming exactly what the yes authorises. A table row reading "judgement: none" next to an unasked question cost a round trip. Source: `docs/history/2026-10-28-owner-d7-approval.md` messages 5 and 6.

### From the 2026-10-28 solution-architect, hiomux and harness sessions (handoff `handoffs/2026-10-28-solution-architect-and-hiomux-layout.md`; OD-0081 to OD-0092)
- [hiomux] Codex CLI 0.164's read-only sandbox reads the whole disk, and Codex auto-loads `AGENTS.md` unless `project_doc_max_bytes=0`; folder trust is read from `config.toml` before any `-c` override. Source: OD-0081; OD-0082.
- [hiomux] An architect sandbox profile must deny file reads under `$HOME` except its session directory and its own `CODEX_HOME`, and needs a full (not `--shared`) clone. Source: OD-0082.
- [review] A leak-free historical evaluation needs `git archive` at the cutoff plus named extra files, with "later" defined by commit time, not reachability. Source: OD-0082.
- [process] Tuning an identity on an evaluation case spends that case. Keep held-out cases, and re-run them only at their original cutoff: the stress cases and their grading are public in the repository. Source: OD-0083; OD-0084; OD-0089 correction 1.
- [ops] The owner uses Warp, which intercepts tmux prefix keys: the orchestrator runs outside tmux, and the owner's view is a Warp launch configuration. Source: OD-0085.
- [ops] A Warp tab running one long-lived command cannot be scrolled while it runs. Long answers belong on a page (`~/.hio-runs/architect.html`); the terminal tab is a ticker. Source: OD-0088 correction 2.
- [review] An evaluation whose cutoff contains its own records (the authorising OD, STATUS) lets the subject infer it is being tested. Choose an earlier cutoff, or disclose it. Source: OD-0087 correction 1; `docs/history/2026-10-28-chatgpt-sa-grading-report.md` §5.5.
- [review] To show whether an agent used the network, inspect its transcript for remote commands and web-search items; a regex over command strings gives false positives (`rg` globs, `uv.lock`, `.git`). Source: OD-0087 correction 2.
- [review] Not every hex-looking string is a commit id: pre-migration `macsmsf` ids (for example `a82aa0d` in `AGENTS.md`) do not resolve in this repository, and long decimals look like hex. Source: OD-0087 correction 2; `MIGRATION-MAP.md`.
- [repo] [rediscovery] In zsh, an argument starting with `=` (for example `echo ======`) is command-path expansion and fails ("= not found"). Quote it. Source: reproducible (session 2026-10-28, twice).
- [repo] [rediscovery] The `HIO-Actor` trailer trap (above) recurred: four pushes to `main` failed CI's harness job although this index listed it. Run `check_repo.py trailers origin/main HEAD` before every push. Source: OD-0092 correction 1.
- [hiomux] Every hiomux change needs a fresh `hiomux sa probe` and its new sha256 recorded in an OD; the orchestrator's session-start check compares the tool against the latest OD. Source: OD-0085; OD-0086; OD-0088.
- [hiomux] `hiomux up --no-orch` reuses an open run or opens a new one, so a `hio-orch` session can open a run that later needs `close` and `cleanup`. Source: OD-0086.
- [hiomux] The architect's context manifest reads `MAP.md` and the findings index from `proposal/harness-0.9`, which is stale now that Phase A is on `main`; a fix is to be drafted. Source: `docs/agents/solution-architect/context-manifest.yaml` (the two `ref: proposal/harness-0.9` entries); OD-0092.
- [ops] `/remote-control` connects a Claude Code session to the Claude app, and push notifications to the phone need `/config agentPushNotifEnabled=true`. Source: session 2026-10-28.
