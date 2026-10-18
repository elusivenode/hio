---
id: HIO-DECISIONS
title: Architecture decision register
status: current
owner: HIO architecture lead (owner)
last_reviewed: 2026-10-18
---

# HIO architecture decision register

**Status values:**

| Status | Meaning |
|---|---|
| `draft` | being written |
| `proposed` | complete, awaiting owner decision; **not policy** |
| `approved` | owner-approved; policy |
| `rejected` | considered and refused |
| `superseded` | replaced; links to its replacement |
| `deferred` | deliberately not decided yet, with a revisit trigger |

Only the owner sets `approved`, `rejected` or `superseded`, and only through an **owner
decision record** ([`owner/`](owner/)) that cites the ADR's exact revision. The ADR's
*Approval* section then references that OD id. A commit or merge never approves anything. An
agent may draft and propose ADRs and OD records; it may not approve them.

## Register

| ID | Title | Status | Owner | Gates |
|---|---|---|---|---|
| [HIO-ADR-0001](HIO-ADR-0001-separate-system-modular-monolith.md) | HIO is a separate system; modular monolith with independently runnable workloads | **approved** (OD-0008, at `a82aa0d`) | owner | creation of the `hio` repository |
| [HIO-ADR-0002](HIO-ADR-0002-systems-of-record-and-smsf-boundary.md) | Systems of record and the SMSF boundary | **approved** (OD-0008, at `a82aa0d`) | owner | any SMSF integration |
| [HIO-ADR-0003](HIO-ADR-0003-instrument-identity-boundary.md) | Instrument identity boundary and HIO-001 | **approved** (OD-0008, at `a82aa0d`) | owner (SMSF and HIO) | HIO-001 activation; the HIO reference context |
| [HIO-ADR-0004](HIO-ADR-0004-temporal-semantics.md) | Temporal semantics: knowable versus captured | **approved** (OD-0008, at `a82aa0d`) | owner | S1 |
| [HIO-ADR-0005](HIO-ADR-0005-rights-model.md) | Multi-dimensional rights model; default deny | **approved** (OD-0008, at `a82aa0d`) | owner | S1 publication; any vendor contract |
| [HIO-ADR-0006](HIO-ADR-0006-releases-artefacts-publication.md) | Immutable releases, artefact envelope, status lifecycle, pinning | **approved** (OD-0008, at `a82aa0d`) | owner | S1 |
| [HIO-ADR-0007](HIO-ADR-0007-return-accounting-standard.md) | Adopt the return accounting and factor construction standard as a CI-enforced gate | **approved** (OD-0008, at `a82aa0d`) | owner | any factor release |
| [HIO-ADR-0008](HIO-ADR-0008-canonical-knowledge-and-harness.md) | Canonical knowledge, precedence and agentic harness | **approved** (OD-0008, at `a82aa0d`) | owner | all work |
| [HIO-ADR-0009](HIO-ADR-0009-catalogue-from-manifests.md) | Catalogue derived from immutable manifests; no hosted database initially | **approved** (OD-0008, at `a82aa0d`) | owner | S1 |
| [HIO-ADR-0010](HIO-ADR-0010-first-slice-scope.md) | The first slice in two stages: S1a synthetic-fixture-only, then S1b live data (revision 3) | **approved** rev 3 (OD-0011, at `760f73e`) | owner | S1 |

### G1 decision package

[`G1-decision-package.md`](G1-decision-package.md): every A01 item pinned at `a82aa0d`, with the evidence, the conditions and the ordered owner decisions. It is a decision aid, not a decision.

### Owner decision records

See [`owner/README.md`](owner/README.md). [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) approves HIO-ADR-0001 to 0009 at `a82aa0d`. [OD-0011](owner/OD-0011-approve-adr-0010-rev3.md) approves HIO-ADR-0010 revision 3 at `760f73e`. **G1 is complete. S1a is not authorised.**

### Deferred decisions (revisit triggers in [`../architecture.md`](../architecture.md#5-measurable-evolution-triggers))

- workflow orchestrator;
- hosted catalogue;
- lakehouse table format;
- artefact API;
- event bus;
- multi-tenant authorisation;
- cloud re-platforming;
- paid futures data contract (after the PoC);
- PIT equity fundamentals.

### Decisions owned elsewhere (referenced, not owned by HIO)

| Decision | Owner | Location |
|---|---|---|
| SMSF investment objective convention | SMSF trustees | `macsmsf` `docs/investment-process-roadmap.md` |
| HIO-001 activation and any amendment to ADR 0003 | owner, under the SMSF preservation principle | `macsmsf` `docs/adr/0003-*`, `docs/hio-001-review-record.md` |
| SMSF backup and promotion procedure (A17) | owner, SMSF programme | `macsmsf` `docs/adr/0004-*` |

## Process

1. Draft from [`template.md`](template.md), with `status: draft`.
2. Set `proposed` when it is complete: context, options, decision, consequences, rollback or
   exit, and the evidence required.
3. An independent review (Codex or a human) is required for ADRs that gate implementation. Its
   record is linked in the ADR.
4. The owner records approval or rejection in an OD record (`owner/OD-*.md`) citing the ADR
   path and commit. The ADR's *Approval* section and front-matter status are then updated to
   reference it.
5. An approved ADR is never edited in substance. Change means a new ADR that supersedes it.
   Typo-level edits are allowed, with a changelog line.
