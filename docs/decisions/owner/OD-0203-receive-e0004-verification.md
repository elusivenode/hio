---
id: OD-0203
title: "Receipt of VERIFY-2026-11-22-e0004-1-1 (NOT READY) under the standing delegation (OD-0184 A3, OD-0061); remediation of its three points under A8"
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
  - path: review/e0004-1-verify-1-codex
    revision: 73840ae38d7663b933c718db745e047c07216731
base_revision: 1cad8c05730327881bc96173b4fe8d5732ed18b5
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1, F-REVIEW-2026-11-22-e0004-1-2, F-VERIFY-2026-11-22-e0004-1-1], ods: [OD-0061, OD-0184, OD-0196, OD-0201, OD-0202]}
---

# OD-0203: E-0004 verification received

**Receipt of `VERIFY-2026-11-22-e0004-1-1`** (NOT READY; tip `73840ae`; hiomux run `20261122T002623Z-7059`, task C1), by §6.2 step 5 under OD-0061's conditions. Three record files reported and imported, sha256 equal to the report; `check_review_branch.sh` and `check_review_assignment.py` PASS; tag `reviews/VERIFY-2026-11-22-e0004-1-1` peels to the tip. The reviewer's two index rows were applied as written (Class N): the verification row and one new finding row, state `open`. Claude looked for a second assignment of this target in `reviews/README.md`, the OD records and the PR comments, and found none.

**What the record says.**
- **F-1: narrowed, still open.** The reviewer rebuilt the ledger from the 257 retained releases (same hash), confirmed exactly four differing levels, and confirmed 0 of 233 periods differ under both rules, also by its own independent calculation. It leaves the finding open because the run's executed inputs still depart from the adopted rule and `tools/e0004_state.py` still reads the flat file. It also found the addendum overstates coverage: the states read 256 months (April 2005 to August 2026); the 257th, September 2026, was published after the last state's cutoff.
- **F-2: open.** One current file still prints a measurement derived from EODHD returns: OD-0190's correction 2 (the step 1b half-width). **Claude's response claimed that correction was redacted; that claim was wrong.**
- **F-VERIFY-2026-11-22-e0004-1-1 (medium, new):** `pypdf` is not in `pyproject.toml` or `uv.lock`; the PDF tests skip and the real check fails from the frozen environment.

**Index reconciliation pending:** none. The record changes no existing finding's state: both stay `open`.

**Remediation under A8** (a separate PR): the 256-month wording; the redaction of OD-0190's correction 2; the PDF dependency declared and its tests required.

**For the owner, not within A8:** F-1's disposition. The reviewer's reason for leaving it open cannot be removed by a record: it needs a waiver, a run on first-release inputs, or to stay open with the line parked.

## Not authorised

Accepting E-0004; closing or waiving any finding; a rerun.

## Corrections (append-only)
