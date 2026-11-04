---
id: OD-0168
title: "Owner assigns one more narrow verification of T-0022's F-3 and F-4, and accepts added front matter on Codex's plans as an exception to byte-identical receipt"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-yes-verify-exception.md (owner's message, verbatim)
  sha256: 2ea741de2bc430c83bbc32d1c4f96c5a91fe147b1d7a43ee428df278b02fc9f1
  date: 2026-11-04
  quote: "yes to all"
base_revision: ff82810538573014ff87afa52c88a2529a69741e
related: {adrs: [], tasks: [T-0022], findings: [F-REVIEW-2026-11-04-t0022-1-3, F-REVIEW-2026-11-04-t0022-1-4], ods: [OD-0162, OD-0167]}
---

# OD-0168: verification 2, and a receipt exception

1. **`VERIFY-2026-11-04-t0022-1-2` is assigned.** Its assigned head is the commit that adds this record: `git log -n1 --format=%H -- docs/decisions/owner/OD-0168-verify-2-receipt-exception.md`. Scope: the remediation claims for F-REVIEW-2026-11-04-t0022-1-3 and -4 only, in `tools/eodhd_eval.py` and its tests. Codex receives no licensed bytes or values, and the workspace is unreadable for the run. It writes only under `reviews/`.
2. **Exception accepted.** Front matter added to `reviews/reports/2026-11-04-t0022-1-test-plan.md` (OD-0167) is accepted. The same block is added to this verification's plan, whose sha256 is `6dbbbab02f668b04a2a7a50fa937c3e2e22fb2cc8d56453689443f8f31865f93` on the reviewer's branch and `6dbbbab02f668b04a2a7a50fa937c3e2e22fb2cc8d56453689443f8f31865f93` imported. It covers front matter on Codex's plan files in T-0022 only, no other file, and no verdict or finding.

## Not authorised

Accepting T-0022; closing a finding before verification; changing the receipt procedure generally.

## Corrections (append-only)
