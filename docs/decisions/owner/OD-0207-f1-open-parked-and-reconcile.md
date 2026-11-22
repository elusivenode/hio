---
id: OD-0207
title: "Owner leaves F-1 open with E-0004 unaccepted and parked (to be resolved before any resumption or reliance), and authorises reconciling the PDF dependency finding to verified_closed"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-f1-parked-and-reconcile.md (owner's message, verbatim, with Claude's questions)
  sha256: 2216530edbebde37c32e183aa467e5d6d506a6ac09605dd4509d8c8148b097dc
  date: 2026-11-22
  quote: "Yes to both"
base_revision: 2282e123717c7cc844da5f7ee66fd2e600c010e1
related: {adrs: [], tasks: [], findings: [F-REVIEW-2026-11-22-e0004-1-1, F-VERIFY-2026-11-22-e0004-1-1], ods: [OD-0139, OD-0191, OD-0201, OD-0203, OD-0205]}
---

# OD-0207: F-1 stays open, E-0004 parked; one finding reconciled

## Decision 1: F-1

**F-REVIEW-2026-11-22-e0004-1-1 stays open. E-0004 stays unaccepted and parked.** The independently verified state equivalence (VERIFY-2026-11-22-e0004-1-1; `docs/evidence/e0004/cpi-first-release-states-1.md`) is kept as evidence. **Before anyone resumes E-0004 or relies on it, a separate owner decision must resolve F-1:** a waiver, or a run on first-release inputs. `tools/e0004_state.py` still reads the flat file and must not be reused for a first-release claim.

This is not a waiver, and it authorises no rerun. The architect advised it (consultation `20261122T103728-ask-8904`): no current decision needs E-0004, and an open finding on a parked experiment creates no dependency for factor work. Claude agreed.

## Decision 2: index reconciliation (§6.2 step 5.12)

| Finding | Received record and reviewed head | Outcome as the record states it | State before | State after |
|---|---|---|---|---|
| F-VERIFY-2026-11-22-e0004-1-1 | VERIFY-2026-11-22-e0004-1-2 at `3528e8e537a7505d4de3af469f9de0a4dcba4183` (received, OD-0205) | "PDF path technically verified": the frozen lock installs `pypdf`, the PDF tests run with none skipped, the first-release check runs on the retained releases | `open` | `verified_closed` |
| F-REVIEW-2026-11-22-e0004-1-1 | VERIFY-2026-11-22-e0004-1-1 at `f349efeaaf1cd3540e8b206d5f79e511ee1f2410` (received, OD-0203) | "narrowed, still open" | `open` | `open` (narrowed; left open and parked by this OD) |

A transcription of the reviewer's outcomes. It accepts no work and grants no waiver.

## Not authorised

Waiving or closing F-1; accepting E-0004; a rerun.

## Corrections (append-only)
