---
id: OD-0129
title: "Owner instructs an architectural review of where HIO stands against a 'base camp' goal (stable footing before data acquisition, AUD 400 a month data budget): a solution-architect report of current state and roadmap, then a Fable review and analysis; advice only, nothing approved"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-basecamp-review.md (owner's message 3, verbatim)
  sha256: 3b7991c1ce4f912a152a0c6791f2bb2963b18f3f4dbee7ea8f718f28612df76a
  date: 2026-10-29
  quote: "prompt the architect to prepare a report of its understanding of current state and the roadmap forward. --- we will then get a fable review and analysis."
applies_to:
  - path: main
    revision: aa05fd0
related: {adrs: [], tasks: [], findings: [], ods: [OD-0081, OD-0089, OD-0090, OD-0128]}
---

# OD-0129: base-camp architecture review

The owner's goal: a set of factors to assess and construct multi-asset portfolios quantitatively; reach "base camp"
before acquiring data; a data budget of about AUD 400 a month; first, evidence of a stable footing.

## What is authorised

1. **A solution-architect consultation** (`hiomux sa ask`, OD-0089), asking for a report of its understanding of the
   current state and the roadmap: stability evidence, a testable definition of base camp, the sequence to it, data
   acquisition within the budget, risks and owner decisions. Claude summarises it to the owner (OD-0081).
2. **A Fable review and analysis** (a Fable subagent, OD-0090) of the architect's report against the repository. Advice
   only; reported to the owner.

## Not authorised

Any spend or vendor contact; any source permission; adopting a base-camp definition or a roadmap change; any change to
an approved document; B-2 or B-3. Each conclusion becomes an owner decision only when the owner says so.

## Corrections (append-only)

### Correction 1 (2026-10-29): both reviews done

**Architect:** consultation `20261029T182940-ask-9dab` (hiomux run `20261029T082922Z-6392`, `gpt-6.1-sol` `high`, 463 s,
checkout `aa05fd0`; answer sha256 `d82a074e896a4bab40178696c8b38772509f928d5c7e88451d1461d02be866b8`), summarised to the
owner. Verdict: sound foundation, stable operation not demonstrated; six base-camp exit criteria; four proposed yes/no.

**Fable** (OD-0090), read-only, reviewed that report against the repository: confirmed the architect's main verified
claims; found two defects Claude then confirmed:
1. **The soak alert would fire every weekend and public holiday.** `infra/tofu/monitoring.tf` counts attempt writes over
   `missing_write_window_hours` (default 26, `infra/tofu/variables.tf`) with no business-day logic, across all datasets,
   and `auto_mitigation_enabled = false`. The alert is created disabled (OD-0126), so nothing fires today; it must be
   fixed before B-3 sets `alert_enabled = true`. Not found by the T-0011 review or verifications.
2. **`tests/test_t0012_infra.py::test_no_email_guid_or_github_numeric_id_is_committed_in_the_probe` fails locally** when
   an ignored `infra/tofu/probe/.terraform/` directory exists (`IsADirectoryError`); CI passes. Hermeticity only.

Both reviews are advice. Nothing is adopted, fixed or approved by this correction.
