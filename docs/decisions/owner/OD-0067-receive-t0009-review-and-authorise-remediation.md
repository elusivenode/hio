---
id: OD-0067
title: "Receipt of REVIEW-2026-10-25-t0009-1 (NOT READY, seven findings open) by byte-identical import under OD-0061, and the owner's bounded remediation instruction; nothing accepted, waived or authorised beyond T-0009"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-t0009-receipt-and-remediation.md (pasted by the owner, verbatim, with the owner's later reply "fix it now. get main sorted")
  sha256: d57aad18bede36fd55262b67371679c298cc86c2450dfecf324b6c1aece029ca
  date: 2026-10-25
  quote: "Proceed under OD-0061's delegated review-receipt authority."
applies_to:
  - path: reviews/records/REVIEW-2026-10-25-t0009-1.md
    revision: 71f5b3737290164eab89dd7f2c6176dbe6bf2b6e   # reviewer tip; tag reviews/REVIEW-2026-10-25-t0009-1
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: [F-REVIEW-2026-10-25-t0009-1, F-REVIEW-2026-10-25-t0009-2, F-REVIEW-2026-10-25-t0009-3, F-REVIEW-2026-10-25-t0009-4, F-REVIEW-2026-10-25-t0009-5, F-REVIEW-2026-10-25-t0009-6, F-REVIEW-2026-10-25-t0009-7]}
---

# OD-0067: receipt of REVIEW-2026-10-25-t0009-1, and the remediation instruction

## Adverse result first

**REVIEW-2026-10-25-t0009-1: NOT READY. Seven findings, all `open`.** Record: `reviews/records/REVIEW-2026-10-25-t0009-1.md`.
High: F-1 (a missing shared-F1 link changes the rights subject checked at publication), F-2 (a substituted link
authorises an unrelated dataset), F-6 (successful capture-run records omit `keys_checked`). Medium: F-3 (index
comparisons silently omit periods), F-4 (S1b releases cite specs describing other inputs and calendars), F-5 (no dated
RITS and NSW reference fixtures), F-7 (no due-time gate or scheduled workflow definition). Nothing is fixed, verified,
closed or waived. The reviewer reproduced F-1 and F-2 by probe; this receipt does not dispute them.

## Receipt (operating model section 6.2, harness-0.7.1 with the OD-0059 correction, enabled by OD-0061)

| Check | Result |
|---|---|
| 5.0.1 owner-authored assignment | OD-0066 and its verbatim history file `docs/history/2026-10-25-owner-subscription-and-review-assignment.md`, plus the Assigned reviews row, on `main` at `c0588d9` (merged by Claude at the owner's instruction "fix it now. get main sorted"; it was on an unmerged branch until then) |
| 5.0.2 independent report | Codex's final message (pasted by the owner) **and** its exchange report `codex/20261025T100159Z__codex__REVIEW-2026-10-25-t0009-1.json`; `hio-exchange check` PASS |
| 5.0.3 second assignment searched | `git grep` of `origin/main` for the review id before the OD-0066 merge: none; the exchange directories (one Claude delivery message, one Codex report); the open `review/*` branches (none other for this id). No conflicting assignment found |
| 5.1 tip | `ls-remote` one line, `71f5b3737290164eab89dd7f2c6176dbe6bf2b6e`, fetched head equals it and Codex's reported tip |
| 5.2 inventory | expected 2, found 2, missing 0, extra 0: `A reviews/records/REVIEW-2026-10-25-t0009-1.md`, `A reviews/handoffs/2026-10-25-t0009-1-codex.md`; reviewed head `ce0c3b5` is the parent |
| sha256 | record `3a822a5b57c7df1f462ccfb1b970858d80700d5b96b2aa0d9469da3dab4ccf22`, handoff `3fc5ebf8078fc6db001e0c1a969648070b5071a1450a306da5d47e647a0da10f`: equal to Codex's report |
| 5.3 | `tools/check_review_branch.sh` PASS; `tools/check_review_assignment.py` PASS |
| 5.4 tag | `reviews/REVIEW-2026-10-25-t0009-1` (annotated) peels to `71f5b37…`, verified by `ls-remote` |
| 5.6 index rows | Class N only: one received-review row and seven new finding rows in state `open`, ids and severities equal to the record. The existing Assigned row is left as written (it still reads "assigned; not started"; 5.6 does not permit rewriting it in the import, see Notes) |
| 5.7 to 5.9 | blobs equal; `check_repo.py` PASS; trailers PASS; remote tip and tag rechecked immediately before the merge |
| Import commit | `e8c1f803dcd8516fdce1c0393233b2e306183a10`; merge `9efabbeebde5b5a4d8a515d9a1a20812f2624fe0` (`Merge receipt/REVIEW-2026-10-25-t0009-1`), pushed |
| 5.10 | remote `main` equals the local merge; blobs on `main` equal `T`'s; the tag peels to `T`. **Receipt complete** (evidence integrity) |

**CI (reported separately, never merged with the integrity result):** run `40183403651` at `c0588d9` (the OD-0066 merge)
success; run `40183536283` at `9efabbe` (the receipt merge) success. The import commit `e8c1f80` was pushed as part of the
merge and has no separate run.

**Receipt sweep** (`git ls-remote origin 'refs/heads/review/*'`, at the end): 17 branches. Every branch other than
`review/t0009-1-codex` is already recorded as received or dispositioned (`adr0012-codex` OD-0050; `adr0012-verify-1`
and `harness-0.7.1-codex` disposed OD-0057; `adr0012-verify-2` OD-0058; `harness-0.7.1-verify-1` OD-0060;
`s1a-1-verify-*` OD-0037). `review/t0009-1-codex` is now received.

## The owner's instruction (not yet executed)

A bounded remediation of all seven findings within T-0009 scope, adversarial regression tests per finding, the
348-test baseline and the S1a hashes preserved, a new exact fixed head for Codex verification via the exchange, and
escalation only for approved standards, scope, source rights, infrastructure or acceptance. **Remediation has not
started in this record's commit.** It will be submitted at a new fixed head and verification will be assigned by a
further owner-authored source.

## Notes and limits

- **Author-receiver.** Claude authored the work under review and received its review. This is not independent
  (accepted weakness, OD-0061); the owner holds Codex's report and can compare it.
- **Assigned row staleness.** Under 5.6 the import could add rows only. The Assigned reviews row for this review still
  reads "assigned; not started". A status rewrite there is an administrative commit; it is made with this OD.
- A receipt is evidence only. This record does **not** accept, approve, waive or close anything, mark any permission
  verified, authorise S1b, provisioning or any live operation, decide Q-013, or change an approved standard.

## Corrections (append-only)

None.
