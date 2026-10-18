---
id: HIO-STD-RIGHTS
title: Data rights and licensing
status: approved
approved_by: OD-0008   # at a82aa0d, blob 1d7296db6670
owner: HIO architecture lead (owner)
version: 0.2
last_reviewed: 2026-10-18
decision: HIO-ADR-0005
---

# Data rights and licensing (v0.2)

## 1. Rights record (per source; per dataset where terms differ)

Each permission takes the value `allow | deny | conditional(<text>) | unknown`. **`unknown`
means deny.**

| Permission | Question it answers |
|---|---|
| `automated_retrieval` | may we fetch the data by scheduled, automated access (API, file download, scraping)? |
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

## 3. Gates: operation-to-permission matrix (fail closed)

Every job checks, **before** it performs an operation, that **every input source** grants
**every** permission the operation requires.
- `unknown` and `deny` both refuse.
- `conditional(<c>)` refuses unless condition `c` is recorded as satisfied, with evidence.
- Verification must be `owner_verified` or `contract`. `unverified` and `vendor_asserted` refuse
  every operation except a one-off manual sample made for T-0002.

| Operation | Performed by | Requires |
|---|---|---|
| **fetch** (scheduled capture) | capture job | `automated_retrieval`; plus `external_processing` if it runs on a CI runner or cloud host |
| **store raw** (receipt to the bucket) | capture job | `raw_retention` (and its duration); plus `external_processing` for a cloud bucket |
| **build** (observations → releases → factors) | build job | `internal_compute`, `derivation`; plus `external_processing` on CI or cloud |
| **store derived** (release or artefact bytes) | build and publish jobs | `derived_storage`; plus `external_processing` for a cloud bucket |
| **rebuild** (reproducibility check) | CI | as **build** and **store derived**, plus `raw_retention` still valid |
| **publish to class C** | publish job | `distribution.C`; plus `quotation_in_documents` if values will be printed |
| **agent use** | any agent session | `agent_context`. Otherwise agents use metadata, schemas or synthetic data only |
| **terminate** (end of rights) | runbook | apply `post_termination_raw` / `post_termination_derived`: delete, or retain as allowed |
| **audit retain** | runbook | `audit_retention` |

**S1 fixtures (fail closed), one per operation S1 performs:** fetch, store raw, build, store
derived, rebuild, publish to `hio_internal`.
- A synthetic source whose required permission is `deny`, `unknown` or an unsatisfied
  `conditional` makes that operation **refuse**, with no partial output written.
- The same source with `allow` and `owner_verified` proceeds.

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
status) [EXT], but they are verified case by case in T-0002 **before S1 performs any operation on them, live
fetch included**, not only before publication.

## Changelog

- 0.1 (2026-10-18): initial.
- 0.2 (2026-10-18): `automated_retrieval` permission; operation-to-permission matrix covering fetch, store, build, rebuild, publish, agent, terminate and audit; fail-closed S1 fixtures (T-0008, F-REVIEW-2026-10-18-a01-5).
