---
id: T-0009-REVIEW-ASSIGNMENT-DRAFT
title: "Draft Codex review assignment for the T-0009 S1b-1.0 implementation slice (shared receipt, returns, reproducibility, rights, storage), for the owner to issue or amend"
status: draft   # NOT an assignment. Only an owner-authored source assigns a review (operating model section 6.2 step 1)
owner: owner (assigns); drafted by claude/implementation-agent
created_at: 2026-10-25
drafted_under: OD-0065
---

# Draft review assignment: T-0009 S1b-1.0

> **Not an assignment.** The owner asked that one fixed head be submitted for review (OD-0065).
> A file cannot contain its own commit id, so the head is **the commit that adds this file**:
> `git log -n1 --format=%H -- docs/decisions/T-0009-review-assignment-draft.md` on branch
> `impl/t0009-shared-receipt-and-storage`. The owner states it in the assignment. Never rebased or
> force-pushed during the review.

## Proposed values

| Field | Proposed value |
|---|---|
| Review id | `REVIEW-2026-10-25-t0009-1` |
| Repository | `elusivenode/hio` |
| Base SHA | `0665b66b1af4aa51ceda89d9e95451e365b2670d` (`origin/main` when the work began) |
| Head SHA | the commit that adds this file (above) |
| Review branch | `review/t0009-1-codex`, cut at the head |
| Reviewer | Codex, independent reviewer; writes only under `reviews/` |
| Not in scope | approving anything; any source right; Q-013; the storage provider choice; S1b authorisation; the harness |

## Questions (bounded; write your own failure scenarios before reading the author's handoff)

1. **Shared receipt.** Does one raw F1 receipt keep separate dataset identity and rights for
   `rba.cash_rate` and `rba.cash_rate_tri` end to end (capture, vintages, build, lineage, publish)?
   Is any approved observation or rights invariant weakened by `SeriesDef.dataset_id`, the link record,
   or the lineage change? Do single-dataset receipts behave exactly as in S1a (compare the diff of
   `lineage.py`, `vintages.py`, `series.py`, `release.py`, `layout.py`)? Can a missing, wrong or
   duplicated link produce a release with fewer rights subjects than it uses?
2. **Return calculations.** RA section 3.2 accrual, compounding, the RITS and derived-US calendars, NSW
   period ends, `cash.aud.overnight` and `cash.usd.overnight`. Check the fixtures independently
   (Fri-to-Mon at 3.60 is 0.000295890411...), the weekend and holiday legs, and the index comparisons'
   expected-bound model. Is any residual explained by something other than the publisher rounding?
3. **Reproducibility.** Rebuilds reproduce `content_sha256`; the Decimal canonicalisation correction
   (`_places`); no dependence on parsed-versus-reloaded values; the four S1a `data.csv` hashes unchanged.
4. **Rights enforcement.** Fail-closed gate before any request or write; per-dataset evaluation;
   `distribution` and `derived_storage` denial; genuine register refuses everything today.
5. **Storage controls.** `BlobBackend` has no overwrite or delete; ordered resumable commits; a crash
   never leaves a capture record without its bytes and link; out-of-band overwrite is detected;
   the OpenTofu definitions encode create-only writes, no static credential, flat namespace, versioning,
   Unlocked immutability. Say what you could not check (provider attribute names; nothing was planned).
6. **Provenance completeness.** Does the capture-run record keep everything T-0009 section 4 says
   cannot be reconstructed later? Is anything in it a claim the run did not earn?

## Output

A `REVIEW-2026-10-25-t0009-1` record with a verdict and findings, `Reviewed-Head` stated, and in the
final message the branch tip SHA, the reviewed head and the sha256 of every file you added. Open no PR.
