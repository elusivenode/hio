---
id: OD-0206
title: "Owner authorises removing EODHD-derived numbers from current files across the repository (E-0002 and T-0023 records included), leaving qualitative readings; a third verification of F-2 follows"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-f2-redactions.md (owner's message, verbatim, with Claude's question)
  sha256: ccb19bf73c06f6b743389a058c82c2786ee350150db48179936392557e245134
  date: 2026-11-22
  quote: "Y"
base_revision: bd2e4717016c470ad581913d3c68c16f5741d5d5
related: {adrs: [], tasks: [T-0022, T-0023], findings: [F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0171, OD-0176, OD-0184, OD-0196, OD-0205]}
---

# OD-0206: EODHD-derived numbers out of current files

VERIFY-2026-11-22-e0004-1-2 left F-2 open because `docs/evidence/e0002/assessment-1.md` still held counts computed from EODHD returns. A read-only sweep of every current tracked file then sorted what it found into three tiers.

**The line the owner set:**

| Tier | Examples | Decision |
|---|---|---|
| Counts and measures from comparisons against EODHD data | periods within a basis-point bar, issuer-check pass counts, AUD/USD agreement counts, a percentage of month ends | **removed**, replaced by readings |
| Counts describing EODHD's records, and measured bounds | rows, distributions, splits and date spans per fund; a bound on a NAV return; a count of matching fund-years | **removed**, replaced by readings |
| Qualitative wording | signs, "slightly above", the dates where EODHD disagrees with a reference, the sample length set by fund availability | **stays**: the readings-and-yes/no pattern of OD-0196 |

**Files changed:** `docs/evidence/e0002/assessment-1.md`, `docs/evidence/t0023/corroboration-1.md`, `docs/evidence/t0023/recommendation-1.md`, `registers/experiments.yaml`, `handoffs/s1b1/2026-11-04-research-e0001-to-e0003.md`, `handoffs/s1b1/2026-11-04-t0023-consolidation.md`, `knowledge/findings.md`. Figures from the RBA, BLS, H.10's own archive and SEC filings are not EODHD-derived and stay.

**Unchanged:** every acceptance (T-0022 as tooling only, OD-0171); the git history (OD-0196); the local reports, which keep the numbers. One AUD/USD rate in `docs/research/T-0003-vendor-assessment-2026-11-04.md` stays: it most likely came from EODHD's public pricing page, not the licensed feed.

**Authorised with it:** a third Codex verification of F-2, assigned by Claude under OD-0184 A2.

## Not authorised

Closing or waiving F-2; rewriting history; any change to a result or an acceptance.

## Corrections (append-only)
