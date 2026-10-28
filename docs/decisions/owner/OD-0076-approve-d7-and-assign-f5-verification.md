---
id: OD-0076
title: "Owner approves D7 (RBA RITS and holiday pages: owner_verified to retain and cite as reference data, manual read only), authorises the one manual read and the F-5 completion, and assigns Codex verification VERIFY-2026-10-28-t0009-1-2 of F-5 at 846974b; nothing accepted or waived"
decision: authorise_work
record_status: recorded
created_at: 2026-10-28
updated_at: 2026-10-28
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-28-owner-d7-approval.md (typed by the owner, verbatim)
  sha256: 6f90225abe2ee93238a9b4925024a6fe9f03f88df51efa435e5cdbc4570c5060
  date: 2026-10-28
  quote: "yes, approve D7 and proceed"
applies_to:
  - path: registers/sources.yaml (entry rba_calendar_pages, on impl/t0009-remediation-1)
    revision: 4f7943ff6460c7c3e2926bd7ad45deda07c70a38
  - path: impl/t0009-remediation-1
    revision: 846974b2c43e5b9839809af0f1ebc08cee4e88b1   # the submission head assigned for verification; fixed
related: {adrs: [HIO-ADR-0012], tasks: [T-0002, T-0009], findings: [F-REVIEW-2026-10-25-t0009-5], ods: [OD-0013, OD-0067, OD-0074, OD-0075]}
---

# OD-0076: D7 approved; F-5 completed; its verification assigned

## Owner actions (verbatim in the source file)

The owner answered "yes, approve D7 and proceed" to Claude's question. The question and the sequence it would set
going are quoted in the source file.

1. **D7 approved** at the T-0002 matrix's recommended values (row D7; readiness package §1.2):
   - **verification:** `owner_verified` for the source `rba_calendar_pages`;
   - **allowed, on conditions:** retain and cite as reference data, compute, derive, store derived results, internal
     use, external processing and agent context. The conditions are RBA attribution, no implied endorsement and the
     RBA copyright §5 Financial Data conditions;
   - **retrieval:** manual only (`automated_retrieval: deny`);
   - **unchanged:** consumer publication, quotation and post-termination rights stay `unknown`.

   This is the first owner verification of an RBA source. It covers D7 only: OD-0013's hold on
   `rba_statistical_tables` (D1–D6) is unchanged.
2. **Manual read authorised, once.** Done 2026-10-28 05:30 UTC by `curl`, with a declared user agent:
   - `https://www.rba.gov.au/payments-and-infrastructure/rits/business-hours.html` (HTTP 200, sha256 `ac946ce4…067b`);
   - `https://www.rba.gov.au/schedules-events/bank-holidays/` (HTTP 200, sha256 `b027fedd…294d`).

   Only a dated, attributed extract is committed. The pages themselves are not.
3. **F-5 completion.** On `impl/t0009-remediation-1`:
   - fix `4f7943f`: the real 2026 calendars, the register entry and 8 tests;
   - response `RESPONSE-REVIEW-2026-10-25-t0009-1-2` at `846974b`;
   - pushed; PR #6 now names `Submission-Head: 846974b2c43e5b9839809af0f1ebc08cee4e88b1`.
4. **Verification assignment** (operating model §6.2 step 1). The owner's "proceed" adopted Claude's stated sequel
   ("Then Codex verifies F-5 alone"). The values below are transcribed from that sequel and the records; this record
   is the owner-authored source.

   | Field | Value |
   |---|---|
   | Verification id | `VERIFY-2026-10-28-t0009-1-2` |
   | Verifies | F-REVIEW-2026-10-25-t0009-5 of `REVIEW-2026-10-25-t0009-1`, left open by `VERIFY-2026-10-28-t0009-1-1` (received, OD-0075) |
   | Repository | `elusivenode/hio` |
   | Base SHA | `76539b536118b2afee5c3aa53eab0c1b49444e86` (the previously verified head) |
   | Head SHA | `846974b2c43e5b9839809af0f1ebc08cee4e88b1` (branch `impl/t0009-remediation-1`, PR #6; fixed) |
   | Scope | F-5 only, against T-0009 §2.7 and A-8: whether the retained RITS and NSW calendars are dated, cited reference data matching the cited RBA pages as the response states them; the two interpretations the response names (27 April, 28 December); and the tests of rate selection and period ends on the dates where RITS and NSW differ. Also: that `76539b5..846974b` changes nothing the six verified findings depend on, apart from the one new register entry, which matches this record; the 416-test suite and the S1a hashes and release identities are unchanged |
   | Review branch | `review/t0009-1-verify-2-codex`, cut at the head |
   | Reviewer | Codex, independent reviewer (`codex/reviewer`); writes only under `reviews/`; no PR |
   | Delivery | hiomux (OD-0072, OD-0073); `--model gpt-6-sol --effort high`, sandbox `workspace-write` (no network: the reviewer checks the extract against the recorded page hashes and quotations, not the live pages) |

   **Stop conditions for the reviewer:**
   - the head differs from the assigned head;
   - `76539b5` is not an ancestor of the head;
   - the record blob of `VERIFY-2026-10-28-t0009-1-1` on `main` differs from its tag.

   The reviewer fixes its test plan before it reads `RESPONSE-REVIEW-2026-10-25-t0009-1-2`.

## What this does not do

- It does not verify any other RBA or NY Fed dataset. D1–D6, D8 and D9 stay `unverified`.
- It does not authorise automated retrieval of anything, a 2027 read (`review_due: 2027-01-31`), or any live
  operation.
- It does not close F-5, accept T-0009 or merge PR #6.
- It does not decide U7: the live RBA terms were not re-read.

## Corrections (append-only)

None.
