---
id: HIO-ADR-0005
title: Multi-dimensional rights model; default deny
status: approved
approved_by: OD-0008   # at a82aa0d, blob 2e223877d9b7
owner: HIO architecture lead (owner)
date: 2026-10-18
gates: [any publication, any vendor contract, agent use of datasets]
review_record: null
supersedes_proposal: "18 Oct proposal AD-6 (single ordered licence_class)"
---

# HIO-ADR-0005: multi-dimensional rights model, default deny

## Context

- A single ordered `licence_class` cannot express real terms.
- A source may allow internal computation but not raw retention after termination. It may allow
  derived indices but not quotation of raw values. It may forbid transmission to third-party
  services, which includes LLM providers used by agents.

## Decision (proposed)

Each source and each dataset carries a **rights record** with independent permissions:
- `automated_retrieval`;
- `raw_retention`;
- `internal_compute`;
- `derivation`;
- `derived_storage`;
- `post_termination_raw` and `post_termination_derived`;
- `distribution` (per consumer class);
- `quotation_in_documents`;
- `agent_context`;
- `external_processing`;
- `audit_retention`;
- `attribution_required`.

Each permission takes a value in `allow | deny | conditional(<condition>) | unknown`.

The record also carries `verification` ∈ {`unverified`, `vendor_asserted`,
`owner_verified(<terms doc, date, section>)`, `contract(<ref>)`}.

**Rules:**
1. `unknown` behaves as `deny`.
2. A derived dataset's permission, per dimension, is the most restrictive of its inputs, unless
   an input's terms explicitly grant derived rights. Such a grant is recorded with evidence.
3. **Every operation is gated, not only publication.** Fetch, store raw, build, store derived,
   rebuild, publish, agent use, terminate and audit-retain each require specific permissions
   (the rights standard §3 matrix). Each job checks them before acting, for every input, and
   fails closed. Verification must be `owner_verified` or `contract`.
4. Agent and external-service use requires `agent_context` / `external_processing` = `allow`.
   Otherwise agents work on metadata, schemas and synthetic samples only.
5. S1 carries a fail-closed fixture for each operation it performs.

Full model: the [rights standard](../standards/rights-and-licensing.md).

## Consequences

- Even public official sources (RBA, US Treasury, NY Fed) start as `unverified` and are
  verified in T-0002 before any S1 operation on them (live fetch included).
- Agent use is procedurally enforced in S1. Technical enforcement (a dataset-access tool that
  checks rights) is deferred.

## Changelog

- 2026-10-18: created (85ef0fa).
- 2026-10-18: `automated_retrieval` added; every operation is gated (T-0008, F-REVIEW-2026-10-18-a01-5). Status unchanged: proposed.

## Approval

**Approved** by [OD-0008](owner/OD-0008-g1-decisions-a82aa0d.md) (owner, 2026-10-18), as this file stood at commit `a82aa0d` (blob `2e223877d9b7`). Edits after that commit record status only.
