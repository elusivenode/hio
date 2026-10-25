---
id: OD-0064
title: "Owner direction: the RBA F1 file may be retained as published for the AONIA and TRI design; recorded as a design direction, not as source-rights verification"
decision: authorise_work
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-f1-file-direction.md (typed by the owner, verbatim)
  sha256: b1dda4d83e9bf956301f0625120609c2e8e6b31559800fcf438bfcf26d64c0fd
  date: 2026-10-25
  quote: "F1 file ... fine to use"
applies_to:
  - path: docs/evidence/S1B1-readiness-package.md
    revision: d6a117008089738b0923b97d8acf721600c6ec41   # section 6.1, the F1 finding
related: {adrs: [HIO-ADR-0012], tasks: [T-0009, T-0002], findings: []}
---

# OD-0064: the F1 file

## Owner action

In reply to the F1 finding (the file that carries AONIA and the TRI also carries ASX and FENICS
columns), the owner wrote "F1 file ... fine to use". The answer is read as option (1): the S1b-1.0
design may assume that the F1 file is retained **unaltered**, as the exact bytes published, with no
column-filtered copy.

## What this is, and is not

- **A design direction** for T-0009 (receipts keep the exact bytes). It authorises no live operation.
- **Not a rights verification.** The wording is informal and records no reading of the RBA copyright
  page, no reasoning on section 7.2, and no operation list. Per the owner's standing direction,
  permissions stay `unverified` until the exact evidence is reviewed and explicitly approved. The
  gate therefore still refuses `rba.cash_rate`, `rba.cash_rate_tri` and `rba.expert_judgement`.
- The F1 finding is **closed as a design question and stays open as a rights question**: when the
  owner records the D1 and D3 verification (readiness package section 6.1), that record should state
  the reasoning for the third-party columns. Claude will draft it for the owner's reading, and will not
  mark anything verified.

## Corrections (append-only)

None.
