---
id: HANDOFF-2026-10-28-t0009-remediation-and-hiomux-pilot
date: 2026-10-28
actor: claude/implementation-agent (Claude Opus 5.5, Claude Code)
work_status: "T-0009 remediation: authorised (OD-0067), done locally, submitted as a claim, not pushed. hiomux pilot: authorised (OD-0072), residuals accepted (OD-0073); outside the repository"
base_revision: 950cce7cbe3c20b4ca4183ee619afbff646c4d70
head_revision: self       # resolve with: git log -n1 --format=%H -- handoffs/2026-10-28-t0009-remediation-and-hiomux-pilot.md
work_commits:
  - 76539b536118b2afee5c3aa53eab0c1b49444e86   # impl/t0009-remediation-1: response and T-0009 handoff (fix commits listed there)
  - 9c100c38c867b6f36c2556de14127d6ac507fbcb   # docs/od0072-hiomux-pilot: OD-0072
work_card: "T-0009 (remediation); none for hiomux (OD-0072, OD-0073)"
---

# Handoff: T-0009 remediation, and the hiomux pilot

> A dated snapshot. **Not a decision**, and never authoritative over ADRs, OD records or the
> review index.

**Role:** implementation agent. Two streams this session.

## Stream 1: T-0009 remediation (OD-0067)

The detail is in
`handoffs/2026-10-28-t0009-remediation-1.md`
and `reviews/responses/RESPONSE-REVIEW-2026-10-25-t0009-1.md`. Both are on
`impl/t0009-remediation-1` at `76539b5`, so the links resolve only on that branch.

- **Prerequisites:** all four held.
- **Fixes:** five commits on top of `ce0c3b5`:
  - F-1/F-2: a fixed publication mapping;
  - F-6: `keys_checked`;
  - F-3/F-4: specs 0.3.0, with S1a pinned to 0.2.0;
  - F-5: dated, cited calendars; synthetic only, D7 open;
  - F-7: a due gate and a disabled workflow outside `.github/workflows/`.
- **Tests:** **408 passed** (348 + 60). The S1a `data.csv` hashes and the full S1a release content
  hashes are unchanged. The review's F-1/F-2 probes write at `ce0c3b5` and are refused at the head.
- **All seven findings remain open.** This is a claim, not verified, and not pushed.

## Stream 2: hiomux (OD-0072, OD-0073)

**What it is:** a tmux orchestration stack, kept in `~/.hio-runs`, not the repository.
- `hiomux` starts an orchestrator session (Opus 5.5 by default; `--model`, `--effort`) in tab 1.
- Tab 2 holds headless Sonnet workers (up to 5) and Codex sessions. They report through files and
  append-only JSONL ledgers.
- Each worker has its own shared clone, Claude permissions, and a macOS `sandbox-exec` profile.
- The orchestrator's `check` judges exactly one commit in a fresh sandboxed checkout, and pins
  `checked_sha` for integration.
- A Codex review needs an assignment that cites an existing OD. The reviewer's commit is built by the
  runner from hash-verified files.

**Fable (same-vendor advice):**
- first pass: FIT WITH CHANGES;
- second pass: **SIGNED OFF WITH CONDITIONS** for the architecture and design.

Claude fixed C1–C3 and C5 and tested them. The owner accepted the C4 residuals, and declined Fable's
re-verification (OD-0073).

**The Codex CLI (0.164.0)**, tested across 11 model and effort pairs. The evidence is in
`~/.hio-runs/notes/codex-cli-assessment-2026-10-28.md`.

**Artefacts** (by sha256, recorded in OD-0073):
- `~/.hio-runs/bin/hiomux`: `752d2cec…`;
- `~/.hio-runs/PROTOCOL.md`: `52fa861a…`;
- the Codex note: `104685b9…`.

## Changed files (this branch, `docs/od0072-hiomux-pilot`, from `main` at `950cce7`)

- OD-0072 and OD-0073, with their verbatim transcripts in `docs/history/`.
- Two OD index rows.
- `STATUS.md`.
- This handoff.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| T-0009 suite | `uv run --no-sync pytest -q` at `30c7b68` | 408 passed |
| Repository checks | `tools/check_repo.py`; trailers | PASS on every commit (pre-commit hook) |
| hiomux isolation | `sandbox-exec` probes against generated profiles | **Denied:** writes to the main `.git` objects and refs, the main checkout, `~/.claude` settings, hooks, skills and `CLAUDE.md`, the shared uv cache, other runs, `task.json` and `brief.md`; reads of `~/.ssh`; SSH and `git push`. **Allowed:** the worker's own clone and the run's ledgers and uv cache |
| N1 (git trap) | `core.fsmonitor` planted in a worker clone, then `check` | no marker; check passed on the pinned SHA |
| N5 (orphans) | `reset` mid-run | the model process group was gone |
| Reviewer commit | synthetic hash mismatch, path traversal, unreported deletion | refused or excluded; a correct file committed with the right trailer |
| Worker loop | real Sonnet workers: parallel, blocked → answer → resume, failure, rejection, acceptance | all paths behaved |
| Codex | 11 model and effort pairs; resume flag tests; the sandbox | see the assessment note |

**Cost:** about $1.10 of Claude workers in tests, and a few hundred thousand Codex tokens. No test
artefacts remain: no `refs/hiomux`, review branches or extra worktrees, and the checkout is clean.

## Known limitations and not verified

- **Fixes not independently verified:** the hiomux C1–C3 and C5 fixes were tested only by their
  author. The owner waived Fable's re-verification (OD-0073), which is not a verification.
- **Codex review not tested end to end:** this needs an owner assignment. A real reviewer correctly
  refused a smoke task that OD-0072 does not assign.
- **The accepted residuals** (OD-0073):
  - open HTTPS;
  - tests run worker code inside the sandbox;
  - a worker can tamper with the ledgers;
  - transcripts hold what workers read.
- **macOS only:** hiomux depends on `sandbox-exec`, which is deprecated but present on 26.3.1.
- **T-0009:**
  - F-5 is open in part (D7);
  - the precision declarations in the 0.3.0 specs are unverified assumptions;
  - three existing assertions were changed, each listed in the response.

## Didn't work

- **Bash allowlist:** a worker read one denied command (`cat …; ls`) as "Bash is unavailable". Fixed
  by a precise prompt: the exact prefixes, one command per call.
- **Smoke contracts:** writing `.txt` under `tmp/` was rejected by the pre-commit `public` check,
  and Markdown without front matter by `check_repo`. These were contract errors; the checks were
  right.
- **Variadic options:** `claude`'s variadic `--allowedTools` swallowed a positional prompt. Prompts
  now go on stdin.
- **tmux targets:** panes inherit the tmux server's environment, not the caller's; pass variables
  explicitly. `-t name` matches by prefix; use `=name:`.
- **pyenv:** it picks Python 3.12 in some directories, so `PurePath.full_match` (3.13+) was
  missing; replaced by our own matcher.
- **Codex arguments:** `--add-dir <DIR>` with a space broke parsing, and `.git` stays read-only in
  `workspace-write` either way.
- **`tmux kill-server`** was rightly denied by the auto-mode classifier; kill only the named
  session.
- **The first `check` design** ran git in a worker's clone: Fable's N1. Replaced by reading the
  clone's commits through git alternates in the main repository.

## For the index (candidates for `knowledge/findings.md` once harness-0.9 Phase A exists; not added anywhere now)

- `[tooling] claude -p: variadic --allowedTools/--disallowedTools swallow a positional prompt; pass the prompt on stdin. Source: hiomux test, 2026-10-28.`
- `[tooling] claude -p --permission-mode dontAsk: a denial message reads as "Bash denied"; workers then stop using Bash; list exact allowed prefixes in the prompt. Source: hiomux W1 smoke test.`
- `[tooling] codex exec: model_reasoning_effort is not validated client-side (gpt-6-luna accepted 'ultra'); validate against ~/.codex/models_cache.json. Source: codex-cli 0.164.0 test.`
- `[tooling] codex exec resume inherits no settings; pass -m, -c model_reasoning_effort, -s before 'resume'. Verify from ~/.codex/sessions turn_context. Source: same.`
- `[tooling] codex workspace-write keeps .git read-only even under --add-dir=/writable_roots; reviewers cannot commit in-sandbox. Source: same.`
- `[tooling] codex exec picks up user MCP servers whose tools need approval and blocks headless; use --ignore-user-config. Source: same.`
- `[security] never run git in a repository an agent has written to: core.fsmonitor in its config runs on git status. Source: Fable N1, reproduced.`
- `[tooling] tmux -t matches session names by prefix; use =name: everywhere. Source: Fable M1, reproduced.`

## Assumptions made

- **"update all harness file"** was read as the session's governance records: the OD records,
  their index, `STATUS.md` and the handoff. It was **not** read as an instruction to edit the
  approved harness texts (`AGENTS.md`, the operating model, skills, templates). OD-0072 routes any
  move of hiomux into the repository through harness-0.9 Phase B, and amending approved text needs
  separate owner approval. If the owner meant the latter, it needs an explicit instruction naming
  the texts.
- **"I accept at this juncture"** was recorded as acceptance of the C4 residuals only, not as
  verification of the fixes, and not as acceptance of T-0009 or of any harness change.

## Conflicts found between documents

- **The T-0009 card §4 and OD-0067 on `keys_checked`:** OD-0067 was followed. See the T-0009
  handoff.
- **None new.**

## NOT approved by this session

Nothing an agent does approves, authorises, accepts, waives or closes anything. In particular:
- no T-0009 finding is closed;
- T-0009 and S1b are not accepted;
- no source right (including D7) is verified;
- no harness text changed or was approved, and harness-0.9 is untouched;
- hiomux holds no authority and is not part of the harness;
- the Fable reports are advice;
- no Codex review is assigned.

## Next authorised action

None without an owner instruction. The owner's queue:
1. **T-0009:** say whether to push `impl/t0009-remediation-1` and open the author PR
   (`Submission-Head`), then assign Codex verification in an owner-authored source.
2. **D7:** the RITS and NSW calendar decision.
3. **This branch:** whether to merge `docs/od0072-hiomux-pilot` to `main` (documentation only)
   and push.
4. **Optional:** an OD assigning a Codex smoke review, to test hiomux's review path end to end.
5. **Harness-0.9 decisions (Q-014):** unchanged.

## Completion block (harness-0.7, operating model §6.2 step 9)

| Field | Value |
|---|---|
| Branch and full SHA | `docs/od0072-hiomux-pilot`: the commit adding this handoff (`git log -n1 --format=%H -- handoffs/2026-10-28-t0009-remediation-and-hiomux-pilot.md`). `impl/t0009-remediation-1`: `76539b536118b2afee5c3aa53eab0c1b49444e86` |
| Pushed? PR link | **No** for both; no PR |
| Received into `main`? | not received; `main` is unchanged at `950cce7` |
| Next actor | owner |
| Prompt for the next actor | see below |

**Prompt for the next Claude session** (after an owner instruction):

> Start an HIO session (hio-session skill). Role: implementation agent. Stop if any of these fail:
> - `docs/od0072-hiomux-pilot` contains this handoff;
> - `impl/t0009-remediation-1` is at `76539b5`;
> - `main` is at `950cce7` or descends from it.
>
> Do only what the owner's instruction names: merge the documentation branch to `main`, and/or
> push the T-0009 remediation branch and open the author PR with
> `Submission-Head: <its head>`. Record the instruction in an OD. No harness text changes and no
> live operation. To use hiomux, read `~/.hio-runs/PROTOCOL.md` first.
