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
