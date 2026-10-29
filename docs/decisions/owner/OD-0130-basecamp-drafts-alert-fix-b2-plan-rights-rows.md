---
id: OD-0130
title: "Owner authorises four bounded items from the base-camp review: drafting a proposed base-camp definition; a task to fix the soak alert and the probe test's hermeticity (code and tests on a branch, no apply); drafting the B-2 probe plan at efb6fa1 (no apply or dispatch); drafting rights rows for FRED/ALFRED, US Treasury, FRB H.10 and RBA historical tables (verification stays the owner's)"
decision: authorise_work
record_status: recorded
created_at: 2026-10-29
updated_at: 2026-10-29
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-29-owner-basecamp-decisions.md (owner's message 4, verbatim, with Claude's decisions put)
  sha256: 8fd2b6833b3e5fd0dbdfc7128a970990a62e20066c3f0a16db931e9a43ce6f44
  date: 2026-10-29
  quote: "yes to 1 - 4.  I want to proceed iteratively and will concerted effort"
applies_to:
  - path: main
    revision: 01120e9
related: {adrs: [HIO-ADR-0012], tasks: [T-0011, T-0012], findings: [], ods: [OD-0119, OD-0126, OD-0128, OD-0129]}
---

# OD-0130: base-camp work, items 1 to 4

The owner wants to proceed iteratively, with concerted effort. Claude reads that as: deliver the four items one at a
time, each small and reviewable, critical path first (2, then 3, then 1 and 4).

## What is authorised

1. **Base-camp definition, drafted as `proposed`:** the architect's six criteria (OD-0129), with criterion 4 reduced
   to finality evaluated and recorded alongside releases, plus Fable's three additions (one duration factor on free
   data, rights decisions for free history sources, a data-need statement per factor family). Approves nothing.
2. **Alert and test fix:** a task card (T-0013), code and tests on a branch for the soak alert (weekend, holiday and
   per-source blindness) and the probe test that fails on an ignored `.terraform/` directory; a Codex review only if
   the owner assigns one. No `tofu plan` or `apply`, no Azure write.
3. **B-2 probe plan:** drafted against accepted T-0012 at `efb6fa1`: operations, retained evidence, how results are read,
   cleanup. No apply, no dispatch.
4. **Rights rows, drafted:** FRED/ALFRED, US Treasury, FRB H.10 and the RBA historical tables, for historical research
   use, `hio_internal` only. Research from public terms pages and drafting only; verifying any right stays the owner's.

## Not decided

Item 5 (freeze harness and hiomux development) and item 6 (budget cap) were not answered; they stay open.

## Not authorised

Any `tofu plan`/`apply`, Azure write or workflow dispatch; B-2 or B-3; marking any right verified; any purchase or
vendor contact; adopting the base-camp definition; any roadmap or G2 ordering change.

## Corrections (append-only)
