---
id: OD-0043
title: "Owner instruction: S1-A16 owner-held evidence relocated from ~/hio-s10/evidence to ~/Documents/hio-evidence (hashes unchanged); test clones and Codex homes deleted; correction note"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-relocate-s1a16-evidence.md (typed by the owner, verbatim)
  sha256: 3c0cd1723e63d701de7ae335fdbeaac6b17bfaf6506c0596dc257da197af2e8a
  date: 2026-10-25
  quote: 'move evidence to ~/Documents/hio-evidence and delete the rest; yes, add the correction note and push'   # two messages, joined with ';'
applies_to:
  - path: reviews/records/HARNESS-2026-10-25-s1a16-1.md
    revision: df5666e927bffe995511ca66eb95e9164dfb79ed   # unedited; this record corrects its evidence paths
  - path: reviews/records/HARNESS-2026-10-25-s1a16-2.md
    revision: df5666e927bffe995511ca66eb95e9164dfb79ed   # unedited; likewise
related: {adrs: [], tasks: [T-0005], findings: []}
---

# OD-0043: S1-A16 evidence relocated (correction note)

## Owner action

The owner instructed two things:
- move the S1-A16 owner-held evidence from `~/hio-s10/evidence` to `~/Documents/hio-evidence`,
  and delete the rest of `~/hio-s10`;
- add this correction note.

## Correction: the path mapping

The harness records, HARNESS-2026-10-25-s1a16-1 and -2, are kept **unedited**. Where they, OD-0041
or a 2026-10-25 handoff name an owner-held evidence path, read it through this mapping:

| Recorded path | Current path |
|---|---|
| `~/hio-s10/evidence/` | `~/Documents/hio-evidence/` |

Everything below that prefix keeps its relative path. For example,
`~/hio-s10/evidence/claude-run-1/session-8628398e.jsonl` is now
`~/Documents/hio-evidence/claude-run-1/session-8628398e.jsonl`.

**The bytes are unchanged.** The move was a same-volume rename. After it, all 12 sha256 recorded
in the two harness records were re-checked at the new location (`shasum -c`: 12 OK), and the
folder holds 337 files.

## Also deleted, and not evidence

These paths are named in the harness records as **setup**, not as evidence, and no longer exist:
- the run-1 clones `~/hio-s10/claude` and `~/hio-s10/codex`, which can be recreated at
  `3fd129e946498e180b9f78a13d3f745afb46c638`;
- the run-2 clone `~/hio-s10/run2/codex`, which can be recreated at
  `df3af48ed874acf3365ecddc1861f93abc1be03e`;
- the Codex homes `~/hio-s10/codex-home` and `~/hio-s10/run2/codex-home`. Their session logs had
  already been preserved in the evidence folder; their sign-in files went with them.

Some originals of the preserved files remain outside both locations, and nothing depends on them:
- the Claude session log in `~/.claude/projects/`;
- the Claude run's scratchpad in `/private/tmp`, which is cleared on reboot.

## Limitations

- `~/Documents/hio-evidence` is the **only** copy of the session logs and the Claude run's
  release outputs. There is no off-machine copy.
- The Codex logs contain account identifiers, so the folder stays private and outside this
  public repository.

## What this record does NOT do

- It does **not** edit any review or harness record, change any recorded hash, or alter the
  S1-A16 result (OD-0041) or the S1a acceptance (OD-0042).

## Corrections (append-only)

None.
