<!-- The owner's message in the Claude Code chat, 2026-10-24, verbatim (a pasted block in the
owner's first person, with no other words). With its correction
(2026-10-24-owner-f6-round3-hash-correction.md), the authority for OD-0025. The SHA-256 it gives
for VERIFY-2026-10-24-s1a-1-2 is 62 characters and did not match the record; Claude stopped,
and the owner corrected it. Kept unaltered. -->

I authorise continuation of the bounded F6 remediation on the existing `remediation/s1a-1` branch and PR #2.

For the purposes of harness-0.7 §6.2, I explicitly record the following disposition of the two outstanding verification records:

- `VERIFY-2026-10-24-s1a-1-1`, commit `0255cb2a3966f87a6c41af6020d0fd621a4fc2f1`, remains preserved as immutable evidence, not received into main.
- `VERIFY-2026-10-24-s1a-1-2`, commit `9a94c3a8a68d9627b205c954065a9210db4c6aa3`, with record SHA-256 `3fda0fd34ba5d4cc64a3663910aa3d186daeefad17b4bb1f5db1f774882c53`, is authorised as evidence for this correction, without receiving it into main.

Preserve the existing review records and PR #3. Do not merge or close either PR as part of this task.

**Technical scope**

Reproduce Codex's F6 round-2 failed-rollback visibility counterexample, and independently investigate the concurrent-writer ownership counterexample.

Correct the storage transaction implementation so that:

1. Uncommitted objects are not observable through the supported object-store interface while their transaction remains unresolved.
2. Rollback and recovery never delete an object created by another writer.
3. Failed rollback leaves sufficient durable journal evidence for recovery.
4. The existing single-writer operating assumption is preserved; do not implement general concurrent-writer transaction support.
5. Financial outputs, immutable receipts and previously verified F1, F2, F3 and F5 behaviour remain unchanged.

Add adversarial regression tests covering visibility before and after reopening the store, rollback failures, journal recovery and object ownership.

If object identity cannot establish the required guarantees under the existing storage contract, stop and escalate the exact architectural limitation rather than weakening the tests.

Append the correction to PR #2, preserving its existing commit history. Submit a new fixed head and reproducible evidence for independent Codex verification.

**Collaboration**

Codex may independently verify successive F6 corrections under the existing bounded review assignment. Neither agent may approve S1a, waive findings or change approved standards.

For this F6 correction cycle, treat the two explicitly identified review records as preserved, owner-disposed evidence. Do not require me to repeat these dispositions for each technical iteration within the same authorised scope.

This instruction does not approve harness-0.8, accept S1a, authorise S1b, or resolve Q-001/Q-002.
