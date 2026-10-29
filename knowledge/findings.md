---
id: HIO-FINDINGS-INDEX
title: Findings index (findings, dead ends and settled assessments, one line each)
status: current   # harness-0.9a (OD-0091); Settled section accepted by OD-0093 at 8393552 (rank 5); Inbox lines are claims (rank 6). Every line cites its source; the source wins
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

_Distil 1, accepted by OD-0093 at `8393552` (2026-10-28). Dispositions of the 57 Inbox lines: `docs/decisions/distil-1-proposal.md`._

### Repository and CI
- [repo] A factor spec file is named `<factor_id>.yaml`; a superseded version that a release still cites lives at `specs/factors/archive/<factor_id>@<version>.yaml`. The YAML check compares the file stem with these. New specs need distinct factor ids. Source: `tools/check_repo.py` (spec naming check, ~l.163–170); F-REVIEW-2026-10-25-t0009-4.
- [repo] Data files (`.csv .json .jsonl .xml .txt .tsv`) live only under `tests/fixtures/synthetic/`, with `SYNTHETIC` on line 1; the repository is public. Source: `tools/check_repo.py` `check_public` (~l.268–271); OD-0019.
- [repo] [rediscovery] Never pipe a gate: `check_repo.py | tail` returns `tail`'s exit status, so a chained `&& git commit` runs on a FAIL. Test the gate's own exit code, or `set -o pipefail`. Source: reproducible; recurred 2026-10-28 (OD-0075).
- [repo] YAML front-matter values containing `: ` must be quoted, or the front matter does not parse as a mapping and the front-matter check fails. Source: reproducible; `tools/check_repo.py` `check_frontmatter`.
- [repo] CI pins every GitHub Action by commit SHA; copy the pins from `.github/workflows/ci.yml` for any new workflow. Source: `.github/workflows/ci.yml`.
- [repo] [rediscovery] Every non-merge commit needs an `HIO-Actor:` trailer; CI's harness job fails without it, and neither the local hook nor `check_repo.py` with no arguments checks it. Run `uv run python tools/check_repo.py trailers origin/main HEAD` before every push. Source: OD-0058; OD-0059; recurred: OD-0092 correction 1 (four failed pushes).
- [repo] [rediscovery] In zsh, `$REF:r…` is a history modifier, so `git show $REF:reviews/x` breaks. Always brace and quote: `git show "${REF}:${path}"`. Source: reproducible; recurred four times on 2026-10-28.
- [repo] [rediscovery] In zsh, an argument starting with `=` (for example `echo ======`) is command-path expansion and fails ("= not found"). Quote it. Source: reproducible (2026-10-28).
- [repo] `git merge -F -` does not read a message from stdin (`git commit -F -` does): write the message to a file. Source: reproducible (git 2.x).
- [repo] In a fresh scratch clone, `tools/check_review_assignment.py` fails "review branch … does not resolve to a commit" until a local branch exists: `git branch review/<id>-codex <T>` first. Source: OD-0075, table row 5.3.
- [repo] A YAML flow mapping cannot hold a double-quoted value containing double quotes; use single quotes inside. Source: reproducible; `registers/sources.yaml` entry `rba_calendar_pages`.
- [repo] When an author branch carries authority records already imported to `main` byte-identically, its PR conflicts in the OD index (`main`'s rows are a superset). Integrate by merging the exact head into `main`, keeping `main`'s index; never merge `main` into a verified head. Source: OD-0079 (merge `7eba3f9`).
- [repo] The owner's global git config rewrites `https://github.com/` to SSH; a sandboxed process with SSH blocked needs `GIT_CONFIG_GLOBAL=/dev/null` to read public refs over HTTPS. Source: OD-0077 tests.

### Releases, specs and rights
- [releases] `spec_ref` is `factor_id@identity.version`. Editing a spec that an accepted release cites changes that release's identity or silently changes a spec at an unchanged version; S1a pins its spec versions (`S1A_SPECS`), and S1b uses its own versions. Source: `src/hio/jobs/s1a.py` (`S1A_SPECS`); F-REVIEW-2026-10-25-t0009-4; OD-0067.
- [releases] Count decimal places from the canonical string, never from a `Decimal`'s exponent: a parsed-then-reloaded value can lose trailing zeros. Source: `src/hio/jobs/s1b1.py` `_places`. Applies to: `main` since `7eba3f9`.
- [rights] A caller-supplied link record is not trustworthy evidence of which dataset a series belongs to (a substituted link authorised an unrelated dataset). Pin the series-to-dataset mapping in code. Source: F-REVIEW-2026-10-25-t0009-2; `hio.contracts.publications`.
- [rights] The pattern for a "facts, no judgement" source (D7, the first `owner_verified` source): one manual read; commit a dated, attributed extract with the page's sha256, never the page. Source: OD-0076; `registers/sources.yaml` `rba_calendar_pages`; `src/hio/reference/calendars/`.
- [sources] The US observation calendar can be derived from verified NY Fed publication dates, avoiding a SIFMA dependency. Source: `src/hio/reference/calendar.py` `calendar_from_observations` (accepted with T-0009, OD-0079; synthetic data only).
- [data] The RBA holidays page lists one year only. RITS closes on holidays "where they are observed in NSW and Victoria", so it is open on NSW-only weekdays (in 2026: 27 April, 3 August, 5 October). A 2027 calendar needs a new manual read (`review_due: 2027-01-31`). RITS Advice 02/2026 has never been read; the 2026 reading rests on the two pages, confirmed by Codex. Source: `src/hio/reference/calendars/*-2026.yaml`; VERIFY-2026-10-28-t0009-1-3. Applies to: the 2026 calendars.
- [tools] WebFetch returns a small model's summary, not the page: unusable for exact facts (dates, quotations, hashes). Fetch the bytes (`curl`), hash them and parse locally. Source: the OD-0076 read (2026-10-28).

### Review practice
- [review] Reuse the two probes that found the T-0009 high findings as standing adversarial tests for any change to the rights subject: allow the publication id but deny the true dataset; substitute a single-owner link with the true dataset denied. Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` F-1, F-2.
- [review] Passing synthetic tests covered the happy paths; all three T-0009 high findings were untested negative cases (missing link, substituted link, missing key). Write the negative cases first. Source: `reviews/records/REVIEW-2026-10-25-t0009-1.md` verdict.
- [review] A silent `continue` on a missing input in a comparison loop drops periods without trace; count every omission and give its reason. Source: F-REVIEW-2026-10-25-t0009-3.
- [review] An offline reviewer cannot verify external facts: a recorded hash authenticates nothing without the bytes. Retain the bytes or give the reviewer network (HIO chose network, OD-0077); the reviewer's own fetch then makes the check independent. Source: VERIFY-2026-10-28-t0009-1-2 and -3; OD-0077.
- [review] Codex may write `assignment` as `<path> on main at <sha>`, which the checker's exact comparison rejects. State the exact expected string in the assignment. Source: OD-0078.
- [review] A same-vendor sub-agent (for example Fable) is advice, never an independent review: it cannot satisfy Codex's gate. Sub-agents return text; the receiver transcribes any report. Source: operating model §10; `reviews/reports/REPORT-2026-10-28-harness-0.9-fable-dryrun-1.md`; OD-0090.
- [review] A leak-free historical evaluation needs `git archive` at the cutoff plus named extra files, with "later" defined by commit time, not reachability. Source: OD-0082.
- [review] An evaluation whose cutoff contains its own records (the authorising OD, STATUS) lets the subject infer it is being tested: choose an earlier cutoff, or disclose it. Source: OD-0087 correction 1; `docs/history/2026-10-28-chatgpt-sa-grading-report.md` §5.5.
- [review] To show whether an agent used the network, inspect its transcript for remote commands and web-search items; a regex over command strings gives false positives (`rg` globs, `uv.lock`, `.git`). Source: OD-0087 correction 2.
- [review] Not every hex-looking string is a commit id: pre-migration `macsmsf` ids (for example `a82aa0d` in `AGENTS.md`) do not resolve here, and long decimals look like hex. Source: OD-0087 correction 2; `MIGRATION-MAP.md`.
- [process] Tuning an identity on an evaluation case spends that case. Keep held-out cases and re-run them only at their original cutoff: the stress cases and their grading are public in the repository. Source: OD-0083; OD-0084; OD-0089 correction 1.

### Harness and process
- [harness] Assigning and receiving one review costs about a dozen mechanical steps (two ODs, transcripts, a tag, an import, merges, index rows, STATUS); the Codex run itself took 5 to 6 minutes. The records dominate the effort (the case for H6). Source: OD-0066; OD-0067; OD-0074 to OD-0079.
- [harness] Authority records left on an unmerged branch make `main` contradict itself (at `eb19ef7`, STATUS omitted T-0009 while OD-0067 authorised its remediation). Source: OD-0069.
- [harness] The HIO-ADR-0012 findings -1 and -3 read `remediation_claimed` in `reviews/README.md` but "technically verified closed" in OD-0054, because `VERIFY-2026-10-25-adr0012-1` was disposed unreceived. Read OD-0054 before relying on either. Source: OD-0053; OD-0054; OD-0057. Applies to: `main` at `624db08`.
- [process] Record the owner's dialog answers verbatim in `docs/history/` with the question text: a selection alone is meaningless without it. Source: the history files behind OD-0074 to OD-0079.
- [process] State each pending owner decision as one precise yes/no naming what the yes authorises. Source: `docs/history/2026-10-28-owner-d7-approval.md` messages 5 and 6.

### hiomux and the owner's tools (outside the repository; `~/.hio-runs`)
- [hiomux] macOS refuses a sandbox inside a non-trivial sandbox: a networked Codex reviewer runs under hiomux's profile with Codex's own sandbox off. Source: OD-0077 tests.
- [hiomux] Denying the macOS security mach services breaks Codex's TLS; denying file reads of `~/Library/Keychains` blocks keychain lookups just as well. Source: OD-0077 tests.
- [hiomux] Claude workers can look up the `gh` token in the login keychain; an accepted residual. Source: OD-0077 correction 1.
- [hiomux] Codex CLI 0.164's read-only sandbox reads the whole disk, and Codex auto-loads `AGENTS.md` unless `project_doc_max_bytes=0`; folder trust is read from `config.toml` before any `-c` override. Source: OD-0081; OD-0082.
- [hiomux] An architect sandbox profile must deny file reads under `$HOME` except its session directory and its own `CODEX_HOME`, and needs a full (not `--shared`) clone. Source: OD-0082.
- [hiomux] Every hiomux change needs a fresh `hiomux sa probe` and its new sha256 recorded in an OD; the orchestrator checks the tool against the latest OD at session start. The change before OD-0077 remains unexplained. Source: OD-0077 finding 1; OD-0085; OD-0086; OD-0088.
- [hiomux] Codex task results carry token usage but `cost_usd: null`, so the run budget does not count Codex. Source: `~/.hio-runs/20261028T043057Z-e4d8/tasks/C1..C3/attempt-1/result.json`.
- [hiomux] `hiomux up --no-orch` reuses an open run or opens a new one, so a `hio-orch` session can open a run that later needs `close` and `cleanup`. Source: OD-0086.
- [ops] The owner uses Warp, which intercepts tmux prefix keys: the orchestrator runs outside tmux and the owner's view is a Warp launch configuration. A tab running one long-lived command cannot be scrolled, so long answers go on `~/.hio-runs/architect.html` and the tab is a ticker. Source: OD-0085; OD-0088 correction 2.
- [ops] `/remote-control` connects a Claude Code session to the Claude app; phone notifications need `/config agentPushNotifEnabled=true`. Source: session 2026-10-28.

## Inbox

_(Empty after distil 1. Append new candidate lines below this note.)_
- [repo] [rediscovery] zsh does not word-split an unquoted variable: `F="a b c"; git checkout T -- $F` passes one path "a b c". Write each path out (or use an array), and run receipt chains under `set -e` so a failing check stops them; a FAIL from `check_repo` was ignored and a broken import pushed. Source: OD-0098.
- [repo] CI's "Lint and format" step runs `ruff check .` **and** `ruff format --check .`; a worker contract or local check that runs only `ruff check` passes while CI fails (all H6 branches, 2026-10-28). Put CI's exact lint commands in every acceptance list. Source: `.github/workflows/ci.yml` (Lint and format); CI runs 40669141245, 40673974716.
- [process] In Claude Code's Bash tool, `set -e` did not stop a `;` chain: gate every step with `|| exit 1`. Source: OD-0101 correction 1.
- [repo] `check_repo`'s link scanner ignores code spans: quoting a Markdown link in an OD, even in backticks, fails the links check; fence it or avoid link syntax. Source: OD-0101 correction 1.
- [review] A reviewer branch cut from an author branch lacks `main`'s newer index rows: its README patch may not apply, and it cannot write state rows. Receipt then needs option B handling. Source: OD-0098; OD-0101.
- [review] Automated authority decisions from prose (word, token or shape matching) failed three adversarial rounds; remove the interpretation from automation instead of patching the parser. Source: OD-0100; VERIFY-2026-10-28-h6-1-1, -2.
- [review] Prove a regression test catches a defect by running the new tests against the pre-fix tools in a worktree (with braced refs). Source: RESPONSE-REVIEW-2026-10-28-h6-1-1, -2.
- [hiomux] Worker `result.json` summaries can be empty; read the transcript's `result` event. Source: hiomux run `20261028T081310Z-d55d`, H6R2, H6R3.
- [hiomux] A per-lock pre-built uv cache with a copy-on-write clone per review gives offline `uv sync` plus tests in about 4 s. Source: OD-0095 correction 1.
- [hiomux] A Codex reviewer needs network or a pre-built environment to run the pinned suite; without either it hunts for unrelated local interpreters. Source: OD-0094 correction 1.
- [process] Each push question names the exact commit range, and nothing beyond it is pushed: two overreaches. Source: OD-0093 correction 1; OD-0099 correction 1.
- [ops] The owner prefers to follow agents from the orchestrator session: relay Codex and worker messages with the Monitor tool. Source: session 2026-10-28.
- [review] Push the assignment OD before launching a Codex reviewer: a source named "on local main" fails check_review_assignment's exact match and needs an owner ruling. Source: OD-0103.
- [review] A reviewer's README diff often fails to apply on main, because review branches lack main's newer index rows; under harness-0.9b, receive without the index and add the navigation row by §5.12. Source: OD-0107.
- [review] Tell the Codex reviewer that every file under reviews/ needs front matter and that check_repo must pass; hiomux does not run check_repo on Codex output. Source: OD-0109, OD-0111.
- [process] A YAML front-matter value written as two quoted strings joined by ';' is invalid; write one string. Source: OD-0113 correction 1.
- [process] [rediscovery] '| tail -1' and 'set -e' hide a failing check's exit status in Claude Code's Bash tool; run check_repo alone and read its exit code before committing or pushing. Source: OD-0113 correction 1; OD-0110.
- [hiomux] A Codex task resuming on its own existing branch needs the runner fix of OD-0111 (update-ref expected old value). Source: OD-0110, OD-0111.
- [harness] Recovery code that reconstructs trust from local or published history it did not build keeps leaking; prefer a narrow boundary (publish only what this run built from a fresh remote main). Source: OD-0109, VERIFY-2026-10-28-h6-1-3 to -7.
- [review] check_review_assignment.py compares the record's assignment field exactly; tell the reviewer the exact string to write (path only, no section). Source: OD-0121 correction 1, OD-0122.
- [repo] With main protected, a receipt's §5.9 merge goes through a PR (receipt/<id>), merged with the §5.9 subject; 5.10 then checks remote main. Source: OD-0121.
- [hiomux] hiomux checks an assignment OD against the LOCAL main; pull main before 'task add --kind codex'. Source: this session (OD-0120 launch).
- [hiomux] A task contract cannot be widened after spawn; supersede the task with a widened one. Source: R2/R2b, OD-0121.
- [repo] Never quote an owner message verbatim into a committed record when it contains an email address or other personal identifier; withhold it. Source: OD-0126 correction 1.
- [infra] A required reviewer on a GitHub Environment pauses every job in it, scheduled ones included. Source: OD-0119 C-4.
- [infra] A stateless scheduled-query alert (auto_mitigation off) fires on every evaluation; gate it until there is something to monitor. Source: OD-0126 correction 1.
- [infra] A workflow_dispatch workflow can be dispatched only once it exists on the default branch. Source: T-0012 submission.
