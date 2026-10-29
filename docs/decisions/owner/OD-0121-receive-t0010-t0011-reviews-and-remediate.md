---
id: OD-0121
title: "Owner go-ahead to receive REVIEW-2026-10-29-t0010-1 and REVIEW-2026-10-29-t0011-1 (both NOT READY; five findings open) by byte-identical import through pull requests, and authorisation to remediate all five findings; nothing accepted or waived"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-receive-t0010-t0011-and-remediate.md (owner's message AT, verbatim, with Claude's decisions put)
  sha256: 1fb92ece88abad9d8b577311ade7e2108d582c03f653b1c4f75256ca75261db1
  date: 2026-10-29
  quote: "yes to both"
applies_to:
  - path: review/t0010-1-codex
    revision: 17cab4836a9be50425fc76021a943faceac3f655
  - path: review/t0011-1-codex
    revision: 8f469d3563e65e2ed3dd9bb24ca7b3f412817309
related: {adrs: [HIO-ADR-0012], tasks: [T-0010, T-0011], findings: [F-REVIEW-2026-10-29-t0010-1-1, F-REVIEW-2026-10-29-t0010-1-2, F-REVIEW-2026-10-29-t0011-1-1, F-REVIEW-2026-10-29-t0011-1-2, F-REVIEW-2026-10-29-t0011-1-3], ods: [OD-0118, OD-0120]}
---

# OD-0121: receive the T-0010 and T-0011 reviews; remediate their findings

## 1. Receipt (go-ahead for operating model §6.2 step 5, harness-0.9b)

| Review | Reviewer tip (hiomux `result.json`) | Verdict | Findings |
|---|---|---|---|
| `REVIEW-2026-10-29-t0010-1` | `17cab4836a9be50425fc76021a943faceac3f655` | NOT READY | F-…-t0010-1-1 (high): cross-origin redirects; F-…-t0010-1-2 (high): any GitHub job satisfies C6 |
| `REVIEW-2026-10-29-t0011-1` | `8f469d3563e65e2ed3dd9bb24ca7b3f412817309` | NOT READY | F-…-t0011-1-1 (high): alert queries a table not written; F-…-t0011-1-2 (medium): no GitHub failure notification; F-…-t0011-1-3 (medium): `tofu output` ignores the external state |

**Delivery change since OD-0118:** `main` is protected, so step 5.9's merge is made through a pull request from
`receipt/<id>` (its CI must pass), merged with a merge commit carrying the §5.9 subject; 5.10 verifies the result.
Every other step is unchanged. Receipt results are appended below as corrections.

## 2. Remediation

hiomux Sonnet workers fix the five findings on `feat/t0010` and `infra/t0011`, each fix tested to catch its defect on
the reviewed head; Claude writes the remediation responses and records `remediation_claimed`. For t0011 F-2 the fix
specifies the GitHub notification setting and its verification step in the runbook (I-5 is not narrowed).

## Not authorised

Changing any finding's state beyond `remediation_claimed`; a verification assignment (comes back with exact heads);
accepting T-0010 or T-0011; any waiver; Authorisation B.

## Corrections (append-only)

### Correction 1 (2026-10-29): receipts completed; the step 5.3 deviation

**Source:** the owner's message AU, verbatim: "yes.  approved to continue and take the appropriate actions", answering
Claude's question whether to continue the receipts that stopped at step 5.3.

**The stop.** `check_review_assignment.py` compares a record's `assignment` field exactly. Both records named OD-0120 with
its section ("… Assignment 1 on main"; "… on main, Assignment 2"), not the bare path. On the owner's instruction, the check
was run with the expected source written from OD-0120's own section headings; both then passed. Future assignments state
the exact `assignment` string for the reviewer to write.

**The receipts (§6.2 step 5; merged by pull request, `main` protected).**

| Review | T (tip = fetch = report) | Inventory | Tag | Import | Merge (PR) |
|---|---|---|---|---|---|
| REVIEW-2026-10-29-t0010-1 | `17cab4836a9be50425fc76021a943faceac3f655` | 3 added files, sha256 reconciled both ways; README unchanged | `reviews/REVIEW-2026-10-29-t0010-1` peels to T | `8561d63` | `c4164d6` (PR #13) |
| REVIEW-2026-10-29-t0011-1 | `8f469d3563e65e2ed3dd9bb24ca7b3f412817309` | 4 added files, likewise | `reviews/REVIEW-2026-10-29-t0011-1` peels to T | `1fb3679` | `821cdd5` (PR #14) |

5.10: remote `main` = local `821cdd5`; blobs on `main` equal each T; both tags peel to T. **Received.** CI: the run for
`c4164d6` was cancelled by the workflow's cancel-in-progress rule when `821cdd5` was pushed; the `821cdd5` run is
reported separately.

A first import attempt stopped twice before any import (a zsh word-split, then bash 3.2's missing `mapfile`); both tags
were already pushed and verified (5.11: "tag pushed, no import"), and the import resumed at 5.5 with the same T.

**§5.12 (this commit):** both *Assigned reviews* rows set to received; two *Reviewed revisions* rows; five finding rows
added as **open**, each with Claude's `remediation_claimed` (fix commits and responses on `feat/t0010` at `62adccd` and
`infra/t0011` at `0c44b18`). No finding changes state beyond open.
