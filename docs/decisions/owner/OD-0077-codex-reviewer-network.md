---
id: OD-0077
title: "Owner instructs network access for the Codex reviewer and accepts its residual (Codex can read and send its own login); hiomux changed outside the repository; VERIFY-2026-10-28-t0009-1-2 not received and superseded by VERIFY-2026-10-28-t0009-1-3, assigned with network; nothing accepted or waived"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-codex-network.md (typed by the owner, verbatim)
  sha256: 6c2cee0fbba5d3b3048db84abcd8e6e727d04709cb22f928eee11018d10338ed
  date: 2026-10-28
  quote: "fix network situation first.  reviewer needs network access"
applies_to:
  - path: ~/.hio-runs/bin/hiomux (outside the repository)
    revision: "sha256 436833b7f5c277f95a0ddca68d58ac621c7e204b7780112a68d852fb06c7a179"
  - path: ~/.hio-runs/PROTOCOL.md (outside the repository)
    revision: "sha256 2f947c5926d601cb9accb762b9aff45797132712de420bce5901045f6a9d0e63"
  - path: impl/t0009-remediation-1
    revision: 846974b2c43e5b9839809af0f1ebc08cee4e88b1   # the head assigned to VERIFY-2026-10-28-t0009-1-3; fixed
related: {adrs: [HIO-ADR-0008], tasks: [T-0009], findings: [F-REVIEW-2026-10-25-t0009-5], ods: [OD-0061, OD-0072, OD-0073, OD-0076]}
---

# OD-0077: network for the Codex reviewer

## Owner actions (verbatim in the source file)

1. **"fix network situation first. reviewer needs network access."** This was said in answer to the stated limit of
   `VERIFY-2026-10-28-t0009-1-2`: offline, Codex could not compare the calendar files with the RBA pages.
2. **"I accept Codex have network access. no less secure than you."** The owner accepts the residual Claude
   stated: a networked reviewer can read and send its own ChatGPT login in `~/.codex/auth.json`. The owner
   declined the alternative of a separate, revocable API key.

## What changed in hiomux (outside the repository; claimed and tested by Claude, not independently verified)

Before this change, hiomux was backed up to `~/.hio-runs/notes/hiomux.pre-network.bak` (sha256 `63c997b3…1b4e`)
and PROTOCOL to `notes/PROTOCOL.pre-network.bak`. Changes:

- **Network by default for a Codex reviewer** (`--sandbox workspace-write`); `--no-network` turns it off. Network
  is refused for any other kind of task.
- **hiomux's own sandbox is the boundary.** A networked reviewer runs under hiomux's own `sandbox-exec` profile,
  with Codex's sandbox set to `danger-full-access` (off). Reason: macOS refuses a sandbox inside a non-trivial
  sandbox (`sandbox_apply: Operation not permitted`, tested), so Codex's `workspace-write` network switch
  cannot run inside an outer profile. This is the arrangement Claude workers already have. The runner's settings
  check now expects `danger-full-access` for a networked task.
- **The profile denies:**
  - reads of `~/.ssh`, `~/.config/gh`, `~/.aws`, `~/.azure`, `~/.netrc`, `data/`, `.hio-store/` and
    `~/Library/Keychains`;
  - outbound port 22, and the launchd SSH agent socket;
  - writes outside the clone, temporary directories and Codex's runtime state. Codex's `config.toml`, rules,
    skills, plugins, packages, memories and app-server control are not writable;
  - any write to the clone's `.git`.
- **No user git config** (`GIT_CONFIG_GLOBAL=/dev/null`) and no credential prompt. The owner's global config
  rewrites `https://github.com/` to SSH, which the profile blocks.
- **The reviewer prompt** gains a network note: public reads only, no authentication or push, and no sending
  of content anywhere. A data source may be read only where the assignment or its rights record allows it.
- **Keychain approach.** The first design denied the macOS security services, which broke Codex's own TLS.
  Denying reads of the keychain files blocks the lookup equally, and was kept.

**Tests (2026-10-28, scratch repository; exit codes only, no secret printed):**

| Probe | Under the profile | Want |
|---|---|---|
| HTTPS to `www.rba.gov.au`; `git ls-remote https://github.com/elusivenode/hio` | 0; 0 (returned `9be46bb`) | works |
| list `~/.ssh`; read `gh` config; `gh auth token`; keychain lookup of `gh:github.com` | 1; 1; 1; 44 | blocked |
| `ssh` to GitHub on 22 and on 443; `ssh-add -l` on the agent socket | 255; 255; 2 | blocked |
| `git credential fill` for github.com; `git push` over HTTPS | no password; 128 (`terminal prompts disabled`); no branch reached origin | blocked |
| write `~/.codex/config.toml`, `~/.codex/skills/`, the clone's `.git`, a commit | 1; 1; 1; 128 | blocked |
| write in the clone, Codex sessions; read `~/.codex/auth.json` | 0; 0; 0 | works (Codex needs them) |
| A real `codex exec` (gpt-6-sol, low) launched as hiomux launches it, running the probes above itself | all as above; its session record shows `danger-full-access` | as wanted |

## Found while doing this (reported, not fixed)

1. **hiomux had changed since OD-0073.** OD-0073 recorded hiomux at sha256 `752d2cec…7ab`. At the start of this
   change it was `63c997b3…1b4e`, last modified 2026-10-28 14:40 (Sydney time), after this run started at 14:30.
   Claude did not make that change, and no copy of the earlier version exists to compare.
   `PROTOCOL.md` still matched its OD-0073 hash then.
2. **Claude workers can look up the `gh` keychain item.** Their profile blocks `~/.config/gh` but not
   `~/Library/Keychains`, and HTTPS is open. So PROTOCOL's "no reads of GitHub credentials" does not fully hold
   for them. A lookup of `gh:github.com` succeeded (exit 0) under the worker profile. Blocking the keychain files
   there may break Claude's own login, which is kept in the keychain. Untested; for the owner.

## VERIFY-2026-10-28-t0009-1-2: not received, superseded

The offline verification (reviewer commit `a6f7f31…`, verdict READY, F-5 `verified_closed`) is **not received**.
On the owner's instruction, the reviewer needs network to compare the calendar files with the RBA pages. Its
branch `review/t0009-1-verify-2-codex` stays local and unpushed, as operational evidence only. The *Assigned
reviews* row records the disposition.

## Assignment: VERIFY-2026-10-28-t0009-1-3

The owner's "fix network situation first" names the next step: the F-5 verification, with network. The values are
transcribed from OD-0076's assignment with three changes: the id, the branch, and the reviewer's network.

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-10-28-t0009-1-3` |
| Verifies | F-REVIEW-2026-10-25-t0009-5 (as OD-0076's assignment, which it replaces) |
| Repository, base, head | `elusivenode/hio`; `76539b536118b2afee5c3aa53eab0c1b49444e86`; `846974b2c43e5b9839809af0f1ebc08cee4e88b1` (branch `impl/t0009-remediation-1`, PR #6; fixed) |
| Scope | as OD-0076, and additionally: compare every date and reason in `src/hio/reference/calendars/` with the two RBA pages as published today, and check the two named interpretations (27 April, 28 December) against them |
| Network reads allowed | `git ls-remote` of the repository; one read each of `https://www.rba.gov.au/payments-and-infrastructure/rits/business-hours.html` and `https://www.rba.gov.au/schedules-events/bank-holidays/` (D7: manual, cited reading, OD-0076). Nothing else from any data source |
| Review branch | `review/t0009-1-verify-3-codex`, cut at the head |
| Reviewer | Codex, independent reviewer; writes only under `reviews/`; no PR |
| Delivery | hiomux with network (this record); `--model gpt-6-sol --effort high` |

## Not authorised or changed

- No harness, repository tool or CI change.
- No other source right. The RBA pages stay `automated_retrieval: deny`; the reviewer's read is a one-off,
  manual, cited read.
- Finding 2 above is not fixed.
- Nothing is received, closed, accepted or waived.

## Corrections (append-only)

1. **2026-10-28: the owner accepts finding 2** (Claude workers can look up the `gh` keychain token): "I don't mind
   if claude workers can access the gh token. they must behave responsibly". Source:
   `docs/history/2026-10-28-owner-gh-token-residual.md` (sha256 `85840a3469de63acfa15bcb0c4ebc887bd53a43a3b5c996c870cab5dafaf28fa`).
   It is now an accepted residual, not a defect, and nothing in hiomux changes for it. `~/.hio-runs/PROTOCOL.md`
   lists it among the residuals and no longer says workers cannot read GitHub credentials (sha256 now
   `c8bac354281d1ebedc54c4ca524817b002b492668bdbac84ec5b4abd0b7f3658`). Finding 1 (the earlier unrecorded hiomux
   change) is still open.
