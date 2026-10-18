---
id: HIO-STD-RIGHTS
title: Data rights and licensing
status: proposed
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0005
---

# Data rights and licensing (v0.1)

## 1. Rights record (per source; per dataset where terms differ)

Each permission takes the value `allow | deny | conditional(<text>) | unknown`. **`unknown`
means deny.**

| Permission | Question it answers |
|---|---|
| `raw_retention` | may we store the raw receipts, and for how long? |
| `internal_compute` | may we compute on the data internally? |
| `derivation` | may we create derived series (factors, models) from it? |
| `derived_storage` | may we store derived series indefinitely? |
| `post_termination_raw` / `post_termination_derived` | what may we keep if the subscription ends? |
| `distribution.<consumer_class>` | may artefacts containing or derived from it go to: `hio_internal`, `smsf_app`, `smsf_trustee_pack`, `smsf_auditor`, `third_party`? |
| `quotation_in_documents` | may raw or derived values be printed in documents (packs, minutes)? |
| `agent_context` | may the data, or samples of it, be placed in an LLM prompt or agent context processed by an external provider? |
| `external_processing` | may it be processed by external cloud services (hosting, CI runners)? |
| `audit_retention` | must or may we retain it for audit, and for how long? |
| `attribution_required` | required attribution text |

Verification fields:
- `verification`: `unverified | vendor_asserted | owner_verified | contract`;
- `evidence`: terms URL or document, retrieval date, section, and who verified it;
- `review_due`: the date the terms must be rechecked.

## 2. Propagation

- **Derived datasets.** Per permission, take the **most restrictive** value across inputs. The
  ordering is `deny < unknown < conditional < allow`; both `deny` and `unknown` block.
- **Override.** An override is allowed only where an input's terms explicitly grant derived
  rights. The override records the clause.
- **Conditional values** carry their conditions forward, concatenated.

## 3. Gates

| Gate | Requires |
|---|---|
| Publication to consumer class C | `distribution.C = allow` (or `conditional`, with conditions satisfied and recorded); verification is `owner_verified` or `contract` for every input |
| Inclusion of values in a document | additionally, `quotation_in_documents = allow` |
| Agent context | `agent_context = allow`. Otherwise agents use schemas, metadata, synthetic data, or aggregate statistics the terms permit |
| CI runners or cloud hosting | `external_processing = allow` |
| Vendor termination | a runbook step applies `post_termination_*` (delete or retain) |

## 4. Agent rules (procedural in S1)

- Agents never fetch licensed data with their own credentials, and never paste licensed values
  into prompts, issues or handoffs unless `agent_context = allow`.
- Handoffs and review bundles cite **artefact ids and hashes**, not raw values, unless rights
  allow.
- Technical enforcement (a dataset-access tool that checks rights before returning data to an
  agent) is deferred until the first licensed source arrives.

## 5. Starting position

Every source in [`registers/sources.yaml`](../../registers/sources.yaml) starts as
`verification: unverified`, with every permission `unknown`.

That includes official, public sources: central banks, treasuries, statistical agencies.
Their terms are commonly permissive (for example Creative Commons licences or public-domain
status) [EXT], but they are verified case by case in T-0002 before S1 publishes anything.
