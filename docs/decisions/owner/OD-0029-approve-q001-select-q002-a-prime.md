---
id: OD-0029
title: "Owner approval of OBS-AMEND-Q001 revision 4 (blob 419992f2) as the governing two-cutoff contract; Q-002 Option A′ selected as direction (not yet approved)"
decision: approve
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-approve-q001-select-q002-a-prime.md (pasted by the owner, verbatim)
  sha256: 894f4a79faddafa71ca6293be62a27131a99c4dd333aae833591cf6a982dc8fb
  date: 2026-10-24
  quote: "I approve Q-001 revision 4, blob `419992f2f0be008dd505a69ed58fb463197ff33c`, as the governing two-cutoff quality and predictive-admissibility contract."
applies_to:
  - path: docs/standards/drafts/OBS-AMEND-Q001-quality-event-time.md
    revision: 4e57fa1ae5f6f5133fc82e2420a50ec5ac312afb   # blob 419992f2f0be008dd505a69ed58fb463197ff33c (checked)
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0029: approve Q-001 revision 4; select Q-002 Option A′

## Owner action

1. **Approved:** OBS-AMEND-Q001 revision 4, as the governing two-cutoff quality and
   predictive-admissibility contract.
   - The approved content is exactly blob `419992f2f0be008dd505a69ed58fb463197ff33c`
     (`git rev-parse 4e57fa1:docs/standards/drafts/OBS-AMEND-Q001-quality-event-time.md`).
   - The file is not edited by this record, so the blob stays what was approved.
   - Its `status: proposed` front matter is superseded by this record.
   - The historical approved standard, observations v0.2, is preserved (OD-0008; blob
     `341cd608604d` in this repository).
   - The amendment is to be incorporated through the existing versioning process: a new standard
     version, approved at an exact revision (operating model §6).
2. **Q-002: Option A′ selected as the architectural direction.**
   - Conflicts are derived from immutable captured evidence at the cutoff.
   - Only append-only owner resolution events are persisted. There are no conflict-detection
     records and no processing artefacts.
3. **Retained for Q-002:**
   - deterministic evidence-derived conflict identity;
   - complete diagnostics;
   - no ingestion-order tie-break;
   - historical stability;
   - refusal of unresolved conflicts;
   - resolution events that identify their exact conflict and take effect under the decision-time
     rules.
4. **Reproducibility and completeness.** Every derived conflict result must be reproducible from
   pinned evidence and a pinned algorithm revision. Results are refused when processing
   completeness cannot be established.
5. **Next work:** the narrow final Q-002 amendment implementing A′, submitted at an exact SHA and
   blob for approval.

## Reading

- **Incorporating Q-001 into the standard.** The approved Q-001 text depends on Q-002 in one
  clause ("not suppressed by an unresolved conflict at Q (OBS-AMEND-Q002)"), and Q-002 is not yet
  approved.
  - A standard version that included Q-001 alone would have to drop or condition that clause,
    which would change approved text.
  - So the consolidated new version (observations v0.3) is prepared once Q-002 is approved, and
    submitted for approval at its own exact revision.
  - Until then, the approved amendment blob governs, alongside v0.2.
  - If the owner prefers a Q-001-only v0.3 now, with the Q-002 clause marked as taking effect on
    Q-002's approval, that is a one-line instruction.
- Implementation of F4 and F7 is **not** authorised by this record.

## What this record does NOT do

- It does not approve Q-002, or edit the approved v0.2 standard file.
- It does not authorise F4 or F7 implementation.
- It does not merge any PR, change any review record, close any finding, accept S1a, or start
  S1b.
