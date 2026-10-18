---
id: HIO-STD-SPEC
title: Factor specification standard
status: approved
approved_by: OD-0008   # at a82aa0d, blob 6d380434c320
owner: quantitative researcher (maintainer); owner (approver)
version: 0.1
last_reviewed: 2026-10-18
decision: HIO-ADR-0007
---

# Factor specification standard (v0.1)

## What a spec is

A factor spec is **versioned data** in [`specs/factors/`](../../specs/factors/), written from
[`_template.yaml`](../../specs/factors/_template.yaml). It is required **before** construction
code is written. Code implements a spec; it never defines one.

## Required content

Each section of the template must be filled. "n/a" needs a reason.

| Section | Must state |
|---|---|
| identity | `factor_id`, `version` (semver), `status`, owner, family |
| economics | the exposure in words; why it is a distinct economic risk or premium; what it is **not** |
| classification | `series_class`, `investability` (return standard §2) |
| return convention | simple or other; period; compounding; for excess returns the cash-leg `factor_id@version`; numeraire; hedging |
| observations | input `series_id`s, sources and the required `knowledge_mode` |
| availability | the `knowable_at` rule and basis per input; earliest history; capture-clock dependency |
| construction | the algorithm, in precise prose or pseudo-code; calendar and alignment; day-count; rolls and rebalancing; costs |
| invariants | the RA-INV/OBS-INV ids that apply, plus spec-specific identities |
| triangulation | references and the pre-registered expected-difference model (return standard §11) |
| limitations | proxy basis, timing, survivorship, non-market risks |
| rights | the permissions the factor needs, per consumer class |
| changelog | — |

## Versioning

| Change | Version bump |
|---|---|
| Changes any number for any date | **major** |
| Extends history or adds fields without changing existing values | **minor** |
| Wording only | **patch** |

Old major versions remain buildable while any artefact pins them.

## Status

`draft → proposed → validated → approved`.

- `validated` requires an independent review of the spec *and* of its first release.
- `approved` is set by the owner only.
