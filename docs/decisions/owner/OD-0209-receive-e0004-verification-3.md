---
id: OD-0209
title: "Receipt of VERIFY-2026-11-22-e0004-1-3 (NOT READY) under the standing delegation (OD-0184 A3, OD-0061)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (A3 and A8; approved, correction 1)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
applies_to:
  - path: review/e0004-1-verify-3-codex
    revision: 1b2f451d2359b48148cce578426cf57dd90d8777
base_revision: 74b79489b2521274ed8996ebb9015f5676c60d28
related: {adrs: [], tasks: [T-0022], findings: [F-REVIEW-2026-11-22-e0004-1-2], ods: [OD-0061, OD-0176, OD-0184, OD-0196, OD-0206, OD-0208]}
---

# OD-0209: third E-0004 verification received

**Receipt of `VERIFY-2026-11-22-e0004-1-3`** (NOT READY; tip `1b2f451`; hiomux run `20261122T010344Z-eb88`, task C1), by §6.2 step 5 under OD-0061's conditions, in a scratch worktree. Three record files reported and imported, sha256 equal to the report; both checks PASS; tag `reviews/VERIFY-2026-11-22-e0004-1-3` peels to the tip. The reviewer wrote no index row; Claude added the verification row (Class N). No second assignment of this target was found in `reviews/README.md`, the OD records or the PR comments.

**What the record says.**
- **F-REVIEW-2026-11-22-e0004-1-2: open.** Exact counts computed from EODHD data remain, written as words: in `docs/evidence/e0002/assessment-1.md` (a residual count in the internal check, and residual counts in the comparison with the issuer's rows) and in `docs/evidence/e0002/stability-1.md` (a count of distribution records whose ex-date moved). **Two of the assessment's counts are in sentences Claude wrote in the previous redaction** ("all but one", "every amount but one"). The stability count was in the sweep's borderline tier, which OD-0206 left in place; the reviewer reads it as a count under that OD's own line. The reviewer says its list is enough for the question, not exhaustive.
- **Regression:** the redactions changed no result, verdict or acceptance statement.
- **An observation for the owner, separate from the verdict:** some qualitative readings that OD-0206 keeps still communicate computed results of EODHD comparisons, and `registers/sources.yaml` still says derived results stay local and no values enter the repository. Whether such readings are restricted is a rights interpretation for the owner.

**Index reconciliation pending:** none.

**Next under A8 and OD-0206:** remove every count from EODHD data in whatever form, words included; a second sweep by a fresh reader with that stricter test; then a fourth verification.

## Not authorised

Closing or waiving F-2; rewriting history; any change to the rights row.

## Corrections (append-only)
