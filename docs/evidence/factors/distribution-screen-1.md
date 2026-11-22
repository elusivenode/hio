---
id: HIO-EVIDENCE-FACTORS-DISTRIBUTION-SCREEN-1
title: "Distribution plausibility screen: run on every held fund (OD-0228)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0228
---

# Distribution screen 1

> **Exploratory and unaccepted.** The rules and the expected reading are in OD-0228, declared before the run and not blind (a manual version had been run on the same funds). **No value from a licensed series is recorded here** (OD-0210): the flagged days are in `~/.hio-research/analytics/distribution-screen/`. Run once, by the author; not reviewed.

## What was built

`tools/factor_build.py` gained the screen (worker W1, checked `9e38d4f`): rules D1, D2 and D3 as OD-0228 declares them, a `distribution_screen` block in every build record, counts-only printing, and `--screen-only` with `--screen-report`. A flag refuses nothing.

## The run

`--screen-only` on all fourteen fund files in snapshots `s2` to `s5`, each against its pinned manifest. BGBL and VTI have no spec; each ran from a throwaway spec outside the repository. No build was written and no series changed.

| Fund (snapshot) | D1 | D2 | D3 | Days flagged by D1 and D2 |
|---|---|---|---|---|
| ASX IVV (`s2`) | 5 | 4 | 0 | **4** |
| IGB (`s4`) | 3 | 0 | **2** | 0 |
| IHVV (`s5`) | 2 | 0 | 0 | 0 |
| IEF (`s2`, `s3`) | 1 | 0 | 0 | 0 |
| VGB (`s4`) | 1 | 0 | 0 | 0 |
| SPY, BIL (`s2`, `s3`); VTI, VAS, BGBL (`s2`); AGVT (`s4`) | 0 | 0 | 0 | 0 |

## Readings

- **The expected reading holds.** ASX IVV flags its four known records before 2014 on both D1 and D2, and the doubtful January 2016 record on D1 alone. No other fund has a day flagged by both rules.
- **New: IGB has a likely duplicate record.** D3 flags one pair: the same amount twice within ten days, where the fund pays quarterly. One record of the pair carries no payment date and no period label. If it is a duplicate, the IGB series (`build-7.md`) counts one distribution twice. **Not checked against the issuer.**
- **The other D1-only flags look like real large distributions:** on each of those days the price fell by about the size of the distribution. Seven days across IEF, IGB, VGB and IHVV. Not checked against the issuer.

## Checks on the tool

| Check | Result |
|---|---|
| An independent recomputation (rational arithmetic, raw files, no HIO code) of every flagged day, its rules and the three checked counts, for all fourteen files | agrees on all |
| Broken on purpose, on a clean real series: one distribution multiplied by eight | flagged by D1 and D2 |
| Broken on purpose: one record copied seven days later | both records flagged by D3 |
| A wrong manifest pin; a report path inside the repository | each refused |

## Limits

- **D2 is blind below a 2% yield,** where a day's ordinary price move hides a distribution. A wrong record of ordinary size passes; so does a missing one. The screen does not replace an issuer check.
- **D3 needs identical amounts.** The known ASX IVV duplicate has a different amount and is caught by D1 and D2, not D3.
- **The thresholds were set after a manual look at these funds.** They are untested on any other fund.
- The existing builds predate the screen: their records carry no `distribution_screen` block until rebuilt.

## Not established

That any flagged record is wrong, or that any unflagged record is right. No series is corrected, excluded or accepted.
