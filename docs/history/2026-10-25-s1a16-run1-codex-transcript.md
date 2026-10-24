
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

I’ll check the version-controlled reviewer instructions and assignment records, then answer with file paths and commit IDs.
• Ran pwd; git rev-parse HEAD; git status --short; rg --files -g 'AGENTS.md' -g 'STATUS.md' -g '*operating-model*' -g 'README.md' -g '*hio-session*' -g '*hio-retu…
  └ docs/decisions/owner/README.md
    docs/research/README.md
    STATUS.md
• Ran git show HEAD:AGENTS.md; git show HEAD:STATUS.md; git show HEAD:reviews/README.md; git show HEAD:docs/harness/operating-model.md
  └ - the harness must save more owner time than it costs;
    - the quarterly review asks this explicitly;
    - the toil target is in [`../architecture.md`](../architecture.md#7-observability-recoverability-and-toil).
• Ran git show HEAD:docs/harness/operating-model.md | sed -n '1,245p'; git show HEAD:docs/decisions/owner/OD-0010-g1-followup-instructions.md; git show HEAD:docs/…
  └ preserves the finding. It is not a verification.
    .claude/skills/hio-return-accounting/SKILL.md
    .claude/skills/hio-session/SKILL.md
The review index contains an outstanding T-0004 assignment in macsmsf. The S1a review is marked received, though its assignment row still says “findings open”; I’ll check the verification records before reporting their state.
• Ran git show HEAD:.claude/skills/hio-session/SKILL.md; git show HEAD:.claude/skills/hio-return-accounting/SKILL.md; git show HEAD:docs/decisions/owner/OD-0018-t…
  └ 
    If PR #2 advances before the owner's fixed-head disposition, assign a new verification
    for the new head; this record does not verify a moving branch.
Role: independent reviewer. This response is an authorised, read-only onboarding assessment; it grants no approval. All paths below are in elusivenode/hio at commit 3fd129e946498e180b9f78a13d3f745afb46c638 (“H” below). This standalone repository uses AGENTS.md, formerly hio/AGENTS.md.

1. Independence relative to the author. I establish my checks from the owner assignment, approved contracts and original findings before reading the author’s completion report. I independently reproduce evidence, never modify the work under review, and write review evidence in an isolated worktree and review branch. Worktrees provide operational isolation; role trailers do not authenticate independence.
   Sources: AGENTS.md; docs/harness/operating-model.md §§2.2, 6.1–6.2 @ H.
2. An outstanding review target is assigned: REVIEW-2026-10-18-t0004.

   | Field | Assignment |
   |---|---|
   | Repository | macsmsf, branch docs/hio-001-boundary-c1 |
   | Base | 1502ab8804c5968a8bf91fa36275c44e6e84f575 |
   | Head | fe3fdc78cb2d2b9f147122528cc5cf97db976397 |
   | Task | T-0004 |
   | Scope | Documentation-only ADR 0003 C1 boundary amendment and HIO-001 review-record pointer; consistency with approved HIO-ADR-0003; no code, schema or activation-prerequisite changes |
   | Review branch | review/t0004-codex, in macsmsf |

   OD-0018 confirms the cross-lineage exception: inspect the target read-only and record evidence on the review branch cut from macsmsf@760f73e, rather than from the target. Receiving that evidence into standalone HIO requires separate handling. The S1a assignment is already received; it is not a new outstanding assignment.
   Sources: reviews/README.md, Assigned reviews; docs/decisions/owner/OD-0010-g1-followup-instructions.md; docs/decisions/owner/OD-0018-t0004-mechanics-parallel-work.md @ H.
3. Governing specifications and acceptance criteria. HIO-ADR-0003’s C1 decision and reference-identity standard v0.1 govern the boundary. OD-0008 approves their exact content at macsmsf@a82aa0dbddcbf63bb3432a3ddcf5df48300ff2b1, respectively blobs 79b3e40fe1a72677f346a321782c7aedf1523076 and 7796e7b3833171879e6b11cabb4f9e4935a44cce. T-0004 specifies:
   - B1: the diff touches only the two documentation files.
   - B2: HIO-001 activation prerequisites remain unchanged.
   - B3: HIO-ADR-0003 status is updated.

   These are criteria to check, not reproduced results. The review procedure is approved harness-0.7 under OD-0021.
   Sources: docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md; docs/standards/reference-identity.md; docs/decisions/owner/OD-0008-g1-decisions-a82aa0d.md; registers/tasks/T-0004-hio-001-boundary-amendment.md; docs/harness/operating-model.md @ H.
4. Finding open findings and evidence. Start at reviews/README.md, then follow stable finding IDs into original reviews/records/REVIEW-*.md, separate author responses and subsequent VERIFY-*.md records. Reconstruct disposition at the cited revisions; individual records override the index.

   The indexed A01 findings are all verified closed by reviews/records/VERIFY-2026-10-18-a01-1.md. S1a F1/F2/F3/F5 close in verification 1, F6 in verification 5, and F4/F7 are confirmed closed in verification 11. Thus no indexed findings remain open. The S1a assignment row’s old “findings open” wording conflicts with those later records and should not control. No T-0004 review record is indexed; its assignment remains outstanding.
   Sources: reviews/README.md; reviews/records/VERIFY-2026-10-18-a01-1.md; reviews/records/VERIFY-2026-10-24-s1a-1-1.md; reviews/records/VERIFY-2026-10-24-s1a-1-5.md; reviews/records/VERIFY-2026-10-24-s1a-1-11.md @ H.
5. Verifying remediation. The author submits a separate response identifying finding IDs, fix commits and evidence; remediation_claimed remains open. The owner assigns the exact submission head. I independently reproduce the original failure and relevant regression checks in a fresh worktree, then create a separate immutable verification record. Successful verification sets verified_closed; failure returns it to open. The author never closes the finding or edits my verdict.
   Source: docs/harness/operating-model.md §3 and §6.2 steps 6–8 @ H.
6. Waivers. Only the owner can grant one, through an explicit action evidenced by an OD record identifying the finding, rationale, risk, affected revision and any revisit conditions. waived is distinct from technical closure.
   Source: docs/harness/operating-model.md §§1.1, 3 @ H.
7. Author’s completion report. It is an unverified claim and historical context. It cannot assign my target, close findings, approve specifications, accept work or authorise a merge. I consult it only after fixing my independent test plan.
   Sources: AGENTS.md; docs/harness/operating-model.md §§1.1, 2.2 @ H.

Completion: branch work, SHA H; no changes or review submission made, no PR or receipt created. Next actor: reviewer for the existing T-0004 assignment. Ready prompt: “Verify the pinned macsmsf commits and OD-0010/OD-0018 review-branch prerequisite, then perform T-0004’s assigned review. Stop and flag any missing revision or conflicting assignment.” Procedure: docs/harness/operating-model.md §6.2 @ H.