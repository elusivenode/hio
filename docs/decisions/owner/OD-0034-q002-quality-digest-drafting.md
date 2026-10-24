---
id: OD-0034
title: "Owner selection of a separate quality_digest pin (direction) and authorisation to draft the Q-002 reproducibility amendment; VERIFY-2026-10-24-s1a-1-9 verified"
decision: authorise_work
record_status: recorded
created_at: 2026-10-24
updated_at: 2026-10-24
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-24-owner-q002-quality-digest-drafting.md (pasted by the owner, verbatim)
  sha256: 54670793ee140350b342e3e082c24225337d213728bb516895478aecbca45f2d
  date: 2026-10-24
  quote: "I select a separate `quality_digest` as the preferred architectural resolution, subject to confirming the exact counterexample and approved contract."
applies_to:
  - path: docs/standards/drafts/
    revision: 0e900e88acc0113fc42c4215b1379af9b7ea2f0e   # PR #2 head reviewed by VERIFY-2026-10-24-s1a-1-9
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-9
  commit: 63df7ff269da03fe0c4542141ad388ddd91bd357
  record: reviews/records/VERIFY-2026-10-24-s1a-1-9.md
  record_blob: 2a1adb1e36ca2695cf7ebff3f60cccaf126f219f
  record_sha256: e3211b1815cee091c93a8e730eb95672b942011d88adabd1866f931f62c8b600
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0034: quality_digest direction; draft the amendment

## Checks performed before drafting (all passed)

| Check | Result |
|---|---|
| Reviewer commit | `63df7ff269da03fe0c4542141ad388ddd91bd357` (located on `origin/review/s1a-1-verify-9-codex-local`). Parent: `0e900e8` (the PR #2 head). Trailer: `HIO-Actor: codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-9.md` |
| Record SHA-256 (independent) | `e3211b1815cee091c93a8e730eb95672b942011d88adabd1866f931f62c8b600`, equal to Codex's handoff (`reviews/handoffs/2026-10-24-s1a-f7-verify-9.md` at `9f7d605`, line 8) |
| Reviewer-only scope | `sh tools/check_review_branch.sh 0e900e8… review/s1a-1-verify-9-codex-local`: exit 0. 2 commits, both `reviews/` only |
| Assigned review identity | `check_review_assignment.py` with id `VERIFY-2026-10-24-s1a-1-9`, base `6720a6c`, head `0e900e8`, branch `review/s1a-1-verify-9-codex-local`, and the record's assignment source: exit 0 |
| The counterexample (reproduced independently, in scratch stores) | Two valid stores with an identical receipt; store B has an owner `QUARANTINED` decision (`decided_at` 2026-01-14). `as_captured_by_hio(T = 2026-01-15)` returns `{2026-01-12: 3.60}` in A and `{}` in B, with identical `evidence_digest`, `resolution_digest` and `algorithm_revision` |

## Owner action

1. **Direction selected:** a separate `quality_digest` pin (Codex's option A), subject to the
   counterexample and the approved contract. Both confirmed above.
2. **Drafting authorised:** a narrow amendment to the Q-002 reproducibility contract. It must
   specify:
   - the events and fields;
   - the ordering and encoding;
   - the empty-history representation;
   - the exclusion of events after Q;
   - the provenance role in results and releases;
   - the acceptance tests.

   The existing meanings of `evidence_digest`, `resolution_digest` and `algorithm_revision` are
   preserved.
3. **Implementation** continues on PR #2 only after:
   - the amendment is approved at an exact revision;
   - the review-evidence prerequisite for VERIFY-2026-10-24-s1a-1-9 is satisfied (its receipt, or
     a specific remediation-before-receipt exception).

## What this record does NOT do

- It does not approve the amendment or change implementation code, an approved standard or a
  Codex record.
- It does not dispose of VERIFY-2026-10-24-s1a-1-9, merge any PR, accept S1a, or authorise S1b.
