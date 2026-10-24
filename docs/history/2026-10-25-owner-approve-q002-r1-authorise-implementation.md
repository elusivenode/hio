<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). With its correction (2026-10-25-owner-approve-q002-r1-correction.md), the authority for
OD-0035. The review commit it names has 39 characters and does not resolve in Git; Claude
stopped, and the owner corrected it. Kept unaltered. -->

**To Claude — HIO S1a quality-digest approval and F7 continuation**

I approve OBS-AMEND-Q002-R1 revision 1 at commit `312de66f5223df55a4dd2e718ccae487817cc121`, blob `cb7a937dc6e8cc20314e2ae33cd20ce1163fd584`, as an amendment to the approved Q-002 revision 5 contract.

Record the owner decision with the exact approved revision and provenance. Preserve the previous approved contract and its history.

For `VERIFY-2026-10-24-s1a-1-9`, I authorise the harness-0.7 remediation-before-receipt exception, subject to verifying:
- Review commit `63df7ff269da03fe0c4542141ad388dd91bd357`.
- The review record's complete SHA-256 directly from Git.
- Reviewer-only scope and assignment.

Record the verified hash and this exception. Stop if any check fails. This is not review receipt or S1a acceptance.

**I authorise bounded implementation of the approved quality-digest amendment on existing PR #2.**

Implement the four-pin reproducibility contract and the amendment's acceptance tests AT-Q2R1-1 through AT-Q2R1-7.

In particular:

1. Derive `quality_digest` from the canonical quality-event history effective at Q, using the approved fields, ordering and encoding.
2. Preserve the meanings of `evidence_digest`, `resolution_digest` and `algorithm_revision`, advancing its value to `hio-obs-select/3`.
3. Enforce refusal when any recorded provenance pin differs from independently reconstructed inputs.
4. Ensure the release manifest contains the new pin and sufficient immutable references to reproduce the actual quality events and captured evidence.
5. Verify reproduction in a fresh, isolated store, including no-event histories, later decisions, and mismatched or unavailable inputs.
6. Preserve all approved Q-001/Q-002 selection, conflict, completeness and predictive-admissibility rules.
7. Compare all four financial `data.csv` outputs byte-for-byte against the previous independently verified implementation, explaining every release-identity change.

Use small, testable commits. Add no new infrastructure, ingestion sources or portfolio-management functionality.

Submit a new fixed `Submission-Head`, a remediation response and reproducible evidence for Codex's independent F7 verification. Codex may continue technical verification within the existing bounded assignment, with its review evidence preserved separately.

Update the observations v0.3 candidate to incorporate the newly approved amendment, but keep the consolidated standard pending its own exact-revision approval.

Do not merge PR #2 or PR #3, close findings on Claude's authority, accept S1a or authorise S1b.

Escalate only a material contradiction with the approved contracts or an issue requiring new architectural authority.
