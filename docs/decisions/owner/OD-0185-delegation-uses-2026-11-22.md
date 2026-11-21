---
id: OD-0185
title: "Uses of the standing delegation, 2026-11-22: #107 merged (A1), the T-0023 review launched (A2), 2027 RITS and NSW calendars added (A7)"
decision: authorise_work
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/decisions/owner/OD-0184-standing-delegation.md (the standing delegation; approved, correction 1)
  sha256: 01cbc499e435698e24e7ac59996c680a81aaa2aef1508c674b7a6c4969e8d52e   # docs/history/2026-11-22-owner-approve-od-0184.md
  date: 2026-11-22
  quote: "y"
base_revision: 963275838d903a07033d887af2d4387f25e5631a
related: {adrs: [], tasks: [T-0023, T-0009], findings: [], ods: [OD-0076, OD-0182, OD-0184]}
---

# OD-0185: delegation uses, 22 November

A log of actions taken under OD-0184 without a per-item yes. It authorises nothing beyond OD-0184.

| Power | Action | Evidence |
|---|---|---|
| A1 | merged PR #107 (records: OD-0184 approval, OD-0182 assignment) at `b8d667a`, as `9632758` | checks green; no excluded path |
| A2 | launched `REVIEW-2026-11-22-t0023-1` as hiomux task C11 (`gpt-6-sol` `high`, public reads only, no licensed data), assignment OD-0182 | `reviews/README.md` *Assigned reviews* row |
| A7 | added `src/hio/reference/calendars/rits-2027.yaml` and `nsw-2027.yaml` from one manual read each of the RBA's RITS Business Hours and 2027 holidays pages (2026-11-21 22:03 UTC; page hashes in the files) | `tests/test_calendars_2027.py`: 2027 closures, RITS within NSW, and the committed files merged across the year boundary; three deliberate file mutations each caught; `tools/soak_report.py` over 2026-12-30..2027-01-06 refuses with the 2026 file alone (`CalendarCoverageError` at 2027-01-01) and reports with both; full suite 1,681 passed |

**Readings to note (Claude's, as in 2026):** the RITS rule text is unchanged. Monday 26 April (the Anzac Additional Day) is listed for NSW but not Victoria, so RITS is read as open. The Additional Days on 27 and 28 December are listed for all states and are read as Christmas and Boxing Day observed, so RITS is closed. The capture workflow already passes every `rits-*.yaml`, so no workflow changed.

## Not authorised

Any change to the capture path beyond the calendar files; accepting anything.

## Corrections (append-only)
