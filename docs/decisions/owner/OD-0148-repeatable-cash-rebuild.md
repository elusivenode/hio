---
id: OD-0148
title: "Owner's instruction to proceed, read narrowly as authorising T-0018, the repeatable cash rebuild"
decision: authorise_work
record_status: recorded
created_at: 2026-11-04
updated_at: 2026-11-04
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-04-owner-proceed-approved.md (owner's message, verbatim, with the sentence it followed)
  sha256: 4928ce05553754da549245f4d4891bdee3568a54bc3ab0da0bfa84bf7f4d68b5
  date: 2026-11-04
  quote: "proceed with next steps.  approved"
base_revision: ac36cbf2520cb38880c80baa093b512a513eb981
related: {adrs: [HIO-ADR-0012], tasks: [T-0014, T-0018], findings: [], ods: [OD-0147]}
---

# OD-0148: T-0018

**How Claude read it.** The report put one item as needing a yes: the task for a repeatable build. Claude reads "approved" as that, and told the owner so at the time. It is open to the owner's correction. T-0018 is non-live code, so it is bounded and reversible.

**Not read as:** the owner's Treasury rights reading, which must be the owner's own reading of the live clauses; acceptance of the cash dispositions or any change to a cash spec; adopting the duration spec, base camp, the roadmap or the plan; sending vendor questions; a duration experiment or any download; accepting T-0018.

## Corrections (append-only)

### Correction 1 (2026-11-04): T-0018 accepted without a Codex review; merged; rerun

Claude asked whether the owner accepts T-0018 at `acf1487` without a Codex review, and said "A yes means you merge #81". The owner ran that merge, and it landed as `a881882`. Claude told the owner it was taking that as the yes, and asked to be told if it was wrong; the owner did not object. **So T-0018 is accepted at `acf1487`, with no independent review.**

**Rerun at `a881882`,** under OD-0147: `tools/cash_rebuild.py`, same cutoff and window as `docs/evidence/b3/cash-rebuild-1.md`. All four `data.csv` files are byte-identical to the first rebuild, with the same classes. Release ids differ, because they include `code_ref`. The local copy was deleted.
