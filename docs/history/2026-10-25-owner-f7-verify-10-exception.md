<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0036. -->

**To Claude — F7 round-10 remediation authorisation**

I authorise a specific harness-0.7 remediation-before-receipt exception for `VERIFY-2026-10-24-s1a-1-10`, followed by the bounded technical correction identified in that record.

Before acting, independently verify:

- The review record at `reviews/records/VERIFY-2026-10-24-s1a-1-10.md`.
- Its commit, resolving from `586b35e`.
- Its SHA-256 against the committed reviewer handoff.
- The reviewer-only scope and assignment.
- PR #2's expected reviewed head, `21e4a07`.

Record the verified provenance and exception in the appropriate owner-decision record. Stop if any evidence or assignment differs.

Then correct loaded quality-event validation so that:

1. `recorded_at > decided_at` is refused.
2. `decided_at` at or before the vintage's capture time is refused.
3. Invalid events cannot enter views, provenance digests, pin verification or releases.
4. Faithful copies with different but valid `recorded_at` values retain identical quality digests.

Add focused regression tests covering reopen and independent reconstruction. Run the relevant F1–F7 regressions, four-pin tests and financial-output comparisons.

Preserve approved Q-001, Q-002 and Q-002-R1 contracts.

Submit a new exact PR #2 implementation head and evidence to Codex for independent verification under the existing bounded assignment.

Do not merge PR #2 or #3, accept S1a, approve observations v0.3 or begin S1b. Escalate only if a contract change or material scope expansion is necessary.
