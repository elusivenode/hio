---
id: OD-0229
title: "Owner asks for a public web check of IGB's flagged distribution pair"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-web-check-igb-pair.md (owner's message, verbatim)
  sha256: 169c3827195206be5a8aea0cbaf6f6ec9ba60dab70ac37874e523be54ef80606
  date: 2026-11-22
  quote: "Can we overlay a web search such as yahoo finance to confirm?"
base_revision: e52cd043594ca68cde63b51d2ebaa4b46bedee56
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0210, OD-0228]}
---

# OD-0229: a public web check of IGB's flagged pair

## Owner action

**Authorised, as Claude read it:** read-only lookups of public web pages to confirm whether the two IGB records flagged by the screen (OD-0228) are one payment or two. Claude read the question as the instruction and says so here, so the owner can correct it.

**Done under it:** one read of a public finance page's distribution history for the fund, one web search, and two failed attempts at the issuer's product page. Nothing was downloaded into a store, and no vendor value went into a query. The result is in `docs/evidence/factors/distribution-screen-1.md`.

## What this record does NOT do

It authorises no change to the IGB series, its spec or any build, no further source and no acceptance. The pages read are not adopted as a source, and their rights were not read.

## Corrections (append-only)

None.
