---
id: T-0013
title: "Soak monitoring fix before B-3: per-slot completeness in the capture job, a weekend-aware dead-man alert, a soak reconciliation report, and the probe test's hermeticity"
status: accepted   # OD-0134 at 39747c5, merged into main as ae84ac6; the alert stays disabled until B-3
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers); independent reviewer: Codex, if the owner assigns one"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0130
base_revision: b1fc6b4
accepted_by: OD-0134   # at 39747c511a5267e80520ca75f3479102e17d1a1f, merged into main as ae84ac6
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0010 (accepted, OD-0123), T-0011 (accepted, OD-0125)]
  blocks: ["Authorisation B stage B-3 (go-live): alert_enabled = true"]
---

# T-0013: soak monitoring fix

> **Authorised by OD-0130 item 2.** Code and tests only. Applying the changed alert is part of B-3, a separate owner yes.

## Defect

Found by the Fable review (OD-0129 correction 1), confirmed by Claude. The no-attempt-write alert (`infra/tofu/monitoring.tf`)
counts successful writes under `catalogue/attempts/` across **all** publications over 26 hours, has no business-day
logic, and does not auto-resolve. Captures run only on business days (`src/hio/sources/schedule.py`), and a run with no
due slot writes nothing. The alert would therefore fire every weekend (a legitimate gap of about 50 hours). It would also
miss one publisher going silent while the other still writes. A second, minor defect:
`tests/test_t0012_infra.py::test_no_email_guid_or_github_numeric_id_is_committed_in_the_probe` fails when an ignored
`infra/tofu/probe/.terraform/` directory exists.

## Design (architect consultation `20261029T185323-ask-0373`, advice; its two corrections adopted)

Per-publication, calendar-aware detection lives in the capture job. Azure becomes an independent dead-man alarm for
"no attempt writes at all". The soak's full gap record comes from a separate reconciliation report, so that a gap
older than the job's alert horizon is never lost.

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| A-1 | `hio.sources.schedule`: `expected_slots(start, end, calendars)` (every slot instance whose local date is a business day of its calendar and whose due instant is in [start, end)) and `missed_slots(now, calendars, records, horizon=24h)`: expected slots whose window (`due_at + LATENESS`) closed in `(now − horizon, now]` and that have **no** attempt record matching publication, slot and due instant (a `failed` record counts as attempted, never as captured). Capture job: on every **live** run, including runs with no due slot, run the check **after** capture; print each missed slot; exit 1 if any is missed (the I-5 failed-scheduled-run email path). Calendar coverage that does not reach the horizon, or an unreadable/corrupt record, fails visibly (non-zero), never silently. The attempts are listed once per run, not once per slot | tests: one publication missing while the others write; first vs final missing; failed, unchanged, corrupt and mismatched (wrong slot or due instant) records; exact `LATENESS` and horizon boundaries; a slot still inside its window is not missed; no-due runs; both DST transitions (Sydney and New York independently) and UTC/local date crossings; a RITS holiday; NY weekday checks; calendar expiry; dry-run unchanged; the existing exit codes for failed captures and for live refusal unchanged |
| A-2 | `infra/tofu`: the alert becomes a weekend-aware dead-man. Keep the query's raw `WriteCount`; add a quiet window **Sat 00:00 UTC to Mon 18:00 UTC** (NY winter first slot 13:30 UTC + 3 h `LATENESS` + an ingestion allowance) during which the rule does not breach; `auto_mitigation_enabled = true`. Document that a resolution during the quiet window is a suppression, not a recovery, and that the alert proves the absence of writes, not the health of capture. Window variable bounds unchanged (Azure's two-day query limit). `alert_enabled` stays `false` | text-level tests like `tests/test_t0011_*`: quiet-window expression and its edges, raw count kept, auto-mitigation on, still disabled by default; `tofu fmt -check`; `tofu validate` (`-backend=false`) |
| A-3 | `tools/soak_report.py`: for a period [start, end), reconcile expected slots against attempt records: each slot `captured`, `verified_unchanged`, `failed` or `missing`, with the start lateness (record start vs due instant) and completion time; summary counts per publication; JSON to stdout; exit 0 always (it reports, it does not judge). Reads through the `BlobBackend` protocol (injectable; the owner's reader identity at run time, C-5). This is the soak's gap and punctuality record (T-0009 §7) | offline tests with a fake backend: a gap older than 24 h still reported; failed-only slots; a late start within `LATENESS`; an empty period; both DST transitions |
| A-4 | `tests/test_t0012_infra.py`: skip directories (and ignored files) when scanning the probe module | the test passes with a `.terraform/` directory present |

## Exclusions

Any `tofu plan`/`apply` or Azure write; enabling the alert; moving the capture workflow; any change to C1–C7, finality,
attempt-record meanings or HIO-ADR-0012; notification deduplication; a separate GitHub workflow.

## Residuals (stated, not fixed here)

- GitHub may disable schedules in a public repository after 60 days without activity, and may delay or drop runs; the
  dead-man alarm detects the silence outside its quiet window. Checking the schedule's status belongs in the B-3 runbook.
- Which address receives a failed-scheduled-run email depends on who last changed the schedule. I-5 is demonstrated
  only by an actual scheduled failure during the soak.
- A missed slot fails each run for up to 24 hours (several emails); accepted for now.

## Submission (filled by the implementer)

Branch `feat/t0013`, base `b1fc6b4`. hiomux workers W1 (`7bee703`, A-1 and A-3) and W2 (`81768e5`, A-2), each `check`ed and
integrated by cherry-pick; A-4 by the orchestrator (`7dc85f6`).

| Item | Delivered | Evidence |
|---|---|---|
| A-1 | `expected_slots`, `missed_slots`, `load_attempt_records` (`src/hio/sources/schedule.py`); `check_completeness` after every live run, exit 1 on a missed slot or an unreadable check (`src/hio/jobs/s1b1_capture.py`); attempts listed once, records before the horizon skipped by key | `tests/test_t0013_completeness.py` |
| A-2 | dead-man alert: raw `WriteCount`, no row in Sat 00:00 to Mon 18:00 UTC, `auto_mitigation_enabled = true`, still disabled; comments and README say it proves only the absence of writes | `tests/test_t0013_alert.py`; `tofu fmt -check`, `tofu validate` pass |
| A-3 | `tools/soak_report.py`: expected vs observed per slot (`captured`, `verified_unchanged`, `failed`, `missing`), start lateness, per-publication counts, JSON | `tests/test_t0013_soak_report.py` |
| A-4 | the probe secrets test skips directories | passes with `infra/tofu/probe/.terraform/` present |

Full suite **951 passed** (868 at base); `ruff`, `ruff format`, `check_repo`, trailers pass.

**Open, for the soak (worker notes W2-1-bf4c, W2-1-17e2):** that Azure treats the quiet window's zero-row result as not
breaching, and the `dayofweek` conversion, are confirmed only against live Azure (the deliberate-failure test). A Monday
18:00 UTC evaluation breaches only if no Sunday-UTC Sydney write and no Monday write has landed by then, which is the
intended case.

## Review and acceptance

Reviewed by REVIEW-2026-10-29-t0013-1 (NOT READY at `caf44da`; F-1 medium). Remediated at `39747c5`; VERIFY-2026-10-29-t0013-1-1
READY (F-1 verified_closed). **Accepted** by the owner (OD-0134) at `39747c5`, merged as `ae84ac6` (PR #40).
