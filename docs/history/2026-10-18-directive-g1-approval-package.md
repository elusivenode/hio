# Directive to Claude — HIO A01 G1 approval preparation

**From:** HIO owner, on architectural advice from ChatGPT  
**To:** Claude — primary HIO documentation and implementation agent  
**Task:** Prepare the A01 Gate G1 approval package; documentation and evidence integration only  
**Authority:** This instruction authorises the bounded work below. It does **not** approve A01, any ADR or standard, T-0008, HIO-S1, repository migration, live source acquisition, or SMSF changes.

## Context

Codex completed independent verification `VERIFY-2026-10-18-a01-1` of the eight original A01 findings and reported all eight `verified_closed` on its review branch. Its readiness opinion is **A01 G1: READY WITH CONDITIONS**, **HIO-S1: NOT READY**.

Reference the exact revisions:

- Original A01 review: base `1502ab8804c5968a8bf91fa36275c44e6e84f575`, head `35c9821f805955914b05991c1c075b8cb3e082b5`.
- Claude remediation: `0e3de4b76398799692cd09f3982c12986e195e7b` through submission head `0c74686fa1de21fb2e7ac6ef361c716df67b35a9`.
- Codex verification commit: `bb4aa7258f2da5951337aa62b0e469d74cefb89e`, branch `review/a01-verify-1-codex`.
- Verification report: `A01-independent-verification-and-readiness-2026-10-18.md` (use the canonical repository record `hio/reviews/records/VERIFY-2026-10-18-a01-1.md` and review index as authoritative evidence).

Do not treat Codex's opinion as owner approval or a substitute for executable S1 tests.

## Work authorised

### 1. Incorporate independent review evidence safely

- Inspect the exact review branch and its ancestry; verify that the delta from the assigned remediation head touches only authorised `hio/reviews/` review-record and index files (and any explicitly approved review handoff path). List every changed path.
- Do not assume a reviewer branch is safe solely because it has a Codex label or trailer. Ensure no reviewed architecture, source specification or implementation file has been modified by the review branch.
- Integrate the reviewer evidence into the A01 staging branch using the documented no-fast-forward convention **only if** the existing harness authorises this integration under this owner instruction. If the reviewer branch contains out-of-scope changes, unexpected conflicts or ambiguous ancestry, stop and report rather than rewriting Codex's evidence.
- Retain the original review record and verification record as distinct, durable artifacts. Do not overwrite or reinterpret the eight finding dispositions. Record exact merge SHA and review lineage.

### 2. Prepare a concise, revision-specific G1 decision package

Provide a single, easy-to-review owner-facing Markdown document, linked from the HIO staging status/handoff entry point. Include:

1. **What is being approved:** A01 charter, each of HIO-ADR-0001 through HIO-ADR-0010, core standards (particularly observations/PIT, return accounting, dataset releases, rights/licensing), agentic harness, and applicable specifications. Use exact file paths and committed revision identifiers.
2. **Decision matrix:** For each item, current status (`proposed`), decision sought (`approve / revise / defer`), scope and material trade-off. Do not make the decision for the owner.
3. **Review evidence:** Original eight finding IDs, Codex verified dispositions, reviewed revision and verification revision; identify anything unverified or dependent on future code/vendor evidence.
4. **Outstanding conditions:** Distinguish A01 approval conditions from separate S1 authorisation and live-data readiness conditions.
5. **Architectural invariants:** Independent HIO/SMSF boundary; factor and vehicle separation; economic total/excess return correctness; value-specific PIT vintage evidence; operation-specific source rights; immutable reproducible research releases; and owner-controlled decisions.
6. **HIO-001 boundary:** Describe the proposed instrument-master/SMSF projection ownership decision and the change impact, without modifying `macsmsf` or implying that the owner has approved the split.
7. **Specific owner decisions required:** Present the minimal decisions in the order they must be made. Make it simple for the owner to accept, reject, or request amendments without inferring approval from silence.

The document must distinguish **verified design and arithmetic** from **untested application code, actual vendor licence grants, publication timings and cloud behaviour**.

### 3. Prepare the next implementation recommendation, but do not start it

Recommend one bounded HIO-S1 starting slice and its acceptance tests. Evaluate explicitly whether to begin with a **synthetic-fixture-only foundation** while T-0002 verifies source rights and timing.

Include the following open design choices and give a preferred resolution or a crisp owner question:

- Canonical logical-content hashing and physical-file hashing, including floating-point/NaN and stable row ordering rules.
- Native US/Australian market calendars, cash fixing/publication availability and AUD rate regime, with the required independent evidence.
- The first equity **total-return** source; no unverified adjusted-price proxy may silently become a total-return index.
- The initial HIO/SMSF projection fields and whether the proposed boundary is still appropriate.
- Operation-specific data rights for any proposed live fetch/store/build/rebuild/publish or external-agent processing.

State the distinction clearly: **G1 approval does not authorise HIO-S1; fixture-only S1 does not authorise live data operations.**

### 4. Refresh durable agent context

Update only the minimum status, task, review-index and handoff pointers necessary for a fresh Claude or Codex session to recover:

- The exact A01 evidence revisions and all eight verified findings.
- The current proposed/approved status of each item.
- The next owner decision, next potential implementation slice, and remaining T-0002 dependencies.
- The fixed review target and the fact that Codex review evidence is independent from Claude's remediation claims.

Avoid duplicating the entire G1 decision package in `AGENTS.md`, `STATUS.md` or handoffs. Use stable links and a single authoritative record for each fact.

## Constraints

- No HIO application code, schemas, infrastructure provisioning, live data capture, vendor purchases or production deployment.
- No changes to `macsmsf` application code, production accounting, SMSF reports, or HIO-001 activation.
- Do not change any ADR/standard/task status to approved or accepted; the owner must explicitly decide.
- Do not close, waive, rewrite or impersonate any Codex finding. No retrospective approval claims.
- No new generic harness framework or new architecture design cycle. If an inconsistency materially changes the approved direction, raise it as an owner decision instead of silently resolving it.

## Completion evidence

Return a brief report containing:

1. Exact branch, starting SHA, final SHA and any merge SHA.
2. File-change inventory, and evidence that changes remained in the authorised documentation/review scope.
3. Link/path to the G1 owner decision package and updated session handoff.
4. The decisions you recommend the owner make, clearly labelled as recommendations.
5. Your preferred first HIO-S1 work package, with explicit entry gates and outstanding conditions.
6. Any blocker requiring architectural escalation or further independent Codex review.

**Stop after delivering the package. Do not commence S1 or represent A01 as approved.**
