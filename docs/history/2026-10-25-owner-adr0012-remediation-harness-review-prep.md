<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0051. -->

**To Claude — ADR-0012 correction and harness-0.7.1 independent-review preparation**

Proceed with two bounded workstreams.

**A. ADR-0012 remediation**

Address the three findings in the received `REVIEW-2026-10-25-adr0012` record on PR #4.

- F1: distinguish evidenced per-vintage publication timestamps from approximate schedules; otherwise use a conservative capture-time basis. Escalate any necessary change to approved observation semantics.
- F2: define finality using verified successful post-window capture evidence, including unchanged content. An attempt alone cannot establish finality; failed or missing checks must fail closed.
- F3: distinguish SOFR Index calculation corrections from SOFR-rate revisions and require independent Index checks.

Preserve accepted S1a, approved return and observation standards, and all unverified source-rights states.

Submit a new exact PR #4 head with a concise remediation response. Do not approve ADR-0012.

**B. Harness-0.7.1 independent review**

Push the existing proposed harness-0.7.1 revision 2 at local commit `9878dd0`, after verifying its full identity and scope.

Prepare a fixed-head assignment for Codex to challenge:

1. Original reviewer provenance and byte-identical import integrity.
2. Assignment and reviewer-only scope enforcement.
3. Unapproved implementation ancestry never entering `main`.
4. Author-as-receiver risks, especially suppression or alteration of adverse evidence.
5. Adversarial cases: deleted records, forged hashes, modified index entries, moving branch heads and conflicting assignments.
6. Stop-on-mismatch and recovery behaviour.
7. The extent to which earlier harness-0.8 concerns have actually been resolved.

For this review, I recommend the owner explicitly authorise a **push-only, no-reviewer-PR pilot exception** to harness-0.7. Codex's review branch remains independent and must be scope- and assignment-checked before receipt.

No harness amendment is approved by this instruction alone.

Return the pushed proposal head and the two exact-review assignment packages for owner confirmation. Do not implement S1b, merge PR #4, approve ADR-0012, mark source rights verified or change the current approved harness.
