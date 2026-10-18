# HIO — Directive to Claude: Collaboration harness refinement before Codex A01 review

**Date:** 18 October 2026  
**Status:** Proposed documentation-only assignment; not architectural or implementation approval.  
**Baseline identified by owner:** `docs/hio-a01-baseline` at `85ef0fa8821e5f538b739c5fe000f3f63d3bfac1` in `macsmsf`.

## Purpose and constraints

Refine the staged HIO agentic harness so that independent Claude and Codex sessions can reliably recover current authority, context, outstanding findings, and the next permitted action from version-controlled files. This brief is based on the owner's description of the staged baseline, **not an independent inspection** of the listed repository files or Claude's completion report. Examine the actual files before editing; if a requirement is already satisfied, point to it and avoid redundant changes.

You are the primary documentation and implementation agent. Codex is the independent, adversarial reviewer. The human owner is the final approver and the authority for architectural decisions and waivers. ChatGPT is a strategic collaborator and drafter, not an approval authority. SMSF trustees retain investment decision authority.

**Permitted:** minimal edits to HIO planning, harness and reviewer documentation within the staged `hio/` directory and a clear report of changes. **Not permitted:** HIO application code, cloud or database infrastructure, `macsmsf` application changes, activation of HIO-001 or HIO-S1, roadmap changes, changes to proposed ADR status, or claims that Codex has endorsed the changes. Keep HIO separate from SMSF accounting and trustee governance.

## Assessment to apply while editing

The proposed `AGENTS.md` / `CLAUDE.md` / `STATUS.md` / task-card / ADR / handoff pattern is directionally sound. The principal risk is **authority laundering**: a Claude-authored statement, unmerged branch, old handoff, or unaudited chat approval starts appearing as an approved decision. A second risk is **review laundering**: Claude marks its own correction as verified, or a future Codex session accepts Claude's summary instead of independently examining evidence. A third is **migration amnesia** when the staging directory moves to the future standalone HIO repository.

Do not solve these problems by creating a sprawling agent-management framework. Introduce only the minimum durable record and checks below.

## Ordered modifications

### 1. Clarify precedence and authority

**Target:** `hio/AGENTS.md`, `hio/docs/harness/operating-model.md`, and, only if required, `hio/docs/decisions/HIO-ADR-0008-canonical-knowledge-and-harness.md`.

Specify these operating rules:

- Git state and approvals are different dimensions. A commit or merge makes a document available, **not approved**. A proposed ADR remains proposed until a human owner decision explicitly approves that exact revision.
- The durable authority is an **owner decision record** tied to a specific document/revision, made by the owner, and referenced from the affected ADR or task. Decisions given in chat or meetings remain **pending transcription/confirmation** until recorded with source, date, scope, and exact revision. Claude may draft the record but cannot attest the owner's approval without evidence.
- Approved decisions and approved standards govern; proposed ADRs and plans are recommendations; task cards limit execution to authorised work; `STATUS.md` is a navigational snapshot, not a source of independent authority; handoffs and chat are historical context only.
- If authoritative documents conflict, or the referenced approved revision is missing, **stop and flag the conflict**. A later timestamp or newer handoff does not override an approved decision.
- Every agent must identify its role and whether the relevant work is `proposed`, `authorised`, `in_review`, or `approved` before acting.

Keep the top-level instruction file short. Put detailed procedures in the operating model.

### 2. Define a small lifecycle for work and findings

**Targets:** `hio/templates/task-card.md`, `hio/templates/review-record.md`, `hio/docs/harness/operating-model.md`.

Use explicit, non-overlapping authority:

| Record | Originator | Allowed transitions | Authoritative closure |
|---|---|---|---|
| Owner decision | Owner, or Claude drafts for explicit owner confirmation | `proposed → approved/rejected/superseded` | Owner, with date, decision and exact revision |
| Work card | Claude drafts; owner authorises | `proposed → authorised → in_progress → submitted_for_review → accepted/changes_required` | Owner accepts only after required review gates |
| Codex finding | Codex opens | `open → remediation_claimed → verified_closed` or `open → waived` | Codex verifies closure; owner alone waives |
| Handoff | Claude or Codex writes | dated snapshot; no approval lifecycle | Never authoritative over ADRs or finding register |

A `remediation_claimed` finding **remains open** until Codex independently checks the changed revision and evidence. If the correction fails, Codex returns it to `open` with a verification note. A waiver is not a technical closure: preserve `waived` as a distinct terminal state with owner name/authority, rationale, risk accepted, affected revision, date and any expiry/revisit condition. Neither Claude nor Codex may create an owner waiver by inference.

Every record should carry a stable ID, `created_at`, `updated_at`, author/actor, status, related task and ADR IDs, repository revision/commit, decision or finding text, evidence links/paths and next action. Keep mandatory fields minimal; do not create a complex tracking database.

### 3. Establish one review index, not a parallel plan

**Target:** `hio/reviews/README.md` or an equivalent existing review index; link from `hio/STATUS.md` and `hio/AGENTS.md`.

A fresh Codex session must find a **single index** of review records, open findings, remediation claims, waivers and reviewed revisions. The index can be a small Markdown table pointing to immutable dated review records; no separate Codex-owned roadmap or duplicated architectural narrative.

- Codex creates or updates findings and verification outcomes.
- Claude links its remediation commit and evidence but does not edit Codex's verdict or close its findings.
- If access controls cannot technically prevent edits in a shared repository, the operating model must say that authorship and independent verification are checked from Git history or PR review provenance; do not pretend file ownership is enforced.
- Retain stable finding IDs and original evidence across sessions and migration. Migration needs an old→new path map, original commit references, and a continuity check that no open/waived finding disappears.

### 4. Make fresh-session bootstrapping explicitly role-specific

**Targets:** `hio/AGENTS.md`, `hio/STATUS.md`, `hio/docs/harness/operating-model.md`, `hio/templates/handoff.md`.

Provide a short common entry path (`AGENTS.md` → `STATUS.md` → current task and approved ADRs → relevant evidence). Then diverge:

**Claude:** determine authorised scope, governing approved standards/decisions, files permitted to change, current blocking findings, acceptance tests and required handoff. Claude must not treat proposed ADRs as approved merely because it authored them.

**Codex:** independently identify the target commit/diff, governing approved plan and contracts, review scope, open findings, and evidentiary tests. Read Claude's completion note **after** establishing the baseline and test plan, and treat it as an unverified claim. Do not edit the reviewed implementation to make tests pass. Codex may critique the harness itself without adopting Claude's authority claims.

Every handoff records base and head revisions, changed files, work card ID, tests/evidence, known limitations, open findings, next authorised action, and explicit statement of what was **not** approved. The latest handoff is not a decision.

### 5. Define the ChatGPT → owner → Claude → Codex chain

**Targets:** `hio/docs/harness/operating-model.md` and task-card template.

A ChatGPT recommendation is **advice**, not an instruction to execute. To authorise work, the owner approves a scoped task card (or an explicit decision record referenced by it). The task card must capture:

- purpose and investment/architecture rationale;
- owner-approved scope, exclusions and exact starting revision;
- governing approved ADRs/standards, with versions;
- acceptance evidence and independent-review requirement;
- decision dependencies, unresolved questions and blockers;
- intended outputs and next approval gate.

Claude submits evidence and a precise change set. Codex examines the actual revision and independently records its verdict. The owner resolves approval/waiver. An agent's opinion cannot silently change architectural status.

### 6. Prove the harness survives a repository move

**Targets:** operating model and migration checklist in existing harness documentation (avoid creating a new subsystem).

Describe migration from `macsmsf/hio/` to the future standalone HIO repository:

- preserve Git commit/revision provenance, authoritative approvals, ADR IDs, task IDs, finding IDs and supersession history;
- create a verified mapping of old paths to new paths;
- transfer all open/waived review records and referenced evidence;
- update `STATUS.md` with the canonical new repo location only at actual migration;
- reject a migration that strands an open finding, alters the approval state or breaks references.

At present, the staging branch and proposed ADRs remain proposed; do not describe migration as completed.

## Cold-start acceptance exercise

Use two fresh sessions (or isolated contexts without prior chat history). Allow access to the staged repository **only** and give each the neutral instruction to follow its documented role. Do not coach them with a summary.

**New Claude must correctly identify:** (1) where authoritative owner decisions live, (2) which ADRs are proposed versus approved, (3) whether HIO-S1 is authorised, (4) current permitted documentation scope, (5) open findings and next handoff, (6) SMSF/HIO ownership boundary.

**New Codex must correctly identify:** (1) that it is independent, (2) which commit and task are under review, (3) relevant approved specifications and acceptance criteria, (4) how it independently finds open findings and evidence, (5) how to verify a remediation without Claude closing it, (6) who can grant waivers, and (7) that an author's completion report is not proof of correctness.

**Owner check:** Require both sessions to cite repository paths and commit IDs for every answer. Compare their recovered status and permissions to the known owner baseline. A pass requires **no false approval or authorisation claims**, no missed open findings, correct next action, and no reliance on chat memory. Record failures and revise the smallest relevant instruction. If actual fresh sessions cannot be run, label any dry-run as unverified and give the owner a reproducible test script/instructions.

## Completion report to return

1. Files examined and their exact starting revision; what was directly verified versus inferred.
2. Concise before/after change summary with paths and rationale; explain where existing rules already satisfied the requirements.
3. State machine and evidence requirements for owner decisions, work, Codex findings, verification and waivers.
4. Results of cold-start exercise or explicit statement that fresh-session verification remains pending.
5. Open questions or conflicts requiring owner decision, limited to genuine blockers.
6. Exact commit(s), changed-file list, clean/dirty worktree status and next recommended reviewer action.

**Do not request architecture or financial-mathematics approval from yourself.** Finish with a proposed request for Codex's independent A01 review, identifying exact revision and review scope.

## Owner approvals needed before this documentation task

The owner need only authorise **documentation-only harness refinement on the staged branch** and confirm that the role/approval boundaries above are intended. No choice of cloud vendor, database, factor methodology, licence, HIO-S1 budget or HIO-001 rework is required for these edits. If an existing approved owner decision conflicts with this directive, stop and seek clarification rather than replacing it.
