---
id: HIO-EVIDENCE-FACTORS-BUILD-9
title: "IGB market total return rebuilt at spec 0.1.1 without one duplicate vendor distribution record (OD-0230)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-22
instruction: OD-0230
---

# Factor build 9: the corrected IGB series

> **Exploratory and unaccepted.** The mechanism and the expected result are in OD-0230, declared before the build. **No value from the series is recorded here** (OD-0210). Run once, by the author; not reviewed.

## What changed

- **The spec** `rates.au.igb.market_total_return` is at 0.1.1 (proposed). It declares one `source_corrections` entry: exclude the distribution record dated on the fund's distribution-dates notice, the duplicate of the record on the true ex-date (`distribution-screen-1.md`; OD-0229). Version 0.1.0 is archived.
- **The tool** `tools/factor_build.py` honours the entry (worker W1, checked `ac0f63e`): it removes exactly one matching record before the series is built, refuses on zero or several matches, and writes what it removed into the build record. The snapshot is never written.

## The build

| Factor | Spec | Snapshot | Build id | `series.csv` sha256 | Invariants |
|---|---|---|---|---|---|
| `rates.au.igb.market_total_return` | 0.1.1 | `s4` | `806c46a7f761cd6d` | `64d68d5789ce4a64779fb41b40434b73a67c3a6f0d76d7f514c888bdba63a2b9` | pass |

Snapshot manifest sha256 `02b24e78d77aba7ef2bb65c7fdf0e0c740611169acf327b09871eee2138de1a5`, unchanged by the build. The 0.1.0 build (`199fc6678055c500`) is kept beside it.

## Checks on real data

| Check | Result |
|---|---|
| Against the 0.1.0 build, row by row | as declared: no price return differs; **one** period's income and total return differ; every index level from that period on differs, none before |
| An independent recomputation of every period and level (rational arithmetic, raw files, no HIO code) | within 1e-12 throughout |
| The screen on the corrected inputs | the D3 flag is gone; the three D1-only days remain |
| Broken on purpose: the same spec with the date moved one day | refused, no record matches |

## Limits

- The duplicate was confirmed on two public pages, one a syndicated copy of the fund's announcement; the issuer's page and the ASX notice itself were not read.
- **The correction lives in this one factor's spec.** Any other series built from IGB's inputs would need the same entry. Nothing else uses IGB today.
- The three remaining D1 flags are unchecked against the issuer.

## Not established

That the series is otherwise right. Nothing is accepted, and no other fund is corrected.
