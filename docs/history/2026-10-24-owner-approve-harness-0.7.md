<!-- The owner's message in the Claude Code chat, 2026-10-24, verbatim (a pasted block in the
owner's first person, with no other words). The authority for OD-0021. -->

I approve HIO harness-0.7 revision 3 at commit `9b58811b75cfaa600e76ab3c50390a39d5828968`, including the proposed changes to `AGENTS.md`, the operating model, review procedures, templates, scripts and CI workflow.

Record this approval in a new owner decision record, referencing the exact approved revision and relevant content hashes.

You are authorised to integrate `proposal/harness-0.7` into `main` using a merge commit (`--no-ff`), after confirming the branch tip is still `9b58811b75cfaa600e76ab3c50390a39d5828968`.

Update the documentation status and version to reflect approval, retaining the original approved revision and its provenance. Do not alter substantive policy during integration.

**Adoption condition:** The first reviewer PR under harness-0.7 must validate the GitHub `pull_request_target` workflow, including a deliberate failing case. Until this evidence is recorded, a green reviewer-PR scope check is not considered an established automated enforcement control. Continue to perform the local scope and assignment checks.

Separately, retain the S1a review evidence and its seven findings. This approval does not accept S1a, close any finding, approve a standards interpretation or authorise S1b.

After integration, report the approval-record commit, merge commit, current `main` SHA, test evidence and any remaining prerequisites for receiving the S1a review.
