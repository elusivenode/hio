---
id: OD-0035
title: "Owner approval of OBS-AMEND-Q002-R1 revision 1 (blob cb7a937d); remediation-before-receipt exception for VERIFY-2026-10-24-s1a-1-9; quality-digest implementation authorised on PR #2"
decision: approve
record_status: recorded
created_at: 2026-10-25
updated_at: 2026-10-25
recorded_by: claude/implementation-agent
owner_statement:
  source: docs/history/2026-10-25-owner-approve-q002-r1-authorise-implementation.md (pasted by the owner, verbatim)
  sha256: 43559bd1d1eb67729f2f1b71ef5e0415bdfb1025313ff8eb72927bc0043e78fb
  date: 2026-10-25
  quote: "I approve OBS-AMEND-Q002-R1 revision 1 at commit `312de66f5223df55a4dd2e718ccae487817cc121`, blob `cb7a937dc6e8cc20314e2ae33cd20ce1163fd584`, as an amendment to the approved Q-002 revision 5 contract."
owner_correction:
  source: docs/history/2026-10-25-owner-approve-q002-r1-correction.md (pasted by the owner, verbatim)
  sha256: a48a41fd367e90cdca5b34d169db4aa45570571911eb7021b870603896c3d949
  date: 2026-10-25
  quote: "The correct review commit for `VERIFY-2026-10-24-s1a-1-9` is: `63df7ff269da03fe0c4542141ad388ddd91bd357`"
applies_to:
  - path: docs/standards/drafts/OBS-AMEND-Q002-R1-quality-digest.md
    revision: 312de66f5223df55a4dd2e718ccae487817cc121   # blob cb7a937dc6e8cc20314e2ae33cd20ce1163fd584 (checked)
evidence:
  review_id: VERIFY-2026-10-24-s1a-1-9
  commit: 63df7ff269da03fe0c4542141ad388ddd91bd357   # as corrected; resolves to the commit adding the record
  record: reviews/records/VERIFY-2026-10-24-s1a-1-9.md
  record_blob: 2a1adb1e36ca2695cf7ebff3f60cccaf126f219f
  record_sha256: e3211b1815cee091c93a8e730eb95672b942011d88adabd1866f931f62c8b600
related: {adrs: [HIO-ADR-0004], tasks: [T-0005], findings: [F-REVIEW-2026-10-24-s1a-1-7]}
---

# OD-0035: approve Q-002-R1; exception for VERIFY-…-9; implement the quality digest

## Provenance

- **The original instruction** named the review commit with 39 characters. It did not resolve in
  Git. Claude stopped, recorded nothing, and reported it.
- The owner corrected the commit and confirmed that every other provision stands. Both messages
  are kept verbatim.

## Checks performed (all passed)

| Check | Result |
|---|---|
| Corrected commit | `63df7ff269da03fe0c4542141ad388ddd91bd357` resolves to a commit. Parent: `0e900e8`. Trailer: `codex/reviewer`. It adds only `reviews/records/VERIFY-2026-10-24-s1a-1-9.md` (`id: VERIFY-2026-10-24-s1a-1-9`) |
| Record SHA-256, from Git | `e3211b1815cee091c93a8e730eb95672b942011d88adabd1866f931f62c8b600` (as in OD-0034 and Codex's handoff) |
| Scope and assignment | `check_review_branch.sh`: exit 0. `check_review_assignment.py` (base `6720a6c`, head `0e900e8`, branch `review/s1a-1-verify-9-codex-local`): exit 0 |
| Approved amendment | `git rev-parse 312de66:docs/standards/drafts/OBS-AMEND-Q002-R1-quality-digest.md` = `cb7a937dc6e8cc20314e2ae33cd20ce1163fd584` |

## Owner action

1. **Approved:** OBS-AMEND-Q002-R1 revision 1, at exactly blob `cb7a937d…`, as an amendment to the
   approved Q-002 revision 5 (OD-0030, blob `d0a25b3b`).
   - The previous approved contract and its history are preserved.
   - The file is not edited; this record supersedes its `status: proposed`.
2. **Exception** (harness-0.7 §6.2 step 6) for VERIFY-2026-10-24-s1a-1-9. It is not receipt and
   not S1a acceptance.
3. **Implementation authorised** on PR #2: the four-pin reproducibility contract and AT-Q2R1-1..7.
   Specifically:
   - `quality_digest` per the approved fields, ordering and encoding;
   - the other pins' meanings preserved, with `algorithm_revision` advanced to `hio-obs-select/3`;
   - refusal on any pin that differs from independently reconstructed inputs;
   - the manifest carries the pin plus immutable references that are enough to reproduce the
     quality events and the captured evidence;
   - reproduction in a fresh store, including empty histories, later decisions, and mismatched or
     unavailable inputs;
   - the Q-001 and Q-002 rules preserved;
   - `data.csv` compared byte for byte, with every release-identity change explained.

   No new infrastructure, sources or portfolio functionality.
4. **Observations v0.3 candidate:** updated to incorporate this amendment, still pending its own
   approval.

## What this record does NOT do

- It does not merge PR #2 or PR #3, close any finding, accept S1a, or authorise S1b.
- It does not approve observations v0.3.
