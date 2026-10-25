<!-- Pasted into the Claude Code chat by the owner, 2026-10-25, verbatim, with no other words (first
person). Recorded by OD-0052. -->

**To Claude — ADR-0012 F2 and harness-0.7.1 bounded corrections**

The owner authorises bounded remediation of the findings in:

- `VERIFY-2026-10-25-adr0012-1`
- `REVIEW-2026-10-25-harness-0.7.1`

First, resolve both records directly from the pushed Codex branches. Verify the exact reviewer commits, complete record SHA-256 values, original assignments, reviewer-only scope and submitted heads.

Preserve the records unchanged. Complete the harness-0.7 receipt or explicitly authorised evidence-disposition prerequisites before remediation. Stop if verification fails or an exception beyond existing authority is needed.

**A. ADR-0012 — F2 only**

F1 and F3 have been independently verified closed as design corrections. Do not reopen them without a material new issue.

Correct F2 by defining the minimum credible provenance for a successful post-window capture:

- Bind completion evidence to an identifiable capture execution and its response or receipt.
- Define which evidence is independently replayable and which relies on a trusted capture adapter.
- Refuse finality for missing, failed, delayed, inconsistent or unverified completion evidence.
- Include the unchanged-response case.
- Explain explicitly that self-recorded events do not cryptographically prove network activity.
- Avoid inventing a second independent bookkeeping system merely to validate the first.

Preserve accepted S1a functionality and all approved point-in-time and return standards.

Keep Q-013 and the release-manifest schema question unresolved unless a separate owner decision is necessary to make this proposal coherent.

Submit a new fixed PR #4 head for scoped Codex F2 verification.

**B. Harness-0.7.1 — four findings**

Revise the existing proposed amendment to:

1. Require the actual owner-authored assignment and independent reviewer evidence inventory; report absent or withheld evidence.
2. Validate the semantics of added index entries against immutable review records, refusing duplicate or unsupported finding dispositions.
3. Correct remote SHA parsing and require a final remote-tip recheck.
4. Ensure provenance tags are published and verified before successful receipt, with an explicit recovery path for partial operations.

Preserve byte-identical import, exact Git provenance, the prohibition on importing unapproved implementation ancestry and stop-on-mismatch.

Keep routine receipt delegated to Claude only within verified assignment and scope, while retaining owner authority over approval, waivers and integration.

Submit a new proposed harness revision for independent Codex verification.

**Constraints**

Do not approve ADR-0012 or harness-0.7.1, mark source rights verified, change accepted S1a, merge PR #4 or authorise S1b.

Return both exact new submission heads and their proposed review assignments. Escalate only genuine changes to approved standards, scope or the trust model.
