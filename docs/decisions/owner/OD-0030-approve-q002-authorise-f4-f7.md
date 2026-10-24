---
id: OD-0030
title: "Owner approval of OBS-AMEND-Q002 revision 5 (blob d0a25b3b) as the governing Q-002 Option A′ contract; bounded F4/F7 implementation authorised on PR #2; v0.3 consolidation to be prepared"
decision: approve
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-approve-q002-authorise-f4-f7.md (pasted by the owner, verbatim)
  sha256: 09bd166695d8c575461c7fa1a6ec737f776646e05204fcc4c24b536dd74eb80c
  date: 2026-10-24
  quote: "I approve OBS-AMEND-Q002 revision 5 at commit `b4c398df4dcba983bce043b0f92a083082527efa`, blob `d0a25b3b981474bbe57304829aaf5379b04c9e91`, as the governing Q-002 Option A′ contract."
applies_to:
  - path: docs/standards/drafts/OBS-AMEND-Q002-same-time-conflicts.md
    revision: b4c398df4dcba983bce043b0f92a083082527efa   # blob d0a25b3b981474bbe57304829aaf5379b04c9e91 (checked)
  - path: docs/standards/drafts/OBS-AMEND-Q001-quality-event-time.md
    revision: 4e57fa1ae5f6f5133fc82e2420a50ec5ac312afb   # blob 419992f2f0be008dd505a69ed58fb463197ff33c, approved by OD-0029 (rechecked, unchanged at b4c398d)
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0030: approve Q-002 revision 5; authorise F4/F7 implementation

## Owner action

1. **Approved:** OBS-AMEND-Q002 revision 5, as the governing Q-002 Option A′ contract.
   - The approved content is exactly blob `d0a25b3b981474bbe57304829aaf5379b04c9e91` at
     `b4c398d`.
   - The file is not edited, so the blob stays what was approved; this record supersedes its
     `status: proposed`.
   - With Q-001 revision 4 (OD-0029), this settles the F4/F7 architectural choices.
2. **Authorised: bounded F4/F7 implementation on PR #2** (`remediation/s1a-1`), in small commits.
   No new implementation PR. Preconditions, checked before starting:
   - the PR #2 head is `b4c398d`;
   - both contract blobs match.

   The work implements the two-clock quality model and the derived conflict semantics, with the
   approved invariants and acceptance tests. Specifically:
   - historical results at fixed T and Q are preserved;
   - predictive point-in-time admissibility is enforced, with no caller override;
   - conflicts are derived deterministically from verified captured evidence;
   - only append-only owner resolution events are persisted;
   - queries and resolutions are refused when completeness cannot be established;
   - completeness is tested against canonical observation contents and identities, not counts;
   - Codex's F4/F7 counterexamples are mandatory regression tests;
   - financial calculations, F1/F2/F3/F5 and the verified F6 behaviour are preserved.
3. **Standards consolidation.** Prepare observations v0.3, incorporating Q-001 and Q-002 without
   changing their approved substance, for **separate** exact-revision approval. It is not to be
   represented as approved.
4. **Verification.** Codex may verify F4/F7 at a new fixed submission head, including regression
   checks of the other five corrections. Review records are preserved, and PR #3 is not merged.

## What this record does NOT do

- It does not approve observations v0.3, or close or waive any finding.
- It does not merge PR #2 or PR #3, accept S1a, or authorise S1b.
