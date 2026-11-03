---
id: OD-0145
title: "Owner authorises one manual download of the expert-judgement file, T-0017 (parser fix) and one Codex review, after the first live run failed that file"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-t0017-fix.md (owner's messages, verbatim, with Claude's decision put)
  sha256: 017d72e620e71b87e349e2e742c5c1db5324027283bd681d745c90c5511dcc80
  date: 2026-11-04
  quote: "approved"
base_revision: 0a2c0a12925fecae3c7de69e8d2e74d12411f98c
related: {adrs: [HIO-ADR-0012], tasks: [T-0016, T-0017], findings: [], ods: [OD-0143, OD-0144]}
---

# OD-0145: T-0017, after the first live run

The sequence stopped at step 6, as OD-0143 requires (`docs/evidence/b3/first-run.md`). The owner authorised:

1. **One manual GET** of the approved expert-judgement URL, into Claude's scratchpad, for structure only. Done once, HTTP 200. It is not committed and no values are recorded; the local copy is deleted before this record is published.
2. **T-0017**, on `feat/t0017` (PR #77).
3. **One Codex review:**

| Field | Value |
|---|---|
| Review id | `REVIEW-2026-11-04-t0017-1` |
| Target | T-0017, rows P-1 and P-2 of `registers/tasks/T-0017-expert-judgement-parser.md` at the head |
| Base SHA | `0a2c0a12925fecae3c7de69e8d2e74d12411f98c` |
| Head SHA | `4576ae5335cd6fb8dbd6bc9bc4c476e523d1d84a` (`feat/t0017`) |
| Scope | the header detection fails closed and can't misread prose; no other parser or behaviour changes; the fixture holds no publisher text or values. No Azure access; no request to the four data URLs; publishers' documentation pages may be read |
| Review branch | `review/t0017-1-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0145-t0017-parser-fix.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

## Not authorised

Accepting or merging T-0017; removing the reviewer rule; enabling the alert; approving any further run; any other parser change. These return to the owner after the review.

## Corrections (append-only)
