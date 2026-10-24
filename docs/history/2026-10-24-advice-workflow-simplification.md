**Role:** HIO implementation and workflow architect.

**Task:** Prepare a minimal, evidence-based transition from the current stacked-PR review arrangement to a simpler collaborative process.

Repository: `elusivenode/hio`.

Current situation:
- PR #2 is Claude's S1a remediation, submitted at `18c80f27a64c8cbba653f347a3bc3401f536d0aa`.
- PR #3 is Codex's independent verification, at `0255cb2a3966f87a6c41af6020d0fd621a4fc2f1`, branched from PR #2's head.
- Both PRs target `main`.
- Codex has independently verified findings 1, 2, 3 and 5 closed.
- Finding 6 remains open following a rejected remediation.
- Findings 4 and 7 remain open pending Q-001 and Q-002.
- Harness-0.7 is currently approved under OD-0021.

**Objective**

Design a simpler operating model with one implementation PR per work item, multiple independent review rounds pinned to exact revisions, and a straightforward owner-controlled integration decision.

Preserve separation of duties, reviewer independence, immutable review evidence, formal owner authority and reproducibility.

**Required work**

1. Inspect the exact commits, approved harness, open PRs, review records and owner decisions. Treat repository evidence as authoritative.
2. Explain the precise cause of the overlapping PRs and distinguish Git ancestry from actual reviewer-authored changes.
3. Propose a safe transition that keeps PR #2 as the implementation PR and preserves the PR #3 verification record byte-for-byte.
4. Recommend where immutable Codex review records should live under the simplified model. Consider GitHub PR reviews as the collaboration surface, with Git as the durable evidence store.
5. Define how the owner authorises reviews, remediation, integration and acceptance without requiring routine intervention for each technical iteration.
6. Specify how F6 can be corrected on PR #2 and independently reverified without creating another competing implementation PR.
7. Preserve Q-001/Q-002 as explicit owner architecture decisions.
8. Identify the smallest harness amendment necessary, including a bounded transition procedure for the existing open PRs.

**Constraints**

- Do not edit approved harness files in place.
- Do not merge or close either PR.
- Do not alter Codex's verification record, verdict or finding states.
- Do not implement F6 or either temporal policy decision.
- Do not create another PR yet.
- Do not expand the scope into S1b, ETF analysis or other workstreams.
- Do not interpret this request as approval of a new process.

**Deliverable**

A concise decision package with:
- proposed future workflow;
- exact transition sequence for PR #2 and PR #3;
- record location and provenance mechanism;
- authority and acceptance boundaries;
- alternatives and tradeoffs;
- risks and rollback;
- exact owner decisions required.

Produce a draft only, on a separate proposal branch if necessary. Stop for owner review before implementation.
