---
id: OD-0018
title: "Owner instructions: confirm OD-0010's T-0004 review mechanics; continue T-0002/T-0003; prepare a proposed SMSF-owned ETF diagnostic card; correct roadmap dates and gates"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-s1a-authorisation.md (the owner's chat message, verbatim)
  sha256: 829b9fd2769c03ce82035e07dadb4242c8ba074ea78ab5d2ac1a3519b7839e8a
  date: 2026-10-24
  quote: "I confirm the cross-lineage review mechanics described in OD-0010. [...] Do not merge the amendment without my subsequent decision. [...] Separately, prepare a proposed, SMSF-owned ETF diagnostic task card. [...] Correct the material roadmap date and gate inconsistencies without changing approved architectural substance."
applies_to:
  - path: docs/roadmap.md
    revision: e32d282   # = macsmsf@dc4fd02 content
related: {adrs: [], tasks: [T-0002, T-0003, T-0004], findings: []}
---

# OD-0018: T-0004 mechanics, parallel work, ETF card, roadmap

## Owner action

1. **T-0004:** OD-0010's cross-lineage review mechanics are **confirmed**. Codex may review the
   pinned target `macsmsf@fe3fdc7` in a separate read-only worktree, and commit its evidence
   only on the scoped review branch. **No merge of the amendment without the owner's later
   decision.**
2. **T-0002 and T-0003** continue under their existing restrictions. Source permissions stay
   unverified and blocked. Vendor questions stay drafts. **No vendor contact.**
3. **Prepare a proposed, SMSF-owned ETF diagnostic task card.** Its objectives:
   - distinguish asset-class returns from fund-specific underperformance;
   - quantify ETF liquidity and tracking characteristics;
   - identify current economic and factor exposures;
   - evaluate hypothetical exposure-replacement scenarios.

   It uses read-only interfaces and preserves all existing `macsmsf` functionality. **Not to be
   implemented until separately authorised.**
4. **Correct the material roadmap date and gate inconsistencies**, without changing approved
   architectural substance. Wording that forms part of an approved blob is preserved unless it
   is changed through the appropriate process.

## Where the work lands

- The ETF card is **SMSF-owned**, so it lives in `macsmsf`, on its own unmerged branch, not
  here. HIO does not depend on it (`AGENTS.md` boundaries).
- **T-0004 receipt.** OD-0010 put the review branch in `macsmsf`, cut from the commit that
  adds OD-0010 (`macsmsf@760f73e`). The staging branch is now frozen as the migration source.
  Receiving the review record into this repository is a separate step, flagged for the owner.

## What this record does NOT do

- It does not merge T-0004 or accept its review.
- It does not authorise the ETF diagnostic workstream, any `macsmsf` code change, or any HIO
  dependency on `macsmsf`.
- It does not verify any source permission, or authorise vendor contact.
