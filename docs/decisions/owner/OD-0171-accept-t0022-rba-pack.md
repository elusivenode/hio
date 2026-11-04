---
id: OD-0171
title: "Owner accepts T-0022 at 888c493 and authorises its finding-state reconciliation; authorises a reading pack for pre-2011 AUD cash"
decision: accept
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-accept-t0022-rba-pack.md (owner's message, verbatim)
  sha256: 5668bc939290f3185bfbd589ffcea5adc26b2b0d36b7e3c5886a2f87d4213068
  date: 2026-11-04
  quote: "yes to both"
base_revision: 888c493425cc90ccae85bd87bfb9dc8792827eba
related: {adrs: [], tasks: [T-0002, T-0022], findings: [F-REVIEW-2026-11-04-t0022-1-1, F-REVIEW-2026-11-04-t0022-1-2, F-REVIEW-2026-11-04-t0022-1-3, F-REVIEW-2026-11-04-t0022-1-4, F-REVIEW-2026-11-04-t0022-1-5], ods: [OD-0162, OD-0167, OD-0168, OD-0169, OD-0170]}
---

# OD-0171: T-0022 accepted; a reading pack for earlier AUD cash

1. **T-0022 is accepted at `888c493`** on `main`: the evaluation tooling, and `docs/evidence/e0002/assessment-1.md` as a draft record. **It accepts no EODHD data as valid,** and allows nothing beyond the owner's personal research (OD-0163). As put to the owner, the acceptance names the tooling; the question's last stated head was `1c05d47`, and `888c493` also holds V3 and the issuer check, which Claude read as within it.
2. **Finding states, under operating model §6.2 step 5.12:** F-REVIEW-2026-11-04-t0022-1-1, -2, -3 and -5 are `verified_closed`. F-REVIEW-2026-11-04-t0022-1-4 is fix accepted, verification waived (OD-0169). VERIFY-2026-11-04-t0022-1-1 and -2 stay NOT READY as written; only these states change.
3. **A reading pack for pre-2011 AUD cash** is authorised: `docs/research/T-0002-rba-history-reading-pack.md`. No download, no rights decision and no new experiment.

**The owner handles the EODHD subscription.** Claude holds no renewal date, and the retained-data decision on cancelling stays open.

## Not authorised

Any consumer use; extending E-0003 before 2011; any download; E-0002, E-0003, V1 or any series accepted as validated.

## Corrections (append-only)
