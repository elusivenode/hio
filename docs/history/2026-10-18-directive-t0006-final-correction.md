# HIO — Final Harness Correction Directive (T-0006)

**Date:** 18 October 2026  
**To:** Claude — HIO primary documentation and implementation agent  
**From:** HIO owner, with ChatGPT acting as strategic architecture collaborator  
**Basis:** Codex focused analysis, `hio-harness-refinement-codex-analysis-for-chatgpt-2026-10-18.md`  
**Scope:** Narrow, documentation-only correction to the staged A01 harness  
**Authorisation:** The owner's explicit instruction to execute this directive authorises the bounded documentation work described below. It does **not** approve the resulting documents, HIO-ADR-0008, other A01 ADRs, HIO-S1, deployment, or changes to `macsmsf`.

## Context and objective

Codex inspected the A01 planning baseline on `docs/hio-a01-baseline`, at `23ad27f3d25763d829b5846815b0568000d6648f`, and found that the general collaboration model is sound. It identified specific ambiguities in task authorisation, advice adoption, reviewer provenance, provisional authority, and cold-start testing. Its analysis was **not** the independent A01 architecture, financial mathematics, or implementation review, and it granted no approval.

The objective is to correct these ambiguities with **the minimum necessary document changes**, preserve durable context across sessions, and then hand a fixed revision to Codex for an independent A01 review. Do not undertake a fresh architecture redesign or enlarge the harness.

Before editing, inspect the current branch and actual files. If the branch has moved, report the actual base/head and assess whether these corrections remain applicable; do not blindly overwrite newer work.

## Required corrections — in order

### 1. Separate authorisation to do work from approval of the result

Review `hio/AGENTS.md`, `hio/docs/harness/operating-model.md`, `hio/docs/decisions/owner/OD-0001-authorise-harness-refinement.md`, `hio/registers/tasks/T-0006-harness-refinement.md`, and the related handoff.

Define an unambiguous rule:

- An explicit instruction from the human owner may authorise **bounded, reversible work immediately**, within its specified scope. The agent records the instruction and its source, scope, and target revision in the task/decision record promptly; transcription is an audit step, **not** a second permission gate.
- A task can be *authorised to execute*, *completed/submitted for review*, and still *not accepted*. A completed task does not approve any ADR or release.
- Approval of an ADR, acceptance of work, approval to merge/promote, and waivers of independent findings are separate **explicit owner actions**, tied to the exact relevant revision.
- Ambiguous instructions are not permission for consequential implementation; request clarification when genuinely required.

Repair T-0006 and OD-0001 so they faithfully describe what happened. Preserve the fact that **the owner has not accepted T-0006 or approved HIO-ADR-0008**. Do not manufacture or backdate an owner approval, and do not rewrite history to hide the original ambiguity. If the record requires correction, distinguish the historical claim from the present correction.

### 2. Clarify advice and adoption

In the operating model and any entry-point wording, clarify that:

- ChatGPT-authored material is **advice or a draft** by default.
- The owner may explicitly adopt that draft as an instruction in the same message or a subsequent message. **The owner's adoption**, not ChatGPT's authorship, supplies task authority.
- Merely forwarding a prompt for discussion, without directing execution, is not authorisation.
- Claude must record the owner's actual instruction or adoption, without transforming strategic advice into approved policy.

Check the archived directive at `hio/docs/history/2026-10-18-directive-harness-refinement.md` for consistency, preserving it as historical evidence rather than silently altering the record of what was sent.

### 3. Fix the provenance claim around `HIO-Actor` trailers

Keep `HIO-Actor` commit trailers, if useful, as **self-declared role metadata only**. They are not authentication and cannot independently prove owner approval or independent Codex verification.

Distinguish:

- declared role/author;
- Git commit and file provenance;
- independently evidenced reviewer action;
- explicitly evidenced owner confirmation tied to a specific revision.

Specify the lightest credible proof available while the work is staged locally (for example, the directly supplied owner instruction recorded with its source and the designated reviewer response attached to a fixed commit). Describe stronger Git-hosted provenance — authenticated PR reviews and/or signing, where available — as an evolution path. Do not create a signing infrastructure or claim a commit trailer constitutes verified identity.

### 4. Explain the provisional harness bootstrap

`HIO-ADR-0008` and the other A01 ADRs remain **proposed**. The staged `AGENTS.md` and related instructions may operate as a **provisional working protocol** for preparing and reviewing A01; complying with them does not approve the harness architecture.

Resolve the circular situation in which a protocol appears to require a prior formally approved owner decision before the first bounded documentation task can occur. Keep the distinction between a working instruction, an approved architectural standard, and approval of a task result explicit.

### 5. Make the cold-start reviewer test state-aware

Update the reviewer bootstrap instructions and cold-start exercise:

- **Before** the owner assigns a fixed review target, a fresh Codex session should correctly answer: **“No review target has been assigned.”** It must not infer one from a candidate branch/head or Claude's self-assessment.
- **After** a review is assigned, Codex should identify the exact repository, base SHA, head SHA, task/scope, relevant ADRs, open findings, and required evidence independently from version-controlled records and the owner assignment.
- An actual fresh Codex session on a fixed revision is required to validate independence. Claude's dry run is useful preparation, **not** independent verification.

Do not report the fresh-session test as passed unless it has actually been run independently. Leave the status pending where appropriate.

### 6. Reduce duplication without losing recoverability

Codex observed significant process growth: 28 changed files and roughly 1,000 inserted lines during the refinement. Do **not** perform a wholesale simplification or delete useful history. Make only clear, low-risk deduplications.

Keep a short session entry point (`AGENTS.md`), a canonical operating-model reference, one owner decision record, one review/findings index, task cards, and handoffs. A new session should not need to read an entire lengthy operating manual to identify its role and the next authorised action. Prefer pointers over replicated rules.

## Hard boundaries

- **Allowed:** Minimal documentation, task/decision-record, harness-index, and test-instruction edits necessary for the six corrections.
- **Not allowed:** Application code, database migrations, infrastructure provisioning, deployment, credential changes, market-data ingestion, factor modelling, `macsmsf` implementation, or HIO-S1 execution.
- **Not allowed:** Approving or changing the `status:` of any proposed HIO ADR to approved; accepting T-0006 on behalf of the owner; waiving or closing Codex findings; rewriting the investment roadmap or architecture proposal substantively.
- The existing one-sentence task-authorisation wording change in `hio/docs/implementation-plan.md` may remain if it is consistent with these rules. Do not expand it into roadmap changes.

## Required evidence and completion report

Commit the minimal edits on the A01 staging branch, leaving the worktree clean. Provide:

1. **Exact base and head SHAs**, changed-file list, and a concise change summary by correction number.
2. The **before/after authorisation semantics**, including the truthful T-0006 state and the remaining unapproved decisions.
3. Evidence that proposed ADR status remains unchanged; no SMSF implementation, HIO-S1 work, or infrastructure was altered.
4. Results of available document consistency checks, link checks, and relevant harness tests. State clearly which checks were **not** run; do not equate a simulated test with a fresh agent session.
5. A **single fixed review target** (base SHA, head SHA, intended scope), ready for the owner to assign to Codex. Until assigned, label it **candidate**, not an active Codex review.
6. Remaining material ambiguities, if any, and an explicit statement that the work is **submitted for owner acceptance and later independent review**, not self-approved.

## Acceptance criteria

A fresh Claude session should be able to recover the owner-authorised task, its boundaries, the current unapproved state and its next permissible action. A fresh Codex session should recover the independent reviewer role, open findings and evidence locations **without treating Claude's report as proof**, and should identify that **no fixed review is assigned** until the owner assigns one.

The authority record must allow the following state sequence without contradictions:

**Owner instruction → task authorised → Claude submits evidence → Codex reviews exact revision (when assigned) → Claude addresses findings → Codex independently verifies → owner accepts/approves or records an explicit waiver.**

Finding closure and work acceptance must remain distinct. An owner waiver must preserve the original finding, rationale, scope, affected revision and accountable decision; it must not make the finding appear independently verified.

## Final instruction

Execute only this focused documentation correction. Do **not** begin the independent A01 review yourself or implement HIO-S1. Stop after committing the correction and providing the fixed-revision handoff. The next independent architecture and financial-mathematics review belongs to **Codex**, upon explicit owner assignment.
