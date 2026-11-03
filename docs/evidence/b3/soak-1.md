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

**The result isn't recorded here yet.** A declared period and bar establish nothing about whether it passes. NY slots run on weekdays, so a check on a US holiday (Veterans Day, 2026-11-11) finds nothing new and records `verified_unchanged`.
