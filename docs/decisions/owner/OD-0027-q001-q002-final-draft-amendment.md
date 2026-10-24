---
id: OD-0027
title: "Owner instruction: final narrow amendment of the Q-001 and Q-002 drafts (revision 3) for the owner's standards decision"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-q001-q002-final-amendment.md (pasted by the owner, verbatim)
  sha256: ffcf56d60074bf0c9024fb3bceccdf6c0f19f6574bf8610dd70cdcb0f6e0e3bc
  date: 2026-10-24
  quote: "I support refined Option A for both, but this is not yet approval of the observation standard or authorisation to implement F4/F7."
applies_to:
  - path: docs/standards/drafts/
    revision: baa8e4e60a0465a59fa10e64388a856ea89364fa   # revision 2, reviewed by the owner
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0027: final narrow amendment of the Q-001 and Q-002 drafts

## Owner action

- **Support** for refined Option A for both drafts. This is **not** approval of the observation
  standard, and **not** authorisation to implement F4 or F7.
- **Drafting authorised.** A narrow revision 3, limited to these two amendments:
  - **Q-001:**
    - keep the two-cutoff model (T and Q);
    - results with Q > T stay labelled, and are **not admissible to predictive point-in-time
      research by default**;
    - historical market knowability and later HIO validation stay distinguishable;
    - any exception needs a separate, evidence-based admissibility rule.
  - **Q-002:**
    - deterministic conflict identity from canonical observation evidence, independent of
      ingestion order;
    - append-only conflict and resolution events;
    - owner-only adjudication in S1a;
    - historical knowledge-state stability;
    - no unresolved contradiction silently hidden from diagnostics by mode-specific selection.
  - The executable invariants and acceptance tests are clarified accordingly.
- **Next:** the drafts are submitted at a fixed SHA for the owner's final standards decision. The
  owner intends to authorise F4/F7 implementation and verification on PR #2 after approving an
  exact version.

## What this record does NOT do

- It does not change implementation code, an approved standard, or Codex's review evidence.
- It does not merge PR #2 or PR #3, accept S1a, or start S1b.
