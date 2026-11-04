---
id: OD-0153
title: "Owner authorises receipt of VERIFY-2026-11-04-t0019-1-1 with §5.12, and accepts T-0019 at fa6370d"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-accept-t0019.md (owner's message, verbatim, with Claude's question put)
  sha256: 9e1fe555b1723ff31513a50d63936623b7f8e1d69e18c5863e9245814217623e
  date: 2026-11-04
  quote: "yes, receive and accept T-0019"
applies_to:
  - path: review/t0019-1-verify-1-codex
    revision: e345c8476278a18082eef1c2520b618dee4fd568
  - path: feat/t0019
    revision: fa6370dc3f55c4d9e6537d502ab4a4727ca85fbd
base_revision: 6a73b79e7aefaf80a0937f338aeb9978a81d95ff
related: {adrs: [], tasks: [T-0019], findings: [F-REVIEW-2026-11-04-t0019-1-1, F-REVIEW-2026-11-04-t0019-1-2, F-REVIEW-2026-11-04-t0019-1-3], ods: [OD-0150, OD-0151, OD-0152]}
---

# OD-0153: T-0019 accepted

1. **Receipt of `VERIFY-2026-11-04-t0019-1-1`** (READY, no new finding; reviewer tip `e345c84`, hiomux C4 report), by §6.2 step 5. **Complete:** PR #87 merged as `6a73b79` by the owner. Remote `main` equals the local merge, the three blobs equal `T`'s and the tag peels to `T`. Assignment source: the *Assigned reviews* row and OD-0152 correction 1. Second assignment: looked for in the *Assigned reviews* table, `docs/history/` and PR #83's comments; none found. Inventory: 3 record files and the README reported; 3 imported, 0 missing, 0 extra, sha256 equal. Index: one Class N row. **CI, reported separately:** runs `41754783108` and `41754789075` success on `dcc49dd`.
2. **§5.12.** F-REVIEW-2026-11-04-t0019-1-1, -2 and -3, against this verification, reviewed head `fa6370d`, outcome "technically verified_closed": open → verified_closed at `fa6370d`. Only the state cells and their citations changed. The Assigned reviews row is set to received.
3. **T-0019 is accepted at `fa6370dc3f55c4d9e6537d502ab4a4727ca85fbd`.** Limits: on invented inputs; the spec stays proposed; pricing-basis error is unmeasured; nothing here can produce a release.

**An order swap, disclosed.** The owner merged #83 (as `29dab6f`) **before** the receipt, on Claude's request. The verification record links to the response file, so `check_repo` refused the import at step 5.7 until #83 was on `main`. The provenance tag had already been published at `T`. No check was skipped.

## Not authorised

Adopting the spec; any rights decision; any real data; the duration experiment; any waiver.

## Corrections (append-only)
