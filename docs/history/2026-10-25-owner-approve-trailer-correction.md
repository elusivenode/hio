<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0059. -->

**To Claude — approve bounded harness trailer correction**

I approve the narrowly scoped correction proposed in `docs/decisions/harness-0.7.1-trailer-correction-proposal.md`, subject to exact-revision and diff verification.

1. Require the applicable `HIO-Actor` trailer on each new receipt import commit.
2. Run the existing `tools/check_repo.py trailers` check against the new import commit before the final merge and push.
3. Add CI status as a mandatory reported result after receipt, distinguishing evidence-integrity checks from CI integration checks.
4. Preserve the original failed CI run at `347da95` and the successful later run at `09c86f7`. Do not rewrite any published history.
5. Verify the correction with one bounded scratch-clone regression demonstrating rejection of a missing trailer and acceptance of the correct trailer.
6. Record the exact approved amendment and test evidence in an owner decision, and integrate the documentation-only correction.
7. Report the resulting `main` revision and CI outcome.

Do not reopen the entire harness review or alter unrelated operating procedures.

**First-use adoption:** Once the corrected procedure and bounded test pass, prepare a concise recommendation on lifting the suspension of routine delegated receipt. Do not enable it automatically.

Do not receive B2, approve source rights, modify accepted S1a or authorise S1b. Stop if this requires changes outside the identified trailer and reporting rules.
