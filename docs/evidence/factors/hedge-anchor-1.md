---
id: HIO-EVIDENCE-FACTORS-HEDGE-ANCHOR-1
title: "Hedge anchor: the CIP-implied hedged SPY series against a traded AUD-hedged S&P 500 fund (OD-0226)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0226
---

# Hedge anchor 1

> **Exploratory and unaccepted.** The checks and their readings are in OD-0226, declared before the fetch; its correction 1 was made before any comparison. **No value from the series is recorded here** (OD-0210): the figures are in `~/.hio-research/analytics/hedge-anchor-ihvv/note.md`. Run once, by the author; not reviewed.

## What was fetched and built

- **One fetch** on 2026-11-22: `tools/eodhd_eval.py fetch --snapshot s5 --symbols IHVV.AU`, four files, no stop; manifest sha256 `c22fe84078fc113000479665dc98abccd76a690b6d16eee1c8686504e7f3bd23`. The fetch list gained the symbol first (worker W1, checked `bc2da74`).
- **Two proposed specs, two local builds,** with `tools/factor_build.py` unchanged:

| Factor | Snapshot | Build id | `series.csv` sha256 | Invariants |
|---|---|---|---|---|
| `equity.us.ihvv.aud_hedged.market_total_return` | `s5` | `e5a5dbf4ff45c95f` | `86cacb576cf95f3d8acb1295fe82350c95783efee4730b581a97e571741fb7f1` | pass |
| `equity.us.ivv_au.market_total_return` | `s2` | `37e6b519c1ed236d` | `2fb6f4aabdef6521a50fea5c953c6a2f7eb3a93551e862c2989f8f80ca865a08` | pass |

Both agree with an independent recomputation in exact arithmetic, every period within 1e-12. **Passing those checks did not make either series right:** see the defects below.

- **The comparison:** `tools/sleeve_comparison.py` on the two funds and HIO's hedged and unhedged AUD SPY series, with AUD cash; `comparison.json` sha256 `4ff15d3dc00a2fd44273486ea6774bddbd0800ace5bf09950b259889096d455e`. The hedge effects (each hedged series minus its unhedged twin, monthly) were computed by a script from its `monthly.csv`.

## Result against the declared readings

| Check | Reading |
|---|---|
| H1 correlation of the two monthly hedge effects | **at or above 0.95: the construction captures the hedge** |
| H2 mean difference of the hedge effects, HIO minus fund | **large** on all common months; **moderate** excluding January 2016. HIO's is the higher in both |
| H3 annualised return, HIO hedged SPY minus the fund | **not consistent:** outside the bar, HIO higher; the interval excludes zero |
| H4 correlation of monthly returns | **just below** the bar |

A control outside the declared checks: the two unhedged series agree closely in level, so the gap sits in the hedge and not in the equity leg.

**So the CIP-implied hedged series follows a traded hedged fund month by month, and overstates its return.** The diagnostic-only label (OD-0225) stays.

## Post hoc, not tests

By calendar year the gap is uneven: a few volatile years carry most of it, and calm years show a small steady part. That pattern fits a fund whose hedge resets about monthly on a drifting notional, month ends that are not simultaneous, the hedged fund's higher fee [EXT], and a USD cash proxy (a bill fund) that returns less than a money-market rate. None of these was tested.

## Vendor data defects found

- **The unhedged twin's distributions are wrong before 2014:** four records are many times a normal distribution on days when the price barely moved, one of them a duplicate. The vendor's adjusted close carries the same error, so a build that agrees with it is no evidence. One record inside the comparison's span is doubtful; H1 and H2 are reported with and without its month (OD-0226 correction 1).
- **The hedged fund's unit split is dated one day early,** which puts two absurd offsetting daily returns in the series. Monthly figures are unaffected; daily figures and drawdown are not usable. One close in March 2020 looks like a bad print.
- **A screen** for a distribution out of line with the day's price move, run on every fund built so far, flags only the twin. The other series show nothing.

## Limits

- One fund, one vendor, 142 months, all after 2014. It anchors US equity only; the hedged US bond series is not anchored.
- The fund's distributions are the vendor's and were not checked against the issuer.
- The fund holds the index through its unhedged twin [EXT, not checked], so the pair is close but not identical in fees.

## Not established

The size of the cross-currency basis; that any hedged series is tradable or fit for a consumer; that a better USD cash leg would close the gap.
