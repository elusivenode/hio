---
id: HIO-EVIDENCE-E0003-RESULT-1
title: "E-0003 result: AUD cash comparator from 2011"
status: draft
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0170
---

# E-0003 result 1

> **Hypothetical and descriptive. No value is recorded here,** and Claude hasn't read the portfolio results: agent use and quotation are denied. They are in the owner's local report.

Run at `b1b3a9f`. Summary sha256 `75147b4ee90f9b4234a8837883ba44aafb02829a57b011bbd3d20e3f30a98397`. 189 months, 2011-01-31 to 2026-10-30, one window for all three allocations. RBA F1 receipt `8b9f41ee…`, read-only from the evidence store; 4,010 TRI levels from 2011-01-04. H.10 rates: one month end used an earlier rate, a day old. V3 was verified READY first (VERIFY-2026-11-04-e0002-v3-1).

## Pre-registered tests

| Effect | Return p.a. | Volatility | Max drawdown |
|---|---|---|---|
| Cash rate and currency (USD bills against AUD cash) | not distinguished | **distinguished at every block length** | not distinguished |
| Treasury duration (Treasuries against USD bills) | not distinguished | not distinguished | not distinguished |
| Total (Treasuries against AUD cash) | not distinguished | **distinguished at every block length** | not distinguished |

"Not distinguished" means every interval spans zero. It isn't evidence of no effect.

**Earlier AUD cash history: indicated by the pre-registered test.** That prompts the owner's own rights decision, and says nothing about 2008 itself.

## Limitations

**No 2008, the period of most interest.** About five non-overlapping three-year periods and few stress episodes; intervals are conditional on this history. Month-end drawdowns. BIL is a bill ETF, and IEF a basket, so the duration effect includes vehicle basis. SPY, IEF and BIL have no independent check, and EODHD's price source is unresolved. The currency-and-rate split is descriptive and makes no causal claim. No costs, tax or hedging. Not reviewed by Codex; the brief asks only for V3's verification.

## Variant V1: back to May 2007 (OD-0173)

**2008 is now in the sample.** Run at `7d4ef02`, summary sha256 `d41aeb34a4fb06839ccab4b96527f1522481a8b12a66895e0bc841117e493509`. 233 months, 2007-05-31 to 2026-10-30; all windows available. AUD cash before 2011 is HIO's accrual of the RBA's `FIRMMCRID`, 932 rates, then the Cash Rate TRI from 2011-01-04. Declared before any V1 result.

| Effect | Return p.a. | Volatility | Max drawdown |
|---|---|---|---|
| Cash rate and currency | not distinguished | **distinguished at every block length** | not distinguished |
| Treasury duration | not distinguished | not distinguished | not distinguished |
| Total | not distinguished | **distinguished at every block length** | not distinguished |

The same pattern as from 2011. **Seam check: passed, 189 of 189 months within 1 bp.** That tests the accrual method against the RBA's index from 2011, because the historical file doesn't overlap the index. The historical rates themselves have no independent check, and neither do the US funds' 2008 inputs, since the issuer check starts in 2016. 2008 is one crisis, and resampling can't add others. Results are in the owner's local report, and Claude hasn't read them. Not reviewed by Codex.

