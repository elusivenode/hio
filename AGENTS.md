---
id: HIO-AGENTS
title: Agent and collaborator onboarding
status: current
owner: HIO architecture lead (owner)
version: harness-0.2
last_reviewed: 2026-10-18
---

# AGENTS.md: start here (any agent, any model, any human)

This file is the **only** thing you must read before choosing what else to read. It points to
canonical documents and does not restate them. The detailed procedures are in
[`docs/harness/operating-model.md`](docs/harness/operating-model.md).

## What HIO is, in five lines

- HIO (Home Investment Office) is an **independent investment research and
  portfolio-construction system** with a five-year horizon.
- It builds point-in-time market observations, investable factor returns, risk and
  expected-return models, and exposure-space portfolio analysis.
- It publishes **versioned artefacts** to consumers. The MacDonald Family SMSF (`macsmsf`) is
  one consumer, not the design centre.
- HIO **never** writes SMSF accounting truth and **never** holds investment authority. SMSF
  trustees decide for the SMSF.
- Full statement: [`docs/charter.md`](docs/charter.md).

## Authority rules (read before acting)

1. **Git state is not approval.** A commit, branch or merge makes a document *available*, not
   *approved*. A `proposed` ADR stays proposed until an **owner decision record** approves that
   exact revision.
2. **Owner decision records** in [`docs/decisions/owner/`](docs/decisions/owner/) are the only
   durable form of owner approval, rejection, authorisation or waiver.
   - Decisions given in chat or meetings are **pending transcription** until recorded there,
     with source, date, scope and revision.
   - An agent may *draft* a record. It may not attest that the owner approved it.
3. **What governs:**
   - **Governs:** approved decisions and approved standards and specs.
   - **Recommendations only:** proposed ADRs and plans.
   - **Limits execution:** task cards, to work that is authorised.
   - **Navigation only:** `STATUS.md`.
   - **Historical context only:** handoffs and chat.

   The full order of precedence is in operating model §1.
4. **On conflict, stop.** If authoritative documents conflict, or a referenced approved revision
   is missing, stop and flag it. Do not resolve it, and do not prefer the newer file.
5. **Declare yourself.** Before acting, state your **role** and the **status** of the work: one
   of `proposed`, `authorised`, `in_review` or `approved`.

## Bootstrap (fresh session; about 25k tokens)

**Common path:**
1. This file.
2. [`STATUS.md`](STATUS.md).
3. Your task card in [`registers/tasks/`](registers/tasks/), and the owner decision record that
   authorised it.
4. The *approved* ADRs and standards that it governs, plus the relevant evidence.
5. The review index [`reviews/README.md`](reviews/README.md), for open findings.

Record `git rev-parse HEAD`.

**Then, by role:**
- **Implementation or documentation agent (Claude):**
  - identify your authorised scope, the files you may change, the governing approved decisions,
    the blocking open findings, the acceptance tests and the required handoff;
  - **a proposed ADR is not approved because you wrote it.**
- **Independent reviewer (Codex):**
  - identify the target commit or diff, the governing approved plan and contracts, the review
    scope, the open findings and your own test plan **first**;
  - only then read the author's handoff or completion note, **as an unverified claim**;
  - never edit the work under review.

Detail: operating model §2.

**Skills** (Claude Code; other agents read the files directly): `hio-session` and
`hio-return-accounting`.

## Boundaries you must respect

- **No dependency on `macsmsf`:** no import, no database, no credential, no reading its tables.
  - While staged inside the `macsmsf` repository, never modify files outside `hio/` unless your
    task card authorises it.
- **HIO-001** (the instrument master in `macsmsf`) is SMSF-owned. Do not modify it
  ([HIO-ADR-0003](docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md)).
- **Return mathematics** follows the
  [return accounting standard](docs/standards/return-accounting-and-factor-construction.md).
  A price-only or state series is never a return factor.
- **Data rights:** unknown means deny. Licensed data never enters an agent prompt, an external
  service or a published artefact unless its rights record allows it.
- **Secrets** never appear in files, prompts, logs or handoffs.

## Who may change what

| You are | You may | You may not |
|---|---|---|
| Any agent | read everything; write handoffs; draft ADRs, specs, hypotheses, task cards and owner decision records (as `proposed`) | approve, authorise, accept, waive or close anything; edit an approved standard or spec in place |
| Implementation agent (Claude) | change files within an **authorised** task card's scope; record a `remediation_claimed` on a finding | widen scope; edit a reviewer's verdict; close a finding |
| Independent reviewer (Codex) | open findings; verify or reject remediation claims; write review records | edit the work under review; grant waivers |
| Owner | approve, reject, authorise, accept, waive, supersede, through owner decision records | — |
| Strategic collaborators (e.g. ChatGPT) | advise and draft | instruct execution: advice becomes work only through an owner-authorised task card |

## Ending a session

Write a handoff from [`templates/handoff.md`](templates/handoff.md) into `handoffs/`. It must
state what was **not** approved. **The latest handoff is not a decision.**
