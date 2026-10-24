<!-- Pasted into the Claude Code chat by the owner, 2026-10-24, verbatim, with no other words (first
person). Recorded by OD-0033. -->

**To Claude — HIO S1a F7 remediation**

Codex reports REQUEST CHANGES at PR #2 head `6720a6cbeac5aa45e51fa8bcd2433f8b9bbe2968`.

The reviewer evidence is:
- Record: `VERIFY-2026-10-24-s1a-1-8`
- Commit: `db1722c35fe2136461b6b936a8d6d9d0044e656b`
- Record SHA-256: `6776d92b47225f5e408824a084ec1162a752bd64c1829e76fe4ee1532ae673d4`

Under harness-0.7, I authorise bounded remediation before receipt of this specific verification record, subject to independent verification of its commit, hash, reviewer-only scope and assignment. Record the exception. Stop if any check fails.

**Correct F7's quarantine-related completeness failures within the existing approved Q-002 contract.**

First reproduce both Codex counterexamples. Then assess the completeness verification mechanism as a whole, especially its trust boundaries.

Required outcomes:

1. Every captured receipt must have independently verifiable raw bytes before it contributes to a completeness determination, including quarantined receipts.
2. A quarantine marker must not independently establish that processing is complete. Verify that the captured evidence genuinely warrants quarantine under the applicable ingest rules.
3. Missing or corrupted receipt data, forged processing outcomes and forged quarantine markers must cause refusal rather than silently producing a result.
4. Preserve valid quarantine behaviour, including malformed-receipt handling.
5. Ensure fixed-(T,Q) results and evidence pins cannot silently change as processing state changes.

Add adversarial tests for both counterexamples and related bypasses. Test behaviour after reopening the store.

Preserve F1–F6 verified behaviour, the approved Q-001/Q-002 contract blobs, the financial calculations and existing release data.

Append the correction to PR #2, with a new fixed Submission-Head and independently reproducible evidence for Codex.

Codex may reverify the correction within its existing bounded assignment. Do not merge PR #2 or PR #3, approve v0.3, close findings yourself, accept S1a or start S1b.

If the completeness mechanism cannot satisfy the contract without a structural change, stop and present the smallest design decision needed rather than continuing to patch isolated cases.

**Collaboration:** Exchange review records and reproducible counterexamples directly through the shared Git repository. Every review must leave the next collaborator with an actionable technical handoff and explicitly identify any mandatory owner prerequisite.
