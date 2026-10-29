---
id: T-0014
title: "Base-camp completion build (criteria 3-6, non-live): cash evidence and comparison dispositions, external finality evaluation records, second-copy and restore exercise, minimal consumer contract test; executed on real receipts only later, under B-3 and the soak"
status: submitted_for_review   # non-live build on feat/t0014; no real data, no Azure, no CI activation
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers); independent reviewer: Codex, if the owner assigns one"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0132
base_revision: 651eb95
accepted_by: null
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: [specs/factors/cash.aud.overnight.yaml, specs/factors/cash.usd.overnight.yaml]
  standards: [docs/standards/datasets-releases-and-artefacts.md, docs/standards/factor-specification.md, docs/standards/return-accounting-and-factor-construction.md]
  findings: []
  depends_on: [T-0009, T-0010, T-0011 (accepted)]
  blocks: ["base-camp criteria 3-6 (docs/base-camp.md, proposed)"]
---

# T-0014: base-camp completion build

> **Authorised by OD-0132 item 3.** Building and testing the machinery on synthetic inputs **does not establish
> criteria 3–6**. Each is met only by its execution on real receipts (the checklist below), which needs B-3, the soak
> and the owner decisions named there.

## Design (architect consultation `20261029T194055-ask-6296`, advice)

## Scope

| # | Work | Files (disjoint) | Acceptance evidence |
|---|---|---|---|
| P-1 | **Cash evidence report** (criterion 3): for a cutoff, from the existing `hio.jobs.s1b1` release and comparison outputs, reconcile **every** eligible period of both currencies' accruals against the publisher indices (Cash Rate TRI, SOFR Index). Classify each period as `agrees within bound`, `differs: precision`, `differs: date alignment`, `missing comparison` or `unexplained residual`. Require a written disposition slot for every non-agreeing class, and emit JSON plus a Markdown report template. It reports; it does not pass or fail. Does not change return mathematics or `s1b1.py` | `src/hio/jobs/s1b1_cash_evidence.py`, `tests/test_t0014_cash_evidence*.py` | synthetic fixtures covering each class; every eligible period appears exactly once; the report is deterministic |
| P-2 | **External finality evaluation record** (criterion 4): evaluate `hio.marketdata.finality` (C1–C7) for the exact inputs of a built release. Write one canonical, content-addressed record at `catalogue/finality/<release_id>/<evaluation_sha256>.json` holding: the release hash and cutoff, the evaluator revision, policy and spec references, the exact contributing vintages, the attempt-record ids, the C1–C7 outcomes and reasons, the aggregate verdict, and references to retained witnesses. **Not** in the manifest (circular), **no signature** (ADR-0012), never rewriting a manifest. A missing or failing evaluation means no final claim; a passing one changes no lifecycle status | `src/hio/marketdata/finality_record.py`, `src/hio/jobs/s1b1_finality.py`, `tests/test_t0014_finality*.py` | round trip; content address verified on read; every C1–C7 failure category; a missing record blocks a final claim; a manifest is byte-unchanged |
| P-3 | **Second copy and restore exercise** (criterion 5): copy a store to a second store with a hash inventory. Restore into an empty store **without access to the primary**, then rebuild releases from pinned code, specs, lockfile and cutoffs. Compare the canonical manifest and payload bytes, and the canonical catalogue rows (not DuckDB file bytes). Preserve the original provider metadata and audit references, since a copy's timestamps never replace a C5 witness. Rehearse state restoration with dummy state in an isolated directory, with no infrastructure applied. Runbook | `tools/second_copy.py`, `tools/restore_exercise.py`, `docs/engineering/recovery-runbook.md`, `tests/test_t0014_recovery*.py` | local and fake stores: a byte-identical rebuild; a tampered or missing object detected; the inventory is complete; original metadata kept |
| P-4 | **Minimal consumer contract test** (criterion 6): through `hio.publish.status.resolve_for_use`, check the exact dataset and hash pin, canonical integrity, complete lineage, and current status and rights on every use. Synthetic refusals: withdrawn, tampered, insufficient or unknown permission, missing status, broken lineage. A success must never manufacture approval on real data. Add an **inactive** CI job template for later read-only runs against a pinned real release. No API, no mandate schema, no SMSF projection, no new distribution semantics | `tests/test_t0014_consumer*.py`, `infra/workflows/consumer-contract.yml` | each refusal case; the template is inactive (outside `.github/workflows/`, no secrets) |

The orchestrator alone owns the card, `src/hio/jobs/s1b1.py`, CI activation and records.

## Exclusions

Real data, Azure or network access; activating any workflow; changing return mathematics, an approved standard,
HIO-ADR-0012 or a manifest schema's input semantics; cash-spec version changes (those come with the approval package,
after real evidence); choosing the second-copy destination.

## Execution checklist (later; each needs its own authority)

1. Under B-3 and the soak: P-1 on real receipts, with written dispositions; P-2 evaluations of the real releases.
2. The second-copy destination is the owner's decision (architect: an owner-controlled encrypted removable drive, kept
   separately; H4 S-7, within the first capture month), then P-3 runs on the real store and the state backup.
3. P-4's job is activated with authorised read-only access to a pinned real release.
4. After real evidence: the cash-spec approval package (specification standard; RA §12), then release approval for
   `hio_internal`. Each is a separate owner act.
5. Adopting base camp with "external finality evaluations satisfy criterion 4 while releases stay exploratory and
   ADR-0012's full finality obligations stay owed" is an owner decision.

## Submission (filled by the implementer)

Branch `feat/t0014`, base `651eb95`. hiomux workers W3 (`cba9c43`, P-1), W4 (`3fffe40`, P-2), W5 (`572a16d`, P-3) and W6
(`4501ffc`, P-4), each `check`ed and integrated by cherry-pick.

| Item | Delivered | Evidence |
|---|---|---|
| P-1 | `src/hio/jobs/s1b1_cash_evidence.py`: every eligible period of both currencies in exactly one of five classes, with a disposition slot for each non-agreeing class; canonical JSON and a Markdown template; no pass or fail | `tests/test_t0014_cash_evidence.py` (13) |
| P-2 | `src/hio/marketdata/finality_record.py`, `src/hio/jobs/s1b1_finality.py`: a content-addressed record at `catalogue/finality/<release_id>/<sha>.json`, verified on read; C1–C7 outcomes and the aggregate verdict; a missing record blocks a final claim; manifests byte-unchanged | `tests/test_t0014_finality*.py` (28) |
| P-3 | `tools/second_copy.py`, `tools/restore_exercise.py`, `docs/engineering/recovery-runbook.md` (proposed): copy with a hash inventory; restore without the primary; byte-identical rebuild; tamper, missing and unlisted objects detected; provider metadata preserved | `tests/test_t0014_recovery*.py` (35) |
| P-4 | `tests/test_t0014_consumer*.py` (23 cases through `resolve_for_use`); `infra/workflows/consumer-contract.yml`, inactive and manual-only, with no secrets | the tests |

Full suite: **966 passed**, plus one local failure that is T-0013's A-4 defect (an ignored `.terraform/` directory). It is
fixed on `feat/t0013` and absent in CI. `ruff`, `ruff format` and `check_repo` pass. **No criterion is established**:
each needs the execution checklist.

## Review and acceptance
