---
id: RESPONSE-REVIEW-2026-10-25-t0009-1-2
author: claude/implementation-agent
findings: [F-REVIEW-2026-10-25-t0009-5]
responds_to: VERIFY-2026-10-28-t0009-1-1   # reviewer tip 639d3566f88d1cf8e9cc299d47451757a12fd038 (tag reviews/VERIFY-2026-10-28-t0009-1-1); received by OD-0075 (merge 5330307); F-5 part verified, open
previous_submission_head: 76539b536118b2afee5c3aa53eab0c1b49444e86
authorised_by: OD-0076   # the owner approved D7 and instructed the remediation to proceed; OD-0067 for the remediation itself
fix_commits:
  - 4f7943ff6460c7c3e2926bd7ad45deda07c70a38   # F-5 (completion)
test_commits: []   # the fix commit carries its own tests
submission_head: self            # resolve: git log -n1 --format=%H -- reviews/responses/RESPONSE-REVIEW-2026-10-25-t0009-1-2.md
created_at: 2026-10-28
---

# Remediation response 2: F-5 completed with real reference calendars

> **Author's claim, not verification.** F-5 stays **open** until Codex verifies it at a fixed head
> the owner assigns. The other six findings were verified closed at `76539b5` (VERIFY-2026-10-28-t0009-1-1);
> `76539b5..` changes no file they depend on except `registers/sources.yaml` (one new entry).

## What VERIFY-2026-10-28-t0009-1-1 left open

"No dated RITS or NSW reference source is retained or checked against a real cited calendar; D7 rights
remain unverified. Thus the original A-8 reference-data requirement is unsatisfied."

## What changed (`4f7943f`)

| Change | Detail |
|---|---|
| D7 rights | The owner approved D7 (OD-0076). New register entry `rba_calendar_pages`: `owner_verified`, `verified_by: OD-0076`. Automated retrieval `deny` (manual, cited read only). Retention, compute, derivation, derived storage, `hio_internal`, external processing and agent context are `conditional` on RBA attribution, no implied endorsement and the RBA copyright §5 Financial Data conditions. Consumer distribution, quotation and post-termination rights stay `unknown` |
| Real calendars | `src/hio/reference/calendars/rits-2026.yaml` and `nsw-2026.yaml`: `kind: reference`, `as_of: 2026-10-28`, coverage 2026-01-01..2026-12-31, the source URLs, the sha256 of each page as read, and the citation with the RITS rule quoted verbatim. Only the extract is committed, not the pages |
| Tests | `tests/test_s1b1_reference_calendars.py` (8 tests): the files load as reference data without `allow_synthetic`; the source is owner-verified for the operations used; RITS closures ⊂ NSW closures, differing on exactly 27 April, 3 August and 5 October; on the NSW Bank Holiday (3 August) the AUD series has a RITS period end and uses that day's rate, while NSW period ends skip it but still select the 3 August RITS rate for one day; `Calendars` accepts both; dates outside 2026 refuse |

**The source pages** (read once, 2026-10-28 05:30 UTC, HTTP 200): the RITS Business Hours page (sha256 `ac946ce4…067b`) gives the
rule; the Public & Bank Holidays – 2026 page (sha256 `b027fedd…294d`) gives the dates.

## Interpretations (Claude's, for the reviewer to check)

1. **RITS closes on a named holiday only where it is observed in both NSW and Victoria** (the rule's wording).
   - **27 April 2026** (NSW "Additional Day"): not a named holiday and not listed for Victoria, so RITS is read as
     **open**. The research note mentions a RITS Advice 02/2026 about this day (search extract only). That advice
     was not read: D7 authorised the two pages only.
   - **28 December** ("Boxing Day Observed", all states) is read as Boxing Day, so RITS is **closed**.
2. **NSW calendar = public and bank holidays observed in NSW** (the F11 publication rule). It includes the
   3 August Bank Holiday, which the page marks "(a) Not a state-wide public holiday".

## Evidence

| Claim | Method | Result |
|---|---|---|
| Suite | `uv run --no-sync pytest -q` at `4f7943f` | **416 passed** (408 + 8) |
| Mutation | the 3 August line deleted from the NSW file | 2 of the 8 tests fail; restored file hash unchanged |
| Checks | `tools/check_repo.py`; `ruff check`; `ruff format --check` | PASS / clean / clean |
| Outputs | release fixtures still use the synthetic calendars | no S1a or S1b release output changes |

## Limits

- **Coverage is 2026 only.** A 2027 calendar needs the 2027 page, which falls under the same D7 approval and is a
  later manual read (register `review_due: 2027-01-31`).
- **The live RBA terms were not re-read (U7).** The rights rest on the matrix's recorded clauses and the owner's
  approval.
- **No real rate data is used.** The rates in the tests are invented.
- **The register is a governance file.** Its one new entry transcribes the owner's D7 action (OD-0076); no other
  entry changed.

Nothing here closes, accepts or waives anything.
