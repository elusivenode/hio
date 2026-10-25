<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0045. -->

**To Claude — Integrate S1b readiness assessment and advance source-rights evidence**

I authorise committing the documentation-only S1b readiness assessment currently prepared on `docs/s1b-readiness-assessment`, after verifying its scope against the current `main`.

Use a controlled `--no-ff` merge and preserve the report's status as proposed. Stop if implementation code, approved standards, ADRs or existing acceptance records have changed unexpectedly.

Following integration, continue T-0002 source-rights verification, prioritising:

1. RBA overnight cash-rate data and AUD/USD observations, as distinct datasets where their rights differ.
2. NY Fed SOFR observations and the SOFR Index.
3. Primary-source evidence of the exact permitted operations: retrieval, raw retention, derived construction, rebuild and internal publication.
4. Publication timing, calendars, revisions and the Australian cash-rate regime.

I authorise limited manual inspection of publicly accessible primary-source documentation and sample data only where the applicable rights permit it. Record access dates, source URLs, terms and uncertainties. Do not automate ingestion or retain data where rights remain unknown.

Prepare an evidence-based recommendation on whether the S1b scope should be staged, including the implications for HIO-ADR-0010 revision 3 and the three originally approved triangulations.

Do not implement S1b, create credentials or infrastructure, schedule capture, contact vendors, or assume any source permission is verified without owner review.

Return only the source-rights decisions that require owner verification and the proposed scope decision.
