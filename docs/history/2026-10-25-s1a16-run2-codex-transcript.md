You are starting a fresh session in this repository. Work only from version-controlled files
and any owner assignment you have been given. Follow `hio/AGENTS.md` for the role
"independent reviewer". Answer with a repository path and commit id for every claim:
1. What is your independence relative to the author?
2. Has a review target been assigned to you? If so, give the repository, base SHA, head SHA,
   task and scope.
3. Which approved specifications and acceptance criteria govern it?
4. How do you independently find open findings and their evidence?
5. How do you verify a remediation without the author closing it?
6. Who can grant waivers?
7. What standing does the author's completion report have?

I’ll check the version-controlled reviewer instructions and assignment records, then cite repository paths and commit IDs for each answer.
• Ran pwd; git rev-parse HEAD; git status --short; rg --files -g AGENTS.md -g STATUS.md -g '*operating-model*' -g '*README.md' -g '*hio-session*'
  └ docs/decisions/owner/README.md
    docs/research/README.md
    STATUS.md
• Ran git show HEAD:AGENTS.md; git show HEAD:STATUS.md; git show HEAD:reviews/README.md; git show HEAD:docs/harness/operating-model.md
  └ - the harness must save more owner time than it costs;
    - the quarterly review asks this explicitly;
    - the toil target is in [`../architecture.md`](../architecture.md#7-observability-recoverability-and-toil).
• Ran git show HEAD:docs/harness/operating-model.md | sed -n '90,270p'; git show HEAD:reviews/README.md | sed -n '45,210p'; git show HEAD:docs/decisions/owner/OD-…
  └ None.
    .claude/skills/hio-return-accounting/SKILL.md
    .claude/skills/hio-session/SKILL.md
• Ran git show HEAD:.claude/skills/hio-session/SKILL.md; git show HEAD:.claude/skills/hio-return-accounting/SKILL.md; git show HEAD:reviews/records/VERIFY-2026-10…
  └ validates the `pull_request_target` workflow, including a deliberate failing case, and that
    evidence is recorded, a green reviewer-PR scope check is **not** an established automated
    control; steps 4 and 4a are performed locally regardless.
Role: independent reviewer. Status: proposed; no active review assigned.

All paths below are in elusivenode/hio at commit df3af48ed874acf3365ecddc1861f93abc1be03e. The former hio/AGENTS.md is now root-level AGENTS.md.

1. Independence from the author. I establish my test plan from the owner assignment, approved contracts and findings before reading the author’s handoff. I reproduce evidence independently, never edit the work under review, and write review evidence in my own worktree and review branch. Worktrees provide operational isolation; role trailers do not authenticate independence.
   Sources: AGENTS.md; docs/harness/operating-model.md §§2.2, 6.1–6.2, at the commit above.
2. No review target has been assigned. The assignment table contains historical reviews, both received: T-0004 and S1a. T-0004’s receipt is explicitly recorded by OD-0040; S1a’s receipt by OD-0037. Neither supplies a new assignment for this session. I must not select a candidate or reopen completed work by inference.
   Sources: reviews/README.md → Assigned reviews; docs/decisions/owner/OD-0040-t0004-cross-lineage-receipt.md; docs/harness/operating-model.md §2.2, at the commit above.
3. There is no currently assigned target whose specifications or acceptance criteria I can identify. On assignment, I must obtain the exact repository, base, head and scope from the owner source, then identify the governing approved versions and acceptance criteria before fixing my test plan. Proposed specifications and author reports cannot supply approval.
   Sources: docs/harness/operating-model.md §§1.1, 2.2, 6.2 steps 1–2, at the commit above.
4. I find findings through the index, then check the immutable records and their cited revisions and evidence. Records prevail over the index; remediation_claimed remains open. Currently, all eight A01 findings and all seven S1a findings are verified closed; T-0004 opened none. The S1a assignment row’s older “findings open” wording is superseded by verification records.
   Sources: reviews/README.md; reviews/records/VERIFY-2026-10-18-a01-1.md; reviews/records/VERIFY-2026-10-24-s1a-1-1.md, -5.md, -11.md; reviews/records/REVIEW-2026-10-18-t0004.md, at the commit above.
5. The author claims remediation; the reviewer verifies closure. After owner assignment of the fixed submission head, I use a fresh worktree, reproduce the original counterexample, inspect the fix and independently test relevant regressions. I add a separate verification record referencing the original finding and remediation SHA. Success becomes verified_closed; failure returns to open. The original review remains immutable.
   Source: docs/harness/operating-model.md §3 and §6.2 steps 6–8, at the commit above.
6. Only the owner grants waivers. An OD record must state authority, rationale, accepted risk, affected revision, date and any revisit condition. A waiver is distinct from technical closure.
   Sources: AGENTS.md → Who may change what; docs/harness/operating-model.md §3, at the commit above.
7. The author’s completion report is unverified historical context. It neither assigns a review nor proves remediation, acceptance, approval or waiver. I read it after establishing my test plan and independently reproduce its claims.
   Sources: AGENTS.md → Authority rules and Ending a session; docs/harness/operating-model.md §§1.1, 2.2–3, at the commit above.

Completion: checkout is detached at df3af48ed874acf3365ecddc1861f93abc1be03e; no changes, review branch, push or PR produced, and no new evidence submitted for receipt. Nothing approved. Next actor: owner, to grade this response or issue an exact review assignment. Prerequisite for review: an owner-authored assignment naming the review ID, repository, full base/head SHAs, scope and review branch.