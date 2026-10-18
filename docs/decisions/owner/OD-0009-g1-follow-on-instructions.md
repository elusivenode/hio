---
id: OD-0009
title: Owner instructions accompanying the G1 decisions (§6.2 reports path; T-0002; T-0003; prepare T-0004; S1a limits)
decision: authorise_work
record_status: recorded
created_at: 2026-10-18
updated_at: 2026-10-18
recorded_by: claude/documentation-agent
owner_statement:
  source: hio/docs/history/2026-10-18-owner-g1-decisions.md (the owner's chat message, verbatim)
  sha256: 111b6fc200c46c70a2f5f20b8120a3c52b1cc54ceb0b2c18ef05ff7ec306a99e
  date: 2026-10-18
  quote: "Add hio/reviews/reports/ to the reviewer paths in §6.2. I authorise T-0002 and T-0003 as research tasks. Prepare the documentation-only T-0004 amendment under C1 for separate review. Do not start S1a until G1 is complete and I explicitly authorise its scope. Do not perform live data operations under S1a."
applies_to:
  - path: hio/
    revision: f7a9ec90bb2f0cbd58272c5bd0f0da07948a4ecb
related: {adrs: [HIO-ADR-0003, HIO-ADR-0008, HIO-ADR-0010], tasks: [T-0002, T-0003, T-0004, T-0005], findings: []}
---

# OD-0009: G1 follow-on instructions

## Owner action

1. **Add `hio/reviews/reports/`** to the reviewer write paths in operating model §6.2. This is a
   content change to the operating model approved in OD-0008, so it is recorded as harness-0.6.
2. **Authorise T-0002 and T-0003** as research tasks.
3. **Prepare the T-0004 amendment** under C1: documentation only, for separate review.
4. **The returned ADR-0010:** the owner returned it "for revision to separate synthetic-fixture
   S1a from live-data S1b" (OD-0008). Claude prepares that revision as `proposed`.
5. **S1a limits:**
   - do not start S1a until G1 is complete and the owner explicitly authorises its scope;
   - no live data operations under S1a.

## What this record does NOT do

- It does not approve the revised ADR-0010 or the harness-0.6 amendment's text.
- It does not authorise S1a.
- It does not authorise any live data operation or merge to `macsmsf` main.
