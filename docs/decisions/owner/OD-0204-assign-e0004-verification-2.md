---
id: OD-0204
title: "Assignment of a second, narrow Codex verification for E-0004: F-2 and the new dependency finding, under the standing delegation (OD-0184 A2)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (A2; approved, correction 1)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
applies_to:
  - path: main
    revision: 3528e8e537a7505d4de3af469f9de0a4dcba4183
base_revision: f349efeaaf1cd3540e8b206d5f79e511ee1f2410
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-2, F-VERIFY-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-1], ods: [OD-0184, OD-0196, OD-0201, OD-0202, OD-0203]}
---

# OD-0204: second verification, narrow

| Field | Value |
|---|---|
| Verification id | `VERIFY-2026-11-22-e0004-1-2` |
| Target | "Response 2" in `reviews/responses/RESPONSE-REVIEW-2026-11-22-e0004-1.md` |
| Base SHA | `f349efeaaf1cd3540e8b206d5f79e511ee1f2410` (the head of VERIFY-2026-11-22-e0004-1-1) |
| Head SHA | `3528e8e537a7505d4de3af469f9de0a4dcba4183` (`main`) |
| Scope | **F-REVIEW-2026-11-22-e0004-1-2:** whether any current file at the head holds a measurement derived from EODHD returns (OD-0190's correction 2 in particular; the whole repository may be searched). Git history is outside the question (OD-0196). **F-VERIFY-2026-11-22-e0004-1-1:** whether a fresh environment from the frozen lock runs the PDF tests without skipping and can run the first-release check on the retained PDF releases. **F-REVIEW-2026-11-22-e0004-1-1, wording only:** whether the corrected 256-month statement in the addendum and in `cpi-first-release-states-1.md` is accurate. The finding's substance is **not** re-verified: no closure of it is claimed, and its disposition is the owner's. **Regression** between base and head |
| Local reads allowed | as OD-0202: the BLS-derived files under `~/.hio-research/E-0004/raw/`, `releases/`, `releases-2005/`, `first-release-states/`, and `runs/20261121T230030Z-6745c1fd/states.csv` |
| Excluded | no licensed data (nothing else under `~/.hio-research/`), no EODHD bytes or values, no Azure, no vendor URL; public reads only |
| Review branch | `review/e0004-1-verify-2-codex`, cut at the head |
| The record's `assignment` field | exactly `docs/decisions/owner/OD-0204-assign-e0004-verification-2.md` |
| Delivery | hiomux Codex task, `gpt-6-sol` `high`, with network (public reads only) |

## Not authorised

Accepting E-0004; a rerun; closing or waiving a finding.

## Corrections (append-only)
