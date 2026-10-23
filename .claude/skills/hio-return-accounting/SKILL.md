---
name: hio-return-accounting
description: "Any HIO work that computes, constructs, compares or validates a return, index or factor series (cash, FX, bonds, credit, equities, futures, commodities, trend), or that writes or reviews a factor spec. Use BEFORE writing construction code, invariant tests, triangulation checks or a spec. Triggers: total return, excess return, price return, factor, index, cash leg, FX translation, hedged, futures roll, CMT, carry, triangulation, invariant."
---

# HIO return accounting

The authority is `docs/standards/return-accounting-and-factor-construction.md` (check its
version). Read the sections your task needs: §1 notation, §2 series classes, the section for
your asset class, §10 and §13.

The most common errors to stop before they happen:
1. **A price or level used as a return.** Check the series' `series_class` first.
2. **A spot FX change used as a currency return.** The investable version needs a foreign cash
   or forward leg (§4.2).
3. **Quote inversion.** Use `s = q_{t−1}/q_t − 1` when quoted foreign per home (RA-INV-007).
4. **Returns from continuous or back-adjusted futures.** Use same-contract settlements (§8).
5. **Cash counted twice**, or excess and funded forms mixed in one portfolio (RA-INV-015).
6. **A single-period identity tested on independently compounded indices** (§10, RA-INV-016).
7. **An agreement test between unlike series.** That is a triangulation with predicted
   differences (§11), not an identity.

Identity tests use a tolerance of 1e-12 relative, unless the standard or spec states a bound.
