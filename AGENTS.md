---
id: HIO-AGENTS
title: Agent and collaborator onboarding
status: current
approved_by: OD-0091   # harness-0.9a, Appendix A of docs/decisions/harness-0.9-proposal.md at 2df83b427896cf5ce413e8cee76f809a267687f6 (earlier: OD-0056, harness-0.7.1 C2 at 8461e99639f0ee7bc8cb9de2895d00d257d12974, blob 6eb9f76668149986c8a0fb0677b1e55218334719; OD-0021, harness-0.7 rev 3 at 9b58811, blob a2dc93d335105; before that OD-0008 at a82aa0d, blob 4000ab1895ee)
owner: HIO architecture lead (owner)
version: harness-0.9a
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

## Authority rules (read before acting; detail in operating model §1.1)

1. **Git state is not approval.** A commit, branch or merge makes a document available, not
   approved.
2. **An explicit owner instruction authorises bounded, reversible work immediately**, within
   its stated scope.
   - Record it promptly (source, scope, base revision) in an OD record in
     [`docs/decisions/owner/`](docs/decisions/owner/README.md). Transcription is an audit step,
     not a second gate.
   - Ambiguous instructions are not permission for consequential work: ask.
3. **Accepting work, approving an ADR, standard, spec, merge or promotion, and waiving a finding
   are separate explicit owner actions**, each tied to an exact revision. Completing a task
   approves nothing.
4. **Collaborator drafts (e.g. ChatGPT) are advice.** They become instructions only when the
   owner explicitly adopts them.
5. **This protocol is approved** (HIO-ADR-0008 and this file, by OD-0008 at `a82aa0d`). Later
   amendments are identified in the operating-model changelog.
6. **On conflict, or a missing approved revision: stop and flag.** State your **role** and the
   work's **status** (`proposed`, `authorised`, `in_review` or `approved`) before acting.

## Bootstrap (fresh session; about 25k tokens)

**Common path:**
1. This file.
2. [`STATUS.md`](STATUS.md).
3. Your task card in [`registers/tasks/`](registers/tasks/), and the recorded owner instruction
   behind it.
4. The *approved* ADRs and standards that govern it.
5. The review index [`reviews/README.md`](reviews/README.md).

Record `git rev-parse HEAD`.

**Then, by role** (detail in operating model §2):
- **Claude** (and other non-reviewer agents): after `STATUS.md`, read [`MAP.md`](MAP.md) and the
  newest handoff in your stream (`handoffs/<stream>/`). Before deriving anything non-trivial,
  `grep` [`knowledge/findings.md`](knowledge/findings.md) and say what you found; its Inbox lines
  are claims, not facts. Then identify your instructed scope, the files you may change, the
  blocking findings, the acceptance tests and the handoff you owe. A proposed ADR is not approved
  because you wrote it.
- **Codex (independent reviewer):** find your assignment in one owner-authored source: an
  *Assigned reviews* row in the review index, an owner comment on the author's PR, or a direct
  owner instruction (operating model §2.2; harness-0.7).
  - **If nothing is assigned, the answer is "No review target has been assigned."** Never infer
    a target from a candidate, a branch or the author's notes.
  - If something is assigned, fix your test plan from the assignment and the records **before**
    reading the author's handoff. Treat the handoff as unverified.
  - Work in your own worktree, on a review branch at the assigned head, and write only under
    `reviews/` (operating model §6.2). Push the branch and **open no PR**. In your final message,
    state the branch tip SHA, the reviewed head and the sha256 of every file you added: the receiver
    reconciles against that report. Never edit the work under review.

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
| Owner | instruct (authorise), accept, approve, waive, supersede. Each is an explicit action, recorded in an OD record | — |
| Strategic collaborators (e.g. ChatGPT) | advise and draft | instruct execution. A draft becomes an instruction only when the owner explicitly adopts it |

## Ending a session

- **Claude and other non-reviewer agents:** write a handoff from
  [`templates/handoff.md`](templates/handoff.md) into `handoffs/<stream>/`, add its *For the
  index* lines to the Inbox of `knowledge/findings.md`, and update `STATUS.md` if the current
  state changed.
- **Reviewer (Codex), on a review branch:** write your handoff into `reviews/handoffs/`. **Do
  not** touch `handoffs/` or `STATUS.md`. The owner or Claude updates STATUS after receipt
  (operating model §6.2).

Every handoff states what was **not** approved, and ends with the completion block (operating
model §6.2 step 9): branch and SHA, pushed or not, received into `main` or not, the next actor,
and a prompt with explicit prerequisites. **The latest handoff is not a decision.**
