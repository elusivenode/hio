---
id: OD-0179
title: "Owner allows their email as the declared SEC contact, for one read of the fund reports covering 2008; C5 to run"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-sec-contact.md (owner's message, verbatim)
  sha256: 9fc312a6ba4a73c6dfdd21af9d79434af7282e65b314f4280724d9b033408342
  date: 2026-11-04
  quote: "yes"
base_revision: 58ee33d04
related: {adrs: [], tasks: [T-0023], findings: [], ods: [OD-0178]}
---

# OD-0179: the SEC contact and C5

As put to the owner: one read-only fetch of the fund reports covering 2008 for SPY, BIL and IEF, with the owner's email in the request header; C5 runs, and its results go into the record. The address goes only in that header, and isn't committed.

IEF's NAV file stays the owner's to download by browser.

## Not authorised

Any other use of the address; any other SEC read; steps 6 and 7; a Codex assignment, a merge, or accepting any result.

## Corrections (append-only)
