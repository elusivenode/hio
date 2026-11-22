---
id: HIO-EVIDENCE-FACTORS-ISSUER-CHECK-1
title: "Issuer check of the Australian funds: VAS and VGB returns and distributions against Vanguard's published figures (T-0024 package A2)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0224
---

# Issuer check 1

> **Exploratory and unaccepted.** The bars are in OD-0224, declared before any issuer figure was read. **No vendor value and no issuer figure is recorded here** (OD-0210; the issuer rights row is unverified): both are in the local report, `~/.hio-research/analytics/a2-issuer-check/report.md`. Run once, by the author; not reviewed.

## Sources, each read once on 2026-11-22

- The issuer's "Exchange traded funds performance summary", data as at end of October 2026. Its returns are at net asset value, after management costs, with distributions reinvested.
- Seven of the issuer's distribution announcements on the ASX platform, covering three ex-dates for each fund (January 2025, April 2026, July 2026). Only the July 2026 figures were read in their **final** form; the others are estimates.

## Result

| Check | VAS | VGB |
|---|---|---|
| R1 returns, NAV basis, each period the issuer publishes (1 month to 10 years) | **pass**, 9 of 9 | **pass**, 9 of 9 |
| R1 since inception | not performed: the vendor's history starts after the fund's inception date | **pass** |
| D1 distribution against a final issuer figure (July 2026) | **fail** | **pass** |
| D1 against estimates (January 2025, April 2026) | not judged: the finals were not read | one agrees with the later of two estimates; one not judged |
| D2 completeness | one vendor record on each of the three dates read; no more can be said | same |

- **Returns.** HIO's market-price return agrees with the issuer's net-asset-value return at every horizon. The multi-year gaps are a small fraction of the bar.
- **The fail stands.** The vendor's July 2026 record for VAS equals the issuer's first estimate, not its final figure. Its size changes no result in `build-5.md`, `build-6.md` or `build-8.md`. It is the second such record found; the first is E-0002's F-1, on another fund and the same ex-date. So a vendor distribution can be an estimate the issuer later revised.

## The US funds: no new read

| Fund | Already checked | Remains |
|---|---|---|
| SPY | returns against issuer fact sheets back to September 2016; distributions per share against audited reports for the two fiscal years around 2008 | its close-based return fails the audited-return bar in both of those years; a post-hoc diagnostic points to the close's discount to net asset value at one date |
| IEF | the same two checks; calendar years 2021 to 2025 | no issuer net asset value was obtained; its check against a 10-year construction failed |
| BIL | the same two checks; net asset value against the issuer's file | one month end in 2008 outside the close bar |

Source: `docs/evidence/t0023/corroboration-1.md` and `docs/evidence/e0002/assessment-1.md` (stubs; content in the local results store). T-0023 stays parked and unaccepted (OD-0215).

## Limits

- **Net asset value against market price.** The two need not agree on a given day; agreement over long horizons is the meaningful part.
- **Three ex-dates per fund,** one of them final. Not a full distribution history.
- **Franking is not tested.** IGB and AGVT are not checked against their issuers.
- **The issuer's documents are not committed;** their rights row stays `unverified`.

## Not established

That the vendor's distributions are final for any other date; that any series is fit for a consumer; that T-0003 is decided.
