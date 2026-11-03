---
id: HIO-EVIDENCE-B3-FIRST-RUN
title: "B-3: the first live run and its read-back (2026-11-04 Sydney)"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0143, go-live package steps 3 to 6
---

# B-3 first live run

Run `41733292506` (`workflow_dispatch`, approved by the owner) at `0a2c0a1`: job started 2026-11-03T22:46:24Z. **Exit 1.** Reviewer rule on; alert off. No values are recorded here.

| Publication | Slot | Outcome | Read-back with the owner's reader identity |
|---|---|---|---|
| `nyfed.sofr` | final | `verified_changed` | HTTP 200, approved URL; receipt hash matches; 30 keys parse |
| `nyfed.sofr_index` | final | `verified_changed` | same; 30 keys parse |
| `rba.f1` | first | `verified_changed` | same; two series, back to 2011-01-04 |
| `rba.expert_judgement` | first | **`failed`, `schema`** | HTTP 200, approved URL; no receipt, as designed |

**Step 3 list (D-2), computed before the run.** Every `missed` line in the run equals this list, and there were no others.

| Publication | Slot | Due (UTC) | Clears (UTC) |
|---|---|---|---|
| `nyfed.sofr`, `nyfed.sofr_index` | final | 2026-11-02T20:00 | 2026-11-03T23:00 |
| `rba.f1`, `rba.expert_judgement` | first | 2026-11-02T22:45 | 2026-11-04T01:45 |
| `rba.f1`, `rba.expert_judgement` | final | 2026-11-03T05:30 | 2026-11-04T08:30 |
| `nyfed.sofr`, `nyfed.sofr_index` | first | 2026-11-03T13:30 | 2026-11-04T16:30 |

**Cause of the failure.** The live file opens with prose, and one prose cell holds both "date" and "type". The parser took that row for the header and then refused the next row. The go-live package named this
risk. Established from one manual download under OD-0145, deleted after use. Fix: T-0017.

**Not shown:** a watched pass of the expert-judgement file; the alert; unattended operation. The failed attempt record is retained under the account's 3,650-day default.
