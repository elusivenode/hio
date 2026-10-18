---
id: HANDOFF-2026-10-18-a01-independent-review
date: 2026-10-18
actor: codex/reviewer
work_status: in_review
base_revision: 35c9821f805955914b05991c1c075b8cb3e082b5
head_revision: self
work_commits: []
work_card: T-0001 (review input; the card itself remains proposed)
---

# Handoff: independent A01 design review

> A dated snapshot, not an owner decision or approval. The exact target reviewed is
> `macsmsf` `1502ab8804c5968a8bf91fa36275c44e6e84f575..35c9821f805955914b05991c1c075b8cb3e082b5`.
> Review-document commits made after `35c9821` are not part of the reviewed baseline.

## Changed files

- `reviews/records/REVIEW-2026-10-18-a01.md`: the independent record and eight findings.
- `reviews/README.md`: reviewed revision and current finding states.
- `STATUS.md`: navigational snapshot of the review verdict.
- This handoff.

No implementation, standard, ADR, factor spec, SMSF file or production data was changed by
the reviewer.

## Done

- Fixed base and head from Git before reading the author reports. The direct owner request in
  this Codex session assigned the review even though the index's *Assigned reviews* table had
  not been updated; the assignment source is stated in the review record.
- Read all three handoffs, the canonical A01 documents, the four SMSF pointer edits and the
  prior HIO-001 review history.
- Reproduced illustrative equity, FX, futures, cash-compounding, coupon and CIP calculations
  independently; recorded the exact counterexamples and corrective direction in the review.
- Verdict: **REQUEST CHANGES**, next-slice **NOT READY**. Findings 1–8 are all `open`.

## Tests and evidence

| Claim | Method | Result |
|---|---|---|
| Fixed target existed and was clean | `git rev-parse HEAD`, `git status --short` before reviewer edits | `35c9821`, clean |
| SMSF pointer scope | `git diff --name-status 1502ab8..85ef0fa -- . ':!hio'` | four documentation files only |
| Mathematical identities and counterexamples | Independent arithmetic in the review record's method table | Four worked cases confirmed; cash bound, CMT coupon and forward-normalisation defects reproduced |
| Review and finding state | `reviews/records/REVIEW-2026-10-18-a01.md` and `reviews/README.md` | eight open; none waived or verified closed |

## Known limitations and not verified

- Vendor rights, publication schedules, data coverage, cloud costs/features and live source
  conventions remain unverified. T-0002 and T-0003 have not run.
- The authoritative SMSF database was not queried in this design review. The HIO-001 status
  relies on its existing review record and static loader inspection; activation remains held.
- No HIO code or releases exist, so there were no implementation tests or rebuilds to run.
- The harness-0.3 cold-start test was not independently run with a separate fresh session.

## Open findings

All eight findings in [`reviews/README.md`](../reviews/README.md) are `open`. The blocking
subjects are historical-vintage PIT truth, S1 USD cash accrual, deterministic release and
status identity, CMT coupon accounting, operation-specific rights gates, and S1 bill
triangulation. The cash compounding bound and FX forward denominator also require correction
before the relevant specifications/standard are approved.

## Assumptions made

- The user's explicit direct request assigned this review of the current fixed head. This
  assignment source is not yet preserved as an owner-authenticated repository artefact. The
  review record states the source without treating a `HIO-Actor` trailer as authentication.

## Conflicts found between documents

- The review index and `STATUS.md` at `35c9821` said no review was assigned. The direct owner
  request supplied the assignment; the index now records the completed review without
  pretending the earlier Claude candidate was an assignment.
- RA §6's general coupon-inclusive bond TR conflicts with its CMT step 3. Finding 4 preserves
  the conflict for Claude to correct; the reviewer did not edit the standard.
- RA §3.2's period-start cash fixing conflicts with the USD cash spec's period-end selection.
  Finding 2 preserves the conflict for correction.

## NOT approved by this session

Nothing: no A01 ADR, standard, spec, T-0006 acceptance, HIO-S1 work, repository migration,
source rights, release, finding waiver or HIO-001 activation. A review verdict is not an owner
decision.

## Next action

The owner reviews the eight findings and, if desired, instructs Claude to prepare a narrowly
corrected A01 baseline with the synthetic tests described in the review. Codex then re-reviews
the exact correction revision. The owner separately decides acceptance, ADR approval and any
waiver; source rights and live capture remain gated.
