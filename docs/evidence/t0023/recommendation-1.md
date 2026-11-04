---
id: HIO-EVIDENCE-T0023-RECOMMENDATION-1
title: "T-0023 step 7: design one conditional-diversification experiment; don't run it yet"
status: proposed
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0180
---

# T-0023 recommendation 1

> **A recommendation, not a decision or a result.** It holds no value, accepts nothing and authorises nothing. Evidence: `corroboration-1.md`, `episodes-1.md`. The architect's answer is `docs/history/2026-11-04-architect-t0023-step7.md`.

## Recommendation

**Design one experiment, and assess whether it's feasible. Don't run it yet.** The preregistered rule gives row 1, "may be warranted": Treasury duration helped in 2008 and Q1 2020 and hurt in 2022, on compounded return. **That's a reason to design a test, not evidence of a relationship.** Three hand-named episodes confirm nothing, and the one reversal is the whole contrast.

**The question:** in otherwise identical USD 60/40 portfolios, rebalanced monthly, does holding Treasuries rather than bills reduce monthly downside losses differently across one observable inflation state, declared in advance?

**The state:** inflation acceleration. At the preceding month end, is the latest published year-on-year CPI rate above the rate published twelve months earlier? Original release values and dates only; missing publication evidence means unavailable.

## What the claim rests on, and its failures

| Item | Status | Effect on the claim |
|---|---|---|
| Income, all three funds | passes, in six audited fund-years | the strongest new support |
| C1, BIL | **fails** at 2008-09-30 | unresolved; inside the 2008 episode |
| C4, IEF | **fails** | against a different, unreferenced construction, so it doesn't show IEF is wrong, and the maturity explanation is untested |
| C5, SPY's return | **fails** | the post-hoc NAV diagnostic is plausible, and doesn't erase the failure |
| IEF's NAV | **not obtained** | the sleeve carrying the duration result has no close-against-NAV check |
| C5's fiscal years | don't isolate calendar 2008 | gaps within a year could offset |
| Rebuild, classes and episodes | run once, by the author, unreviewed | no permitted verifier has traced them |

**"Robust" is narrower than it sounds.** The 2-point size applies to the frozen panel only, and a sensitivity need only keep the sign. **On the duration effect's return, S6 to S9 can't change the sign at all,** so S1 to S5 are the real challenge, not nine. See the report's "Margins" section for how close each came.

## What it needs

1. **Aligned monthly USD total returns** for equity, Treasury duration and bills, with income, valuation and splice conventions stated.
2. **One state history with evidenced publication dates and rights.** CPI with its release dates is **a new source, which needs its own yes.**
3. **Frozen before any conditional result:** the primary outcome, the state, the sample rule and an economic relevance threshold.
4. **An information count before anything else:** months, distinct state runs and separate equity-stress clusters in each state.
5. **Independent corroboration** of the consequential inputs, and calculation from retained bytes.

## Don't run it if

- one stress episode supplies almost all of the state contrast;
- publication timing or permitted use can't be established;
- an unresolved return discrepancy could decide the conclusion;
- the state or threshold would need adjusting to separate the episodes as hoped; or
- the feasible uncertainty is too wide to see an economically useful effect.

## Where Claude and the architect differ

| Point | Claude's draft | Architect | Claude now |
|---|---|---|---|
| Measure | equity-against-Treasury diversification benefit | a defined portfolio outcome: monthly downside loss | **the architect's.** A return difference in a crisis doesn't by itself show dependence |
| State | inflation or the policy path | one only: inflation acceleration | **the architect's,** so a second state isn't tried after seeing the first |
| Long history | needed | assess the information count first; E-0001 stays a sensitivity | **the architect's.** Length from an unreferenced construction isn't trustworthy information |
| USD first | to avoid a second conditional question | agrees, and shows translation can't change the return sign | **the architect's reason,** which I checked and a test now pins |
| IEF's NAV | before starting | valuable, but a comparable independent reference could serve, and drafting needn't wait | **agree for drafting.** I'd still want it or an equivalent before any inference, since this is the sleeve the result rests on |

**One limit neither of us can remove:** Claude and the owner already know how 2022 went, and the state was picked knowing that. Adding older history doesn't make an untouched sample. The acceleration rule may also classify parts of 2008 alongside 2022, and that has to be allowed to stand.
