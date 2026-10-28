---
id: OD-0094
title: "Owner assigns Codex review REVIEW-2026-10-28-h6-1 of the H6 tools at 9e07b8b (phase-b/h6); nothing accepted, approved or activated"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-assign-h6-review.md (owner's messages, verbatim, with the questions they answer)
  sha256: 34b6253966066738c52054dd4b6620685a0e41382d5d16af45d49dc7bc34acb5
  date: 2026-10-28
  quote: "yes"
applies_to:
  - path: phase-b/h6
    revision: 9e07b8b1493a4b4dca2a7d1eb3cf6e7de3f8f33c   # the head; fixed, never rebased during the review
related: {adrs: [HIO-ADR-0008], tasks: [], findings: [], ods: [OD-0092, OD-0072, OD-0077]}
---

# OD-0094: Codex review of H6 assigned

## Assignment (operating model §6.2 step 1)

This record is the owner-authored source. Claude drafted the values; the owner approved them as written (source
file, message I).

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-10-28-h6-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `2cc537428a1ddc33f7434fab8fbb55fe88d20a59` (`main` with OD-0093 correction 1) |
| Head SHA | `9e07b8b1493a4b4dca2a7d1eb3cf6e7de3f8f33c` (branch `phase-b/h6`; fixed) |
| Scope | (1) `tools/hio_assign.py`, `tools/hio_receive.py` and their tests (H6, unactivated); (2) fidelity to operating model §6.2 steps 1, 3, 4, 4a and 5.0–5.11 as approved on `main`, and to the H6 design (`docs/decisions/harness-0.9-proposal.md` §6.1 at `2df83b4`); (3) the nine H6 failure cases, tested by the reviewer itself, not only through the author's tests; (4) a dry run makes no remote write, `main` is never pushed without `--publish`, `main`'s check tools are reused and not weakened, and the 5.11 recovery table holds |
| Review branch | `review/h6-1-codex`, cut at the head |
| Reviewer | Codex, independent reviewer (`codex/reviewer`); writes only under `reviews/`; no PR |
| Delivery | hiomux Codex task, `--model gpt-6-sol --effort xhigh`, `--no-network`; the runner builds the reviewer commit from reported bytes; the push follows the run |

**Stop conditions for the reviewer:**
- the head differs from the tip of `phase-b/h6`;
- the base is not an ancestor of the head;
- this assignment conflicts with another owner-authored source.

With `--no-network`, the reviewer compares the head with the `origin/phase-b/h6` ref in its clone. Claude ran
`git ls-remote origin refs/heads/phase-b/h6` immediately before launching, and it returned the head.

**Index row:** added to *Assigned reviews* with `tools/hio_assign.py --apply` from `phase-b/h6` (its first real
use; it creates no commit), with `--branch review/h6-1-codex`.

## What this does not do

- Accept, approve or activate H6.
- Amend §6.2.
- Make the tools part of any receipt. Receipt of this review follows §6.2 step 5 manually (OD-0061).

## Corrections (append-only)

1. **2026-10-28, delivery changed to network (owner instruction).**
   - **What happened:** under `--no-network`, the first run (hiomux task `CH6`) could not build the pinned test
     environment. uv could not download packages, and the sandbox blocked uv's install directories. It tried
     unrelated local Python environments, including one of the owner's pyenv virtualenvs; none had the project's
     dependencies. **No such run counts as test evidence.**
   - **Cause:** Claude chose `--no-network` without accounting for the test environment.
   - **The owner's words (message J, source file):** "I would rather is had network access and install the tools
     needed to do a good job."
   - **Change:** `CH6` was stopped (reset to `failed`; kept as a failed attempt, never hidden). The review was
     relaunched as task `CH6N`:
     - **with network:** the default under OD-0077, with the same boundary;
     - **told to:** build the pinned environment (Python 3.13, uv), install any tools it needs, run the full suite
       and its own adversarial tests there, and verify the head with `ls-remote`;
     - **unchanged:** every other value (id, base, head, scope, branch, model `gpt-6-sol`, effort `xhigh`).
   - **Check:** Claude re-ran `git ls-remote origin refs/heads/phase-b/h6` before the relaunch, and it returned the
     head.
