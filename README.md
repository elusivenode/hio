---
id: HIO-INDEX
title: HIO planning index and staging notice
status: current
owner: HIO architecture lead (owner)
version: 0.1
last_reviewed: 2026-10-24
---

# HIO: Home Investment Office (staged planning baseline)

> **Staging notice.** HIO is a separate system from the MacDonald Family SMSF application
> (`macsmsf`), and the target `hio` repository **does not exist yet**. This directory stages
> HIO's canonical planning documents so that they are version-controlled now. Its layout mirrors
> the future repository root. Migration moves this directory **with its history** into the new
> repository (operating model §8.1), not as a plain copy or `git mv` (see [Migration](#migration)).
>
> Nothing in this directory is part of `macsmsf`. No `macsmsf` code, test, pipeline or
> deployment reads it. **`macsmsf` is not the permanent system of record for HIO.**

**Start here:** read [`AGENTS.md`](AGENTS.md), then [`STATUS.md`](STATUS.md).

## Document index (the one current plan)

| Question | Canonical document |
|---|---|
| What is HIO for? | [`docs/charter.md`](docs/charter.md) |
| What has the owner actually decided? (the only authority) | [`docs/decisions/owner/README.md`](docs/decisions/owner/README.md) |
| What does the owner need to decide for G1? | [`docs/decisions/G1-decision-package.md`](docs/decisions/G1-decision-package.md) |
| What has been proposed as architecture decisions? | [`docs/decisions/README.md`](docs/decisions/README.md) |
| How is HIO built, and what may run where? | [`docs/architecture.md`](docs/architecture.md) |
| Which return mathematics is authoritative? | [`docs/standards/return-accounting-and-factor-construction.md`](docs/standards/return-accounting-and-factor-construction.md) |
| How are observations, point-in-time knowledge and vintages represented? | [`docs/standards/observations-and-point-in-time.md`](docs/standards/observations-and-point-in-time.md) |
| How are instruments, listings, indices and futures identified? | [`docs/standards/reference-identity.md`](docs/standards/reference-identity.md) |
| What may we do with a dataset? | [`docs/standards/rights-and-licensing.md`](docs/standards/rights-and-licensing.md) |
| How are releases and artefacts built, versioned and published? | [`docs/standards/datasets-releases-and-artefacts.md`](docs/standards/datasets-releases-and-artefacts.md) |
| How is a factor specified? | [`docs/standards/factor-specification.md`](docs/standards/factor-specification.md), with specs in [`specs/factors/`](specs/factors/) |
| How do humans and agents collaborate? | [`docs/harness/operating-model.md`](docs/harness/operating-model.md) |
| What is the programme over 90 days, 18 months and five years? | [`docs/roadmap.md`](docs/roadmap.md) |
| What is the next implementation slice? | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| What is open, risky, unverified or blocked? | [`docs/risks-and-open-decisions.md`](docs/risks-and-open-decisions.md) |
| What is under construction, and what is verified? | [`STATUS.md`](STATUS.md) |
| What work is authorised, and what is queued? | [`registers/tasks/`](registers/tasks/) |
| What has been reviewed, and which findings are open? | [`reviews/README.md`](reviews/README.md) |
| What research has been proposed, tried or rejected? | [`registers/hypotheses.yaml`](registers/hypotheses.yaml), [`registers/experiments.yaml`](registers/experiments.yaml) |
| Which data sources are under consideration, and with what verified rights? | [`registers/sources.yaml`](registers/sources.yaml) |
| What happened in past sessions? | [`handoffs/`](handoffs/) |
| Why was HIO separated from `macsmsf`? (superseded inputs) | [`docs/history/`](docs/history/) |

## Relationship to `macsmsf`

| `macsmsf` artefact | Status relative to HIO |
|---|---|
| `CLAUDE.md`, `.claude/skills/*` | SMSF harness. **Not loaded for HIO work**, except where a HIO document links to it as evidence |
| `docs/investment-process-roadmap.md` | **SMSF operating roadmap** (trustee programme). Independent of HIO; integration points are listed in [`docs/roadmap.md`](docs/roadmap.md#5-smsf-integration-points) |
| `docs/adr/0003-*` (HIO-001 instrument master) | SMSF-owned, code-complete, not activated. Its boundary with HIO reference data is assessed in [HIO-ADR-0003](docs/decisions/HIO-ADR-0003-instrument-identity-boundary.md). **No HIO-001 change is approved** |
| A17 backup and promotion work, reconciliation, the quarterly pack | SMSF programme; not absorbed into HIO |

## Migration

**Not performed.** Migration happens only through an owner decision record under
[HIO-ADR-0001](docs/decisions/HIO-ADR-0001-separate-system-modular-monolith.md). It must follow
the continuity checklist in
[operating model §8.1](docs/harness/operating-model.md#81-migration-continuity-macsmsfhio--the-standalone-hio-repository):
- history preserved;
- an old→new path map;
- ids, approval states and open or waived findings unchanged;
- the migration is rejected if anything is stranded.
