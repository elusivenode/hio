---
id: HIO-EVIDENCE-E0001-VARIANT-1
title: "E-0001 variant V1: zero-curve valuation, with interpolation sensitivity"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0163
---

# E-0001 variant V1

> **Post-hoc and UNREFERENCED. E-0001's verdict stands:** the flat-yield approximation failed B6 and B7. Valuing on the zero curve is a construction convention, not evidence of being closer to market prices. Spec 0.2.0 stays proposed. **No value is recorded here.**

Run at `7399b55` on the bytes retained for E-0001. Summary sha256 `099577812e6942d45c6291380aa7e6412133220d5e5f9678555c8bea64ec9fff`. Release `rel-1eed9b84100cf6abb02d3fa2b9a7996d369970446c8a0e4698e5191384995652`, exploratory, local store only. 9,215 periods, none uncovered or refused.

| Comparison, against B6 to B8's numbers | 1 bp on 99% | 5 bp at worst | 10 bp a year |
|---|---|---|---|
| Zero curve against flat yield (E-0001's own comparison) | fail | fail | pass |
| Monotone cubic against linear par grid | **pass** | **pass** | **pass** |

**Reading, as pre-registered:** the choice between these two interpolations isn't decisive here, and that says nothing about market accuracy. The valuation basis matters much more than this interpolation choice. Only one alternative was tried, so other curve models are untested.

**Not established:** which series is closer to a traded return. No independent reference exists. Not reviewed by Codex.
