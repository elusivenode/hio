---
id: HIO-EVIDENCE-S1B1-GO-LIVE
title: "S1b-1 go-live package (proposed): stage B-3, its URLs, punctuality bar, staging statement and order of steps"
status: proposed            # drafted under OD-0142; a request for an owner decision; authorises nothing
owner: HIO architecture lead (owner); drafted by claude/implementation-agent
created_at: 2026-11-03
base_revision: 387eee7ee39d91f5ab983284089a0949bda0fb9f
instruction: OD-0142 (draft only)
governs: [docs/evidence/S1B1-authorisation-B-package.md, docs/evidence/S1B1-authorisation-B-revision-1.md, OD-0063, OD-0116, OD-0119, OD-0140]
---

# S1b-1 go-live package (proposed)

> **Proposed.** Nothing here authorises go-live, a code change, a dispatch, an Azure write or a request to a data URL. While drafting, only
> publishers' documentation pages were read. No data URL was requested.

## What a yes would start

HIO's first real capture: four files a day from the RBA and the NY Fed, written to the evidence store and retained for 3,650 days. The
ten-business-day soak follows. Every release stays `exploratory`, and nothing is labelled final.

## Three things the earlier documents got wrong or left out

1. **Four URLs, not five.** The five datasets come from four published files, because F1 serves both AONIA and the TRI
   (`PUBLICATIONS`, `src/hio/sources/datasets.py:228`). The job refuses unless each of the four has a URL (`src/hio/jobs/s1b1_capture.py:214`).
2. **Merging arms the schedule.** The Authorisation B package has one watched dispatch and "then the schedule runs", but no separate step
   turns the schedule on. Moving the workflow with the constant set makes every cron firing live. The reviewer rule is the only hold
   point, because it pauses scheduled jobs too (OD-0119 C-4). So it comes off **after** the watched run, not before as the package lists it.
3. **The first live runs will fail, even if capture works.** The completeness check has no start date, so it counts slots from before go-live as
   missed (`missed_slots`, `src/hio/sources/schedule.py:130`). Simulated with no attempt records, a run at 2026-11-04T22:50Z reports **eight** missed
   slots and so exits 1. Each one is reported until 27 hours after its due instant. With a dispatch at about 22:50 UTC, the last clears at **16:30 UTC the next
   day, about 18 hours later**. See decision D-2.

## The URLs

| Publication | Datasets | Proposed URL | Source of the URL |
|---|---|---|---|
| `rba.f1` | `rba.cash_rate`, `rba.cash_rate_tri` | `https://www.rba.gov.au/statistics/tables/csv/f1-data.csv` | RBA statistical tables page, read 2026-11-03 |
| `rba.expert_judgement` | `rba.expert_judgement` | `https://www.rba.gov.au/statistics/tables/csv/f1-use-of-expert-judgement.csv` | same page |
| `nyfed.sofr` | `nyfed.sofr` | `https://markets.newyorkfed.org/api/rates/secured/sofr/last/30.json` | NY Fed API specification (`/static/docs/markets-api.yml`), read 2026-11-03 |
| `nyfed.sofr_index` | `nyfed.sofr_index` | `https://markets.newyorkfed.org/api/rates/secured/sofrai/last/30.json` | same specification |

- **Why `last/30`:** it is a judgement. About six weeks of values means a long outage leaves no gap in the receipts. A value that rolls off the start of
  the window is not treated as missing (`missing_keys`, `src/hio/sources/run.py:170`). The specification states no limit on the number.
- **Not `all/latest`:** the parser refuses any entry of another type (`src/hio/sources/datasets.py:161`).
- **What is not confirmed:**
  - The parsers' layouts rest on one structure check on 2026-10-25, whose samples were deleted (`docs/research/T-0002-rba-nyfed-evidence-2026-10-25.md`).
  - That check did not use the `sofrai/last` endpoint. It saw SOFRAI's fields in `all/latest`.
  - The watched run is the real test. A mismatch fails closed as a failed attempt record, with no receipt. That record is retained for 3,650 days, and the
    fix needs a PR.
- **Request rate:** rights rest on "two scheduled requests a day" (OD-0116 correction 1). That holds on a normal day. A slot that fails is retried on later cron
  firings, so a bad day can reach six requests per file. Claude reads this as within the "modest schedule" for the NY Fed, and asks the owner to confirm it for
  the RBA, as D-3.

## The punctuality bar

**What it measures:** slot delivery punctuality, per publication and in total. It doesn't prove the scheduler is punctual or that operation was unattended, and it
doesn't replace the architecture's scheduler trigger, which stays as written: scheduled runs over 20 business days (`docs/architecture.md` §5).

**The unit:** one slot instance from `tools/soak_report.py`, over a fixed period `[start, end)` declared before the soak. The report derives the exact count: about
**80 slots** for ten Sydney business days (four files, two slots each). **A miss** is any of:
- a slot reported `missing`;
- a slot whose deciding attempt started more than two hours after its due instant (`docs/implementation-plan.md`, stop condition 2);
- a slot delivered only by a manual run. The report doesn't separate these, so each attempt's `execution.event` is read as well.

| Misses over the soak | Result | Basis |
|---|---|---|
| 5% or fewer (at most 4 of 80) | bar met | a judgement, borrowing the architecture trigger's 5%. It is not that trigger |
| Over 5%, up to 20% | bar not met; the soak still finishes; the owner decides what follows | a judgement |
| Over 20% (more than 16 of 80) | stop and return to the owner | stop condition 2, applied to slots |

**The bar is necessary, not sufficient.** Meeting it doesn't pass the soak if any of these is open:
- a `failed` slot without a written cause;
- an entry in `unreadable_records` without a written cause;
- an unreconciled slot (base-camp criterion 2).

**Reported beside it:** the distribution of start lateness, and first checks that found nothing new, which reflect the publisher and not the scheduler.

**Limit:** slots aren't independent, because one dropped firing can hit two files at once.

## The staging statement (from revision 1, unchanged)

> Live S1b-1 capture runs under the OD-0063 staging until finality is met: every vintage is `schedule_only`; every release is `exploratory`, states its knowledge
> cutoff and is never labelled final; C5 is unresolved. C1–C7 evaluations, when recorded, are reported as they fall, and a failure is never overridden. Nothing
> here discharges a finality obligation.

## Prerequisites (revision 1's list, at the base revision)

| # | Prerequisite | State |
|---|---|---|
| 1 | The URLs approved | proposed above |
| 2 | Constant, workflow move, alert, reviewer rule | the steps below |
| 3 | `~/.hio-state/` backed up | **conflict:** revision 1 requires it; the owner's words make it optional (OD-0140 correction 1). See D-4 |
| 4 | Punctuality bar | proposed above |
| 5 | Staging statement | above |
| 6 | T-0015 merged | **done** (OD-0138) |
| 7 | R-1 and 7b | **done** (OD-0140 correction 1; `docs/evidence/b2/rerun-1.md`); the stop rule did not fire |
| 8 | C5 decided | no longer a gate (OD-0139) |
| 9 | Storage-error limit | **accepted for the soak** (OD-0140) |
| 10 | 2027 calendars | a hard date, not a gate. The calendar ends 2026-12-31, so without the 2027 file runs fail from then. A soak started in November finishes first |

## The steps, in order

**The go-live PR (Claude; merged with the owner's yes):**
- set `LIVE_AUTHORISATION` to the go-live OD's id (`src/hio/jobs/s1b1_capture.py:61`);
- set the four URLs on `PUBLICATIONS`, with a test pinning them;
- move the workflow to `.github/workflows/s1b1-capture.yml`, and correct its name and its "disabled" comments;
- update the tests that pin the disabled state: `tests/test_t0010_capture_cli.py:94`, `tests/test_t0013_completeness.py:700`,
  `tests/test_s1b1_remediation_schedule.py:26,57`, `tests/test_t0012_script_workflow.py:15`. The refusal must stay tested, with the constant patched to `None`.

**On the day, with the owner present:**

| # | Step | Who | Check |
|---|---|---|---|
| 1 | Confirm the GitHub failure-email setting is on for the owner's account (`infra/tofu/README.md`, I-5) | owner | scheduled-run emails go to whoever last changed the cron schedule, so the moved file must land under the owner's account |
| 2 | Merge after the 21:00 UTC cron firing and before 22:45 UTC, with the reviewer rule still on | owner | CI green; no run approved yet |
| 3 | Compute the exact list of pre-go-live gaps and when each expires, and keep it with the evidence | Claude | this list is the whole of D-2's exception |
| 4 | Dispatch between **22:46 and 22:53 UTC**, and approve that identified run | owner | the only overlap of the RBA first slot and the NY final slot ends at 23:00 UTC, and the job needs time to start. One run can then exercise all four files (simulated) |
| 5 | Watch it | Claude reads; owner sees | a `ran` line for each file. Exit 1 is expected only if every `missed` line is on the step 3 list |
| 6 | Read back: one attempt record and one receipt for each file; the requests went to the approved URLs; the receipts parse | owner's reader identity | any failure stops here, with the rule still on |
| 7 | `tofu plan`, then `tofu apply` with `alert_enabled = true`, and read the rule back | owner (C-6) | only that change in the plan. It follows the first write, because the rule would otherwise fire at once |
| 8 | Remove the reviewer rule (C-4; keep the `main`-only branch policy) | owner | monitoring is on before anything runs unattended |
| 9 | Check the schedule's status, and that the next scheduled firing ran | Claude | T-0013's residual on disabled or dropped schedules |

**Times are for AEDT and EST,** in force until March 2027. The dispatch needs a date that is a RITS day in Sydney and a weekday in New York. The overlap is a
convenience, not a condition: if it is missed, keep the rule on and dispatch again in the other publisher's next window, so each file has a watched run before step 8.
Scheduled firings can queue behind the rule, and GitHub's handling of that is unverified. A waiting scheduled run inside a due window may be approved instead, and
any other is rejected. A later run skips slots that are already verified.

These attempts come before the soak starts, so their lateness doesn't count: the NY final attempts in the overlap are nearly three hours late.

**If step 4 or 6 fails:** reject any waiting runs and fix by PR. The failed records stay. Backing out needs only a PR that sets the constant to `None`. Objects
already written stay under retention (revision 1, risks).

**The failure email (I-5), before the soak counts.** A **scheduled** run must fail on purpose and the owner must receive the email; a dispatched failure doesn't count
(`infra/tofu/README.md`). Proposed method, the day after the dispatch: once the 20:00 UTC NY slots have verified records, make a `capture` Environment variable invalid,
let the 21:00 UTC retry firing fail with exit 2, then restore the variable. No code changes, the `schedule:` line isn't touched, and no slot is lost, because that firing has
nothing left to do. That GitHub accepts the temporary value is unverified, and Claude will confirm the exact change with the owner first.

**The soak** starts at a declared boundary after that: the next RBA first-slot due instant. It runs for ten Sydney business days, ending at the RBA first-slot due instant
ten business days later. Illustration: a dispatch on Monday 2026-11-09 at 22:50 UTC gives a soak over `[2026-11-10T22:45Z, 2026-11-24T22:45Z)`, which is 80 slots.

**Owed after it starts:**
- the sampled CI-run audit;
- replay and reconstruction on live receipts;
- **the dead-man alert firing and recovering, as a separate exercise after the ten days.** It counts attempt-record writes, and a failed capture still writes one, so the I-5 test
  doesn't exercise it. `infra/tofu/README.md` says the same test proves both, which `infra/tofu/monitoring.tf` contradicts. The exercise stops writes for the whole window,
  outside the weekend quiet window, and recovery means an attempt record seen written, not the alert resolving. Base-camp criterion 2 stays open until it passes.

## Where the architect and Claude differ

One consultation informed this revision (`20261103T165541-ask-dee0`, at `310d7dd`; see OD-0142 correction 1). It changed the alert order, the length of the startup failures,
the definition of a miss, the timing of the failure email and the review recommendation.

- **Agree:** four URLs; a watched run with the rule on; no start-date feature in the go-live PR, with the exception limited to named gaps; a separate dead-man exercise.
- **The architect's weighting of the overlap:** it would not rely on it. This draft keeps it as the first attempt, with the fallback above.
- **Review:** the architect withdrew the argument for skipping review and leaves the choice to the owner. Claude goes further and recommends one Codex review (D-5).

## Decisions the go-live yes would carry

| # | Decision | Claude's recommendation |
|---|---|---|
| D-1 | The four URLs, the bar and the staging statement, at this revision | adopt |
| D-2 | The startup failures. **A:** a bounded exception: only the slots on the step 3 list, until each expires. About 18 hours of red runs and several emails. Any other gap or failure is investigated. **B:** add a start date to the completeness check in the go-live PR | **A.** No new logic at the last step, it ends by itself, and the soak begins after it. Cost: failed runs that day must be read one by one |
| D-3 | Retries up to six requests per file on a bad day, within "two scheduled requests a day" for the RBA | accept; recorded as the owner's judgement on the terms |
| D-4 | `~/.hio-state/` backup at go-live. Revision 1 requires it. OD-0140 correction 1 records only Claude's reading that the owner's words make it optional | your call. Claude recommends not required: it protects no captured data, and state can be rebuilt |
| D-5 | Review of the go-live PR. **A:** CI, full suite and the watched run. **B:** add one Codex review of the PR, including the URLs and this order of steps | **B, changed after the architect's challenge.** The diff reverses tests that deliberately pin the disabled state, earlier reviews didn't see it, and the first writes last 3,650 days. Codex found a real defect in each of the last three tasks. Cost: one review round before go-live |

## Not approved by this document

Everything above. In particular: go-live, `LIVE_AUTHORISATION`, any URL in code, the workflow move, the reviewer rule, `alert_enabled`, any dispatch or capture, and
any C5 amendment. Rights stay as they are: the five owner-verified datasets, for `hio_internal`.

## The owner decision this draft awaits

"Go live under `docs/evidence/S1B1-go-live-package.md` at `<revision>`, with its four URLs, punctuality bar and staging statement, and D-2, D-3 and D-5 as recommended, and the backup not required under D-4?"
A yes authorises the go-live PR, a Codex assignment if D-5 is B, and the steps above, and so starts capture and the soak. It discharges no finality obligation and approves nothing for a consumer.
