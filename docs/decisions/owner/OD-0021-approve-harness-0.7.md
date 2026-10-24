---
id: OD-0021
title: "Owner approval of harness-0.7 revision 3 at 9b58811, with an adoption condition; integration into main authorised"
decision: approve
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/documentation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-approve-harness-0.7.md (the owner's chat message, verbatim)
  sha256: 443842c9515b0059f6188fb3c6f3a2410d1205d607bdf06ed8c87bc013838312
  date: 2026-10-24
  quote: "I approve HIO harness-0.7 revision 3 at commit `9b58811b75cfaa600e76ab3c50390a39d5828968`, including the proposed changes to `AGENTS.md`, the operating model, review procedures, templates, scripts and CI workflow."
applies_to:
  - path: /
    revision: 9b58811b75cfaa600e76ab3c50390a39d5828968   # the tip of proposal/harness-0.7, confirmed locally and on origin before integration
related: {adrs: [HIO-ADR-0008], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-1, F-REVIEW-2026-10-24-s1a-1-2, F-REVIEW-2026-10-24-s1a-1-3, F-REVIEW-2026-10-24-s1a-1-4, F-REVIEW-2026-10-24-s1a-1-5, F-REVIEW-2026-10-24-s1a-1-6, F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0021: approve harness-0.7 (revision 3)

## Owner action

1. **Approved:** harness-0.7 revision 3, as it stands at `9b58811b75cfaa600e76ab3c50390a39d5828968`.
   That includes the changes to `AGENTS.md`, the operating model, the review procedures, the
   templates, the scripts and the CI workflow. The approved content is exactly these blobs at
   that commit (`git rev-parse 9b58811:<path>`):

   | Blob | Path |
   |---|---|
   | `af908c548b7993510d5e935f5b6fe0c445305903` | `.github/pull_request_template.md` |
   | `bb19c82edf7e8e8224b8fffe51aeeb92906ac83b` | `.github/workflows/review-scope.yml` |
   | `a2dc93d335105cf6175b145f68d8c6b588627f82` | `AGENTS.md` |
   | `ac1dba4bbc47cf71f016fb71d8ad4e730da73094` | `docs/decisions/harness-0.7-proposal.md` |
   | `c2af58b1eb984063b3226b3006ae955403e7d2a5` | `docs/decisions/open-decisions.md` |
   | `90e2565fe814b371a536f5091a878ac31d2dbe61` | `docs/harness/operating-model.md` |
   | `14de0cb41be80fef10bc67970daf56e3f4bcd175` | `reviews/README.md` |
   | `a85fbde52d991d35922f31d4a1c420ab40b29e57` | `templates/handoff.md` |
   | `963fea27670da2d92ac2f4871885e39dc8b3be01` | `tests/test_review_gate.py` |
   | `c94afb7d94b624850c2064ae7d493451ae6e9b79` | `tools/check_repo.py` |
   | `1089df9d24360a39eac247fae4c3dc44ec9cd7b4` | `tools/check_review_assignment.py` |
   | `89c2f4e6ee0503fc543f35e937ae97ccfb134dd7` | `tools/review_gate.py` |

2. **Integration authorised:** merge `proposal/harness-0.7` into `main` with `--no-ff`, after
   confirming the tip is still `9b58811`. Then make status and version edits that record this
   approval and keep the earlier approved revision and its provenance. **No substantive policy
   change during integration.**
3. **Adoption condition:** the first reviewer PR under harness-0.7 must validate the GitHub
   `pull_request_target` workflow, including a deliberate failing case. **Until that evidence is
   recorded, a green reviewer-PR scope check is not an established automated enforcement
   control.** The local scope check (§6.2 step 4) and the assignment check (step 4a) continue to
   be performed.

## Supersession

harness-0.7 supersedes harness-0.6 (OD-0012, `f2275e2`, blob `e3114bd188ad`) as the operating
model's approved content. OD-0012 and harness-0.6 remain the record of what was approved before.

## What this record does NOT do

- It does not accept S1a, close or waive any of the seven findings of REVIEW-2026-10-24-s1a-1
  (retained), or approve any standards interpretation (Q-001…Q-008 stay open).
- It does not authorise S1b.
- It does not treat the CI scope gate as an established control (see the adoption condition).
