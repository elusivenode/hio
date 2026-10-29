---
id: OD-0111
title: "Owner assigns Codex verification VERIFY-2026-10-28-h6-1-6 of response 6 at 3d376ba (F-VERIFY-2026-10-28-h6-1-5-1, regression against harness-0.9b, consistency with the proposed recovery clarification at 6d3fe3c); hiomux runner fix (new hash 54fe4e86…, superseding OD-0095 correction 1); nothing approved or activated"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-assign-h6-verify-6-and-hiomux-fix.md (owner's message AD, verbatim, with Claude's decisions)
  sha256: 0c645664ea715b6f716e1950c7703fc52a04c8a700a24666141ce3486bd0cd3e
  date: 2026-10-29
  quote: "yes to all"
applies_to:
  - path: phase-b/h6
    revision: 3d376ba11519a87dc5d802d96d3d75570c69c917   # the head; fixed
  - path: proposal/harness-0.9
    revision: 6d3fe3c8916d7595e837f7097a722fc48cd65fe5   # the proposed clarification; fixed
  - path: ~/.hio-runs/bin/hiomux
    revision: "sha256 54fe4e863a1e48b101d3241e6506b4d873d21177a379996409f124151454ceac"
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [F-VERIFY-2026-10-28-h6-1-5-1], ods: [OD-0095, OD-0109, OD-0110]}
---

# OD-0111: sixth verification of H6 assigned; hiomux runner fixed

## Decision 1: assignment

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-10-28-h6-1-6` |
| Verifies | F-VERIFY-2026-10-28-h6-1-5-1 (opened by VERIFY-2026-10-28-h6-1-5, received by OD-0110) |
| Repository | `elusivenode/hio` |
| Base SHA | `5e1582934e1ef88198ff59ffd7b8c947c1ba693b` |
| Head SHA | `3d376ba11519a87dc5d802d96d3d75570c69c917` (branch `phase-b/h6`; fixed; `ls-remote` confirmed) |
| Scope | (1) F-VERIFY-2026-10-28-h6-1-5-1 under `reviews/responses/RESPONSE-REVIEW-2026-10-28-h6-1-6.md` at the head (narrowed recovery: stop when local `main` is ahead; published receipts inspected only; the publication guard); (2) no regression of F-REVIEW-2026-10-28-h6-1-1 to -4 and F-VERIFY-2026-10-28-h6-1-3-1 and -4-1, against operating model §6.2 as amended by harness-0.9b; (3) whether the receiver matches the **proposed** recovery-boundary clarification in `docs/decisions/harness-0.9-proposal.md` §6.1 at `proposal/harness-0.9` `6d3fe3c8916d7595e837f7097a722fc48cd65fe5` (a consistency target, not adopted); (4) the 523-test baseline; CI's exact lint commands |
| Review branch | `review/h6-1-verify-6-codex`, cut at the head |
| Reviewer | Codex, independent reviewer; writes only under `reviews/`; no PR; **every file added under `reviews/` carries YAML front matter with at least `id`** (`tools/check_repo.py` must pass) |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network and the pre-built review environment |

**Stop conditions for the reviewer:**
- the head or the clarification revision differs from `ls-remote`;
- the base is not an ancestor of the head;
- this assignment conflicts with another owner-authored source.

## Decision 2: hiomux runner fix

**The defect (OD-0110):** `commit_for_reviewer` passed an empty expected old value to `git update-ref` whenever the
branch's tip equalled the task base, so a Codex run resuming on its own existing branch could not be committed.

**The fix:** two lines. It keeps the result of `rev-parse --verify -q <ref>` as `existing`, and passes `existing or ""` as
the expected old value.

| File | sha256 |
|---|---|
| `~/.hio-runs/bin/hiomux` | `54fe4e863a1e48b101d3241e6506b4d873d21177a379996409f124151454ceac` (supersedes `25f7b272…`, OD-0095 correction 1) |

`hiomux sa probe`: **ALL PASS** (writes, four canaries not leaked, settings `gpt-6.1-sol`/`high`, AGENTS.md not
autoloaded). The resumed-branch path itself has not yet been exercised end to end. PROTOCOL.md (`13a45eb7…`, OD-0089)
and `orch-prompt.md` are unchanged. Note: `orch-prompt.md` still names OD-0095 correction 1 as the hiomux hash record;
the next session checks this OD's hash instead.

## Not authorised

Receipt of the result (a separate owner yes); adopting the clarification; H6 approval or activation.

## Corrections (append-only)

### Correction 1 (2026-10-29, owner instruction recorded in OD-0112, decision 3)

`~/.hio-runs/orch-prompt.md` now names this OD as the hiomux hash record: one reference, "OD-0095 correction 1" →
"OD-0111", changed in the start-of-session step 2.

| File | sha256 |
|---|---|
| `~/.hio-runs/orch-prompt.md` | `f68cb55eb88a06ca3b980dc70c52a35bdf912c6791c3f45db04063afbd90325b` (supersedes `d2ae1f8e…`, OD-0095 correction 1) |
| `~/.hio-runs/bin/hiomux` | unchanged: `54fe4e863a1e48b101d3241e6506b4d873d21177a379996409f124151454ceac` |
| `~/.hio-runs/PROTOCOL.md` | unchanged: `13a45eb7…` (OD-0089) |
