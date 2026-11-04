---
id: HIO-EVIDENCE-T0023-CORROBORATION-1
title: "T-0023 steps 3 to 5: what the comparison's inputs were checked against, and what remains"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0178
---

# T-0023 corroboration 1

> **Exploratory and unaccepted.** Bars are in `preregistration-1.md`, declared before any comparison. **No EODHD-derived value is recorded here;** gaps and sizes are in the local reports under `~/.hio-research/T-0023/corroboration/`. Not reviewed by Codex. Tools run at `ab4c870` (step 3 and 5) and `baff168` (step 4), on panel `1aa29918…`.

## The conclusion so far

**The pre-registered classes held under all nine sensitivities:** cash rate and currency, and total, are distinguished on volatility at every block length, and nothing else is distinguished. **That is narrower than it sounds.** Classes are full-sample. They don't test the size of any 2008 effect, and that's what step 6 would lean on.

**2008 is partly corroborated, not established:**
- **SPY:** its close and return agree with the issuer's NAV, including 2008. Its income isn't independently checked.
- **BIL:** agrees with the issuer's NAV and the 1-month Treasury yield, except that one month end falls outside the close bar.
- **IEF:** the weakest. No issuer NAV was obtained, and its only 2008 check failed its bar.
- **AUD cash:** consistent with the RBA's own target every day, but no third party checks it.

## Step 3: the sleeves

| Check | SPY | BIL | IEF |
|---|---|---|---|
| C1 close against NAV | pass | **fail** | not performed |
| C2 market return against NAV return | pass | pass | not performed |
| C3 against the 1-month par yield | | pass | |
| C4 against the 10-year construction | | | **fail** |
| C5 audited reports | not performed | not performed | not performed |

- **C1, BIL:** within the bar at over 99% of month ends, but 2008-09-30 is outside it, and the bar requires every month of 2008. That was the month of Lehman's failure, so a real dislocation is plausible; that's a guess, and this check can't tell a real one from a bad record.
- **C2 doesn't test income:** the NAV return uses EODHD's distributions, so a wrong distribution would pass.
- **C4, IEF:** correlation passes in full and over 2008-2009, but the 2008 gap exceeds its bar. A 10-year construction has more duration than a 7-to-10-year fund, which would push the gap this way in a year when yields fell. That's untested, and the construction is itself unreferenced (E-0001).
- **C5 and IEF's NAV weren't obtained.** SEC EDGAR refuses an automated tool that doesn't declare a contact, and iShares' page didn't give its file to a plain request. Neither was worked around.

## Step 4: the cash seam

| Question | Check | Result |
|---|---|---|
| Does the method match the RBA's index? | M1: monthly, from 2011 | 189 of 189 months within 1 bp |
| | M2: cumulative drift to the last month | within 0.10% |
| Are the pre-2011 rates consistent with the RBA's target? | R1: each published day, within 5 bp | 2007: 171 of 171. 2008: 254 of 254. 2009: 254 of 254. 2010: 253 of 253 |
| | R2: accrual on the target against accrual on the overnight rate, monthly | 43 of 43 months within 1 bp |
| Does the page parser read the target correctly? | R3: against F1, from 2011 | 4,009 of 4,009 days equal |

**These are separate claims.** M1 and M2 show the method agrees with the RBA's index where both exist. R1 and R2 show the older rates agree with the RBA's own published target. **Neither is a third party's check of the rates,** and the method's agreement after 2011 says nothing about accuracy before it. A benchmark accrual isn't an investable deposit return. Seven very old rows of the target page couldn't be read and were left out; all fall before the panel.

## Step 5: what remains

**FX and close timing.** H.10 is noon New York and fund closes are 4 pm, so each month end mixes two instants. Shifting H.10 to the next published date (S9) and using EODHD's AUD/USD instead (S8) change no class. X1: of 234 month ends, H.10 and EODHD are within 0.5% at 215, 1% at 231 and 2% at all. Neither is a reference for the other. Monthly aggregation lessens the mismatch and doesn't remove it.

**Vehicle basis.** BIL is a 1-to-3-month bill fund, not overnight cash. IEF is a 7-to-10-year basket, not a 10-year constant maturity, so "Treasury duration" includes vehicle basis. All carry fees in their prices, with no trading cost, tax or hedge. These are the funds' results, not pure factors.

**The SPY gap to the issuer: still unexplained.** Reinvesting on the payment date (G1) didn't halve every SPY gap, so the verdict is "unexplained" under the declared rule. **The earlier guess of reinvestment timing isn't supported.** BIL and IEF stay within 0.10 points a year either way. The gap stays inside the issuer check's bar.

## Limits

- **All of this ran once, on the owner's Mac, by the author.** No permitted verifier has traced any reference.
- **The workers' tests use invented data.** Real runs found three things they missed: the page's fourth column, H.10's last date and BIL's split. All were fixed before any result, and S9's is amendment 1. The mutation check done for step 2 wasn't repeated here.
- **Two full test runs stalled at 99% CPU and were stopped, with no stack captured;** two later full runs passed, 1,638 tests in about 115 seconds. The stall wasn't reproduced and isn't explained.
- **Issuer files' rights row is unverified.** They were read once, and stay local.
- **F-1 (BGBL) is unaffected:** BGBL isn't in this panel.
