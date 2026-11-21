---
id: OD-0190
title: "Owner adopts E-0004's preregistration at 067bd7b with the 0.20-point threshold; step 1 tooling and run authorised; 1b reported first; step 2 not authorised"
decision: approve
record_status: recorded
created_at: 2026-11-22
updated_at: 2026-11-22
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-11-22-owner-adopt-e0004.md (owner's message, verbatim, with Claude's question)
  sha256: c7a6892982d0e2d0ebdf8512eeea2eba67c6e2cabf30fcee9f9ba9ef0ccdb6fb
  date: 2026-11-22
  quote: "Y"
applies_to:
  - path: docs/evidence/e0004/preregistration-1.md
    revision: "067bd7b19763046f71a7627bae010b4f1ec769bc, blob a71339d323fccdc5f6a227447a4d69cdcc8b80c3"
base_revision: 067bd7b19763046f71a7627bae010b4f1ec769bc
related: {adrs: [], tasks: [T-0023], findings: [], ods: [OD-0181, OD-0187, OD-0188, OD-0189]}
---

# OD-0190: E-0004 preregistration adopted

**Approved:** the preregistration at `067bd7b` (blob above), with the **0.20-point** relevance threshold confirmed. Any change after this is an amendment, recorded in the file and an OD, before the result it could affect.

**Authorised:**
1. Workers build the step 1 and step 1b tools, tested on invented data.
2. Claude runs **step 1** (the information count: months, runs, stress clusters, concentration; no outcome) on the pinned inputs.
3. **Step 1b** (the precision check) runs only after step 1's counts are reported to the owner.

## Not authorised

Step 2 (the estimate), which needs its own yes and IEF's NAV corroboration; any further download.

## Corrections (append-only)

### Correction 1 (2026-11-22): step 1 ran

The screen passes in both states (`docs/evidence/e0004/step1-1.md`). Counts reported to the owner; step 1b may now run under item 3.

### Correction 2 (2026-11-22): step 1b ran

The precision check passes: median half-width 0.167 points against 0.20 (`docs/evidence/e0004/step1b-1.md`). Step 2 still needs its own yes and IEF's NAV corroboration.
