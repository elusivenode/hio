---
id: HIO-EVIDENCE-T0023-EPISODES-1
title: "T-0023 step 6: three stress episodes, signs and robustness"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0180
---

# T-0023 episodes 1

> **Retrospective description only: three hand-named episodes confirm nothing.** Not a regime model or a forecast. Declared in `preregistration-2.md` before it ran, and not blind. **Signs only here;** sizes are in the owner's local report. Run at `42ad0f3` on panel `1aa29918…`; all nine sensitivities performed. Unreviewed and unaccepted.

## Compounded return

`+` means the later allocation did better. "Robust" means at least 2 points, and the same sign under S1 to S9.

| Effect | 2008 | Q1 2020 | 2022 |
|---|---|---|---|
| Cash rate and currency (USD bills against AUD cash) | + robust | + robust | + robust |
| Treasury duration (Treasuries against USD bills) | + robust | + robust | **- robust** |
| Total | + robust | + robust | - robust |

## Maximum drawdown

**`+` here means a deeper drawdown,** so it reads the other way.

| Effect | 2008 | Q1 2020 | 2022 |
|---|---|---|---|
| Cash rate and currency | + robust | - robust | - not robust (under 2 points) |
| Treasury duration | - not robust (under 2 points) | - robust | + robust |
| Total | + robust | - robust | + robust |

## Reading it

- **The duration effect reverses in 2022, on both measures.** That's the contrast the decision rule looks for: **row 1**.
- **Cash rate and currency has one sign on return, in all three.** Within it, the currency move outweighs the rate gap in each episode (descriptive split). Three episodes aren't a reliable hedge, and the sample holds no episode in which the AUD rose in an equity sell-off, by construction of what was named.
- **Return and drawdown can disagree.** In 2008, USD bills beat AUD cash over the window with a deeper month-end drawdown on the way. A fixed window's return isn't what an investor lived through; month ends hide more.
- **Q1 2020 is three months:** one path, not a sample.

## What this rests on

`corroboration-1.md` in full. In particular: C1 for BIL and C5's return bar for SPY fail around 2008-09-30, inside the 2008 episode; C4 fails for IEF; IEF has no NAV check; and the C5 fiscal years don't isolate calendar 2008. The sensitivities test sign, not the accuracy of any size.
