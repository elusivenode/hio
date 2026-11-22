---
id: OD-0226
title: "Owner authorises one EODHD fetch of IHVV, a proposed spec and local build, and a comparison of the CIP-implied hedged SPY series against it, expected differences declared first"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-hedge-anchor.md (owner's message, verbatim, with Claude's question)
  sha256: 4e69c314179983c5d1367e21d67bd60bc0652956e696d9b8d456c2d877b9d7bc
  date: 2026-11-22
  quote: "Y"
base_revision: 5959073248afa22d6b57d635b390b5acf2bc727d
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0163, OD-0176, OD-0210, OD-0222, OD-0225]}
---

# OD-0226: anchoring the hedged series against a traded fund

## Owner action

**Authorised:**

1. **One fetch of IHVV** from EODHD under `eodhd.personal_evaluation` into a new pinned local snapshot, with the small worker change that lets the fetch name it.
2. **A proposed spec and a local, exploratory build,** with Claude's real-data checks.
3. **A comparison** of the CIP-implied hedged SPY series against it over their common months, local, with a stub record. No value from the series enters the repository (OD-0210).

**Read as included, stated so the owner can correct it:** a proposed spec and local build of the fund's unhedged twin, IVV on the ASX, from snapshot `s2`, which HIO already holds. No fetch. The comparison below needs it.

## The comparison, declared before the fetch

A hedged fund and its unhedged twin trade in one market at one time, so their difference isolates what the hedge did. HIO's two SPY series (hedged and unhedged in AUD) do the same in HIO's construction.

- **Fund hedge effect,** monthly: IHVV's return minus IVV's.
- **HIO hedge effect,** monthly: the CIP-implied hedged SPY return minus the unhedged AUD SPY return.

| Check | Reading declared now |
|---|---|
| H1 correlation of the two monthly hedge effects | 0.95 or more: the construction captures the hedge. Below 0.90: it does not |
| H2 mean difference of the two hedge effects, a year (HIO minus fund) | within 0.50 points: **small**. 0.50 to 1.00: **moderate**. Over 1.00: **large** |
| H3 annualised return, HIO hedged SPY minus IHVV | reported with its bootstrap interval; within 0.75 points reads as consistent |
| H4 correlation of monthly returns, HIO hedged SPY with IHVV | 0.95 or more reads as consistent |

**Expected differences, by mechanism:** the cross-currency basis and forward spreads (either sign; this is what the check is for); the fund's hedge resets about monthly, HIO's every period (small, either sign); fees (the hedged fund charges more than its twin [EXT], which lowers the fund's hedge effect by a few basis points a year); the month ends are not simultaneous (the fund pair at the Sydney close, HIO's pair at the New York close with a noon rate), which adds noise with no expected sign and lowers H1; the fund's distributions are the vendor's and may include unrevised estimates (`issuer-check-1.md`).

A reading stands as declared. Anything examined after the result is labelled post hoc.

## What this record does NOT do

It authorises no other symbol (the bond side is not anchored), no new source and no acceptance. It does not change the hedged series or lift their diagnostic-only label; that would be a later owner decision.

## Corrections (append-only)
