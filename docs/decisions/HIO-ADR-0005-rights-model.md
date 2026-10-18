---
id: HIO-ADR-0005
title: Multi-dimensional rights model; default deny
status: proposed
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
3. The publication gate refuses an artefact unless, for the target consumer class,
   `distribution` and (if numbers are quoted) `quotation_in_documents` are `allow`, and
   verification is `owner_verified` or `contract`.
4. Agent and external-service use requires `agent_context` / `external_processing` = `allow`.
   Otherwise agents work on metadata, schemas and synthetic samples only.

Full model: the [rights standard](../standards/rights-and-licensing.md).

## Consequences

- Even public official sources (RBA, US Treasury, NY Fed) start as `unverified` and are
  verified in T-0002 before S1 publication.
- Agent use is procedurally enforced in S1. Technical enforcement (a dataset-access tool that
  checks rights) is deferred.

## Approval

_Unapproved._
