---
id: OD-0023
title: "Owner authorisation: bounded S1a remediation of findings 1, 2, 3, 5 and 6; draft (not implement) Q-001 and Q-002 amendments"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-authorise-s1a-remediation.md (the owner's chat message, verbatim)
  sha256: 713e285ab8a0c9297eab51e82dd3c2f67ffea444ef15c2f795865f0383c8159a
  date: 2026-10-24
  quote: "I authorise a bounded S1a remediation slice under harness-0.7, addressing findings F-REVIEW-2026-10-24-s1a-1-1, -2, -3, -5 and -6."
applies_to:
  - path: /
    revision: 6fe35cf6f85ec421ec6f8d67acc04134f2bdbd39   # main when the branch was cut; receipt e55cc89 is an ancestor (checked)
related: {adrs: [HIO-ADR-0004, HIO-ADR-0005, HIO-ADR-0006], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-1, F-REVIEW-2026-10-24-s1a-1-2, F-REVIEW-2026-10-24-s1a-1-3, F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-5, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0023: S1a remediation slice

## Owner action

Remediate findings **1, 2, 3, 5 and 6** on a branch from `main`, with the receipt commit
`e55cc89` as an ancestor. The five corrections:
1. lineage-derived sources;
2. class-specific approval;
3. receipt integrity before selection or use;
4. a corrupt-byte-sensitive rebuild check;
5. atomic multi-object commits.

Each finding gets a regression test that reproduces Codex's counterexample before the
correction. Then:
- draft (do not implement or approve) amendments for Q-001 and Q-002;
- submit a remediation response naming all seven findings, with **five remediation claims and two
  unresolved policy questions**;
- open an author PR stating `Submission-Head`, with CI evidence and a completion handoff.

## What this record does NOT do

- It does not change the approved temporal semantics, the observation standard, or findings 4
  and 7 (blocked on Q-001 and Q-002).
- It does not close or verify any finding, merge the implementation, accept S1a or authorise S1b.
- It does not assign the verification. That needs a separate owner assignment at the
  submission head.
