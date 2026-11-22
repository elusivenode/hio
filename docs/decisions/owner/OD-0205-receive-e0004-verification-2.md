---
id: OD-0205
title: "Receipt of VERIFY-2026-11-22-e0004-1-2 (NOT READY) under the standing delegation (OD-0184 A3, OD-0061)"
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
  - path: review/e0004-1-verify-2-codex
    revision: 1de039c2ec91ca6ef2a8b40cf11b7fdf5f8b85e3
base_revision: 0855be3
related: {adrs: [], tasks: [T-0022], findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2, F-VERIFY-2026-11-22-e0004-1-1], ods: [OD-0061, OD-0176, OD-0184, OD-0196, OD-0203, OD-0204]}
---

# OD-0205: second E-0004 verification received

**Receipt of `VERIFY-2026-11-22-e0004-1-2`** (NOT READY; tip `1de039c`; hiomux run `20261122T004427Z-1679`, task C1), by §6.2 step 5 under OD-0061's conditions, in a scratch worktree. Three record files reported and imported, sha256 equal to the report; `check_review_branch.sh` and `check_review_assignment.py` PASS; tag `reviews/VERIFY-2026-11-22-e0004-1-2` peels to the tip. The reviewer's one index row was applied as written (Class N). Claude looked for a second assignment of this target in `reviews/README.md`, the OD records and the PR comments, and found none.

**What the record says.**
- **F-REVIEW-2026-11-22-e0004-1-2: open.** OD-0190's correction 2 is now clean, but another current file holds measurements derived from EODHD returns: `docs/evidence/e0002/assessment-1.md` (per-fund counts of periods within a basis-point threshold, a count of periods differing under a return check, a count of comparisons passing an issuer bar). The assignment allowed a whole-repository search; Claude's own sweep had covered the E-0004 files only.
- **F-VERIFY-2026-11-22-e0004-1-1: technically verified.** A fresh environment from the frozen lock installs `pypdf`, runs the PDF tests with none skipped, and runs the first-release check on the retained releases.
- **F-REVIEW-2026-11-22-e0004-1-1, wording only: verified.** The reviewer's own enumeration gives 256 months, April 2005 to August 2026. The finding's substance was outside this verification and stays open.

**Index reconciliation pending (the owner's, §6.2 step 5.12):** F-VERIFY-2026-11-22-e0004-1-1, from `open` to `verified_closed` at `3528e8e`, as this record states. No other state changes.

**Next under A8:** a whole-repository sweep for EODHD-derived measurements in current files, then their removal, then a third verification. `assessment-1.md` is E-0002's record (T-0022, accepted as tooling only, OD-0171); removing its measurements changes no acceptance.

## Not authorised

Accepting E-0004; closing or waiving any finding; a rerun; rewriting history (OD-0196).

## Corrections (append-only)
