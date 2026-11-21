---
id: HIO-EVIDENCE-B3-SOAK-1
title: "S1b-1 soak: declared boundaries and bar, before it starts"
status: current
owner: HIO architecture lead (owner); recorded by claude/implementation-agent
created_at: 2026-11-04
instruction: OD-0143 (the package's bar), OD-0149
---

# Soak 1: declared before it starts

| Item | Value |
|---|---|
| Period | `[2026-11-04T22:45:00Z, 2026-11-18T22:45:00Z)`: Thursday 2026-11-05 09:45 Sydney to Thursday 2026-11-19 09:45 Sydney; ten Sydney business days |
| Expected slots | **80** (`expected_slots`): 20 for each of `rba.f1`, `rba.expert_judgement`, `nyfed.sofr`, `nyfed.sofr_index` |
| Bar | at most 4 misses: met. 5 to 16: not met; the soak finishes and the owner decides. More than 16: stop and return to the owner (`docs/evidence/S1B1-go-live-package.md`) |
| A miss | `missing`; or a deciding attempt that started more than two hours after its due instant; or a slot delivered only by a manual run (read from each attempt's `execution.event`) |
| Also needed to pass | a written cause for every `failed` slot and every entry in `unreadable_records`; every slot reconciled |
| Startup gaps | every gap on the step 3 list clears by 2026-11-04T16:30Z, before the period starts. None is in the period |
| I-5 | met (OD-0149) |
| Owed after it | the dead-man exercise, the sampled CI-run audit, replay and reconstruction on live receipts |

**Report at the end:** `tools/soak_report.py` over exactly this period, with the owner's reader identity. No manual run is planned during the period; any that happens is recorded here with its reason.

A declared period and bar establish nothing about whether it passes. NY slots run on weekdays, so a check on a US holiday (Veterans Day, 2026-11-11) finds nothing new and records `verified_unchanged`.

## Result (recorded 2026-11-22 under OD-0181 item 5)

**The bar is met: 0 misses out of 80 slots.** This is the soak's record against its own bar, not acceptance of S1b-1, and it validates nothing beyond these ten days.

| Check | Method | Result |
|---|---|---|
| Every slot reconciled | `tools/soak_report.py --start 2026-11-04T22:45:00Z --end 2026-11-18T22:45:00Z`, the committed RITS 2026 calendar, run on 2026-11-22 by the owner's `az` login (read-only) | 80 of 80 slots; output sha256 `8417962a…76948`, kept outside the repository |
| Missing | the report | **0** |
| Failed | the report | **0**, so no cause is owed |
| `unreadable_records` | the report, and a direct load of every attempt record since the start | **empty**; 96 records loaded, none failed verification |
| Late (started > 2 h after due) | `start_lateness_seconds` per slot | **0**; median 446 s, latest 1,222 s (about 20 min) |
| Manual runs | each attempt's `execution.event`; separately, GitHub's run list for `s1b1-capture.yml` in the period | every attempt `schedule`; 164 workflow runs, all `schedule`, none `workflow_dispatch`. No manual run happened, so none is recorded above |
| One attempt per slot | the report's `attempts` | 80 slots, each decided by its only attempt |

| Publication | Expected | Captured | Verified unchanged |
|---|---|---|---|
| `rba.f1` | 20 | 10 | 10 |
| `rba.expert_judgement` | 20 | 0 | 20 |
| `nyfed.sofr` | 20 | 9 | 11 |
| `nyfed.sofr_index` | 20 | 9 | 11 |

**What this shows, and what it doesn't.** Ten Sydney business days of scheduled capture with no gap, failure or late start. It doesn't show publication timing (a `verified_unchanged` slot may mean the publisher hadn't posted yet), and it doesn't show that the alert would fire, since nothing failed. Owed next, each needing its own yes: the dead-man exercise, the sampled CI-run audit, and replay and reconstruction on live receipts. Run by one author, unreviewed.
