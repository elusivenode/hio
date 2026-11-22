---
id: OD-0228
title: "Owner authorises a distribution plausibility screen in the build tool, run on every held fund, rules declared first"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-yes-distribution-screen.md (owner's message, verbatim, with Claude's question)
  sha256: 808daa5d95fd96af608948419c8485c128911b5711564d934219d4a3e889e0dc
  date: 2026-11-22
  quote: "Y"
base_revision: 6e7a538e41af2f618ae94e4a7d07b5bb24751475
related: {adrs: [], tasks: [T-0024], findings: [], ods: [OD-0199, OD-0210, OD-0213, OD-0224, OD-0226, OD-0227]}
---

# OD-0228: a distribution plausibility screen in the build tool

## Owner action

**Authorised:**

1. **One worker task** that adds the screen to `tools/factor_build.py`, with tests on invented data.
2. **Claude's run of the screen** on every fund held in local snapshots `s2` to `s5`, with a check on real data.
3. **An evidence note** that holds no value from a licensed series (OD-0210).

## Why

The build's structural checks, and its agreement with the vendor's adjusted close, passed on a series whose distribution records were wrong (`docs/evidence/factors/hedge-anchor-1.md`; OD-0226 correction 1). Only a manual look caught them.

## The screen, declared before the run

A **distribution day** is a period whose income return is above zero. Its **yield** is that income return: the day's distributions over the previous close.

| Rule | Flags a distribution day when |
|---|---|
| D1 neighbours | its yield is at least 0.5% **and** more than 3 times the median yield of its nearest distribution days (up to four before and four after). Not evaluated with fewer than four neighbours |
| D2 price move | its yield is at least 2% **and** the price fell by less than half the yield that day |
| D3 duplicate | two vendor records carry the same unadjusted amount, dated within 10 calendar days of each other |

- **A flag refuses nothing.** The build still writes its series; the flag is a prompt to check the record against the issuer.
- **The build record** (local) carries the rule thresholds, the counts and the flagged days. **The command prints counts only.**
- **A screen-only mode** runs the screen on a pinned snapshot and writes no build.

**Not blind.** A manual version of this screen was run in the hedge-anchor work and flagged only the unhedged ASX twin of the hedged fund. The thresholds above were set knowing that. The expected reading is therefore: the twin flags on its known records before 2014, and no other held fund has a day flagged by both D1 and D2. A legitimate large final distribution may flag D1 alone. Anything examined after the run is labelled post hoc.

## What this record does NOT do

It authorises no fetch, no new source, no issuer check and no change to any series or spec. It accepts nothing. Excluding or correcting a flagged record would be a later owner decision.

## Corrections (append-only)

None.
