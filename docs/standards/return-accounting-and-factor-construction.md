---
id: HIO-STD-RA
title: Return accounting and factor construction standard
status: approved
approved_by: OD-0008   # at a82aa0d, blob 651c3abe1259
owner: HIO architecture lead (owner); quantitative researcher (maintainer)
version: 0.2
last_reviewed: 2026-10-18
decision: HIO-ADR-0007
---

# Return accounting and factor construction standard (v0.2)

**Normative language.** MUST, MUST NOT and SHOULD are requirements. Worked examples use
illustrative numbers, not market data. Statements about specific vendors, indices or market
conventions marked **[EXT]** are unverified and must be confirmed before a spec relies on them.

**The gate this standard enforces.** A price index, a state indicator, or a level derived from
yields, spot rates or adjusted prices is **not** an investment return, unless a construction in
this standard turns it into one.

## Contents

1. Notation and conventions
2. Series classes
3. Return types: price, income, total, cash, excess
4. Numeraire, FX translation and investable currency positions
5. Equities
6. Bonds
7. Credit
8. Futures, commodities and trend strategies
9. Home currency (AUD) and cash legs
10. Single-period identities versus cumulative relationships
11. Triangulation against independent references
12. Promotion gate
13. Invariant catalogue
14. Worked examples

---

## 1. Notation and conventions

| Symbol | Meaning |
|---|---|
| `t` | period end (a valid date in the series calendar); `t−1` is the previous period end in the same calendar |
| `P_t` | price (clean or traded, per context) in the instrument currency |
| `D_t` | cash distribution per unit with **ex-date** `t` (gross unless stated) |
| `w` | withholding tax rate applied to `D` |
| `R_t` | simple single-period return over `(t−1, t]` |
| `r^c_t` | cash-leg return over the same period, in the stated currency |
| `X_t` | excess return over the stated cash leg |
| `S_t` | FX rate as **home currency per unit of foreign currency** (for AUD home: AUD per USD) |
| `q_t` | the quoted market rate where the quote is foreign per home (for example AUD/USD quoted as USD per AUD); `S_t = 1/q_t` |
| `s_t` | spot return of foreign currency to a home investor: `S_t / S_{t−1} − 1 = q_{t−1}/q_t − 1` |
| `F_{t,T}` | forward or futures price at `t` for delivery `T` |
| `τ` | year fraction under the stated day-count |

**Conventions (MUST):**
- Accounting returns are **simple returns**. Log returns are permitted only inside statistical
  estimation, and MUST NOT be stored as a series' return.
- Every series declares:
  - currency;
  - numeraire (the home currency it is measured in);
  - calendar;
  - day-count, where accrual applies;
  - compounding rule;
  - for excess returns, the exact cash leg series id.
- **Excess return is arithmetic per period:** `X_t = R_t − r^c_t`, with both in the same
  currency over the same period. A geometric excess `(1+R)/(1+r^c) − 1` is a different
  quantity. It MAY be computed for analysis, but MUST NOT share a series id with arithmetic
  excess.
- An index level is `I_t = I_{t−1} (1 + R_t)`. Its base value and base date are declared.

## 2. Series classes

| `series_class` | Definition | May be used as a portfolio return factor? |
|---|---|---|
| `price_only` | price or level without income, or with an undeclared adjustment (spot FX, price index, unadjusted continuous futures, a back-adjusted futures level, an `Adj Close` of unknown method) | **No** |
| `state_indicator` | an economic or market state (CPI level, yield level, spread level, valuation ratio, PMI) | **No** (it may be a model *input* or *conditioning variable*) |
| `total_return` | income-inclusive return of a funded position, in a stated numeraire | Yes |
| `excess_return` | return over a stated cash leg, per §1 | Yes |
| `strategy_return` | return of a rule-based dynamic position set, built from `total_return` or `excess_return` components | Yes |
| `reference_academic` | a published factor or strategy series held for validation (French, AQR) | Only as a labelled reference, never silently in place of an own-built factor |

`investability` is declared separately:
- `investable`: replicable by holding the stated position, ignoring costs;
- `investable_with_costs`: costs are modelled;
- `replicable_with_basis`: a proxy whose basis is declared, for example SOFR accrual standing in
  for an overnight USD deposit;
- `non_investable`.

## 3. Return types

### 3.1 Price, income and total return (cash distributions)

For a distribution with ex-date `t`:

```
PR_t = P_t / P_{t−1} − 1                   (price return)
IR_t = D_t (1 − w) / P_{t−1}               (income return; w = 0 for gross)
TR_t = (P_t + D_t (1 − w)) / P_{t−1} − 1   (total return)
```

The identity **TR_t = PR_t + IR_t** holds exactly (RA-INV-001).

**Reinvestment convention.** The spec MUST declare one of these:
- **`reinvest_ex_close`** (index convention): income is reinvested at `P_t` on the ex-date.
  This is equivalent to the TR formula above, chained.
- **`receivable_to_pay_date`** (holder convention): income is a non-earning receivable from the
  ex-date until the pay date, then reinvested or held as cash. This is the convention
  `macsmsf` uses for the fund's own accounting [OBS].

The two differ by the return on the asset between ex-date and pay-date, applied to the
receivable. They MUST NOT be mixed in one series.

### 3.2 Cash return (overnight benchmark accrual)

An overnight cash leg is defined by an **accrual window**, the **rate applicable to each day in
the window**, and a **compounding convention**. Knowability is recorded separately. It never
selects the rate.

**1. Window.** For a period `(t−1, t]` on the series calendar, the window is the calendar days
`d` with `t−1 ≤ d < t`. Each day is one overnight, starting on `d`. For a foreign leg on another
calendar, the spec declares how its calendar dates map to the window (§4.4).

**2. Applicable rate.** For each day `d`, use the rate **fixed for the overnight starting on
the latest business day `b ≤ d`** of that rate's market. A weekend or holiday therefore carries
the preceding business day's rate. No rate fixed after the window's last overnight starts is
ever used.

**3. Compounding** (overnight-index convention, compounded in arrears):

```
r^c_t = Π_b (1 + rate_b × n_b / B) − 1
```

- `b` runs over the rate-business days whose overnight lies in the window;
- `n_b` is the number of window days that use `rate_b`;
- `B` is 365 for AUD (ACT/365F) and 360 for USD (ACT/360) [EXT].

This is exact by definition, so no compounding-approximation bound applies.

**4. Two different rate regimes.** The spec MUST state which applies:

| Regime | When the rate is known | Example | Label |
|---|---|---|---|
| **ex-ante** | before the overnight starts (the fixing is published by the window start) | a deposit with a rate set at placement | `investable` |
| **in arrears** | after the overnight, e.g. the next business-day morning | SOFR | `replicable_with_basis` |

An in-arrears benchmark has **no look-ahead in the return**: each day earns the rate fixed for
that day's overnight. Its index level becomes **knowable later**, so the observation's
`knowable_at` is the publication instant of the last rate used. An investor cannot lock an
in-arrears period rate at the period start.

**5. Fixtures** (synthetic rates; window days by date):

| Case | Window | Rates applied | `r^c_t` |
|---|---|---|---|
| USD, Fri → Mon | NY Fri, Sat, Sun | Fri 4.30% × 3 | `3 × 0.043/360` = **0.000358333333** |
| USD, Fri → Tue, Monday holiday | Fri, Sat, Sun, Mon | Fri 4.30% × 4 | `4 × 0.043/360` = **0.000477777778** |
| USD, Thu → Mon | Thu; Fri, Sat, Sun | Thu 4.30% × 1; Fri 4.40% × 3 | `(1 + 0.043/360)(1 + 0.044 × 3/360) − 1` = **0.000486154907** |
| USD, Fri → Mon, look-ahead trap | NY Fri, Sat, Sun | **Monday's SOFR is NOT used** (its overnight starts after the window) | as row 1 |
| AUD, Fri → Mon | Fri, Sat, Sun | Fri 3.60% × 3 | `3 × 0.036/365` = **0.000295890411** |

Daily compounding *within* a weekend would give `(1 + 0.043/360)^3 − 1 = 0.000358376136`. That
is a different convention, and it is not used.

### 3.3 Excess return

```
X_t = R_t − r^c_t
```

Here `R_t` is a total return in the same currency as the cash leg. Equivalently, for a funded
position, `R_t = r^c_t + X_t` (RA-INV-004/005).

## 4. Numeraire, FX translation and investable currency positions

### 4.1 Translation of a foreign total return

For a foreign total return `R^f_t`, translated to home currency:

```
1 + R^h_t = (1 + R^f_t)(1 + s_t)     ⇒     R^h_t = R^f_t + s_t + R^f_t s_t
```

This holds exactly (RA-INV-006). The **cross term** `R^f_t s_t` MUST be reported in any
decomposition.

**Quote inversion.** Where the market quotes AUD/USD as USD per AUD (`q`), the AUD investor's
spot return on USD is `s_t = q_{t−1}/q_t − 1`, **not** `q_t/q_{t−1} − 1` (RA-INV-007).

### 4.2 Spot change is not an investable return

`s_t` alone is `price_only`. An investor earns currency exposure only by holding a
foreign-currency asset (cash, a deposit, a bill) or a forward or futures position.

- **Investable currency position: foreign cash held by a home investor.**

  ```
  1 + R^{FXcash,h}_t = (1 + r^{c,f}_t)(1 + s_t)
  X^{FX}_t = R^{FXcash,h}_t − r^{c,h}_t
           = s_t + (r^{c,f}_t − r^{c,h}_t) + r^{c,f}_t s_t       (spot + carry + cross)
  ```

- **Forward-based equivalent, on the same capital.** Compare the two constructions on the
  **same initial home capital `K`**, with settlement at `T`.
  - **Funded cash** (period rates `r^h`, `r^f`): convert `K` at `S_0`, earn `r^f`, convert back
    at `S_T`, and repay funding `K(1 + r^h)`. The excess per unit of `K` is
    `(1 + r^f) S_T/S_0 − (1 + r^h)`.
  - **Forward:** buy `N = K(1 + r^f)/S_0` units of foreign currency forward at `F`. That is the
    foreign amount the cash position delivers at `T`. The excess per unit of `K` is
    `(1 + r^f)(S_T − F)/S_0`.
  - **Under covered interest parity (CIP),** `F = S_0 (1 + r^h)/(1 + r^f)`, and the two are
    **identical**: both equal `(1 + r^h)(S_T/F − 1)`.
  - **`S_T/F − 1` is a return per unit of forward notional `F`, not per unit of capital.** It
    differs from the capital-normalised excess by the certain factor `(1 + r^h)`. This is a
    normalisation, not market basis.
  - **After normalising** to the same capital and cash flows, the only remaining differences are
    the **CIP basis and the fixing and timing basis**. Those are triangulation terms, never part
    of the identity (RA-INV-021).
  - **Fixtures:**

    | Case | Inputs | Cash excess | `S_T/F − 1` | `(1 + r^h)(S_T/F − 1)` |
    |---|---|---|---|---|
    | (a) | `S_0 = S_T = 1`, `r^h = 10%`, `r^f = 0`, so `F = 1.1` | −10.000000% | −9.090909% | −10.000000% |
    | (b) | `S_0 = 1.5385`, `S_T = 1.5000`, `r^h = 0.036 × 30/365`, `r^f = 0.043 × 30/360`, so `F = 1.5375427458` | −2.4489615842% | −2.4417367194% | −2.4489615842% |

### 4.3 Hedged foreign return

The hedge ratio is `h`, applied to the start-of-period foreign value. The forward is set at
`t−1` for the period, with forward premium `f = F_{t−1,t}/S_{t−1} − 1`:

```
R^H_t = (1 + R^f_t)(1 + s_t) − 1 − h (S_t − F_{t−1,t}) / S_{t−1}
      = R^f_t + s_t + R^f_t s_t − h (s_t − f)
with h = 1:   R^H_t = R^f_t + f + R^f_t s_t       (exact; RA-INV-009)
```

The residual currency exposure `R^f_t s_t` comes from foreign gains or losses during the period
that are not hedged until the next reset.

The spec MUST declare:
- the hedge reset frequency;
- the notional rule (start-of-period value);
- the source of `F`: market forward points (`market_forward`), or a rate differential
  (`cip_implied`, with the rate series ids).

`cip_implied` is `replicable_with_basis`.

### 4.4 Fixing time and calendar

- FX fixings are taken at a stated time and venue, for example the RBA 4pm Sydney rate, or a New
  York noon rate [EXT].
- A foreign asset priced at its own market's close and translated at a fixing taken many hours
  earlier or later produces **daily** returns with timing noise. That noise does not cancel day
  by day; it largely cancels over longer windows.
- The spec MUST declare the joint calendar and alignment rule.
- Statistical uses SHOULD prefer weekly or monthly sampling, or synchronised data.

## 5. Equities

- **Market-price TR versus NAV TR.**
  - Market-price TR uses traded closes. NAV TR uses the fund's published NAV.
  - For ETFs these differ by the premium or discount and by timing. They are different series
    ids.
  - An index TR (provider-calculated) is a third object, with no fund fees.
- **Gross versus net index TR.** Index providers define "net" TR by deducting withholding at a
  provider-defined rate [EXT]. A spec using a provider TR MUST cite the provider's methodology
  document and version.
- **Corporate actions.** These are stored as their own observations, never pre-applied to
  prices:
  - splits and consolidations;
  - bonus issues;
  - rights issues;
  - spin-offs;
  - special and return-of-capital distributions;
  - mergers and delistings.

  The construction applies the adjustment factor to the prior price or the unit count so that
  the price return is continuous, and the action creates no spurious return (RA-INV-020).
- **Adjusted closes.**
  - A vendor `Adj Close` MUST NOT be used as a TR unless the vendor's adjustment method is
    documented and verified, and its revisions are captured as vintages.
  - [OBS] `macsmsf` rejected yfinance `Adj Close` in favour of unadjusted closes plus explicit
    distributions ("Policy A"), and recorded a retroactive vendor revision (`sql/043`).
- **Withholding tax.** Declare `w` and its basis (treaty rate, provider rate, none).
- **Franking credits** (Australia) are a **tax attribute**, not part of a pre-tax return.
  - They are recorded as their own observation (franking per unit, franking percentage).
  - They are applied in the implementation and after-tax bridge for a mandate's tax profile.
  - They are never folded into a factor's TR.

## 6. Bonds

- **Dirty price.** `P^{dirty} = P^{clean} + AI`. The TR over a period is
  `(P^{dirty}_t + C_t) / P^{dirty}_{t−1} − 1`, where `C_t` is a coupon paid in the period.
  Coupons are reinvested per the declared convention: in the index on the payment date, or held
  as cash.
- **Day-count and frequency** are declared per market. For example, Australian and US
  government bonds pay semi-annual coupons, with ACT/ACT conventions [EXT].
- **Constant-maturity (CMT) synthetic bond return** (the construction for "duration factor"
  series):
  1. At `t−1`, create a bond with maturity `M` and coupon equal to the par yield `y_{t−1}(M)`,
     priced at par.
  2. At `t`, revalue the same bond, now with remaining maturity `M − τ`, on the curve at `t`
     interpolated at `M − τ`. Include the accrued coupon.
  3. `R_t = (P^{dirty}_t + C_{(t−1,t]}) / P^{dirty}_{t−1} − 1`, where `C_{(t−1,t]}` is all coupon
     cash the bond pays in the period. **Convention:** coupon cash is held, without interest,
     to the period end and reinvested at the re-strike. The re-strike uses total wealth
     `P^{dirty}_t + C`, so no coupon is lost. Then re-strike a new par bond at `t`.

     **Fixtures (RA-INV-013):**

     | Case | Calculation | Return |
     |---|---|---|
     | coupon date | `P^{dirty}_{t−1} = 102`, coupon `C = 2` paid, `P^{dirty}_t = 100` (ex-coupon) | `(100 + 2)/102 − 1` = **0** |
     | non-coupon date | `101.00 → 101.05`, `C = 0` | **0.000495049505** |

     Omitting `C` would report −1.9607843137% on the coupon date, which is wrong.

  The spec MUST declare:
  - the curve source and type (par, zero or yield-to-maturity of benchmark lines; treating a
    benchmark YTM as a par yield is an approximation that must be declared);
  - the interpolation method;
  - the pricing method (full discounting on a zero curve, or a flat-yield approximation);
  - the re-strike frequency (daily or monthly).
- **Decomposition** (reported; it is not the definition):

  ```
  R_t ≈ carry (y τ) + roll-down (−D [y_{t−1}(M−τ) − y_{t−1}(M)]) + curve change (−D [y_t(M−τ) − y_{t−1}(M−τ)]) + ½ C Δy² + residual
  ```

  The full revaluation is the definition. The residual MUST be reported, and SHOULD be bounded
  (for example, under 1 bp a day when |Δy| < 25 bp). That bound is a test of the approximation,
  not an identity.
- **Masquerade risk.** `−D × Δy` on its own is a *price* approximation (`price_only`), not a TR.

## 7. Credit

- **Rate duration versus spread duration.** A floating-rate note has rate duration ≈ time to the
  next reset, but spread duration ≈ maturity. A fixed-rate corporate bond has both ≈ its
  duration.
- **Excess return reference.** Two different series, with two series ids:
  - credit excess over **duration-matched (or key-rate-matched) government bonds**, which
    isolates spread;
  - credit excess over **cash**, which includes the rate leg.

  The spec MUST name which.
- **Default and recovery.** Index returns include defaults through price falls and the recovery
  methodology [EXT]. **The spread is not the expected return:** expected excess ≈ spread − expected
  loss (default probability × loss given default) − downgrade drift. This belongs in
  expected-return models, not in return accounting.
- **Funding.** Excess over cash uses the stated cash leg (§9).

## 8. Futures, commodities and trend strategies

- **Contract P&L.** Same-contract, settlement to settlement:
  `PnL_t = n (F_t − F_{t−1}) × multiplier`, in the contract's currency. Contract specs
  (multiplier, tick, currency, settlement method, expiry, first notice) are reference data
  [EXT per contract].
- **Excess return of a fully collateralised position** with capital `K_{t−1}` and `n` contracts:

  ```
  X_t = n (F_t − F_{t−1}) × multiplier / K_{t−1}
  ```

  If the notional is reset to capital each period (`n = K_{t−1} / (F_{t−1} × multiplier)`),
  then `X_t = F_t / F_{t−1} − 1` on the **held** contract. If the contract count is fixed
  between rolls, leverage drifts, and the rule MUST be declared.
- **Total return** = collateral return + excess return: `TR_t = r^c_t + X_t`. This is exact by
  construction when collateral equals capital (RA-INV-011).
  - Margin is posted from collateral, which still earns `r^c` under the declared assumption.
  - Fees, commissions and roll slippage are declared costs (`investable_with_costs`).
- **Rolls.**
  - The roll rule (dates, a schedule such as *N business days before first notice*, or an
    open-interest crossover) is declared.
  - On a roll date, the old contract is closed and the new contract opened **at the same
    settlement timestamp**.
  - **No cross-contract price difference enters the return** (RA-INV-010).
- **Continuous series:**
  - an unadjusted stitched front-month series jumps at rolls, so it is `price_only`;
  - an additively back-adjusted series has distorted percentage changes and can go negative, so
    it is `price_only`;
  - a ratio-adjusted series preserves held-contract percentage returns *only* if it is built on
    our own roll dates at our settlements.

  We compute returns from contracts, never from continuous levels (RA-INV-012).
- **Spot versus futures.** For commodities, the futures excess return ≈ spot change + roll yield
  (basis convergence).
  - A spot commodity price is `price_only`.
  - The fully collateralised TR adds `r^c`.
  - Gold spot, gold futures XR and gold futures TR are three different series.
  - **None of them is an inflation measure.**
- **FX futures** may quote foreign per home or home per foreign (for example a contract quoted in
  USD per AUD [EXT]). Signs and numeraire are converted per §4.
- **Currency of P&L.** A home-currency investor holding a foreign futures position, collateralised
  in home cash, has currency exposure **only on accumulated P&L** until it is swept. The sweep
  frequency is declared. A fully collateralised foreign futures position is therefore close to
  currency-hedged. This differs from holding the foreign asset itself.
- **Trend and other strategies** (`strategy_return`):
  - weights are a declared function of signals observable at or before `t−1`, with the
    `knowable_at` rule;
  - returns are `Σ_i w_{i,t−1} X_{i,t}` plus `r^c` if the strategy is reported as a TR;
  - volatility scaling, leverage caps, rebalancing and costs are declared;
  - validation is by unit tests against the spec, and by replicating a published study on its
    own sample. Comparison with other trend series is triangulation only.

## 9. Home currency (AUD) and cash legs

- **One cash-leg definition per currency per release:**

  | Currency | Default | Basis |
  |---|---|---|
  | AUD | overnight accrual at the RBA cash rate (interbank overnight rate), ACT/365F, per §3.2; regime (ex-ante or in arrears) per its publication timing [EXT, T-0002] | `replicable_with_basis` |
  | USD | SOFR compounded in arrears, ACT/360, per §3.2, from its first publication date; any earlier splice (EFFR, bills) declared as a separate segment | `replicable_with_basis` |

  The rate definitions and history are [EXT].
- **No omission or double-counting of cash.** A portfolio combines factors either as:
  - **excess form:** `R^p_t = r^{c,home}_t + Σ_i w_i X^{home}_{i,t}`, where the weights are
    exposures, need not sum to 1, and cash is counted once; **or**
  - **funded form:** `R^p_t = Σ_i w_i R^{home}_{i,t}`, with `Σ w_i = 1`, including any explicit
    cash holding.

  Mixing the two forms in one portfolio is prohibited (RA-INV-015).
- **Foreign excess returns in home terms.** A home investor's excess return on a foreign asset
  depends on whether the currency is held (unhedged) or hedged. The spec MUST state which. A
  "USD excess return translated at spot" is neither, unless its construction is defined.

## 10. Single-period identities versus cumulative relationships

The identities in §3 to §8 hold **per period**. Independently compounded cumulative indices do
**not** satisfy the same identities.

For example, `Π(1 + r^c_t + X_t) ≠ Π(1 + r^c_t) + Π(1 + X_t) − 1`. The two-period difference is
`c (x_1 + x_2)` plus higher-order terms (worked example §14.5).

**Tests MUST:**
- verify identities period by period;
- compare cumulative quantities only after compounding the *per-period identity*.

Comparing a cumulative TR index with the "sum" of cumulative component indices, and calling the
gap an error, is itself an error (RA-INV-016).

## 11. Triangulation against independent references

A comparison between independently constructed series is a **triangulation**, not an identity.
The spec MUST pre-register, for each comparison:
1. the reference series and why it is comparable;
2. the **expected-difference model**: the mechanisms (fees, withholding, basket versus constant
   maturity, CTD and delivery option, fixing time, hedge mechanics, valuation lag), each with a
   predicted sign and, where possible, a magnitude;
3. the metrics:
   - annualised tracking difference;
   - tracking error;
   - correlation of weekly differences;
   - maximum cumulative gap;
   - behaviour around known events;
4. the outcome categories:
   - **explained**: within predicted mechanisms;
   - **partly explained**;
   - **unexplained**: opens an investigation. It does not automatically fail the series, and it
     does not pass it.

## 12. Promotion gate (anti-masquerade)

Before a series can be referenced as a return factor by any model or portfolio spec, CI checks:
- `series_class` ∈ {`total_return`, `excess_return`, `strategy_return`};
- the applicable invariants (§13) pass;
- the triangulation report exists;
- the rights record allows the intended use;
- the status is at least `validated` for use outside exploratory work.

A `price_only` series can be promoted only through a new spec that derives an income-inclusive
return from additional observations.

## 13. Invariant catalogue

These are identities unless marked *(bound)*. The tolerance is 1e-12 relative, unless stated.

| ID | Invariant |
|---|---|
| RA-INV-001 | `TR_t = PR_t + IR_t` per period (same `w`) |
| RA-INV-002 | a series uses one valuation basis (market price, NAV or index), never mixed |
| RA-INV-003 | cash accrual follows §3.2: window `t−1 ≤ d < t`, the rate applicable to each day's overnight, and `Π(1 + rate_b n_b / B) − 1`; the §3.2 fixtures reproduce exactly; the index is the product of `(1 + r^c)` |
| RA-INV-004 | `X_t = R_t − r^c_t`, same currency and period, with the cash-leg id recorded |
| RA-INV-005 | the funded TR reconstructs from cash + excess exactly |
| RA-INV-006 | `(1 + R^h) = (1 + R^f)(1 + s)`; the cross term reported |
| RA-INV-007 | `s` from an inverted quote uses `q_{t−1}/q_t − 1` |
| RA-INV-008 | an investable currency return includes a foreign cash or forward leg; spot-only series are `price_only` |
| RA-INV-009 | hedged return decomposition per §4.3 holds exactly for the declared `h`, `F` and reset |
| RA-INV-010 | the futures excess return uses same-contract settlement changes only; no cross-contract difference on a roll date |
| RA-INV-011 | futures TR = collateral + excess, exactly, under the declared notional rule |
| RA-INV-012 | no return is computed from continuous or back-adjusted futures levels |
| RA-INV-013 | bond TR = `(P^{dirty}_t + C_{(t−1,t]})/P^{dirty}_{t−1} − 1`, including in CMT step 3; the coupon-date and non-coupon-date fixtures (§6) reproduce; decomposition residual reported *(bound declared per spec)* |
| RA-INV-014 | credit excess declares its reference (government duration-matched, or cash); distinct series ids |
| RA-INV-015 | portfolio combination uses excess form or funded form, never mixed; cash counted once |
| RA-INV-016 | cumulative comparisons compound the per-period identity; never single-period identities across independently compounded indices |
| RA-INV-017 | net-of-withholding distributions use `D(1 − w)` with the declared basis |
| RA-INV-018 | multi-currency series use a declared joint calendar and alignment rule; accrual carried across non-business days |
| RA-INV-019 | `price_only` and `state_indicator` series are never referenced as returns (CI) |
| RA-INV-020 | corporate-action adjustments produce no spurious return on the action date |
| RA-INV-021 | cash-versus-forward FX comparisons are normalised to the same capital and cash flows before any difference is attributed to basis; the §4.2 fixtures reproduce |

## 14. Worked examples

### 14.1 Equity distribution day (§3.1)

- `P_{t−1} = 50.00`, ex-date `t`, `P_t = 49.20`, `D_t = 0.75`.
  - `PR = −1.600%`, `IR = +1.500%`, `TR = −0.100%`. The identity holds: −1.6 + 1.5 = −0.1.
- With `w = 15%`: `IR = 1.275%`, `TR = −0.325%`.
- A price-only series would report −1.600%. That is the masquerade this standard exists to
  prevent.

### 14.2 AUD investor holding USD overnight cash (§4.2; the HIO-S1 factor)

Illustrative inputs: one day; `q_{t−1}/q_t = 1.005` (the AUD weakens 0.5% against the USD,
so `s = +0.5%`); USD rate 4.30% ACT/360; AUD rate 3.60% ACT/365F.

| Quantity | Value |
|---|---|
| `r^{c,USD} = 0.043/360` | 0.000119444 |
| `r^{c,AUD} = 0.036/365` | 0.000098630 |
| `R^{FXcash,AUD} = (1 + r^{USD})(1 + s) − 1` | 0.005120042 |
| `X^{FX} = R − r^{AUD}` | 0.005021412 |
| decomposition: spot `s` + carry `(r^{USD} − r^{AUD})` + cross `r^{USD} s` | 0.005 + 0.000020814 + 0.000000597 = 0.005021412 ✓ |

### 14.3 Hedged foreign return (§4.3)

Illustrative inputs:
- `R^f = +2.00%` over 30 days;
- `S_{t−1} = 1.5385` AUD per USD;
- `S_t = 1.5000`, so `s = −2.5024%`;
- `F = S_{t−1} × (1 + 0.036 × 30/365)/(1 + 0.043 × 30/360) = 1.537543`, so `f = −0.0622%`.

| Quantity | Value |
|---|---|
| unhedged `(1.02)(1.5/1.5385) − 1` | −0.5525% |
| hedge P&L `(F − S_t)/S_{t−1}` | +2.4402% |
| hedged | **+1.8877%** |
| check: `R^f + f + R^f s = 2.0000 − 0.0622 − 0.0500` | 1.8877% ✓ |

### 14.4 Futures roll (§8)

Illustrative inputs:
- multiplier 50;
- capital 1,000,000;
- the notional is reset to capital at each roll.

| Day | Held | Settlements | Return |
|---|---|---|---|
| t−1 | Dec | Dec 5000.00 | — |
| t (roll date) | Dec → Mar | Dec 5010.00; Mar 5045.00 | Dec only: 5010/5000 − 1 = **+0.2000%** (4 contracts × 10 × 50 = 2,000) |
| t+1 | Mar | Mar 5040.00 | 5040/5045 − 1 = **−0.0991%** |

Three wrong constructions:
- **Unadjusted stitched series:** 5045/5010 − 1 = **+0.6986%** on day t. This is a roll artefact,
  not a return.
- **Additive back-adjustment (+35):** t−1 = 5035, so 5045/5035 − 1 = +0.1986% ≠ +0.2000%. Close,
  but wrong, and the error grows with each roll.
- **Total return:** add the collateral leg: `TR = r^c + X`.

### 14.5 Single-period identity versus cumulative indices (§10)

Illustrative inputs: `r^c = 0.0002` each day, `X_1 = +1.0%`, `X_2 = −0.5%`.

| Quantity | Value |
|---|---|
| per-period TR | 1.0102%, −0.4800% (identity holds each day) |
| cumulative TR `1.010200 × 0.995200 − 1` | **0.535104%** |
| cumulative cash `1.0002² − 1` | 0.040004% |
| cumulative excess `1.01 × 0.995 − 1` | 0.495000% |
| cumulative cash + cumulative excess | 0.535004% |
| gap | **0.000100% = c (X_1 + X_2)**: not an error, a compounding fact |

### 14.6 Bond CMT day (§6; approximation for intuition only)

Illustrative inputs:
- a 10-year par bond, coupon 4.00%, semi-annual coupons;
- next day the curve at 9.997 years is 4.05%;
- modified duration ≈ 8.18, convexity ≈ 79.

| Component | Contribution |
|---|---|
| price | ≈ −8.18 × 0.0005 = −0.409% |
| convexity | ≈ +0.001% |
| carry (one day of coupon) | ≈ +0.011% |
| total | **≈ −0.397%** |

The standard requires full revaluation. These approximations exist to bound and explain the
residual.

## Changelog

- 0.1 (2026-10-18): initial proposed version.
- 0.2 (2026-10-18): §3.2 overnight accrual (window, applicable rate, in-arrears compounding, ex-ante versus in-arrears, fixtures); §4.2 same-capital forward identity; §6 CMT coupon cash; RA-INV-003/013 revised; RA-INV-021 added (T-0008, F-REVIEW-2026-10-18-a01-2, -4, -7, -8).
