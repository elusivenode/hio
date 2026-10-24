<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0037. -->

**To Claude — HIO S1a controlled integration and evidence receipt**

I approve the integration-first route under the existing harness-0.7 procedure.

Authorise a controlled `--no-ff` merge of HIO PR #2 into `main` at the exact independently reviewed head `084154c`, followed by receipt of the independently verified Codex review branches. This authorises integration and evidence receipt only, **not S1a acceptance**.

Before merging:

1. Resolve complete Git identifiers directly from the repository.
2. Confirm PR #2 remains at the tested head and that its required CI and review evidence still match.
3. Verify all reviewer branches, record commits, hashes, scope checks and assignment checks.
4. Perform an isolated integration rehearsal, including the planned reviewer-branch merges, confirming preservation of reviewer commit identities and no unintended implementation changes.
5. Confirm no new material blocker or unresolved merge conflict exists.

Stop and report if any prerequisite fails or the integration would alter unreviewed implementation content.

If all checks pass:

1. Merge PR #2 into `main` using `--no-ff`; preserve the exact tested implementation.
2. Receive the relevant Codex verification branches under harness-0.7, using `--no-ff` and retaining original reviewer commit identities. Handle PR #3 according to its verified evidence status; do not merge it blindly.
3. Record the resulting integration and receipt commits.
4. Update `reviews/README.md` to reflect independently verified closure of F1–F7 at their respective reviewed revisions.
5. Update `STATUS.md` and the owner-decision trail, accurately distinguishing technical verification, integration, receipt and acceptance.
6. Compile the S1-A1 to S1-A15 requirement-to-evidence matrix.
7. Prepare concise recommendations for Q-007, Q-008, Q-005a and the capture-clock archive question, explicitly identifying which genuinely block S1a acceptance.
8. Identify the exact observations v0.3 revision awaiting separate approval and prepare the instructions for the owner's §10 fresh-session test.

Do not declare S1a accepted, approve observations v0.3, authorise S1b or make unrelated architecture changes.

Return an acceptance-readiness package listing only the remaining owner decisions and unmet acceptance tests.
