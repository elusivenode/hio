---
id: HIO-AGENTS
title: Agent and collaborator onboarding
status: current
owner: HIO architecture lead (owner)
version: harness-0.1
last_reviewed: 2026-10-18
---

# AGENTS.md: start here (any agent, any model, any human)

This file is the **only** thing you must read before choosing what else to read. It is
deliberately short. It points to canonical documents and does not restate them.

## What HIO is, in five lines

- HIO (Home Investment Office) is an **independent investment research and
  portfolio-construction system** with a five-year horizon.
- It builds point-in-time market observations, investable factor returns, risk and
  expected-return models, and exposure-space portfolio analysis.
- It publishes **versioned artefacts** to consumers. The MacDonald Family SMSF (`macsmsf`) is
  one consumer, not the design centre.
- HIO **never** writes SMSF accounting truth and **never** holds investment authority.
- Full statement: [`docs/charter.md`](docs/charter.md).

## Bootstrap (fresh session)

Context budget: aim for about 25k tokens before you start work.

1. Read this file, then [`STATUS.md`](STATUS.md). STATUS says what is under construction, what
   is verified, and the next approved work.
2. Read your **task card** in [`registers/tasks/`](registers/tasks/). If you have none, you may
   only read, propose, or write a draft task card for the owner.
3. Read only the ADRs and standards your task card links. Do not bulk-load `docs/`.
4. Read the latest file in [`handoffs/`](handoffs/) that names your task.
5. Record the repository revision you started from (`git rev-parse HEAD`). Every output you
   produce cites it.

**Skills** (Claude Code; other agents read the same files directly):
- `hio-session`: the bootstrap and handoff procedure;
- `hio-return-accounting`: required before any return, index or factor work.

## Precedence: when documents disagree

1. **Owner approval records**: an ADR with `status: approved`, or an approval entry in a review
   record.
2. **Approved standards** (`docs/standards/*`, by version).
3. **Approved specifications** (`specs/**`, by version).
4. **Charter, architecture, roadmap, implementation plan.**
5. **`STATUS.md` and task cards.**
6. **Handoffs.**
7. **Anything else**: chat transcripts, model memory, external notes. These are never
   authoritative.

A conflict is a defect.
- Do not resolve it silently.
- Record it in your handoff, and fix the lower-precedence document if your task permits.
- Otherwise raise it to the owner.

A document with `status: proposed` or `draft` is **not policy**, however confident it sounds.

## Boundaries you must respect

- **No dependency on `macsmsf`:** no import, no database connection, no credential, no reading
  its tables.
  - The future interface is a consumed projection artefact
    ([HIO-ADR-0002](docs/decisions/HIO-ADR-0002-systems-of-record-and-smsf-boundary.md)).
  - While staged inside the `macsmsf` repository, never modify files outside `hio/` unless your
    task card explicitly authorises it.
- **HIO-001** (the instrument master in `macsmsf`) is SMSF-owned. Do not modify it. See
  [HIO-ADR-0003](docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md).
- **Return mathematics** follows the
  [return accounting standard](docs/standards/return-accounting-and-factor-construction.md).
  A price-only or state series is never a return factor.
- **Data rights:** unknown means deny. Licensed data never enters an agent prompt, an external
  service or a published artefact unless its rights record allows it
  ([rights standard](docs/standards/rights-and-licensing.md)).
- **Secrets** never appear in files, prompts, logs or handoffs.

## What you may change

| You are | You may | You may not |
|---|---|---|
| Any agent | read everything in `hio/`; write handoffs; propose (draft) ADRs, specs, hypotheses and task cards | set any `approved`, `validated` or `approved_for_consumer` status; edit an approved standard or spec in place |
| Implementation engineer | change code and tests within an approved task card's scope | widen scope; change a spec's numbers without a new spec version |
| Independent reviewer | write review records | edit the work under review |
| Owner | approve, reject, supersede | — |

Roles and the full change-control table: [`docs/harness/operating-model.md`](docs/harness/operating-model.md).

## Ending a session

Write a handoff from [`templates/handoff.md`](templates/handoff.md) into `handoffs/`. It must
include:
- the start and end revisions;
- artefact ids;
- what was verified (and how);
- assumptions;
- open questions;
- the next step.

If it is not in the repository, the next agent does not know it.
