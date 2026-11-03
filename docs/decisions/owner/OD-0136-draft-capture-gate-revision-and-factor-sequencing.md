---
id: OD-0136
title: "Owner authorises two drafts only: a revision of the B-2 and B-3 prerequisites, and a proposal to reorder work around factors"
decision: authorise_work
record_status: recorded
created_at: 2026-11-03
updated_at: 2026-11-03
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-03-owner-capture-gate-factor-sequence-drafts.md (owner's messages, verbatim, with Claude's decisions put)
  sha256: ac350f720ce140c84cf2a500957e1ec2247f2f0444eb814a3b1cc82d55637fe2
  date: 2026-11-03
  quote: "yes to both"
base_revision: 6030c17c980591bc8498d8cb77852647616ffb83
related: {adrs: [HIO-ADR-0009, HIO-ADR-0012], tasks: [T-0009, T-0015], findings: [], ods: [OD-0063, OD-0089, OD-0119, OD-0132, OD-0135]}
---

# OD-0136: two drafts authorised

1. **A draft revision of the B-2 and B-3 prerequisites**, allowing exploratory capture labelled P3 once storage integrity and access
   controls are shown. C5 stays explicitly unresolved, and finality stays owed before any final claim, S1b-1 completion or G2.
   Drafted as `docs/evidence/S1B1-authorisation-B-revision-1.md` (proposed).
2. **A draft proposal to reorder the work around factors**, moving the duration factor and the Parquet and DuckDB analytical layer ahead
   of further storage work, and setting out the effect on base camp and the roadmap. Drafted as
   `docs/decisions/factor-first-sequencing-proposal.md` (proposed).

Both are on `proposal/capture-gate-factor-first`. **Neither is adopted.** The solution architect was consulted twice
(`20261103T141451-ask-15e3`, `20261103T142328-ask-3901`); advice only.

**The decision on REVIEW-2026-11-03-t0015-1 stays open:** "yes to both" answered these two drafts, not that question.

## Not authorised

Capture; any Azure write or dispatch; B-3; a C5 amendment; a change to any gate or ordering; any download, build, purchase or vendor
contact; any rights verification; a stack change; receipt or remediation of the T-0015 review; acceptance of T-0015.

## Corrections (append-only)
