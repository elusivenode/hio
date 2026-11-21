---
id: OD-0195
title: "E-0004 review received (NOT READY, two high findings), under the standing delegation (OD-0184 A3, A8)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (A3 receipt under OD-0061's conditions; A8 remediation)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
base_revision: dee96f1
related: {adrs: [], tasks: [T-0023], findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0061, OD-0176, OD-0190, OD-0191, OD-0192]}
---

# OD-0195: E-0004 review received

**Receipt of `REVIEW-2026-11-22-e0004-1`** (NOT READY; received tip `8d2ae05`: the review at `b26b4a8` (task C2) plus the reviewer's front-matter fix (task C3); hiomux run `20261121T232821Z-7052`), by §6.2 step 5 under OD-0061's conditions. Three record files reported and imported, sha256 equal to the report; `check_review_branch.sh` and `check_review_assignment.py` PASS; tag `reviews/REVIEW-2026-11-22-e0004-1-r2` peels to the received tip; the first tip is tagged `reviews/REVIEW-2026-11-22-e0004-1` and not received. Claude added the Class N rows: one review row and two finding rows, state `open`. An earlier attempt (C1) stopped because the assignment postdated the head, and the Codex CLI couldn't resume it; C2 read the assignment from public `main`.

**The findings.**
- **F-1 (high):** the CPI state used today's flat file and a 10-release sample, so it doesn't establish the adopted first-release rule at every month used. Not shown that any level differs.
- **F-2 (high):** public evidence records measurements derived from EODHD returns (stress-month counts, clusters and concentration in `step1-1.md`; the precision half-width in `step1b-1.md`; both repeated in `result-1.md`), which OD-0176 keeps out of the repository.

**Remediation under A8:** F-2's measurements are removed from the current files. **Not within A8, and for the owner:** whether to rewrite the public git history that still holds them, and F-1's path (a further CPI download to establish first-release levels, or a prospective amendment and a new run).

## Not authorised

Accepting E-0004; closing either finding before verification; a second E-0004 run; rewriting history; any further download.

## Corrections (append-only)
