---
id: HIO-EVIDENCE-T0023-CORROBORATION-2
title: "T-0023 corroboration with IEF's NAV: C1 and C2 pass for IEF; C5's NAV row fails"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0178 (step 3); E-0004's data condition, OD-0190
---

# T-0023 corroboration 2: IEF's NAV obtained

> **Exploratory and unaccepted.** No EODHD-derived value is recorded here; gaps are in the local report (`~/.hio-research/T-0023/corroboration/20261121T231045Z-60cd1edf/`). The issuer's file was downloaded once by the owner's browser on 2026-11-22: `iShares-7-10-Year-Treasury-Bond-ETF_fund.xls`, sha256 `a195241c…`, iShares (BlackRock) fund data, no endorsement implied, not redistributed. Extracted to `nav-ief.csv` by `tools/t0023_reference.py` (the iShares reader by worker W13; the bare-ampersand fix by Claude, found on the real file): 6,127 days, 2002-07-22 to 2026-11-20. Tools run at `60cd1ed`.

| Check, IEF | Corroboration 1 | Now |
|---|---|---|
| C1 close against NAV, every month of 2008 | not performed | **pass** |
| C2 market return against NAV return | not performed | **pass** |
| C5 distributions, two fiscal years | pass | pass |
| C5 total return, two fiscal years | pass | pass |
| C5 NAV against the audited report | not performed | **fail** |

Every other check is unchanged (C1 BIL fail, C4 IEF fail, C5 SPY fail; S1 to S5 pass).

**C5's NAV row.** The issuer's daily NAV is within the 0.01 bar at the first fiscal start but exceeds it at the 2008-02-29 boundary and at the 2009 fiscal end (gaps local only). Two untested explanations: audited year-end NAVs can include financial-statement adjustments that the published daily NAV doesn't, and 2009-02-28 was a Saturday, so the end anchor moves to the next trading day. **The fail stands.** It doesn't touch E-0004, whose data condition is C1 and C2 for IEF.

**What this closes.** The sleeve carrying the duration result now has a close-against-NAV check, which `recommendation-1.md` asked for before any inference.
