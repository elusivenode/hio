---
id: OD-0146
title: "Owner authorises receipt of REVIEW-2026-11-04-t0017-1, accepts T-0017 at 4576ae5, and authorises one watched re-run and, if clean, resuming the go-live package at steps 7 and 8"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-receive-accept-t0017.md (owner's message, verbatim, with Claude's decision put)
  sha256: d11d33bdef8a5c378e91a41767fec21eaf73958c3c6e683cfcc9ba03bd8ef3b8
  date: 2026-11-04
  quote: "yes to all"
applies_to:
  - path: review/t0017-1-codex
    revision: 1aa4f3b92b1d1b09e16869392b4c83db589fd58c
  - path: feat/t0017
    revision: 4576ae5335cd6fb8dbd6bc9bc4c476e523d1d84a
base_revision: 6ee8922639a0801045864d94dd9586b5d27c8e96
related: {adrs: [HIO-ADR-0012], tasks: [T-0016, T-0017], findings: [], ods: [OD-0143, OD-0144, OD-0145]}
---

# OD-0146: T-0017 accepted; B-3 resumes

1. **Receipt of `REVIEW-2026-11-04-t0017-1`** (READY, no findings; reviewer tip `1aa4f3b`, hiomux C2 report), by §6.2 step 5.
2. **T-0017 is accepted at `4576ae5335cd6fb8dbd6bc9bc4c476e523d1d84a`**, effective once the receipt is complete; the owner merges #77 with the head match enforced. The review used synthetic inputs and could not reproduce Claude's result on the live file.
3. **Rejecting the stale scheduled run** `41734200727`, and **one more watched dispatch** to test the fixed parser.
4. **If that run is clean,** the go-live package resumes at step 7 (the alert) and step 8 (removing the reviewer rule). Anything other than the expected output stops the sequence and returns to the owner.

**Receipt record (§6.2 5.0–5.7).** Assignment source: the *Assigned reviews* row and OD-0145. Second assignment: looked for in the *Assigned reviews* table, `docs/history/` and the comments on PR #77 (none); none found.

| T | Inventory | Index |
|---|---|---|
| `1aa4f3b92b1d1b09e16869392b4c83db589fd58c` | 3 record files and the README reported; 3 imported, 0 missing, 0 extra, sha256 equal | the reviewer's diff applied: one added Class N row, whose id, base, head, record path and verdict equal the record |

## Not authorised

Any other parser change; any finality claim; any waiver; the probe destroy; the dead-man exercise; any further dispatch beyond the one in item 3 before the rule is removed.

## Corrections (append-only)
