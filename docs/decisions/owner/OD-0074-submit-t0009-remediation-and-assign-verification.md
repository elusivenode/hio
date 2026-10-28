---
id: OD-0074
title: "Owner instructs the T-0009 remediation push and author PR (#6, Submission-Head 76539b5), and assigns Codex verification VERIFY-2026-10-28-t0009-1-1 of REVIEW-2026-10-25-t0009-1 at that head; nothing accepted, closed or waived"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-t0009-push-pr-and-verification.md (typed by the owner, verbatim)
  sha256: f54beca9bd1d2de596542920215627e8399b09c29216fe764a7049e45b868d2b
  date: 2026-10-28
  quote: "Push the T-0009 remediation branch and open its PR, then assign Codex verification."
applies_to:
  - path: impl/t0009-remediation-1
    revision: 76539b536118b2afee5c3aa53eab0c1b49444e86   # the submission head; fixed, never rebased during verification
related: {adrs: [HIO-ADR-0012], tasks: [T-0009], findings: [F-REVIEW-2026-10-25-t0009-1, F-REVIEW-2026-10-25-t0009-2, F-REVIEW-2026-10-25-t0009-3, F-REVIEW-2026-10-25-t0009-4, F-REVIEW-2026-10-25-t0009-5, F-REVIEW-2026-10-25-t0009-6, F-REVIEW-2026-10-25-t0009-7], ods: [OD-0067, OD-0072, OD-0073]}
---

# OD-0074: T-0009 remediation submitted; Codex verification assigned

## Owner actions (verbatim in the source file)

1. **Submission (operating model §6.2 step 0).** Done by Claude on this instruction, before this record:
   - `impl/t0009-remediation-1` pushed; `ls-remote` = `76539b536118b2afee5c3aa53eab0c1b49444e86`;
   - author PR [#6](https://github.com/elusivenode/hio/pull/6) to `main`, `Submission-Head: 76539b536118b2afee5c3aa53eab0c1b49444e86`;
   - diff `ce0c3b5..76539b5` scanned for credentials before the push: none.
2. **Verification assignment (operating model §6.2 step 1).** This record is the owner-authored source. The
   values below were drafted by Claude from the records and confirmed by the owner (source file, message 2).

   | Field | Value |
   |---|---|
   | Verification id | `VERIFY-2026-10-28-t0009-1-1` |
   | Verifies | `REVIEW-2026-10-25-t0009-1` (record on `main`, blob `69ccb93`, equal to tag `reviews/REVIEW-2026-10-25-t0009-1`; received by OD-0067, merge `9efabbe`) |
   | Repository | `elusivenode/hio` |
   | Base SHA | `ce0c3b534ac98eb89663cf15c439f5ccad93b969` (the reviewed head) |
   | Head SHA | `76539b536118b2afee5c3aa53eab0c1b49444e86` (branch `impl/t0009-remediation-1`, PR #6; fixed) |
   | Scope | the remediation claims for F-1 to F-7 in `reviews/responses/RESPONSE-REVIEW-2026-10-25-t0009-1.md` at the head: for each finding, `verified_closed`, `remediation_rejected`, or (F-5, claimed in part) the part verified and the part still open; any regression the fixes introduce against the original review's six questions, T-0009 Authorisation A, HIO-ADR-0012 (approved rev 3) and the return accounting standard; the 348-test baseline and the S1a `data.csv` hashes and release identities preserved |
   | Review branch | `review/t0009-1-verify-1-codex`, cut at the head |
   | Reviewer | Codex, independent reviewer (`codex/reviewer`); writes only under `reviews/`; no PR |
   | Delivery | hiomux (OD-0072, OD-0073), Codex task with `--model gpt-6-sol --effort high`, sandbox `workspace-write`; the runner builds the reviewer commit from reported bytes; the push follows the run |

   **Stop conditions for the reviewer:** the head differs from `ls-remote`; `ce0c3b5` is not an ancestor of the
   head; the review record blob on `main` differs from the tag. The test plan is fixed before the response is read.

## What this does not do

Accept, approve, close or waive anything; merge PR #6 (it merges only on a separate owner instruction); decide D7
(F-5 cannot fully close without it); verify any source right; authorise any live operation, schedule, provisioning
or credential; change the harness. Receipt of the verification follows operating model §6.2 step 5 (OD-0061).

## Corrections (append-only)

None.
