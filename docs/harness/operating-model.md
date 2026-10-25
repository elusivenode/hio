---
id: HIO-HARNESS
title: Agentic operating model and harness specification
status: approved      # harness-0.7.1 approved by OD-0056 at 552d4fb (blob a74a41453d10). Adoption is conditional on a supervised first receipt recorded in an OD; routine delegated receipt is NOT authorised until then
approved_by: OD-0056   # harness-0.7.1 at 552d4fbde6f4256bf969b908d721a765aae84e17, blob a74a41453d10b54161136ff08ac36e6ca86f33bc (earlier: OD-0021, harness-0.7 rev 3 at 9b58811, blob 90e2565fe814; before that OD-0012, harness-0.6 at f2275e2, blob e3114bd188ad; OD-0008, harness-0.5 at a82aa0d, blob 7172659cf4ba)
owner: HIO architecture lead (owner)
version: harness-0.7.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0008
changelog:
  - "harness-0.7.1 correction 1 (2026-10-25, APPROVED by OD-0059; docs/decisions/harness-0.7.1-trailer-correction-proposal.md revision 1, blob b8d2fac0dc18): section 6.2 steps 5.7, 5.8 and 5.10 only. Requires the HIO-Actor trailer on each receipt import commit, runs tools/check_repo.py trailers on the import commit before the 5.9 recheck, and makes CI status a mandatory reported result kept separate from the evidence-integrity checks. Tested by a bounded scratch-clone regression (OD-0059). No tool, workflow or hook changed"
  - "harness-0.7.1 (2026-10-25, APPROVED by OD-0056 at 552d4fb, blob a74a41453d10; STATUS-ONLY edits follow): review evidence is delivered by a pushed review branch with no reviewer PR, and received by a byte-identical import with a verified provenance tag (docs/decisions/harness-0.7.1-proposal.md revision 3 at 8ed13fd, blob 72deffc37a4c; verified by VERIFY-2026-10-25-harness-0.7.1-1). Content change: the section 6.2 preamble sentence and steps 3, 4, 5 and 6 only. Adoption condition (OD-0056): the first receipt is supervised and its result recorded in an OD before routine delegated receipt is enabled; until then each receipt needs the owner's explicit go-ahead before anything is pushed to main"
  - "harness-0.7 rev 3 (2026-10-24): APPROVED by OD-0021 at 9b58811 (blob 90e2565fe814); integrated by merge 910c5d5; later edits record status only. Adoption condition: the CI reviewer-PR gate is not an established control until the first reviewer PR validates it. Content: step 4a compares the record's assignment source with an owner-supplied expected source. Rev 2 (fcabd7f): adds assignment verification (step 4a), the trusted-base CI gate, the remediation-before-receipt exception, conflicting-channel handling, and a pointer-only decisions queue. Rev 1: integrated review flow after REVIEW-2026-10-24-s1a-1 exposed handoff gaps. §2.2 and the review index reconcile the assignment sources; §6.2 adds PRs as the visible surface (records stay authoritative), CI scope check of reviewer PRs against the pinned head, CI-run citations, an explicit completion block in every handoff, and standalone-repository paths; §6.3 adds the open-decisions queue"
  - "harness-0.1 (2026-10-18, 85ef0fa): initial"
  - "harness-0.6 (2026-10-18): CONTENT change after approval: §6.2 step 3 adds reviews/reports/ (owner instruction OD-0009). STATUS-ONLY edits recording OD-0008: front matter, the 'Bootstrap history' paragraph and §6.2 status replace the provisional wording, and precedence row 3 drops 'provisional'. Approved blob at a82aa0d: 7172659cf4ba. harness-0.6 approved by OD-0012 at f2275e2 (blob e3114bd188ad); later edits record status only. 2026-10-24: §8.1 status sentence updated (status only, OD-0016; migration performed, OD-0017). Paths written hio/<p> mean <p> after migration (MIGRATION-MAP.md)"
  - "harness-0.5 (2026-10-18): per-commit scope check and required record; reviewer handoff and STATUS exception; fix commits vs submission head (T-0007 remediation of a Codex assessment)"
  - "harness-0.4 (2026-10-18): review branch and worktree protocol §6.2; immutable findings with separate response and verification records; scope-check script (T-0007, OD-0003)"
  - "harness-0.3 (2026-10-18): authorise vs accept vs approve vs waive; advice and adoption; trailers as metadata only; provisional protocol; state-aware reviewer test (T-0006 final correction, docs/history/2026-10-18-directive-t0006-final-correction.md)"
  - "harness-0.2 (2026-10-18): owner decision records; record lifecycles; review index and findings; role-specific bootstrap; advice→authorisation chain; migration continuity; role-specific cold-start test (per docs/history/2026-10-18-directive-harness-refinement.md)"
---

# Agentic operating model and harness specification

**Design goal.** Any new collaborator (the owner, Claude, Codex, a specialised agent or a
human), in any model generation, can answer from the repository alone:

1. What is HIO for?
2. What has been decided?
3. Which factor mathematics is authoritative?
4. What is under construction?
5. What was verified?
6. Who owns this boundary?
7. What can I safely change next?

It does this at a bounded context cost, without relying on any chat transcript or model memory.

## 0. Evidence from `macsmsf`: what to keep and what to fix

Everything below was observed in the `macsmsf` repository on 2026-10-18 [OBS].

| Pattern | Evidence | Verdict for HIO |
|---|---|---|
| Short root rules file, read every session | `CLAUDE.md` is "deliberately short…holds the rules that cause real damage" | **keep**, as `AGENTS.md` (model-neutral) imported by `CLAUDE.md` |
| Skills with trigger descriptions | `.claude/skills/*/SKILL.md` frontmatter; `CLAUDE.md` notes that a skill without triggers "gets missed" | **keep**; scoped to `hio/` |
| ADRs with rollback and status | `docs/adr/0001–0004` | **keep**; add a register with explicit statuses |
| Review records with an evidence method | `docs/hio-001-review-record.md`, `docs/a17a-p1-review-record.md` (rounds, findings, dispositions, evidence) | **keep**; templated |
| Evidence tags in investigations | `docs/quarterly-pack-v2-investigation.md` ([OBSERVED], [DISCLOSED], [ESTIMATE], …) | **keep**: [OBS], [INF], [PROP], [EXT] |
| "Cross-check two figures that must agree" | `CLAUDE.md` | **refine** into *identity* checks versus *triangulation* (return standard §11) |
| Append-only progress log as the status source | `IMPLEMENTATION_PROGRESS.md` is 3,958 lines. Its "Status Summary" still says production deployment is "agreed…not yet built" and whole-fund MWR is "still blocked", both later untrue | **fix**: bounded `STATUS.md` (current only) + dated handoffs (history) |
| Competing planning essays | benchmark plan v1 and v2; pack v2 investigation; roadmap; three HIO essays outside the repository | **fix**: one index ([`../../README.md`](../../README.md)); supersession front matter; history folder |
| Project status in model memory | auto-memory held "next direction: Azure + Prefect", later stale | **fix**: memory is a cache; precedence puts it last |
| Stale blockers | `CLAUDE.md`: "Whole-fund MWR was documented as blocked on work that turned out to be unnecessary" | **fix**: blockers are dated claims with a re-verify date (§8) |
| Ad hoc session handovers | `docs/session-handover-2026-09-*.md` (useful, but free-form and in `docs/`) | **keep the idea, template it**: `handoffs/` |
| Owner directives as prompts outside the repository | the HIO assignments existed only in `~/Downloads` | **fix**: directives that change direction are committed to `docs/history/`, and their decisions become ADRs |

## 1. Canonical knowledge and precedence

| Knowledge | Canonical home | Format |
|---|---|---|
| Mission, philosophy, trajectory | `docs/charter.md` | Markdown + front matter |
| Decisions | `docs/decisions/HIO-ADR-*.md` + register | Markdown + front matter |
| Architecture, triggers | `docs/architecture.md` | Markdown |
| Return mathematics | `docs/standards/return-accounting-and-factor-construction.md` | Markdown (versioned) |
| Data, PIT, rights, releases, identity | `docs/standards/*.md` | Markdown (versioned) |
| Factor definitions | `specs/factors/*.yaml` | YAML (machine-checked from S1) |
| Programme | `docs/roadmap.md`, `docs/implementation-plan.md` | Markdown |
| Risks and open decisions | `docs/risks-and-open-decisions.md` | Markdown |
| Current state | `STATUS.md` | Markdown, ≤150 lines |
| Work items | `registers/tasks/T-*.md` | Markdown from template |
| Research memory | `registers/hypotheses.yaml`, `registers/experiments.yaml` | YAML |
| Sources and rights | `registers/sources.yaml` | YAML |
| Session history | `handoffs/YYYY-MM-DD-<slug>.md` | Markdown from template |
| Superseded inputs | `docs/history/` | verbatim + index |
| Owner decisions (approvals, rejections, authorisations, acceptances, waivers) | `docs/decisions/owner/OD-*.md` | Markdown + front matter |
| Reviews, findings, remediation claims, verification, waivers | `reviews/README.md` (index) + `reviews/records/*.md` | Markdown |

### 1.1 Authority model

**Availability is not authority.** Git state (committed, branched, merged) makes a document
*available*. Only an explicit owner action gives it authority.

**Four distinct owner actions.** None of them implies another.

| Action | What it does | Takes effect | Recorded as |
|---|---|---|---|
| **Instruct (authorise work)** | lets an agent do bounded, reversible work within a stated scope | **immediately**, on the owner's explicit instruction | an OD record (`decision: authorise_work`), written promptly by the agent. Transcription is an **audit step, not a second permission gate** |
| **Accept work** | accepts a submitted task result | only by an explicit owner statement tied to the exact revision | an OD record (`accept_work`) |
| **Approve** (an ADR, standard or spec; a merge or promotion) | makes it policy, or permits the merge | only by an explicit owner statement naming the exact revision | an OD record (`approve`) |
| **Waive** an independent finding | accepts a risk without technical closure | only by an explicit owner statement | an OD record (`waive_finding`): the original finding, rationale, scope, affected revision and accountable decision are all preserved |

**Consequences:**
- A task can be authorised, completed and submitted, and still **not accepted**. Completing a
  task approves nothing, including any ADR it touches.
- **Ambiguous instructions are not permission** for consequential work. Ask the owner when it
  genuinely matters. Reversible documentation work inside a stated scope is not consequential;
  code, infrastructure, data, merges, promotions and `macsmsf` changes are.
- An agent records what the owner **actually said**, quoting or citing the source. It never
  upgrades a request, a forwarded draft or its own reading into an approval.

**Advice and adoption.**
- Material written by ChatGPT or another strategic collaborator is **advice or a draft** by
  default.
- The owner may explicitly **adopt** it as an instruction, in the same message or a later one.
  The owner's adoption, not the draft's authorship, gives it task authority.
- Forwarding a draft for discussion, without directing execution, is not authorisation.
- The agent records the adoption (source, date, scope, target revision). It never turns the
  draft's recommendations into approved policy.

**Bootstrap history.**
- Until G1, this protocol operated *provisionally*, to prepare and review A01. Following it did
  not approve it.
- It was approved, with HIO-ADR-0008, by OD-0008 at `a82aa0d`. Later amendments are listed in
  this file's changelog, against the approved blob.
- The rule that an explicit owner instruction authorises the first bounded task (row 1 above)
  still stands.

**Precedence of authority:**

| Rank | Source | Authority |
|---|---|---|
| 1 | explicit owner actions (approve, accept, waive), recorded in OD records **at the stated revision** | governs |
| 2 | approved standards and specs (by version) | governs |
| 3 | `proposed` ADRs, charter, architecture, roadmap, plans | recommendation only |
| 4 | task cards, with the recorded owner instruction | limit execution to the instructed scope |
| 5 | `STATUS.md` | navigational snapshot; **no independent authority** |
| 6 | handoffs, chat, model memory, meeting notes, collaborator drafts | historical context only |

**Conflict rule.** If two authoritative sources conflict, or a referenced approved revision is
missing or does not match, **stop and flag**. Record the conflict in the handoff and ask the
owner. A later timestamp, a newer handoff, or a more confident document does not override an
approved decision.

**Self-declaration.** Every agent states its role and the status of the work (`proposed`,
`authorised`, `in_review` or `approved`) before acting, and repeats both in its handoff.

`proposed` is never policy.

## 2. Repository navigation and onboarding

- **Common bootstrap (≈25k tokens):**
  1. `AGENTS.md`
  2. `STATUS.md`
  3. the task card **and the recorded owner instruction (OD) behind it**
  4. the *approved* ADRs and standards it governs
  5. `reviews/README.md` (open findings)
  6. the relevant evidence

  Then record `git rev-parse HEAD`.
- **Never bulk-load `docs/`.** Skills point to sections, not whole documents.
- **Skills (scoped):**
  - `hio-session`: the bootstrap and handoff procedure;
  - `hio-return-accounting`: a pointer to the standard plus its invariant list.

  New skills are added only when a repeated task has a stable procedure. Each has a trigger
  description.

### 2.1 Claude (implementation or documentation agent)

Before changing anything, write down:
1. the owner instruction that authorised the card (its OD record, or, if it is not yet
   transcribed, the source you were given; record it first), and the card's status;
2. the governing **approved** decisions and standards, with versions. Treat proposed ADRs as
   recommendations, including your own;
3. the files you may change;
4. the open findings that block or touch the work;
5. the acceptance tests;
6. the handoff you must leave.

If the card is not authorised, you may only read and draft.

### 2.2 Codex (independent reviewer)

1. **Find your assignment.** It comes from exactly one owner-authored source (§6.2 step 1): a
   row in the *Assigned reviews* table of `reviews/README.md`, an owner-authored comment on the
   author's pull request, or an assignment the owner gave you directly. Your review record
   cites which source it used.
   - **If there is none, your answer is "No review target has been assigned."** Stop there.
     Never infer a target from a candidate row, a branch tip or an author's self-assessment.
   - If there is one, take the repository, review id, base SHA, head SHA, task, scope and
     review branch **from the assignment**, not from the author's summary.
   - Then create your own worktree and review branch at the assigned head (§6.2), and work
     only there.
2. Read the governing approved plan, contracts and acceptance criteria, and the open findings in
   `reviews/README.md`.
3. Write your test plan.
4. **Only then** read the author's handoff or completion note. Treat every claim in it as
   unverified until you have reproduced the evidence.
5. Never edit the implementation under review to make it pass. Record findings instead.

You may critique the harness itself. You do not inherit any authority claim the author makes.

## 3. Records and their lifecycles

| Record | Originator | Allowed transitions | Authoritative closure |
|---|---|---|---|
| **Owner decision** (`docs/decisions/owner/OD-*`) | the owner, or an agent transcribing an explicit owner statement | `draft → recorded`; `recorded → corrected \| superseded`. `draft` means the text awaits an owner statement and has no authority | the owner's explicit statement (cited source); the record only evidences it |
| **Work card** (`registers/tasks/T-*`) | Claude drafts; the owner instructs | `proposed → authorised → in_progress → submitted_for_review → accepted \| changes_required` (`changes_required → in_progress`) | the owner accepts, only after the card's required review gates pass |
| **Codex finding** (in a review record; listed in `reviews/README.md`) | Codex opens | `open → remediation_claimed → verified_closed`; `remediation_claimed → open` (failed verification); `open → waived` | Codex verifies closure; **only the owner waives** |
| **Handoff** (`handoffs/*`; reviewers: `reviews/handoffs/*`) | Claude or Codex | none: a dated snapshot | never authoritative over ADRs, OD records or findings |

**Rules:**
- **A `remediation_claimed` finding is still open.** Only Codex, after independently checking the
  changed revision and its evidence, sets `verified_closed`. A failed check returns the finding
  to `open`, with a verification note.
- **Submitted findings are immutable.**
  - Claude's response is a separate *remediation response* record: the finding ids, what was
    changed, the remediation SHA and the evidence.
  - Codex's check is a separate *verification record* that references the original finding ids
    and the remediation SHA.
  - Neither edits the original review record.
  - The directive's suggested states map onto ours:

    | Directive state | Our state |
    |---|---|
    | REMEDIATION_PROPOSED / IMPLEMENTED | `remediation_claimed`, with a SHA |
    | VERIFIED + CLOSED | `verified_closed` |
    | REJECTED | back to `open` |
    | WAIVED | `waived` |
- **A waiver is not a technical closure.** `waived` is a distinct terminal state, recorded by an
  OD record. That record holds:
  - the owner's authority;
  - the rationale;
  - the risk accepted;
  - the affected revision;
  - the date;
  - any expiry or revisit condition.

  No agent creates a waiver by inference.
- **Work-card authorisation** comes from the owner's explicit instruction. The card cites the
  OD record of that instruction (`authorised_by`) and the exact starting revision
  (`base_revision`). Acceptance cites an OD id (`accepted_by`) and the review records relied
  on.

**Minimum fields on every record:**
- stable id;
- `created_at`, `updated_at`;
- actor (role / agent or person);
- status;
- related task and ADR ids;
- revision;
- the decision or finding text;
- evidence paths or links;
- next action.

There is no tracking database: these are Markdown and YAML files under git.

- **Task card** ([`../../templates/task-card.md`](../../templates/task-card.md)). See also §5.1
  for what an authorised card must capture. **Implementation requires an `authorised` card.**
- **Handoff** ([`../../templates/handoff.md`](../../templates/handoff.md)), written at the end
  of every session that changed anything. Non-reviewers write to `handoffs/`; a reviewer on a
  review branch writes to `reviews/handoffs/` (§6.2). It contains:
  - base and head revisions. `head_revision: self` means the commit that adds the handoff,
    resolved with `git log -n1 --format=%H -- <handoff path>`. Earlier commits are listed by id;
  - changed files;
  - the work card id;
  - tests and evidence;
  - known limitations;
  - open findings;
  - the next *authorised* action;
  - **an explicit statement of what was not approved.**

  A handoff that relies on conversational knowledge fails review.

## 4. Research memory

- **`hypotheses.yaml`.** One entry per hypothesis:
  - economic thesis;
  - predicted sign and size;
  - data and return definitions (spec ids);
  - knowledge mode required;
  - status: `proposed | registered | testing | supported | not_supported | inconclusive | retired`;
  - linked experiments.
- **`experiments.yaml`.** One entry per experiment run:
  - hypothesis id;
  - pre-registration (test, sample, PIT mode, metrics, decision rule) **committed before
    results**;
  - variants tried (count and list);
  - release and run ids;
  - results with uncertainty;
  - negative findings;
  - outcome;
  - follow-up.
- **Failed and abandoned experiments are never deleted.** The variant count per hypothesis is
  the input to multiple-testing haircuts.

## 5. Roles and permissions

| Role | Typical actor | Inputs | Outputs | May | May not |
|---|---|---|---|---|---|
| **Owner / architecture lead** | the human owner | everything | OD records: approvals, rejections, authorisations, acceptances, waivers | approve ADRs, specs and standards; authorise and accept work cards; waive findings; hold credentials | — |
| **Strategic collaborator** | ChatGPT, or a human advisor | anything the owner shares | advice, drafts | advise; draft briefs | instruct execution; approve anything |
| **Architecture agent** | Claude (design session) | charter, ADRs, evidence | draft ADRs, plans, risk entries | propose | approve; change code |
| **Implementation engineer** | Claude (repository session) | an authorised task card | code, tests, releases (`exploratory`), handoff | change code within scope; run jobs with dev credentials | widen scope; edit approved specs or standards in place; set `validated` or `approved` |
| **Quantitative researcher** | Claude or a human | specs, releases, hypotheses | spec drafts, pre-registrations, experiment results | register hypotheses; draft specs | mark its own results `validated`; promote to a consumer |
| **Data-quality investigator** | an agent (later) | quarantine queue, run records | triage notes, proposed releases or quarantines | propose | release quarantined data; alter receipts |
| **Independent reviewer** | Codex or a human | a review bundle (task card, diff, evidence, specs) | a review record with findings and a verdict | read; run tests | edit the work under review; approve it |

**Separation of duties.** For any `validated` or approved state, author ≠ reviewer ≠ approver.
The owner may be the approver, but is not also the sole reviewer of their own code. SMSF
trustees keep investment decision authority for the SMSF. Nothing in HIO's lifecycle grants it.

### 5.1 From advice to authorised work: ChatGPT → owner → Claude → Codex → owner

1. **Advice.** A strategic collaborator's recommendation, or a brief it drafted, is **advice**.
   It is not an instruction to execute, even when it is pasted into a session.
2. **Adoption and authorisation.** The owner explicitly instructs execution, or adopts the
   draft as an instruction (§1.1). The agent records that instruction (source, date, scope,
   base revision) in an OD record and the task card. The card must capture:
   - purpose, and the investment or architecture rationale;
   - the owner-approved scope, exclusions and **exact starting revision**;
   - the governing *approved* ADRs and standards, with versions (proposed ones are listed as
     context, not authority);
   - the acceptance evidence, and whether an independent review is required;
   - decision dependencies, unresolved questions and blockers;
   - the intended outputs, and the next approval gate.
3. **Execution.** Claude works within the card and submits the evidence plus a precise change
   set (base..head, changed files). The card moves to `submitted_for_review`.
4. **Review.** Codex examines the actual revision independently (§2.2) and records its verdict
   and findings in a review record. It does not rely on Claude's summary.
5. **Resolution.** The owner accepts the card, sends it back (`changes_required`), or waives
   specific findings, each through an OD record.

An agent's opinion never changes the architectural status of anything.

## 6. Change control

| Change | Proposed by | Reviewed by | Approved by | Evidence | CI checks (from S1, where practical) |
|---|---|---|---|---|---|
| ADR | any agent or owner | independent reviewer, if it gates implementation | owner | context, options, consequences, rollback | front matter valid; links resolve |
| Standard (new version) | researcher or architect | independent reviewer | owner | worked examples + invariant updates | version bump; changelog |
| Factor spec | researcher | independent reviewer | owner (for `approved`) | template complete; invariants listed; triangulation pre-registered | YAML schema; `series_class` rules; referenced series exist |
| Rights record | any agent (research) | owner verifies the terms | owner | terms reference + date + section | schema; no `allow` without evidence |
| Dataset release | job | reviewer (for `validated`) | owner (for consumer) | manifest; invariants; rebuild hash | invariants; reproducibility |
| Model promotion | researcher | reviewer | owner | pre-registration; OOS evidence; costs; uncertainty | lineage present |
| Roadmap change | architect | — | owner | rationale + dependency impact | links |
| Harness change | anyone | — | owner | why; what it replaces | harness version bump |

**Exploratory versus approved.** Exploratory outputs may be produced freely by any role. They
carry `exploratory` status and never reach a consumer.

"Approved by owner" in the table above always means **an OD record citing the exact revision**.

### 6.1 Review index and provenance

- **One index.** [`../../reviews/README.md`](../../reviews/README.md) lists:
  - reviewed revisions;
  - review records;
  - every finding, with its current state;
  - remediation claims;
  - verifications;
  - waivers.

  The detail lives in immutable, dated review records (`reviews/records/`). There is no
  separate reviewer roadmap, and no duplicated architecture narrative.
- **Who writes what:**
  - **Codex** opens findings and records verification outcomes.
  - **Claude** may add only a remediation claim (commit id + evidence path) to a finding's
    row. Claude never edits a verdict and never closes a finding.
  - **The owner** records waivers, by OD reference.
- **Provenance: four different things, not to be conflated.**

  | Claim | Evidence while staged locally | It is not |
  |---|---|---|
  | **Declared role or author** | an `HIO-Actor:` commit trailer (and `Co-Authored-By`) | **not** authentication. Anyone can write any trailer. It is self-declared metadata, from `72d1e56` onward; `85ef0fa` carries only `Co-Authored-By` |
  | **Git provenance** | the commit id, the files changed and the committer identity (every commit here uses the owner's local git identity, whoever drafted it) | not proof of who decided anything |
  | **Independent reviewer action** | the reviewer's own output (review record or response), supplied by the owner and committed **verbatim**, attached to the fixed commit it reviewed, with a sha256 of the supplied file | not established by Claude's summary of it |
  | **Owner confirmation** | the owner's explicit statement, committed verbatim under `docs/history/` with a sha256, and cited by an OD record that names the exact revision | not inferable from a merge, a trailer or silence |

  **The lightest credible proof available now** is the last two rows: verbatim, hashed
  artefacts supplied directly by the owner.

  **Evolution path, with no infrastructure built now:** a hosted repository with authenticated
  PR reviews (the reviewer account's approval on the exact head), then signed commits or tags
  for owner decisions.

  A trailer mismatch is a red flag to investigate, never proof either way.
- **Review targets are commit ids.** A review request names its exact base and head SHAs. They
  are set when the owner issues the go-ahead, never by pointing to an author's handoff.
- **Stable finding ids.** Ids are `F-<review id>-<n>` and are never reused or renumbered. The
  original evidence references are kept, including across migration (§8.1).

### 6.2 Review branch and worktree protocol

**Status:** adopted by owner instruction (OD-0003); accepted at `b48f83c` (OD-0004); approved as
part of this operating model by OD-0008 at `a82aa0d`. The `reports/` path was added by
harness-0.6 (OD-0009). Harness-0.7 (approved, OD-0021) adds pull requests as the visible surface, CI
checks on reviewer PRs, CI-run citations and the completion block.

**Adoption condition (OD-0021; status: met, OD-0022: runs 40047802547 failing deliberately and 40047873419 passing, PR #1).** Until the first reviewer PR under harness-0.7
validates the `pull_request_target` workflow, including a deliberate failing case, and that
evidence is recorded, a green reviewer-PR scope check is **not** an established automated
control; steps 4 and 4a are performed locally regardless.

**Pull requests are the visible surface, not the authority.** Records stay authoritative: the
review record, the remediation response, the verification record and the OD records. A PR makes
a fixed head, its CI result and its diff visible to every agent; receipt (step 5) is evidence delivery, never acceptance. Reviewers do not open PRs.

0. **Submission** (author). The author pushes a branch and opens a PR to `main` whose
   description states `Submission-Head: <full sha>`. That head is never rebased or
   force-pushed while it is under review. An author PR merges only on the owner's instruction.
1. **Assignment** (owner). The owner assigns one review in **one** owner-authored source: an
   *Assigned reviews* row (an owner commit), an owner comment on the author's PR, or a direct
   instruction to the reviewer. A direct instruction is valid but hard to discover, so the owner
   or Claude adds the matching index row at receipt.

   **Conflicting channels.** If two owner-authored channels give different values for one
   review (id, base, head, scope or branch), or two reviews are assigned the same target with
   different scopes, nobody picks one. The reviewer stops before reviewing, the author stops
   before remediating, and either reports the conflict. The owner reconciles it in one
   statement that names the assignment that stands; that statement is the source the review
   record cites. The assignment states:
   - review id;
   - repository;
   - **full base and head SHAs**;
   - scope (files, work package, standards);
   - review branch name;
   - reviewer (a declared role).

   The head is never rebased or force-pushed during the review. If the work changes, a new
   review, or a scoped verification against the new head, is needed.
2. **Isolated checkout** (reviewer):

   ```
   git worktree add ../hio-review-<id> <head> -b review/<id>-codex
   ```

   Worktrees isolate checkouts operationally. **They are not a security boundary.**
3. **Allowed writes** (reviewer). Only add or modify `.md` files under `reviews/`:
   - review records and verification records in `reviews/records/`;
   - the reviewer's own session handoff in `reviews/handoffs/`, since its other handoff
     locations are out of bounds;
   - reviewer opinion or readiness reports in `reviews/reports/`. These are supporting opinion;
     the records stay authoritative (harness-0.6, OD-0009);
   - its own rows in `reviews/README.md`.

   The reviewer never edits `STATUS.md`, `handoffs/`, the work under review or any
   submitted record. There are no merge commits on the review branch. The reviewer **pushes the review branch** and does **not** open a pull request. An unpushed
   review branch has not been submitted. The reviewer's **final message** is its independent
   report: it states the pushed branch, the branch **tip SHA**, the reviewed head, and the
   **sha256 of every file the reviewer added**. The handoff cannot carry its own commit id, so the
   final message is the source the receiver reconciles against.
4. **Scope check** (the receiver, before receipt). Run **`main`'s copy** of
   `tools/check_review_branch.sh <assigned head> review/<id>-codex` against the pushed branch. It checks **every commit** in
   the range, not just the final diff, so a disallowed file that is committed and then reverted
   still fails. It fails on:
   - an empty branch, or a branch that adds no `records/REVIEW-*.md` or `records/VERIFY-*.md`;
   - paths outside `reviews/`;
   - non-`.md` files;
   - symlinks, executables or submodules;
   - deletions or renames;
   - modified submitted records: a record is immutable from its first commit, so finish or
     amend it before committing;
   - merge commits.

   **A pass is a content-scope constraint, not reviewer authentication, and not assignment
   verification.** The owner also reads the diff. CI takes the checking policy
   (`tools/review_gate.py`, `tools/check_review_branch.sh`) from the trusted event base commit
   with `git show`, under `pull_request_target`, so a reviewer PR cannot weaken its own check;
   the PR's commits are read as data and never executed.

4a. **Assignment verification** (owner, before receipt). Confirm that the record matches the
   authoritative assignment: run `tools/check_review_assignment.py --review-id … --base …
   --head … --branch … --assignment-source "…" [--scope-terms …]` with the values **from the
   assignment source**, not from the record or the PR, and read the record's scope statement
   against the assigned scope. It fails if the record's id, base, head or branch differ, if its
   `assignment` field is missing or differs from the expected source, or if the branch does not
   descend from the assigned head. A branch can pass
   step 4 while reviewing the wrong head; only 4a catches that.
5. **Receipt by byte-identical import** (Claude or the owner; routine, not acceptance). Run it in
   a scratch clone, never in a reviewer's worktree. Every step is idempotent and re-checks the state
   it depends on. Stop and report on any failure.

   **5.0 Inputs the receiver must hold first.** If any is absent or withheld, the receiver
   **reports it as absent** and stops. It never substitutes the record's own statements.
   1. The **owner-authored assignment source**, cited by location: a file in `docs/history/` holding
      the owner's assignment text verbatim, an *Assigned reviews* row committed by the owner, or an
      owner PR comment. The expected review id, repository, full base and head SHAs, scope, branch
      and any delivery exception are taken **from it**. The record's `assignment` field and the
      reviewer's branch are **never** the expected source.
   2. The **reviewer's independent report** (step 3): the branch tip SHA and the sha256 of every
      file the reviewer added, from the reviewer's own final message and relayed by the owner. It
      must come from somewhere other than the branch.
   3. A statement that the receiver looked for a **second owner-authored assignment** for the same
      target (step 1, conflicting channels), naming where it looked.

   **5.1 Resolve the tip.**
   - `T=$(git ls-remote origin refs/heads/review/<id>-codex | awk '{print $1}')`. `T` must be
     exactly one 40-character lowercase hex id. Stop on no line, on several lines, or on any other
     shape.
   - `git fetch origin refs/heads/review/<id>-codex`, then `git rev-parse FETCH_HEAD` must equal `T`.
   - `T` must equal the tip in the reviewer's report (5.0.2). If not, the branch moved after the
     report or the report is wrong: stop. The owner decides. Changed work needs a new assignment at
     a newly stated head.

   **5.2 Inventory, reconciled both ways.** List `git diff --name-status <head> T`. Allowed: `A`
   under `reviews/records/`, `reviews/handoffs/` or `reviews/reports/`, and `M reviews/README.md`.
   Anything else: stop. Then reconcile with the reviewer's report: every reported file exists at `T`
   with the reported sha256, **and** no file exists at `T` that was not reported. Record the
   inventory (expected, found, missing, extra) in the receipt's OD. A missing or extra file is a
   stop, never a note.

   **5.3 Checks.** Scope: `main`'s copy of `tools/check_review_branch.sh <head> T`. Assignment:
   `tools/check_review_assignment.py` with the values from 5.0.1. Both must pass.

   **5.4 Publish and verify the provenance tag first.**
   - Create the annotated tag `reviews/<id>` at `T`, push it, and verify that
     `git ls-remote origin 'refs/tags/reviews/<id>^{}'` returns exactly `T`.
   - If the tag already exists, it must peel to `T`; otherwise stop. A tag is never moved or deleted.
   - Nothing has been imported yet, so a tag without a receipt is harmless and recoverable.

   **5.5 Import.** On `receipt/<id>` cut at the current `main`: `git checkout T -- <each added
   file>`. For `reviews/README.md`, apply `git diff <head> T -- reviews/README.md`. Stop if it does not
   apply cleanly.

   **5.6 Index-row semantics.** The staged `reviews/README.md` may differ from `main`'s only by lines
   of these two classes. Each is checked against the **imported immutable records**: the receiver
   reads the record, not the row.
   - **Class N (navigation).** A new row for the imported record itself (assigned-review or
     received-review row), whose id, base, head, record path and verdict equal the record's front
     matter, and whose assignment cell matches 5.0.1. Or a new finding row for a finding that the
     imported **review** record defines: the same id and severity, and the state `open`.
   - **Class S (state transition).** The rewrite of an existing finding row. It is allowed only when
     the imported record is a **verification** (`VERIFY-*`) of that finding at its reviewed head,
     and states that finding's outcome. The row's id, review, severity and remediation-claim cells
     are unchanged. The state cell begins with the state word the record states (`verified_closed`,
     `remediation_rejected` or `open`), and any further text is traceable to the record.

   **Refuse and stop** on any of these:
   - a duplicate id: a first-column id appearing twice in one table, or a finding id appearing twice
     anywhere in the file;
   - `verified_closed`, `waived` or `accepted` that no imported record supports. A waiver exists
     only as an owner OD, which the receiver may cite and never creates;
   - a state transition with no verifying record;
   - a removed or changed line that is not the superseded version of a Class S row;
   - any other change.

   Where the reviewer's own `README` diff fails this check, the receiver does not apply it, and
   reports the discrepancy to the owner.

   **5.7 Verify.** Each imported file's blob id (`git rev-parse :<path>`) equals
   `git rev-parse T:<path>`; nothing outside `reviews/` is staged; `tools/check_repo.py` passes; and
   5.6 passes. Once the 5.8 commit exists and before the 5.9 recheck, run
   `uv run python tools/check_repo.py trailers origin/main HEAD`: it must pass. (The local hook does
   not check trailers; CI does. If it fails, stop and fix the **unpublished** import commit.)

   **5.8 Commit the pure import**, with the trailers:
   - `Review-Id`, `Review-Branch`, `Review-Commit: <T>`, `Reviewed-Base`, `Reviewed-Head`;
   - `Assignment-Source`: the location in 5.0.1, never the record's field;
   - `Reviewer-Report`: how it was supplied;
   - one `Record: <path> blob <id> sha256 <hex>` per imported file;
   - `Inventory: complete` and `Receipt-Checks`;
   - `HIO-Actor: <role> (evidence receipt, OD-NNNN)`, as CI requires on every non-merge commit
     (`tools/check_repo.py trailers`); and `Co-Authored-By` when the receiver is an agent.

   Keep it pure: no status cell, `STATUS.md` or OD change in this commit. The merge commit of 5.9
   and any administrative commit that follows carry the same `HIO-Actor` trailer by the same rule
   (merge commits are exempt in CI, but carry it for consistency).

   **5.9 Final remote recheck, then merge and publish.** Immediately before merging, re-run the
   `ls-remote` of 5.1 and of the tag. The branch tip must still equal `T` and the reported tip, and
   the tag must still peel to `T`. If the branch moved, **do not merge**: leave the tag, report, and
   let the owner decide. Otherwise merge `--no-ff` into `main` as `Merge receipt/<id>: receive <id>
   evidence (receipt only)`, and push `main`.

   **5.10 Complete only when verified.** After the push, verify that remote `main` equals the local
   merge, that the blobs on `main` equal `T`'s, and that the remote tag peels to `T`. Only then write
   "received" in the index and report completion. Until then the status word is **"receipt
   incomplete"**, and the receiver reports it to the owner by name. A partial receipt is never
   presented as complete.

   **Report CI as a separate, mandatory result.** After the push, the receiver reports the CI
   conclusion (run id and head SHA) for every commit pushed, in a section separate from the
   evidence-integrity result. *Evidence-integrity checks* (5.1 to 5.10: tip, tag, inventory, blobs,
   tree) decide whether the receipt is complete. *CI integration checks* (workflow results) are
   reported alongside: a CI failure does not by itself change a verified receipt, and a green run does
   not substitute for those checks. A failed run is never rewritten away: published history and its
   run stay on record, and a later green run is reported as a separate run, never as a repair.

   **5.11 Recovery from a partial operation.** Restart at 5.1 each time. The steps check state before
   acting.

   | State found | Action |
   |---|---|
   | checks failed, nothing pushed | stop and report; nothing has changed |
   | tag pushed, no import | harmless. Resume at 5.5 with the same `T`, or abandon with a note in the OD. Never delete or move the tag |
   | tag push failed or rejected | nothing else was done; retry. If the tag exists at a different commit, stop: a mismatch for the owner |
   | import committed, not merged | re-verify 5.9, then merge; or discard `receipt/<id>` (disposable: the reviewer's evidence is untouched) |
   | merged locally, push of `main` failed | re-verify 5.9, then push. The status stays "receipt incomplete" |
   | `main` pushed, tag missing (an outside action removed it) | recreate the exact tag at `T`, verify, and record in the OD that the receipt was incomplete until then |
   | reviewer branch moved or deleted after the tag | `T` stays pinned by the tag and by the blobs on `main`; report it and take no other action |

   **Accountability, not mechanism.** The author of the work may be the receiver (Claude receives
   Codex's review of Claude's proposal). **Blob identity detects substitution when the comparison
   runs.** It does not authenticate the reviewer, discover conflicting owner instructions, or make
   the receiver import an adverse record. So **timely receipt and completeness depend on procedural
   accountability**, which these rules make visible to the owner:
   - the owner holds the reviewer's report (5.0.2) and can compare it with the receipt;
   - a **receipt sweep**: at the start and end of every session that touches reviews, and in every
     completion report, the receiver lists `git ls-remote origin 'refs/heads/review/*'` and reports
     every branch whose tip is not recorded as received or dispositioned, so that silence is
     visible;
   - the receiver reports adverse verdicts and open findings first, with the record path, and never
     describes findings as resolved;
   - absent or withheld evidence is reported, not inferred.

   These do not make an author-receiver independent. Where the owner wants independence, the owner
   or a different agent performs the receipt.

   **A receipt means the evidence has been received.** It does not mean that the conclusions are
   accepted, that defects are fixed, that an ADR is approved, that a slice is authorised, or that the
   work under review is integrated or accepted. Those remain separate owner actions (§1.1).

   **Stop conditions:**
   - the tip changed (5.1 or 5.9);
   - a 5.0 input is absent;
   - a scope or assignment check failed;
   - an inventory mismatch, a missing or extra file, or any file outside the allowed set;
   - a `README` hunk that does not apply or fails 5.6;
   - any blob id differs;
   - `check_repo` failed;
   - the reviewed head differs from the assignment;
   - a tag that exists at a different commit.
6. **Remediation** (Claude, on the work's own author branch, submitted at a new fixed `Submission-Head` per step 0, which
   Claude states in the author PR or a comment on it. Claude starts only from a prompt naming the
   receipt commit, reads the record from `main`, and stops if that commit is not in `main` or if
   the record's blob differs from the tag `reviews/<id>`.). Claude starts only from a prompt naming the receipt commit, and stops if that commit
   is not in `main`.

   **Exception: remediation before receipt** (only by an explicit owner instruction, recorded in
   an OD). It applies where immutable review evidence exists at a verified commit but cannot be
   received normally (for example, the receipt merge is blocked). The instruction names the
   review id, the commit holding the record, and the sha256 of each record file. Claude reads the
   record only with `git show <commit>:<path>`, checks the hashes before relying on it, and cites
   commit and hashes in the remediation response. The record must still be received, or its
   disposition recorded by the owner, before verification of the remediation is assigned. The
   exception never applies by inference, and never to a review branch whose steps 4–4a have not
   passed. There are two SHAs:
   - commit the fix: these are the **fix commit(s)**;
   - then commit the remediation response (`reviews/responses/`) and the *Remediation claim*
     cell: this is the **submission head**. The response names the fix commits; the index cell
     and the handoff name the submission head, because a file cannot name the commit that adds
     it.
7. **Verification** (reviewer). The owner assigns the **submission head**, so the fix and
   Claude's evidence are seen at one fixed revision. The reviewer uses a fresh worktree and
   branch there, and adds a verification record. Steps 3–5 apply again.

8. **Evidence citations** (both). A claim about a build cites the exact CI run id, attempt and
   head SHA (for example `run 40044606055, attempt 1, 98e6a8e…`). The reviewer still reproduces
   independently and writes its own counterexamples; CI is shared evidence, not a substitute
   for review.
9. **Completion block** (every handoff and every agent's final message). State:
   - branch and full SHA;
   - pushed (yes/no) and PR link;
   - received into `main` (receipt commit, or "not received");
   - the next actor (owner, author or reviewer);
   - a ready prompt for that actor whose **prerequisites are explicit** (for example "stop if
     commit X is not in `main`"). If a prerequisite is not met, the agent stops and reports;
     it does not assume the step happened.

   After receipt, the owner or Claude updates `STATUS.md`; the reviewer never does.

**Index.** The records are the source of truth. `reviews/README.md` is a manually maintained
navigation summary. If the two disagree, the record wins. Generating the index from record
metadata is a later option, not built now.

**Transition note.** The first A01 review (`bada952`) was committed directly on the staging
branch, before this protocol existed. It also changed `hio/STATUS.md` and added
`hio/handoffs/2026-10-18-a01-independent-review.md`. The scope check correctly fails on it. It
is accepted as pre-protocol history, not as a precedent.

**Hosted evolution** (harness-0.7 built the first two; the CI gate is subject to the adoption condition): PRs at exact heads, and the scope check
in CI. Still not built: authenticated reviewer accounts, branch protection with required checks,
and signed owner acceptance and waiver records.

### 6.3 Open-decisions queue (harness-0.7)

[`docs/decisions/open-decisions.md`](../decisions/open-decisions.md) lists every question that
needs an owner or solution-architect decision, whether it comes from a review finding, an
evidence package or a research note. Each entry links its source, gives the options and a
recommendation, and later names the OD record that decided it. **The queue grants no
authority** and is navigation only, like STATUS. `pending-owner-decisions.md` stays as the
resolved G1 history.

## 7. Artefact-driven collaboration

- Prefer committed Markdown, YAML or JSON over chat summaries.
- Every handoff and review cites:
  - the exact `git` revision;
  - artefact and release ids and hashes;
  - assumptions;
  - unresolved questions.
- Templates: [`../../templates/`](../../templates/).
- Worked example: [`worked-example.md`](worked-example.md).

## 8. Long-term maintainability

- **Front matter on every canonical file:** `id`, `status`, `owner`, `version`,
  `last_reviewed`, `supersedes` / `superseded_by`.
- **Retiring guidance.** Set `status: superseded`, link the replacement, and move the file to
  `docs/history/` in the next harness review. Never delete rationale.
- **Dated blockers.** Any "blocked, impossible or unclassified" claim carries `as_of` and
  `reverify_by` (default 90 days). Expired claims surface in the quarterly harness review.
- **Quarterly harness review** (a task card each quarter):
  - check STATUS length and accuracy;
  - check stale `last_reviewed` (>180 days for current documents);
  - check broken links;
  - check duplicated content;
  - check expired blockers;
  - evaluate the architecture triggers;
  - consider whether any harness element is unused and should go.
- **Harness version** in `AGENTS.md` (`harness-0.x`). A change follows §6.
- **CI, from S1:**
  - link check;
  - front-matter schema;
  - YAML schemas for specs and registers;
  - a STATUS line-count limit;
  - the import-rule check;
  - a "no secret patterns" check;
  - an `HIO-Actor` trailer on every commit touching `hio/` (metadata hygiene only; not proof).

### 8.1 Migration continuity (`macsmsf/hio/` → the standalone `hio` repository)

**Status: performed 2026-10-24** (OD-0017; evidence in `MIGRATION-MAP.md`). The A01 ADRs, standards and this harness are approved (OD-0008, OD-0011, OD-0012); migration changes no approval state (item 5). This is
the checklist for when migration is authorised (an OD record under HIO-ADR-0001).

1. **Preserve provenance.** Migrate with history, using `git subtree split --prefix=hio` or an
   equivalent. Record the source repository, branch and final source commit in the migration
   OD record.
2. **Path map.** Commit `MIGRATION-MAP.md` in the new repository. It lists every old path →
   new path, plus the source commit. Every relative link must still resolve; this is checked by
   the link check.
3. **Preserve ids and states.** Every ADR, OD, task, finding, review, hypothesis and experiment
   id, and its status and supersession links, is identical before and after. A continuity check
   lists the ids and states on both sides and must report no differences.
4. **Carry open and waived review state.** All review records, open and `waived` findings, and
   the evidence they reference move. Commit ids referring to `macsmsf` history are kept
   verbatim, qualified with the source repository name.
5. **Approval state is unchanged.** Migration never approves, authorises or closes anything. An
   approval that cited a `macsmsf` revision remains valid only for that content. The continuity
   check compares content hashes of approved documents before and after.
6. **Update `STATUS.md`** with the canonical new location **only once migration has actually
   happened**. Replace `macsmsf/hio/` with a pointer file, in a separate `macsmsf` commit.
7. **Reject the migration** if any finding is stranded, any approval state changes, or any
   reference breaks.

## 9. Minimum viable harness and deferred behaviours

**Minimum viable harness (S1):**
1. `AGENTS.md` + `CLAUDE.md` import; `README.md` index; `STATUS.md`.
2. Decision register + ADR template; owner decision records (`docs/decisions/owner/`) + template.
3. Task-card and handoff templates; `registers/tasks/`; `handoffs/`.
4. Hypothesis and experiment registers (schema + seeds).
5. Sources register with the rights model.
6. Two scoped skills (`hio-session`, `hio-return-accounting`).
7. Review-record template; the review index (`reviews/README.md`); `HIO-Actor` role trailers (metadata).
8. CI documentation checks (§8). These are delivered **with** S1 code, because no CI exists
   while staged.
9. The cold-start tests (§10): run for harness-0.2 as an owner exercise; an S1 acceptance criterion.

**Deferred** (each with an adoption criterion):

| Behaviour | Adopt when |
|---|---|
| Autonomous data-quality triage agent | ≥3 sources in capture, and >2 quarantine events a month |
| Agent-generated hypotheses at scale | the walk-forward harness exists (Y4 track), and the hypothesis register has the variant accounting proven |
| A rights-enforcing data-access tool for agents | the first licensed source with `agent_context ≠ allow` arrives |
| Automated review-bundle assembly | ≥2 independent reviews per month |
| Multi-agent orchestration | never by default; only through an ADR with measured benefit |

## 10. Cold-start (fresh-agent) tests

Run these at harness changes and at the end of each slice. Keep the record in `reviews/records/`
as a harness review.

**Setup.**
- Two fresh sessions with no prior chat history, given access to the repository at revision X
  only.
- No summary or coaching. Each gets only the neutral instruction for its role, below.

**Claude prompt:**

> You are starting a fresh session in this repository. Work only from version-controlled files.
> Follow `hio/AGENTS.md` for the role "implementation/documentation agent". Answer with a
> repository path and commit id for every claim:
> 1. Where do authoritative owner decisions live?
> 2. Which HIO ADRs are proposed and which are approved?
> 3. Is HIO-S1 authorised?
> 4. What documentation scope are you currently permitted to change?
> 5. What findings are open, and what is the next handoff or action?
> 6. What is the HIO/SMSF ownership boundary?

**Codex prompt** (the same text in both states):

> You are starting a fresh session in this repository. Work only from version-controlled files
> and any owner assignment you have been given. Follow `hio/AGENTS.md` for the role
> "independent reviewer". Answer with a repository path and commit id for every claim:
> 1. What is your independence relative to the author?
> 2. Has a review target been assigned to you? If so, give the repository, base SHA, head SHA,
>    task and scope.
> 3. Which approved specifications and acceptance criteria govern it?
> 4. How do you independently find open findings and their evidence?
> 5. How do you verify a remediation without the author closing it?
> 6. Who can grant waivers?
> 7. What standing does the author's completion report have?

**Expected answers, by state:**
- **Before the owner assigns a review:** Q2 is **"No review target has been assigned."** A
  session that names a candidate row, a branch tip or the author's proposed head **fails**.
- **After an assignment:** Q2 matches the owner assignment exactly. The session also lists the
  relevant ADRs, the open findings and the required evidence, from records rather than from the
  author's report.

**Pass** requires all of:
- **no false approval or authorisation claim**;
- no missed open finding;
- the correct next action;
- a path and commit for every answer;
- no reliance on chat memory.

The owner grades against the known baseline. A failure produces the **smallest** instruction
fix, recorded in the harness changelog, not a better prompt.

**Slice add-on.** At the end of each implementation slice, the Claude session also reproduces a
named release hash.

**Dry runs.** A run that uses the same vendor's sub-agent as a proxy for Codex, or that is
otherwise not genuinely independent, is labelled **unverified dry run**. It is useful
preparation. It does not satisfy the test.

**Validating independence** requires an actual fresh Codex session, on a fixed revision, run by
the owner. Until then the test status is **pending**.

## 11. Security and licences

- **Least privilege:**
  - reviewers get read-only credentials, or none;
  - implementation sessions get development credentials only;
  - production write keys exist only in the CI secret store and owner custody.
- Secrets never appear in prompts, files, logs, handoffs or review bundles. A CI secret-pattern
  check runs from S1.
- **Licences apply to agent contexts and external services** (the rights standard §3–4).
- **No research data crosses the HIO/SMSF boundary automatically.** Only pinned, approved
  artefacts cross, under HIO-ADR-0002.

## 12. Efficiency

| Durable (committed) | Ephemeral (not committed) |
|---|---|
| ADRs, standards, specs, registers, STATUS, task cards, handoffs, review records | scratch analysis, intermediate notebooks, transcripts, agent working notes |

Ephemeral work lives in the session's scratch space. Anything worth keeping is distilled into
a handoff or register entry.

**Context budget:** about 25k tokens for bootstrap, 40k as a hard target before work starts. If
the bootstrap set grows past that, the harness review splits or summarises documents.

**Operator burden:**
- the harness must save more owner time than it costs;
- the quarterly review asks this explicitly;
- the toil target is in [`../architecture.md`](../architecture.md#7-observability-recoverability-and-toil).
