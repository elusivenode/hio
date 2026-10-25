---
id: HIO-HANDOFF-VERIFY-2026-10-25-adr0012-1
role: codex/independent-reviewer
date: 2026-10-25
verification: VERIFY-2026-10-25-adr0012-1
---

# Handoff: ADR-0012 verification round 1

The immutable [verification record](../records/VERIFY-2026-10-25-adr0012-1.md) examines HIO PR #4 at `860fd7879c6c663980bc4bf037a8c29e8c7df769` against received review `REVIEW-2026-10-25-adr0012`. F1 and F3 are **verified_closed** as proposed design corrections. F2 is **still open**: a forged successful unchanged-attempt record can make an old value satisfy the finality predicate without a post-window request. The record gives the exact counterexample and required correction.

Q-013 and the release-manifest schema consequence remain open owner decisions. No ADR, right, S1b work, waiver or harness amendment is approved by this verification.

## Completion block

- Review branch: `review/adr0012-verify-1-codex`, cut at reviewed head `860fd7879c6c663980bc4bf037a8c29e8c7df769`. The commit adding this handoff is the reviewer evidence commit; its full SHA and the record SHA-256 are in the reviewer's completion report.
- Delivery: push-only under the owner's specific harness-0.7 §6.2 step 3 exception; no reviewer PR. Received into `main`: **not received** at this handoff.
- Next actor: owner to arrange receipt of the exact reviewer evidence, then author for F2 correction.
- Ready prompt: "Confirm the pushed `review/adr0012-verify-1-codex` tip and the record SHA-256 against Codex's report; run the scope and assignment checks against the owner assignment. Stop on mismatch. Receive the record without merging the proposed ADR. Ask the author for a new fixed remediation head addressing F2's forged unchanged-attempt scenario; do not treat receipt as ADR approval or S1b authorisation."
