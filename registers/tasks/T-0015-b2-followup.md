---
id: T-0015
title: "B-2 follow-up: narrow 403 UnauthorizedBlobOverwrite mapping in the Azure backend, C5 timing instrumentation in the storage probe, and a revised probe plan (one watched re-run plus step 7b)"
status: submitted_for_review   # code and plan on feat/t0015; the re-run and 7b each need the owner's "go"
owner: owner
assignee_role: "implementation engineer (Claude orchestrator; hiomux workers); independent reviewer: Codex, if the owner assigns one"
created_at: 2026-10-29
updated_at: 2026-10-29
authorised_by: OD-0134
base_revision: a71f0ff
accepted_by: null
review_required: owner (Codex review if the owner assigns one)
links:
  adrs_governing_approved: [HIO-ADR-0012]
  adrs_context_proposed: []
  specs: []
  standards: []
  findings: []
  depends_on: [T-0010 (accepted), T-0012 (accepted)]
  blocks: ["a C5 amendment decision", "Authorisation B stage B-3"]
---

# T-0015: B-2 follow-up

> **Authorised by OD-0134 item 5**, after the B-2 result (`docs/evidence/b2/README.md`) and the architect consultation
> `20261029T202344-ask-4dcb` (advice). Code and a plan only.

## Scope

| # | Work | Files | Acceptance evidence |
|---|---|---|---|
| F-1 | **`AzureBlobBackend.create`:** on the conditional create (`If-None-Match: *`), HTTP 403 with error code `UnauthorizedBlobOverwrite` becomes `BlobExists` **only after** a properties read confirms that the exact key exists. Every other 403 or authorisation failure propagates unchanged, and so does any existence check that fails or is inconclusive (the original error is raised). Nothing else in the backend changes. `BlobExists` stays a conflict signal, never proof of storage: the existing lost-response recovery (read back, single version, byte comparison) is unchanged | `src/hio/storage/azure_blob.py`, `tests/test_t0015_backend*.py` | fakes: 403 `UnauthorizedBlobOverwrite` with the key present gives `BlobExists`; the same with the key absent, or with the check failing, gives the original error; 403 `AuthorizationPermissionMismatch` and other codes propagate; 409/412 behave as before; all existing backend tests unchanged |
| F-2 | **`tools/storage_probe.py` C5 instrumentation:** for each timing create, record a **publisher-completion surrogate** taken immediately before the write (as HIO-ADR-0012 defines `completed_at`), the pre-PUT, post-PUT and post-metadata instants, and monotonic durations between them. Perform the PUT through the SDK client so that the raw response headers can be captured: `Date`, `Last-Modified`, `x-ms-version-id` and `x-ms-request-id`. Report the existing rule and the candidate amendment `floor_s(completed_at) ≤ s ≤ completed_at + δ` side by side, **both without tolerance**. Add per-observation `Date` brackets that bound the runner-to-storage clock offset (`Date − post_put` and `Date + 1 s − pre_put`). Record the runner's clock-synchronisation state if available (e.g. `timedatectl show`), and report its absence otherwise. The existing six checks stay | `tools/storage_probe.py`, `tests/test_t0015_probe*.py` | offline fakes: a floored `s` shows the candidate rule passing where the current one fails; a real violation fails both; header capture; offset brackets; missing headers reported, never invented; existing T-0012 probe tests unchanged |
| F-3 | **Revised plan** for one watched re-run (`repeats=50`) on the held probe account and for step 7b (privileged-actor immutability test of the exact retained version: deleting that version, and an overwrite which may create a new version while the retained version stays intact), then the destroy 24 hours after the last write | `docs/evidence/S1B1-B2-rerun-plan.md` (orchestrator) | proposed; each step names its "go" |

## Exclusions

A C5 amendment (an owner decision after the re-run evidence); any Azure write or dispatch without a "go"; changing
C1–C7, finality or attempt-record meanings; any other backend behaviour.

## Submission (filled by the implementer)

Branch `feat/t0015`, base `a71f0ff`. hiomux workers W7 (`321e181`, F-1) and W8 (`87ac2a7`, F-2), each `check`ed and
integrated by cherry-pick; F-3 by the orchestrator (`4cc9c36`, `docs/evidence/S1B1-B2-rerun-plan.md`, proposed).

| Item | Delivered | Evidence |
|---|---|---|
| F-1 | `_is_overwrite_refusal` + `_key_exists`: a 403 `UnauthorizedBlobOverwrite` becomes `BlobExists` only when a properties read of the exact key succeeds; otherwise the original error is raised | `tests/test_t0015_backend.py` |
| F-2 | probe C5 instrumentation: a publisher-completion surrogate before the write; pre-PUT, post-PUT and post-metadata instants; monotonic durations; raw `Date`, `Last-Modified`, version id and request id; the current and candidate rules side by side without tolerance; `Date` offset brackets; the clock-sync state | `tests/test_t0015_probe.py` |
| F-3 | the re-run plan: R-1 to R-3, 7b-1 to 7b-3, D-1 | the document |

Full suite **1000 passed**; `ruff`, `ruff format` and `check_repo` pass. Nothing has run against Azure.

## Review and acceptance
