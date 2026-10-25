<!-- Typed and pasted into the Claude Code chat by the owner, 2026-10-25, verbatim. The first line is
the owner's own words; the rest was pasted with them. Recorded by OD-0049. -->

## The owner's words

Codex (the reviewer) keeps creating PRs and I don't want this workflow ... how can we fix it?
---

## Pasted with them

**To Claude — simplify HIO independent-review evidence workflow**

I want to simplify harness-0.7's independent-review delivery process.

The objective is to preserve independent verification, immutable records, exact-revision provenance and stop-on-mismatch requirements, while eliminating the requirement for Codex to open a separate PR for each review or verification record.

Prepare a narrowly scoped proposed amendment covering:

1. Claude uses PRs for implementation, standards and architectural proposals where appropriate.
2. Codex commits review and verification records in an isolated worktree, on an independent short-lived review branch.
3. Codex pushes the review branch but does not open a separate reviewer PR.
4. The review evidence is received through a controlled, documented Git operation that does not inadvertently integrate unaccepted implementation commits.
5. The receiving process verifies exact reviewer assignment, head, record hashes, reviewer-only scope and preserved provenance.
6. Findings remain immutable and only Codex independently verifies technical closure.
7. Owner approval remains necessary for standards, scope changes, waivers, integration and acceptance—not routine evidence-delivery mechanics.

Explicitly compare safe receipt mechanisms, including the trade-off between preserving original reviewer commit identities and using byte-identical record imports. Recommend the simplest procedure consistent with our integrity requirements.

Address how existing PR #5 can be received or dispositioned without another independent review and without prematurely approving HIO-ADR-0012.

Preserve the current approved harness until an exact-revision amendment is independently checked and explicitly approved.

Do not change implementation code, accepted S1a content, approved standards or the existing review record.

Return a concise proposed amendment, its exact revision, the migration treatment for PR #5 and the smallest owner approval decision required.
