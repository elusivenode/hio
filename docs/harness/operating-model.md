---
id: HIO-HARNESS
title: Agentic operating model and harness specification
status: proposed
owner: HIO architecture lead (owner)
version: harness-0.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0008
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

**Precedence** (also in `AGENTS.md`): owner approvals > approved standards > approved specs >
charter, architecture, roadmap and plan > STATUS and task cards > handoffs > everything else.

**Conflict resolution:**
- the higher-precedence document wins;
- the conflict is recorded in the session handoff;
- the lower document is corrected in the same change if the task permits; otherwise a task card
  is raised.

`proposed` is never policy.

## 2. Repository navigation and onboarding

- **Bootstrap read set (≈25k tokens):**
  - `AGENTS.md`;
  - `STATUS.md`;
  - the task card;
  - its linked ADRs and standards sections;
  - the latest relevant handoff.
- **Never bulk-load `docs/`.** Skills point to sections, not whole documents.
- **Skills (scoped):**
  - `hio-session`: the bootstrap and handoff procedure;
  - `hio-return-accounting`: a pointer to the standard plus its invariant list.

  New skills are added only when a repeated task has a stable procedure. Each has a trigger
  description.

## 3. Task cards and session handoffs

- **Task card** ([`../../templates/task-card.md`](../../templates/task-card.md)):
  - id, objective, approved scope, non-goals;
  - linked ADRs and specs, dependencies;
  - acceptance tests, environment constraints, rights constraints;
  - evidence required, open issues;
  - owner, assignee role, review status.

  A task card is `proposed` until the owner sets `approved`. **Implementation requires an
  approved card.**
- **Handoff** ([`../../templates/handoff.md`](../../templates/handoff.md)), written at the end
  of every session that changed anything:
  - start and end revisions;
  - tasks touched;
  - artefact and release ids;
  - what was verified, and how (commands, test ids);
  - what was *not* verified;
  - assumptions made;
  - open questions;
  - conflicts found;
  - the exact next step.

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
| **Owner / architecture lead** | the human owner | everything | approvals, rejections, priorities | approve ADRs, specs, task cards and status changes; hold credentials | — |
| **Architecture agent** | Claude (design session) | charter, ADRs, evidence | draft ADRs, plans, risk entries | propose | approve; change code |
| **Implementation engineer** | Claude (repository session) | an approved task card | code, tests, releases (`exploratory`), handoff | change code within scope; run jobs with dev credentials | widen scope; edit approved specs or standards in place; set `validated` or `approved` |
| **Quantitative researcher** | Claude or a human | specs, releases, hypotheses | spec drafts, pre-registrations, experiment results | register hypotheses; draft specs | mark its own results `validated`; promote to a consumer |
| **Data-quality investigator** | an agent (later) | quarantine queue, run records | triage notes, proposed releases or quarantines | propose | release quarantined data; alter receipts |
| **Independent reviewer** | Codex or a human | a review bundle (task card, diff, evidence, specs) | a review record with findings and a verdict | read; run tests | edit the work under review; approve it |

**Separation of duties.** For any `validated` or approved state, author ≠ reviewer ≠ approver.
The owner may be the approver, but is not also the sole reviewer of their own code.

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
  - a "no secret patterns" check.

## 9. Minimum viable harness and deferred behaviours

**Minimum viable harness (S1):**
1. `AGENTS.md` + `CLAUDE.md` import; `README.md` index; `STATUS.md`.
2. Decision register + ADR template.
3. Task-card and handoff templates; `registers/tasks/`; `handoffs/`.
4. Hypothesis and experiment registers (schema + seeds).
5. Sources register with the rights model.
6. Two scoped skills (`hio-session`, `hio-return-accounting`).
7. Review-record template.
8. CI documentation checks (§8). These are delivered **with** S1 code, because no CI exists
   while staged.
9. The fresh-agent reproduction test (§10) as an S1 acceptance criterion.

**Deferred** (each with an adoption criterion):

| Behaviour | Adopt when |
|---|---|
| Autonomous data-quality triage agent | ≥3 sources in capture, and >2 quarantine events a month |
| Agent-generated hypotheses at scale | the walk-forward harness exists (Y4 track), and the hypothesis register has the variant accounting proven |
| A rights-enforcing data-access tool for agents | the first licensed source with `agent_context ≠ allow` arrives |
| Automated review-bundle assembly | ≥2 independent reviews per month |
| Multi-agent orchestration | never by default; only through an ADR with measured benefit |

## 10. Fresh-agent reproduction test

The test is run at the end of each slice, and its record is kept with the slice's review.

1. Start a new session (a different model or vendor where practical) with **only** the
   repository at revision X, and this instruction: "Bootstrap per `AGENTS.md`; answer the seven
   design-goal questions with file references; then reproduce release R."
2. **Pass** when:
   - the answers match the canonical documents (owner-graded);
   - every answer cites a file;
   - the reproduced `content_hash` equals R's;
   - the session read no more than about 40k tokens before starting reproduction (self-reported
     plus the file list).
3. Any failure produces a harness fix, not a better prompt.

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
