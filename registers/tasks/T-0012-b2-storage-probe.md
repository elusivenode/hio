---
id: T-0012
title: "B-2 storage-validation probe: a short-lived probe account, a manually dispatched probe workflow and script that test write-once behaviour and C5 timing against real Azure Blob Storage"
status: accepted   # OD-0128 at efb6fa1, merged into main as 01edfe9; nothing created or run in Azure (B-2 needs its own yes)
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers)"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0127
base_revision: d3ae240
accepted_by: OD-0128   # at efb6fa115ede33869f1e21c4ee6030ba35b92e28, merged into main as 01edfe9
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0010 (accepted, OD-0123), T-0011 (accepted, OD-0125)]
  blocks: ["Authorisation B stage B-3 (go-live)"]
---

# T-0012: B-2 storage-validation probe

> **Authorised by OD-0127 to build.** Creating the probe account and running the probe are Authorisation B stage B-2,
> a separate owner yes with a plan. Nothing here writes to the evidence store.

## Purpose

H4 S-6 (OD-0119) requires evidence, from real Azure, that the store behaves as HIO's write-once design and HIO-ADR-0012
§4.3.3 C5 assume. The evidence account's 3,650-day immutability would retain probe objects for a decade, so the probe uses
its own short-lived account with a one-day period, destroyed afterwards (Authorisation B package, B-2).

## Scope

| # | Work | Acceptance evidence |
|---|---|---|
| P-1 | `infra/tofu/probe/`: own resource group `rg-hio-probe`, a storage account with the evidence account's settings except immutability 1 day, a private container, its own user-assigned identity with a federated credential for the `capture` Environment (subject from a variable), its own create-only custom role on the container; local state outside the repository | `tofu fmt -check`, `tofu validate` (`-backend=false`); text-level tests like the infra tests |
| P-2 | `tools/storage_probe.py`: using `hio.storage.azure_blob.AzureBlobBackend` and `hio.storage.azure_auth`, with injectable clients: create; conditional create of the same key refused (`BlobExists`); overwrite and delete attempted by the writer **refused** (SDK client directly); version listing; and N repeated creates measuring `completed_at` against the provider `Last-Modified` (C5: `completed_at ≤ s ≤ completed_at + δ`), reporting every observation without tolerance; output one JSON report to stdout | offline tests with fakes for each check, including a C5 failure case |
| P-3 | `.github/workflows/storage-probe.yml`: `workflow_dispatch` only, `environment: capture`, `permissions: contents: read, id-token: write`, pinned actions, probe variables from `vars.*`, uploads the JSON report as a workflow artifact | text-level test: no schedule, no secrets, dispatch only |

## Exclusions

Any Azure resource creation, any run of the workflow, any write to the evidence account, any change to the accepted
backend, a C5 tolerance (an ADR-0012 change for the owner after B-2's evidence).

## Submission (filled by the implementer)

Branch `feat/t0012`, base `68697ee`, head `7cbed07` plus this section. hiomux workers P1 (`e583385`) and P2 (`e82a641`), each
`check`ed, integrated by cherry-pick; the orchestrator pinned `actions/upload-artifact` to v7.0.2 by commit SHA
(`cf430e0…`, resolved read-only from GitHub; P2 had left a marked placeholder rather than invent one) and committed the
probe's provider lock (azurerm 4.81.0, as the other modules).

| Item | Delivered | Evidence |
|---|---|---|
| P-1 | `infra/tofu/probe/`: `rg-hio-probe`, probe account (1-day Unlocked immutability, no soft delete), container `probe`, `id-hio-probe` with a `capture` federated credential, create-only role on the container; no backend block | `tests/test_t0012_infra.py`; `tofu fmt -check`, `tofu validate` pass |
| P-2 | `tools/storage_probe.py`: six checks (create, duplicate refused, overwrite refused, delete refused, one version, C5 timing over N repeats with no tolerance); JSON report; exit 0/1/2 | `tests/test_t0012_script.py` (offline fakes, pass and fail cases) |
| P-3 | `.github/workflows/storage-probe.yml`: `workflow_dispatch` only, `capture` Environment, `id-token: write`, SHA-pinned actions, report uploaded as an artifact | `tests/test_t0012_script_workflow.py` |

Full suite 868 passed; `ruff`, `ruff format`, `check_repo`, trailers pass. **Note:** a `workflow_dispatch` workflow can be
dispatched only once it is on the default branch, so running B-2 needs this branch merged into `main` first.

## Review and acceptance

Accepted by the owner on their own judgement, without a Codex review (OD-0128), at `efb6fa1`; merged into `main` as
`01edfe9` (PR #33). Running the probe is B-2, which needs a probe plan and the owner's yes.
