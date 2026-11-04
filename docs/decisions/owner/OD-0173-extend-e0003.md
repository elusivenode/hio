---
id: OD-0173
title: "Owner authorises E-0003 variant V1: back to May 2007, with 2008 as a named window"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-extend-e0003.md (owner's message, verbatim)
  sha256: 77b1a91a63acce07534b9533d0350da8945b76b7aa9f92ac1428654ba0a118ec
  date: 2026-11-04
  quote: "yes, extend"
base_revision: 51f35874b6796c74ffff313331734ab05d4818d6
related: {adrs: [], tasks: [T-0022], findings: [], ods: [OD-0170, OD-0172]}
---

# OD-0173: E-0003 back to May 2007

As put to the owner: pre-registered before any result; daily accrual of `FIRMMCRID` on published dates to the end of 2010, then the RBA's index from 2011, with the seam stated; the same three allocations, FX, rebalancing and bootstrap, now over about 233 months, with 2008 as a named window; a seam check; results local, for the owner.

## How Claude read it

**No new dependency.** The series is extracted once from the retained `.xls` with a temporary reader (`uv run --with xlrd`) into a local file with its hash, and only that is used. The seam check tests the accrual method where it can be tested: the same method on the current F1's `FIRMMCRID` against the RBA's index, from 2011. The two files don't overlap in time.

## Not authorised

Any other source; any release; E-0003's first result is unchanged and stands. Nothing is accepted.

## Corrections (append-only)
