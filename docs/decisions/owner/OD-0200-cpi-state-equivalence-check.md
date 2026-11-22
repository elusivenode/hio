---
id: OD-0200
title: "Owner authorises a CPI-only check for E-0004 F-1: 12 earlier releases (cap 15 requests), a first-release series, and a state comparison; no re-estimation"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-cpi-state-check.md (owner's message, verbatim, with Claude's question)
  sha256: d4f027ccc527a310bfc70aadb321329a84d09bdf11d7ceb2ed29b87c445faaee
  date: 2026-11-22
  quote: "Y"
base_revision: 447c72878884714d7e8d6a0b421171606f108765
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1], ods: [OD-0188, OD-0190, OD-0191, OD-0195, OD-0197, OD-0198]}
---

# OD-0200: CPI-only state check

OD-0197's comparison found four first-release levels that differ from the flat file (May to August 2016; `docs/evidence/e0004/cpi-first-release-check-2.md`), and Claude stopped as that OD requires.

**Authorised, once:**

1. **Download** the 12 archived CPI releases dated 2005-05-01 to 2006-04-30 in `release-dates.csv`, which first published the levels for April 2005 to March 2006. Hard cap **15 requests**. Same rights, notice, contact handling and retention as OD-0197; kept in `~/.hio-research/E-0004/releases-2005/`.
2. **Build the first-release series:** each month's level as printed in its own release, for every level the state calculation reads.
3. **Compare states:** recompute the state for every period of the run from the first-release series, and compare it date by date with the states the run used, for the primary rule and the equality-as-accelerating sensitivity, with the unavailable periods.

`bls_cpi`'s automated-retrieval condition is satisfied for this download only.

**The architect's advice** (consultation `20261122T101027-ask-d155`): recommend this check; an amendment alone would not show the deviation's effect, and a rerun now is premature. If the states are identical, an owner-approved deviation record and result addendum without re-estimation; if they differ, a separately authorised corrected run or the line left parked with its limitation. Claude agreed.

## Not authorised

Any portfolio re-estimation or rerun of E-0004; any design change; any change to the preregistration; any other download; any disposition of F-1, which follows the result and is a separate owner action.

## Corrections (append-only)
