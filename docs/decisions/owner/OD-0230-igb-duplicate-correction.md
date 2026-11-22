---
id: OD-0230
title: "Owner authorises a rebuilt IGB series without its duplicate distribution record, and asks for a critique of a medallion storage design"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-igb-rebuild.md (owner's message, verbatim, with Claude's question)
  sha256: 240f3a1466b32927a2bc4e0c1c147a59172e4134ac2c5e2d2ed3b607fd442b12
  date: 2026-11-22
  quote: "Yes. What we want to do here is build up our data series for factor and portfolio construction with any small corrections we need."
base_revision: 405717a19fb506f3aa1f9602ee67cdf0724eade9
related: {adrs: [HIO-ADR-0009], tasks: [T-0024], findings: [], ods: [OD-0210, OD-0213, OD-0222, OD-0228, OD-0229]}
---

# OD-0230: correcting IGB's duplicate distribution record

## Owner action

**Authorised:**

1. **A proposed spec version** of `rates.au.igb.market_total_return` that names the one excluded vendor record and why. Version 0.1.0 is archived.
2. **One worker change** so the build tool honours an exclusion a spec declares, with tests on invented data.
3. **A local build** of the corrected series, with Claude's real-data check, and an evidence note with no licensed value (OD-0210).

**How a correction works, declared before the build:**

- A correction lives **in the spec**, never in the raw snapshot. The snapshot stays as fetched.
- The spec names the record by its ex-date, with a reason and its evidence. The date is that of a public notice.
- The tool refuses unless **exactly one** distribution record matches, and the build record states what was removed.
- **Expected result:** the corrected series differs from the 0.1.0 build in exactly one period's income and total return, and in every index level from that period on; the screen's D3 flag clears; nothing else changes.

## The owner's direction and question

The owner states the aim: series for factor and portfolio construction, with small corrections as needed. The owner is concerned that no database persists the series, favours a medallion design (bronze, silver, gold) with ELT, and asked Claude to critique it. **That is a request for advice.** This record authorises no storage design, database, service or cost. The approved storage design is `docs/architecture.md` §2 and HIO-ADR-0009; changing it needs an ADR and the owner's approval.

## What this record does NOT do

It corrects no other record and no other fund, and it accepts nothing. "Any small corrections we need" is read as the aim, not as standing permission: each further correction is put to the owner.

## Corrections (append-only)

None.
